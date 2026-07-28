"""
AI MATCHMAKING AGENT ENTRY POINT (`agent.py`)
Tải và re-export MatchmakingAgent từ Cấp độ 3 ReAct Agent (`src/ai_levels/level3_reactive_agent.py`).
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.abspath(__file__), "src"))

from src.ai_levels.level3_reactive_agent import (
    MatchmakingAgent,
    parse_and_execute_tool,
    reactive_agent_process
)


def main():
    print("==========================================================")
    print("AI MATCHMAKING AGENT - BÀ MỐI AI (INTERACTIVE CLI)")
    print("==========================================================")
    print("Hệ thống ghép đôi & đánh giá tương thích chuẩn Production-grade")
    print("Gõ 'exit' hoặc 'quit' để thoát, gõ 'reset' để bắt đầu hội thoại mới.\n")

    agent = MatchmakingAgent()

    while True:
        try:
            user_input = input("Người dùng: ").strip()
            if not user_input:
                continue

            if user_input.lower() in ["exit", "quit", "thoát"]:
                print("Bà Mối AI chào tạm biệt bạn! Chúc bạn một ngày tràn đầy yêu thương!")
                break
            elif user_input.lower() in ["reset", "làm mới"]:
                agent.reset_state()
                print("Đã reset phiên hội thoại thành công!\n")
                continue

            print("\nBà Mối AI đang suy luận...")
            response = agent.process_message(user_input)
            print(f"\n{response}\n")
            print("-" * 60)

        except KeyboardInterrupt:
            print("\nTạm biệt!")
            break
        except Exception as e:
            print(f"\nLỗi hệ thống: {e}\n")


if __name__ == "__main__":
    main()
