import json
import os
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

# Giả lập cơ sở dữ liệu ứng viên ghép đôi
MOCK_USER_DB = [
    {"id": 1, "name": "Minh Anh", "age": 24, "gender": "Nữ", "hobbies": ["đọc sách", "cà phê", "mèo"], "location": "Hà Nội"},
    {"id": 2, "name": "Đức Huy", "age": 27, "gender": "Nam", "hobbies": ["chơi game", "cà phê", "du lịch"], "location": "Hà Nội"},
    {"id": 3, "name": "Bảo Ngọc", "age": 22, "gender": "Nữ", "hobbies": ["vẽ tranh", "âm nhạc", "du lịch"], "location": "TP.HCM"}
]

@tool
def search_match_candidates(hobby: str, location: str) -> str:
    """Tra cứu danh sách ứng viên phù hợp dựa trên sở thích và khu vực sinh sống."""
    matched = [
        user for user in MOCK_USER_DB
        if location.lower() in user["location"].lower() and 
        any(hobby.lower() in h.lower() for h in user["hobbies"])
    ]
    if matched:
        return json.dumps(matched, ensure_ascii=False)
    return "Không tìm thấy ứng viên nào phù hợp với yêu cầu này."

class Level3ReactiveCupid:
    def __init__(self, api_key: str = None):
        llm = ChatOpenAI(
            model="gpt-4o-mini", 
            api_key=api_key or os.getenv("OPENAI_API_KEY"),
            temperature=0
        )
        
        tools = [search_match_candidates]
        
        system_prompt = (
            "Bạn là Cupid Reactive Agent. Khi người dùng muốn tìm bạn đời/đối tượng hẹn hò, "
            "bạn PHẢI gọi công cụ 'search_match_candidates' để tìm kiếm dữ liệu thực tế trước khi trả lời. "
            "Trình bày kết quả tìm được một cách sinh động."
        )
        
        self.agent_executor = create_react_agent(llm, tools, state_modifier=system_prompt)

    def run(self, user_input: str) -> str:
        messages = [{"role": "user", "content": user_input}]
        response = self.agent_executor.invoke({"messages": messages})
        return response["messages"][-1].content