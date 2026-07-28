"""
🌐 CUPID AGENT WEB SERVER (Import từ src/ mà KHÔNG sửa codebase cũ)
"""

import json
import os
import re
import sys
import http.server
import socketserver
import urllib.parse

# Import các module từ src/ bằng cách thêm sys.path (Không sửa bất kỳ file nào trong src/)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from tools import (
    AVAILABLE_TOOLS,
    CANDIDATES_DATABASE,
    DATA_PATH,
    USER_DATABASE,
    get_user_profile,
    search_candidate_profiles,
    calculate_compatibility,
    synthesize_recommendation
)
from providers import get_llm_provider

# Khớp dòng xếp hạng đầu tiên (điểm cao nhất) mà calculate_compatibility() trả về, ví dụ:
# "- Mai: 98/100. Điểm mạnh: cùng mục tiêu ...; cùng thích .... Điểm cần lưu ý: ..."
TOP_RANKED_LINE_RE = re.compile(
    r"^- (?P<name>.+?): (?P<score>\d+)/100\. Điểm mạnh: (?P<strengths>.+?)\. Điểm cần lưu ý:",
    re.MULTILINE,
)


def _save_mockdata():
    """Ghi USER_DATABASE/CANDIDATES_DATABASE hiện tại (đang nằm trong bộ nhớ của
    module tools) trở lại config/mockdata.json, để hồ sơ người dùng mới nhập
    không bị mất khi restart server."""
    with DATA_PATH.open("w", encoding="utf-8") as f:
        json.dump(
            {"USER_DATABASE": USER_DATABASE, "CANDIDATES_DATABASE": CANDIDATES_DATABASE},
            f,
            ensure_ascii=False,
            indent=2,
        )


