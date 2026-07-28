"""
🧠 CẤP ĐỘ 3: REACTIVE AGENT (ReAct Agent - Thought -> Action -> Observation)
Agent suy luận đa bước, chủ động gọi công cụ (search_candidates / calculate_compatibility) và quan sát kết quả.
"""

import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tools import calculate_compatibility, search_candidates
from agent import MatchmakingAgent

def reactive_agent_process(user_query: str, agent=None) -> str:
    if agent is None:
        agent = MatchmakingAgent()
    
    print(f"🎯 User Goal: {user_query}")
    res = agent.process_message(user_query)
    return f"🧠 [Cấp 3 - ReAct Agent]:\n{res}"

if __name__ == "__main__":
    print("=== DEMO CẤP ĐỘ 3: REACTIVE MATCHMAKING AGENT ===")
    agent = MatchmakingAgent()
    q = "Đánh giá độ tương thích giữa hồ sơ C001 (Nguyễn Văn Tuấn) và C002 (Trần Thị Ngọc Bích)."
    print(reactive_agent_process(q, agent))
