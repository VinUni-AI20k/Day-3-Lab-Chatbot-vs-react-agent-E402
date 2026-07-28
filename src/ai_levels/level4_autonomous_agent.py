"""
🚀 CẤP ĐỘ 4: AUTONOMOUS AGENT (Agent tự chủ với Planning & Memory)
Tự chia nhỏ mục tiêu phức tạp thành nhiều bước, duy trì bộ nhớ (Memory) và tự đánh giá tiến độ.
"""

class AutonomousGoalAgent:
    def __init__(self, goal: str, max_steps: int = 4):
        self.goal = goal
        self.max_steps = max_steps
        self.memory = []  # Bộ nhớ lưu vết các bước đã thực hiện
        
    def execute(self):
        print(f"🚀 === Bắt đầu Autonomous Goal: {self.goal} ===")
        
        for step in range(1, self.max_steps + 1):
            print(f"\n--- Vòng lặp tự chủ Planning & Action (Step {step}/{self.max_steps}) ---")
            
            if step == 1:
                plan = "Bước 1: Tra cứu lịch rảnh và thời tiết điểm đến"
                action = "Call Tool: get_weather('Hà Nội')"
                result = "Hà Nội 28°C, nắng nhẹ."
            elif step == 2:
                plan = "Bước 2: Tìm chuyến bay phù hợp với ngân sách"
                action = "Call Tool: search_flights('TP.HCM', 'Hà Nội')"
                result = "Chuyến bay VN123 giá 1.500.000 VNĐ."
            elif step == 3:
                plan = "Bước 3: Tổng hợp lập lịch trình 3 ngày 2 đêm"
                action = "Generate Itinerary"
                result = "Lịch trình hoàn tất: Khách sạn + Quán cafe sống ảo."
            else:
                print("🎯 [Goal Evaluation]: Mục tiêu đã hoàn thành 100%!")
                break
                
            self.memory.append({"step": step, "plan": plan, "result": result})
            print(f"📋 [Planning]: {plan}")
            print(f"🛠️ [Execution]: {action} ➔ {result}")
            print(f"💾 [Memory Saved]: Logged step {step} to memory.")

if __name__ == "__main__":
    agent = AutonomousGoalAgent("Lên kế hoạch du lịch Hà Nội 3 ngày 2 đêm")
    agent.execute()
