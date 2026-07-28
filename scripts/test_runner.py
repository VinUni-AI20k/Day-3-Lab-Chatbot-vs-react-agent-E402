import os
import sys
import json

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from tools import AVAILABLE_TOOLS
from prompts import REACT_SYSTEM_PROMPT, MAX_ITERATIONS
from providers import get_llm_provider
from app import parse_action

def run_headless_agent(user_query: str, provider) -> dict:
    history_prompt = f"User: {user_query}\n"
    log = []
    
    for step in range(1, MAX_ITERATIONS + 1):
        response = provider.generate(history_prompt, system_prompt=REACT_SYSTEM_PROMPT)
        history_prompt += f"{response}\n"
        log.append({"step": step, "response": response})
        
        if "Final Answer:" in response:
            return {"status": "success", "log": log, "final_answer": response.split("Final Answer:")[-1].strip()}
            
        tool_name, params = parse_action(response)
        if tool_name:
            if tool_name in AVAILABLE_TOOLS:
                try:
                    tool_func = AVAILABLE_TOOLS[tool_name]
                    if isinstance(params, dict):
                        obs = tool_func(**params)
                    elif isinstance(params, (list, tuple)):
                        obs = tool_func(*params)
                    else:
                        obs = tool_func()
                except Exception as e:
                    obs = f"Lỗi khi chạy tool {tool_name}: {str(e)}"
            else:
                obs = f"Lỗi: Tool '{tool_name}' không tồn tại."
            
            history_prompt += f"Observation: {obs}\n"
            log[-1]["tool_call"] = f"{tool_name}({params})"
            log[-1]["observation"] = obs
        else:
            if "Final Answer:" not in response:
                return {"status": "error", "log": log, "error": "No Action or Final Answer"}
                
    return {"status": "timeout", "log": log, "error": "Max iterations reached"}

if __name__ == "__main__":
    provider = get_llm_provider()
    print(f"Testing with provider: {provider.__class__.__name__}")
    res = run_headless_agent("Tìm phòng Cầu Giấy dưới 4 triệu", provider)
    print(json.dumps(res, indent=2, ensure_ascii=False))
