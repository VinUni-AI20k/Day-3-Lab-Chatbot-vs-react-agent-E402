import json
import os
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

# Tools hỗ trợ cho quy trình tự trị
@tool
def search_candidates(location: str) -> str:
    """Tìm kiếm danh sách các đối tượng đang độc thân tại một địa điểm."""
    candidates = [
        {"name": "Thanh Thảo", "age": 23, "hobbies": ["cà phê sách", "mèo", "chụp ảnh"], "location": "Hà Nội"},
        {"name": "Tuấn Kiệt", "age": 26, "hobbies": ["chạy bộ", "cà phê", "công nghệ"], "location": "Hà Nội"}
    ]
    return json.dumps(candidates, ensure_ascii=False)

@tool
def calculate_compatibility_score(user_hobbies: str, candidate_hobbies: str) -> str:
    """Phân tích và tính toán % độ tương thích giữa người dùng và ứng viên."""
    # Giả lập logic tính điểm dựa trên độ trùng lặp sở thích
    return "Độ tương thích: 85%. Lý do: Cả hai đều cùng thích không gian cà phê và có lối sống trải nghiệm."

@tool
def suggest_date_plan(hobby: str, location: str) -> str:
    """Lên gợi ý địa điểm và kế hoạch hẹn hò chi tiết."""
    return f"Gợi ý cho buổi hẹn tại {location}: Gặp nhau tại Quán Cà Phê Sách Nhã Nam, sau đó đi dạo hồ và chụp ảnh."

class Level4AutonomousCupid:
    def __init__(self, api_key: str = None):
        llm = ChatOpenAI(
            model="gpt-4o-mini", 
            api_key=api_key or os.getenv("OPENAI_API_KEY"),
            temperature=0.3
        )
        
        tools = [search_candidates, calculate_compatibility_score, suggest_date_plan]
        
        system_prompt = (
            "Bạn là Cupid Autonomous Agent - Thần Tình Yêu AI Tự Trị Nâng Cao.\n"
            "Khi nhận yêu cầu ghép đôi phức tạp từ người dùng, bạn hãy thực hiện theo quy trình 3 bước tự động:\n"
            "1. **Tự lập kế hoạch**: Phân tích thông tin người dùng.\n"
            "2. **Thực thi chuỗi công cụ**: "
            "   - Sử dụng `search_candidates` để lấy danh sách.\n"
            "   - Sử dụng `calculate_compatibility_score` để đánh giá độ hợp nhau.\n"
            "   - Sử dụng `suggest_date_plan` để thiết kế buổi hẹn hoàn chỉnh.\n"
            "3. **Đánh giá & Tổng hợp**: Tạo ra một 'Báo Cáo Ghép Đôi & Kế Hoạch Hẹn Hò' chỉn chu, chi tiết cho người dùng."
        )
        
        self.agent = create_react_agent(llm, tools, state_modifier=system_prompt)

    def execute_plan(self, user_request: str) -> str:
        messages = [{"role": "user", "content": user_request}]
        result = self.agent.invoke({"messages": messages})
        return result["messages"][-1].content