import os
import sys
import json

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from tools import AVAILABLE_TOOLS
from prompts import REACT_SYSTEM_PROMPT, MAX_ITERATIONS, MAX_REPEATED_ACTIONS
from providers import get_llm_provider
from agent_protocol import extract_final_answer, parse_action

def run_headless_agent(user_query: str, provider) -> dict:
    history_prompt = f"User: {user_query}\n"
    log = []
    action_counts = {}
    
    for step in range(1, MAX_ITERATIONS + 1):
        response = provider.generate(history_prompt, system_prompt=REACT_SYSTEM_PROMPT)
        history_prompt += f"{response}\n"
        log.append({"step": step, "response": response})
        
        final_answer = extract_final_answer(response)
        if final_answer is not None:
            if not final_answer:
                return {"status": "error", "log": log, "error": "Empty Final Answer"}
            return {"status": "success", "log": log, "final_answer": final_answer}
            
        tool_name, params = parse_action(response)
        if tool_name:
            action_key = (tool_name, repr(params))
            action_counts[action_key] = action_counts.get(action_key, 0) + 1
            if action_counts[action_key] > MAX_REPEATED_ACTIONS:
                return {"status": "error", "log": log, "error": "Repeated action"}

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
                    obs = f"LỖI: Không thể chạy tool {tool_name}: {str(e)}"
            else:
                obs = f"LỖI: Tool '{tool_name}' không tồn tại."
            
            history_prompt += f"Observation: {obs}\n"
            log[-1]["tool_call"] = f"{tool_name}({params})"
            log[-1]["observation"] = obs
        else:
            return {"status": "error", "log": log, "error": "No Action or Final Answer"}
                
    return {"status": "timeout", "log": log, "error": "Max iterations reached"}

if __name__ == "__main__":
    provider = get_llm_provider()
    print(f"Testing with provider: {provider.__class__.__name__}")
    res = run_headless_agent("Tìm phòng Cầu Giấy dưới 4 triệu", provider)
    print(json.dumps(res, indent=2, ensure_ascii=False))
