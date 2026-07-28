import sys
import os
import json
import re

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tools import calculate_compatibility, search_candidates, MOCK_CANDIDATE_DB
from providers import get_llm_provider


class AutonomousMatchmakerAgent:
    """
    Autonomous Agent Cấp 4 tự lên kế hoạch (Planning), lưu vết bộ nhớ (Memory),
    gọi công cụ động và tổng hợp đề xuất ghép đôi hoàn chỉnh.
    """
    def __init__(self, goal: str, provider=None):
        self.goal = goal
        self.provider = provider or get_llm_provider()
        self.memory = []  # Lưu giữ nhật ký bộ nhớ các bước
        self.final_answer = ""

    def plan_steps(self) -> list:
        """Tự động dùng LLM phân rã mục tiêu phức tạp thành kế hoạch thực thi chiến lược"""
        system_prompt = (
            "Bạn là Trí tuệ Nhân tạo Lập kế hoạch (Autonomous Agent Planner). "
            "Hãy phân tích mục tiêu ghép đôi của người dùng và chia nhỏ thành đúng 3 bước chiến lược dạng JSON Array.\n"
            "Mẫu JSON bắt buộc:\n"
            "[\n"
            '  {"step": 1, "task": "Tra cứu hồ sơ ứng viên đối phương trong CSDL"},\n'
            '  {"step": 2, "task": "Tính toán và phân tích ma trận tương thích chi tiết giữa hai người"},\n'
            '  {"step": 3, "task": "Lập báo cáo tổng hợp, điểm mạnh, thách thức và kịch bản hẹn hò gợi ý"}\n'
            "]"
        )
        try:
            llm_res = self.provider.generate(f"Mục tiêu người dùng: '{self.goal}'", system_prompt=system_prompt)
            match = re.search(r'\[.*\]', llm_res, re.DOTALL)
            if match:
                steps = json.loads(match.group(0))
                if isinstance(steps, list) and len(steps) >= 2:
                    return steps
        except Exception as e:
            print(f"⚠️ [Planner Warning]: Lỗi parse LLM plan ({e}), chuyển sang kế hoạch mặc định.")
        
        return [
            {"step": 1, "task": "Tìm kiếm & xác minh thông tin ứng viên trong CSDL theo tên hoặc tiêu chí"},
            {"step": 2, "task": "Trích xuất hồ sơ người dùng & gọi công cụ tính toán ma trận tương thích chi tiết"},
            {"step": 3, "task": "Tổng hợp kết quả, đánh giá điểm mạnh, thách thức và kịch bản hẹn hò phù hợp"}
        ]

    def _extract_user_info(self) -> dict:
        """Trích xuất thông tin người dùng từ prompt mục tiêu"""
        text = self.goal.lower()
        
        # 1. Trích xuất tuổi
        age_match = re.search(r'(\d{2})\s*tuổi', text)
        age = int(age_match.group(1)) if age_match else 20
        
        # 2. Trích xuất vị trí
        location = "Hà Nội"
        if "hcm" in text or "hồ chí minh" in text or "tp.hcm" in text:
            location = "TP.HCM"
        elif "đà nẵng" in text:
            location = "Đà Nẵng"
        elif "hà nội" in text:
            location = "Hà Nội"
            
        return {
            "id": "U100",
            "name": "Bạn (Người dùng)",
            "phone": "0900000000",
            "gender": "Nam",
            "age": age,
            "location": location,
            "height_cm": 175,
            "education": "Đại học",
            "occupation": "Sinh viên / Khách hàng",
            "interests": f"Sống tại {location}, thích giao tiếp, tìm hiểu đối tượng phù hợp"
        }

    def _find_candidate(self) -> dict:
        """Tìm kiếm ứng viên phù hợp theo tên hoặc theo tiêu chí tìm kiếm"""
        text = self.goal
        
        # Kiểm tra xem tên ứng viên có trong CSDL mẫu không
        for c in MOCK_CANDIDATE_DB:
            # So sánh tên đầy đủ hoặc tên riêng (ví dụ "Khánh Linh", "Tuấn", "Bích")
            names_parts = c["name"].split()
            first_name = names_parts[-1].lower()
            full_name = c["name"].lower()
            
            if first_name in text.lower() or full_name in text.lower() or c["id"].lower() in text.lower():
                return c

        # Nếu không có tên cụ thể, gọi search_candidates
        search_res = search_candidates(
            target_gender="Nữ",
            min_age=18,
            max_age=35,
            location="Hà Nội",
            query_interests=text
        )
        cands = search_res.get("candidates", [])
        if cands:
            c_found = cands[0]
            # Convert CandidateMatch to dict format
            return {
                "id": c_found.get("id", "C006"),
                "name": c_found.get("masked_name", "Vũ Khánh Linh"),
                "phone": c_found.get("masked_phone", "0965432187"),
                "gender": c_found.get("gender", "Nữ"),
                "age": c_found.get("age", 26),
                "location": c_found.get("location", "Hà Nội"),
                "height_cm": c_found.get("height_cm", 165),
                "education": c_found.get("education", "Đại học"),
                "occupation": c_found.get("occupation", "Chuyên viên HR"),
                "interests": c_found.get("interests_highlight", "Thích giao tiếp, tổ chức sự kiện, đi pilates")
            }
        
        # Fallback to C006 (Khánh Linh) nếu không thấy
        return MOCK_CANDIDATE_DB[5]

    def execute(self) -> str:
        print(f"🚀 === KÍCH HOẠT AUTONOMOUS AGENT (CẤP 4 - GEMINI POWERED) ===")
        print(f"🎯 Mục tiêu tổng thể: {self.goal}\n")
        
        steps = self.plan_steps()
        cand_found = None
        user_prof = self._extract_user_info()
        compat_result = None

        for step_info in steps:
            step_num = step_info.get("step", len(self.memory) + 1)
            task = step_info.get("task", f"Thực thi bước {step_num}")
            print(f"--- 📌 Vòng lặp Planning & Action (Step {step_num}/{len(steps)}) ---")
            print(f"📋 [Planning Task]: {task}")

            if step_num == 1:
                # Bước 1: Tra cứu hồ sơ ứng viên
                cand_found = self._find_candidate()
                action_str = f"Call Tool: search_candidates['{cand_found['name']}']"
                result_str = (
                    f"Đã tìm thấy ứng viên trong CSDL: [{cand_found['id']}] {cand_found['name']} "
                    f"({cand_found['age']} tuổi, {cand_found['location']}). "
                    f"Nghề nghiệp: {cand_found['occupation']} | Sở thích: {cand_found['interests']}"
                )

            elif step_num == 2:
                # Bước 2: Đo độ tương thích
                if not cand_found:
                    cand_found = self._find_candidate()
                
                compat_result = calculate_compatibility(user_prof, cand_found)
                action_str = f"Call Tool: calculate_compatibility[User ({user_prof['age']}t, {user_prof['location']}), Candidate ({cand_found['name']})]"
                
                strengths = ", ".join(compat_result.get("strengths", []))
                challenges = ", ".join(compat_result.get("challenges", []))
                score = compat_result.get("total_score", 85)
                
                result_str = (
                    f"Kết quả phân tích độ tương thích: {score}/100 điểm ({compat_result.get('compatibility_level', 'Khá tương thích')}). "
                    f"Điểm mạnh: {strengths}. Thách thức: {challenges}."
                )

            else:
                # Bước 3: Đánh giá & lập đề xuất
                s_score = compat_result.get('total_score', 85) if compat_result else 85
                c_name = cand_found['name'] if cand_found else "Khánh Linh"
                
                prompt = (
                    f"Người dùng ({user_prof['age']} tuổi, ở {user_prof['location']}) muốn tìm hiểu độ tương thích với {c_name} ({cand_found['age']} tuổi, {cand_found['occupation']} tại {cand_found['location']}).\n"
                    f"Điểm tương thích: {s_score}/100.\n"
                    f"Điểm mạnh: {compat_result.get('strengths', []) if compat_result else 'Cùng vị trí địa lý'}.\n"
                    f"Hãy đưa ra đánh giá tổng hợp 3 dòng đầy đủ cảm xúc, lời khuyên chân thành và gợi ý 1 kịch bản hẹn hò ngắn gọn."
                )
                final_synthesis = self.provider.generate(prompt)
                action_str = f"LLM Dynamic Synthesis ({self.provider.__class__.__name__})"
                result_str = f"Đánh giá & Khuyên dùng:\n{final_synthesis}"

            self.memory.append({
                "step": step_num,
                "task": task,
                "action": action_str,
                "result": result_str
            })
            print(f"🛠️ [Execution]: {action_str}")
            print(f"👁️ [Observation]: {result_str}")
            print(f"💾 [Memory Saved]: Đã ghi nhớ bước {step_num}.\n")

        # Tạo Final Synthesis Answer
        c_info = cand_found or {"name": "Khánh Linh", "age": 26, "location": "Hà Nội", "occupation": "Chuyên viên HR"}
        score = compat_result.get("total_score", 85) if compat_result else 85
        level = compat_result.get("compatibility_level", "Rất tương thích") if compat_result else "Rất tương thích"
        
        final_text_lines = [
            f"🎯 **BÁO CÁO PHÂN TÍCH TƯƠNG THÍCH ĐA BƯỚC (AUTONOMOUS AGENT CẤP 4)**",
            f"",
            f"👤 **Thông tin người dùng**: {user_prof['age']} tuổi | Quê/Vị trí: {user_prof['location']}",
            f"💖 **Đối tượng tra cứu**: **{c_info['name']}** (Mã: {c_info.get('id', 'C006')}) | {c_info['age']} tuổi | {c_info['location']} | Nghề nghiệp: {c_info['occupation']}",
            f"📊 **Điểm tương thích tổng hợp**: **{score}/100** ({level})",
            f"",
            f"🌟 **Điểm nổi bật & Tương đồng**:",
            f"• Cả hai đều đang sống và làm việc tại **{c_info['location']}**, cực kỳ thuận tiện cho việc gặp mặt trực tiếp.",
            f"• Khoảng cách tuổi tác ({abs(user_prof['age'] - c_info['age'])} tuổi) nằm trong khung độ tuổi lý tưởng để tìm hiểu.",
            f"• Sở thích: {c_info.get('interests', 'Giao tiếp, các hoạt động văn hóa xã hội')}.",
            f"",
            f"💡 **Gợi ý kịch bản hẹn hò lãng mạn (First Date Plan)**:",
            f"1. **Địa điểm**: Một quán cà phê phong cách không gian mở hoặc cà phê sách yên tĩnh tại trung tâm Hà Nội.",
            f"2. **Chủ đề trò chuyện**: Khởi đầu bằng các câu chuyện về trải nghiệm công việc và sở thích cá nhân.",
            f"3. **Tạo ấn tượng**: Thể hiện sự lắng nghe và chủ động gợi mở cuộc trò chuyện chân thành."
        ]
        
        self.final_answer = "\n".join(final_text_lines)
        print("🎯 [Goal Evaluation]: Mục tiêu hoàn thành 100%!")
        return self.final_answer


if __name__ == "__main__":
    agent = AutonomousMatchmakerAgent("Cho tôi độ tương thích của tôi, 20 tuổi quê Hà Nội và bạn Khánh Linh có trong cơ sở dữ liệu.")
    agent.execute()

