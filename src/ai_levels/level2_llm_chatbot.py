import os
from typing import List
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

class Level2LLMCupid:
    def __init__(self, api_key: str = None, model: str = "gpt-4o-mini"):
        self.llm = ChatOpenAI(
            model=model,
            api_key=api_key or os.getenv("OPENAI_API_KEY"),
            temperature=0.7
        )
        
        # Thiết lập cá tính (Persona) cho Cupid
        self.system_prompt = SystemMessage(
            content=(
                "Bạn là Cupid - Thần Tình Yêu AI thông minh, tinh tế và hóm hỉnh. "
                "Nhiệm vụ của bạn là lắng nghe tâm sự tình cảm, đưa ra lời khuyên thả thính, "
                "hoặc giúp người dùng xây dựng mẫu trò chuyện gây ấn tượng với 'crush'. "
                "Hãy giao tiếp bằng giọng văn ấm áp, có chút hài hước nhẹ nhàng."
            )
        )
        self.history: List = [self.system_prompt]

    def chat(self, user_input: str) -> str:
        # Thêm câu hỏi của người dùng vào lịch sử
        self.history.append(HumanMessage(content=user_input))
        
        # Gọi LLM
        response = self.llm.invoke(self.history)
        
        # Lưu câu trả lời vào lịch sử
        self.history.append(AIMessage(content=response.content))
        
        return response.content