def _scale_to_unit(value, default=0.5):
    """Chuẩn hóa 1 câu trả lời dạng thang đo 1-5 (questions_list.json) về 0.0-1.0."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return default
    v = max(1.0, min(5.0, v))
    return round((v - 1.0) / 4.0, 2)


def _scale_to_percent(value, default=80):
    """Chuẩn hóa 1 câu trả lời dạng thang đo 1-5 về khoảng 60-95 cho radar chart."""
    return round(60 + _scale_to_unit(value, (default - 60) / 35) * 35)


def _build_user_vector(interests, goal, answers):
    """Tính vector đặc trưng [Hướng ngoại, Công nghệ, Đọc sách/Chill, Nghiêm túc]
    từ sở thích/mục tiêu người dùng nhập thật + câu trả lời khảo sát thật
    (thay vì dùng cứng 1 vector cố định cho mọi người dùng)."""
    interests_text = " ".join(interests).lower()

    tech = 0.85 if any(k in interests_text for k in ("công nghệ", "cong nghe")) else 0.35
    chill = (
        0.85
        if any(k in interests_text for k in ("đọc sách", "cà phê", "trà đạo", "thơ"))
        else 0.4
    )

    extraversion = _scale_to_unit(answers.get("social_intensity"), default=0.5)

    goal_lower = (goal or "").lower()
    seriousness_from_goal = 0.9 if "nghiêm túc" in goal_lower or "hôn" in goal_lower else 0.5
    seriousness_from_answers = _scale_to_unit(
        answers.get("individual_vs_family_values"), default=seriousness_from_goal
    )
    seriousness = round((seriousness_from_goal + seriousness_from_answers) / 2, 2)

    return [extraversion, tech, chill, seriousness]

PORT = 8000
WEB_DIR = os.path.dirname(os.path.abspath(__file__))

class CupidHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        if parsed_path.path == "/api/questions":
            questions_file = os.path.join(ROOT_DIR, "questions_list.json")
            if not os.path.exists(questions_file):
                questions_file = os.path.join(ROOT_DIR, "question_list.json")
            
            if os.path.exists(questions_file):
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                with open(questions_file, "r", encoding="utf-8") as f:
                    self.wfile.write(f.read().encode("utf-8"))
            else:
                self.send_error(404, "Questions file not found")
            return
        
        return super().do_GET()

    def do_POST(self):
        parsed_path = urllib.parse.urlparse(self.path)
        
        # ENDPOINT 1: RUN AGENT MATCHMAKING
        if parsed_path.path == "/api/run-agent":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length).decode("utf-8")
            payload = json.loads(post_data) if post_data else {}
            
            user_name = payload.get("name", "Minh")
            user_student_id = (payload.get("student_id") or "").strip() or "Chưa cập nhật"
            user_age = payload.get("age", "21")
            user_gender = payload.get("gender", "Nam")
            user_goal = payload.get("goal", "Mối quan hệ nghiêm túc")
            interests_raw = payload.get("interests", "đọc sách, cà phê yên tĩnh")
            interests = [i.strip() for i in interests_raw.split(",") if i.strip()]
            user_personality = (payload.get("personality") or "").strip() or "Chưa cập nhật"
            answers = payload.get("questionnaire_answers", {})

            # LƯU LẠI hồ sơ người dùng vừa nhập thành "current_user" thật trong
            # USER_DATABASE, rồi ghi xuống config/mockdata.json để không mất khi restart.
            # USER_DATABASE khởi đầu RỖNG (chưa có current_user nào) cho tới khi người
            # dùng nộp form lần đầu — nên hồ sơ dựng ở đây phải tự đủ mọi field bắt buộc
            # (student_id, personality, ...), không được trông chờ dữ liệu cũ còn sót lại.
            USER_DATABASE["current_user"] = {
                "student_id": user_student_id,
                "name": user_name,
                "age": user_age,
                "gender": user_gender,
                "personality": user_personality,
                "interests": interests,
                "goal": user_goal,
                "vector": _build_user_vector(interests, user_goal, answers),
            }
            _save_mockdata()

            # Chạy chuỗi ReAct Agent sử dụng các tool đã import
            obs1 = get_user_profile("current_user")
            obs2 = search_candidate_profiles(f"relationship_goal={user_goal}; interests={interests_raw}")

            # Tính tương thích với TOÀN BỘ ứng viên thật trong mockdata.json (không hard-code 1 cái tên),
            # NHƯNG loại trừ chính người dùng ra khỏi danh sách ứng viên — nếu tên họ nhập trùng tên
            # 1 ứng viên có sẵn (vd họ tự gõ "Bảo"), ứng viên đó sẽ không được tính là 1 lựa chọn để
            # tránh việc người dùng bị match với chính mình.
            user_key = user_name.strip().lower()
            eligible_candidates = [
                c for c in CANDIDATES_DATABASE if c["name"].strip().lower() != user_key
            ]
            all_candidate_names = [c["name"] for c in eligible_candidates]
            obs3 = calculate_compatibility("current_user", all_candidate_names)

            # Ứng viên đứng đầu là dòng đầu tiên (calculate_compatibility đã tự xếp hạng giảm dần)
            top_match = TOP_RANKED_LINE_RE.search(obs3)
            if top_match:
                top_name = top_match.group("name")
                top_score = int(top_match.group("score"))
                top_strengths = [
                    s.strip().capitalize()
                    for s in top_match.group("strengths").split(";")
                    if s.strip()
                ]
            else:
                top_name, top_score, top_strengths = None, 0, []

            candidate = next(
                (c for c in eligible_candidates if c["name"] == top_name), None
            )
            summary = synthesize_recommendation("current_user", top_name) if top_name else obs3

            if candidate:
                shared_topic = ", ".join(candidate["interests"][:2])
                icebreaker = (
                    f"Chào {candidate['name']}, mình thấy bạn cũng thích {shared_topic}. "
                    f"Bạn có thể kể thêm cho mình nghe một chút về điều đó không?"
                )
            else:
                icebreaker = "Chưa tìm được ứng viên phù hợp để gợi ý câu mở đầu."

            # Dùng giá trị THẬT (thang 1-5) của từng câu khảo sát thay vì chỉ kiểm tra
            # "có trả lời hay không" — trước đây dù trả lời 1 hay 5 điểm số cũng như nhau.
            radar_scores = {
                "values": _scale_to_percent(answers.get("individual_vs_family_values")),
                "communication": _scale_to_percent(answers.get("communication_frequency")),
                "lifestyle": _scale_to_percent(answers.get("social_intensity")),
                "finance": _scale_to_percent(answers.get("financial_style")),
                "career": _scale_to_percent(answers.get("career_priority")),
                "humor": 93
            }
            
            steps = [
                {
                    "step": 1,
                    "thought": f"Đọc thông tin hồ sơ và sở thích của người dùng ({user_name}, {user_age}t, {user_gender}).",
                    "action": "get_user_profile['current_user']",
                    "observation": obs1
                },
                {
                    "step": 2,
                    "thought": f"Lọc danh sách các ứng viên phù hợp với mục tiêu '{user_goal}' và sở thích '{', '.join(interests)}'.",
                    "action": f"search_candidate_profiles['goal={user_goal}']",
                    "observation": obs2
                },
                {
                    "step": 3,
                    "thought": f"Tính toán điểm tương thích Vector giữa {user_name} và toàn bộ {len(all_candidate_names)} ứng viên để xác định người phù hợp nhất.",
                    "action": f"calculate_compatibility['{user_name}', danh_sách_ứng_viên]",
                    "observation": obs3
                }
            ]

            result = {
                "user": {"name": user_name, "age": user_age, "gender": user_gender, "goal": user_goal},
                "match": {
                    "id": candidate["id"] if candidate else None,
                    "name": top_name,
                    "age": candidate["age"] if candidate else None,
                    "match_score": top_score,
                    "mbti": candidate.get("mbti", "") if candidate else "",
                    "bio": candidate.get("bio", "") if candidate else "",
                    "personality": candidate.get("personality", "") if candidate else "",
                    "strengths": top_strengths,
                    "icebreaker": icebreaker
                },
                "radar_scores": radar_scores,
                "react_steps": steps,
                "summary": summary
            }
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode("utf-8"))
            return

        # ENDPOINT 2: CHATBOT ASSISTANT FOR CUSTOM QUERIES
        if parsed_path.path == "/api/chat":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length).decode("utf-8")
            payload = json.loads(post_data) if post_data else {}
            
            user_message = payload.get("message", "").strip()
            user_name = payload.get("name", "Minh")
            
            provider = get_llm_provider()
            
            # Kiểm tra xem câu hỏi có chứa từ khóa yêu cầu lọc danh mục/tra cứu cụ thể hay không
            msg_lower = user_message.lower()
            if any(k in msg_lower for k in ["tìm", "lọc", "người", "ứng viên", "du lịch", "mèo", "công nghệ", "gặp"]):
                # Kích hoạt tool tìm kiếm thật và trả thẳng kết quả — không tự bịa thêm kết luận
                reply = search_candidate_profiles(user_message)
            else:
                # Trả lời hội thoại bằng LLM Provider
                system_prompt = (
                    f"Bạn là Cupid Agent — Trợ lý tư vấn tình cảm và ghép đôi thông minh cho {user_name}. "
                    f"Hãy trả lời thân thiện, tinh tế và đưa ra những lời khuyên hẹn hò bổ ích."
                )
                raw_response = provider.generate(user_message, system_prompt=system_prompt)
                reply = raw_response
                
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"reply": reply}, ensure_ascii=False).encode("utf-8"))
            return

        self.send_error(404, "API endpoint not found")

if __name__ == "__main__":
    print(f"🚀 CUPID AGENT WEB SERVER: http://localhost:{PORT}")
    with socketserver.TCPServer(("", PORT), CupidHTTPRequestHandler) as httpd:
        httpd.serve_forever()
