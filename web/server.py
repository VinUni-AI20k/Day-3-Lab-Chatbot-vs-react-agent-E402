"""
🌐 CUPID AGENT WEB SERVER (Import từ src/ mà KHÔNG sửa codebase cũ)
"""

import json
import os
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
    get_user_profile,
    search_candidate_profiles,
    calculate_compatibility,
    synthesize_recommendation
)
from providers import get_llm_provider

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
            user_age = payload.get("age", "21")
            user_gender = payload.get("gender", "Nam")
            user_goal = payload.get("goal", "Mối quan hệ nghiêm túc")
            interests = payload.get("interests", "đọc sách, cà phê yên tĩnh")
            answers = payload.get("questionnaire_answers", {})
            
            # Chạy chuỗi ReAct Agent sử dụng các tool đã import
            obs1 = get_user_profile("current_user")
            obs2 = search_candidate_profiles(f"relationship_goal={user_goal}; interests={interests}")
            obs3 = calculate_compatibility(user_name, "Mai")
            summary = synthesize_recommendation(user_name, "Mai")
            
            radar_scores = {
                "values": 95 if answers.get("individual_vs_family_values") else 90,
                "communication": 92 if answers.get("communication_frequency") else 88,
                "lifestyle": 89 if answers.get("social_intensity") else 85,
                "finance": 91 if answers.get("financial_style") else 87,
                "career": 90 if answers.get("career_priority") else 86,
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
                    "thought": f"Lọc danh sách các ứng viên phù hợp với mục tiêu '{user_goal}' và sở thích '{interests}'.",
                    "action": f"search_candidate_profiles['goal={user_goal}']",
                    "observation": obs2
                },
                {
                    "step": 3,
                    "thought": f"Tính toán điểm tương thích Vector giữa {user_name} và ứng viên xuất sắc nhất (Mai).",
                    "action": f"calculate_compatibility['{user_name}', 'Mai']",
                    "observation": obs3
                }
            ]
            
            result = {
                "user": {"name": user_name, "age": user_age, "gender": user_gender, "goal": user_goal},
                "match": {
                    "id": "cand_01",
                    "name": "Mai",
                    "age": 22,
                    "match_score": 91,
                    "mbti": "INFJ",
                    "bio": "Hướng nội vừa phải, tinh tế, yêu sách & không gian cà phê yên tĩnh.",
                    "strengths": ["Cùng mục tiêu nghiêm túc", "Cùng thích đọc sách & cà phê", "Phong cách giao tiếp nhẹ nhàng"],
                    "icebreaker": f"Chào Mai, mình thấy bạn cũng thích không gian cà phê yên tĩnh và đọc sách. Dạo này bạn đang đọc cuốn sách nào hay không?"
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
                # Kích hoạt ReAct Agent Search Tool
                obs = search_candidate_profiles(user_message)
                reply = (
                    f"🧠 **[Cupid ReAct Agent]**: Đã kích hoạt công cụ `search_candidate_profiles['{user_message}']`.\n\n"
                    f"👁️ **Observation**: {obs}\n\n"
                    f"🏁 **Tư vấn Agent**: Dựa trên tiêu chí '{user_message}', Mai (22t, INFJ) và Lan (21t) là những lựa chọn phù hợp nhất!"
                )
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
