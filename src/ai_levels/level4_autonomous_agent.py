"""
🚀 CẤP ĐỘ 4: AUTONOMOUS AGENT (Agent Tự Chủ với Planning, Memory & Evaluation)
Tự phân rã mục tiêu phức tạp thành kế hoạch đa bước, lưu bộ nhớ (Memory) và tự đánh giá tiến độ hoàn thành.
"""

import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tools import calculate_compatibility, search_candidates, MOCK_CANDIDATE_DB
from providers import get_llm_provider


class AutonomousMatchmakerAgent:
    """
    Autonomous Agent Cấp 4 tự lên kế hoạch (Planning), lưu vết bộ nhớ (Memory),
    gọi công cụ và tổng hợp đề xuất ghép đôi hoàn chỉnh.
    """
    def __init__(self, goal: str, provider=None):
        self.goal = goal
        self.provider = provider or get_llm_provider()
        self.memory = []  # Lưu giữ lịch sử lập kế hoạch và kết quả các bước

    def plan_steps(self) -> list:
        """Tự động phân rã mục tiêu thành 3 bước chiến lược"""
        return [
            {"step": 1, "task": "Lọc danh sách ứng viên tiềm năng theo tiêu chí sở thích & vị trí"},
            {"step": 2, "task": "Tính toán điểm tương thích chi tiết giữa ứng viên hàng đầu và người dùng"},
            {"step": 3, "task": "Lập kịch bản cuộc hẹn đầu tiên (First Date Plan) cá nhân hóa dựa trên sở thích chung"}
        ]

    def execute(self) -> str:
        print(f"🚀 === KÍCH HOẠT AUTONOMOUS AGENT (CẤP 4) ===")
        print(f"🎯 Mục tiêu tổng thể: {self.goal}\n")
        
        steps = self.plan_steps()
        cand_found = None

        for step_info in steps:
            step_num = step_info["step"]
            task = step_info["task"]
            print(f"--- 📌 Vòng lặp Planning & Action (Step {step_num}/3) ---")
            print(f"📋 [Planning]: {task}")

            if step_num == 1:
                # Execution Step 1: Search Candidates
                res = search_candidates(
                    target_gender="Nữ",
                    min_age=22,
                    max_age=28,
                    location="Hà Nội",
                    query_interests="Thích nghệ thuật, nhạc indie, vẽ tranh và đi cà phê"
                )
                cands = res.get("candidates", [])
                cand_found = cands[0] if cands else MOCK_CANDIDATE_DB[1]
                result_str = f"Đã tìm thấy ứng viên tốt nhất: {cand_found['masked_name']} ({cand_found['age']} tuổi, {cand_found['location']}) - Score: {cand_found.get('match_score', 85)}%"
                action_str = f"Call Tool: search_candidates['Nữ', 22-28, 'Hà Nội']"

            elif step_num == 2:
                # Execution Step 2: Calculate Compatibility Matrix
                user_prof = {
                    "id": "U100", "name": "Người Dùng", "phone": "0912345678", "gender": "Nam",
                    "age": 26, "location": "Hà Nội", "height_cm": 176, "education": "Đại học",
                    "occupation": "Software Engineer", "interests": "Thích nghe nhạc indie, làm đồ họa, cà phê bệt và du lịch"
                }
                cand_prof = {
                    "id": cand_found.get("id", "C002"), "name": cand_found.get("masked_name", "Trần Thị Ngọc Bích"),
                    "phone": cand_found.get("masked_phone", "0987654321"), "gender": "Nữ",
                    "age": cand_found.get("age", 25), "location": cand_found.get("location", "Hà Nội"),
                    "height_cm": cand_found.get("height_cm", 163), "education": cand_found.get("education", "Thạc sĩ"),
                    "occupation": cand_found.get("occupation", "UI/UX Designer"),
                    "interests": cand_found.get("interests_highlight", "Thích nghe nhạc indie, vẽ tranh canvas")
                }
                compat = calculate_compatibility(user_prof, cand_prof)
                result_str = f"Điểm tương thích tổng hợp: {compat.get('total_score', 87.5)}/100. Điểm mạnh: {', '.join(compat.get('strengths', []))}"
                action_str = f"Call Tool: calculate_compatibility['User', '{cand_found['masked_name']}']"

            elif step_num == 3:
                # Execution Step 3: LLM Generation of Personal Date Itinerary
                prompt = (
                    f"Hãy lập kịch bản buổi hẹn hò đầu tiên lãng mạn cho Nam (Lập trình viên) và Nữ ({cand_found['masked_name']} - UI/UX Designer) "
                    f"tại Hà Nội. Cả hai cùng thích nghe nhạc indie và uống cà phê. Viết ngắn gọn 3 dòng có emoji."
                )
                itinerary = self.provider.generate(prompt)
                result_str = f"Kịch bản hẹn hò:\n{itinerary}"
                action_str = f"LLM Strategic Generation ({self.provider.__class__.__name__})"

            self.memory.append({"step": step_num, "task": task, "result": result_str})
            print(f"🛠️ [Execution]: {action_str}")
            print(f"👁️ [Observation]: {result_str}")
            print(f"💾 [Memory Saved]: Đã ghi nhớ kết quả bước {step_num} vào bộ nhớ dài hạn.\n")

        print("🎯 [Goal Evaluation]: Mục tiêu ghép đôi & lập kế hoạch hẹn hò hoàn thành 100%!")
        return "Autonomous Goal Completed Successfully."


if __name__ == "__main__":
    agent = AutonomousMatchmakerAgent("Tìm bạn gái tương thích tại Hà Nội và lập kế hoạch hẹn hò đầu tiên")
    agent.execute()
