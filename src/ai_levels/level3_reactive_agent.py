"""
🧠 CẤP ĐỘ 3: REACTIVE AGENT (ReAct Agent - Thought -> Action -> Observation)
Agent biết suy nghĩ, tự ra quyết định gọi Tool thực tế và quan sát kết quả để trả lời.
"""

import json

# Định nghĩa Tool thực tế
def get_weather(city: str) -> str:
    return f"Thời tiết tại {city}: 28°C, Nắng nhẹ, Độ ẩm 65%."

def search_flights(origin: str, destination: str) -> str:
    return f"Chuyến bay {origin} -> {destination}: Vé VN123 giá 1.500.000 VNĐ."

def reactive_agent_step(user_goal: str):
    print(f"🎯 Goal: {user_goal}")
    
    # Bước 1: Thought & Action gọi weather tool
    print("\n🧠 [Thought 1]: Cần kiểm tra thời tiết thực tế trước.")
    print("🛠️ [Action 1] : get_weather('Hà Nội')")
    obs1 = get_weather("Hà Nội")
    print(f"👁️ [Observation 1]: {obs1}")
    
    # Bước 2: Thought & Final Answer
    print("\n🧠 [Thought 2]: Đã có dữ liệu thời tiết 28°C nắng nhẹ. Đưa ra câu trả lời.")
    print(f"🏁 [Final Answer]: Thời tiết Hà Nội hôm nay 28°C nắng nhẹ. Bạn nên mặc áo phông thoáng mát!")

if __name__ == "__main__":
    print("=== DEMO CẤP ĐỘ 3: REACTIVE AGENT (ReAct Loop) ===")
    reactive_agent_step("Thời tiết Hà Nội hôm nay thế nào và nên mặc gì?")
