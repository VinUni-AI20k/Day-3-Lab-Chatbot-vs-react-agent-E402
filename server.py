"""
🌐 WEB APP SERVER & API FOR SMART RETURN ASSISTANT
Chạy file này để khởi chạy giao diện UI & Live Backend API: python server.py
"""

import http.server
import socketserver
import webbrowser
import os
import sys
import json
from dotenv import load_dotenv

# Đảm bảo import src/
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

load_dotenv(override=True)

from providers import get_llm_provider, MockProvider
from prompts import REACT_SYSTEM_PROMPT, MAX_ITERATIONS
from app import plan_next_step, parse_action, execute_tool, safe_json_loads

PORT = 8000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))


def run_live_agent_api(user_query: str):
    """Thực thi ReAct Agent và trả về mảng các bước Thought, Action, Observation, Final Answer"""
    load_dotenv(override=True)
    provider = get_llm_provider()
    is_mock = isinstance(provider, MockProvider)
    provider_info = f"{provider.__class__.__name__} ({getattr(provider, 'model_name', 'Offline Mock Mode')})"

    observations = []
    action_history = set()
    steps = []
    finished = False

    for step in range(1, MAX_ITERATIONS + 1):
        if not is_mock:
            history_prompt = f"User Question: {user_query}\n"
            for obs in observations:
                history_prompt += f"\nAction: {obs['tool_name']}{obs['args']}\nObservation: {obs['raw']}\n"
            
            agent_output = provider.generate(history_prompt, system_prompt=REACT_SYSTEM_PROMPT) or ""
            if not agent_output or (agent_output.startswith("[") and ("Exception" in agent_output or "Error" in agent_output)):
                agent_output = plan_next_step(user_query, observations)
        else:
            agent_output = plan_next_step(user_query, observations)

        # Trích xuất Thought
        thought = ""
        if "Thought:" in agent_output:
            thought_part = agent_output.split("Thought:")[1]
            if "Action:" in thought_part:
                thought = thought_part.split("Action:")[0].strip()
            elif "Final Answer:" in thought_part:
                thought = thought_part.split("Final Answer:")[0].strip()
            else:
                thought = thought_part.strip()
        else:
            thought = agent_output

        # Trích xuất Final Answer
        if "Final Answer:" in agent_output:
            final = agent_output.split("Final Answer:")[1].strip()
            steps.append({
                "step": step,
                "thought": thought,
                "final": final
            })
            finished = True
            break

        # Parse Action
        parsed = parse_action(agent_output)
        if not parsed:
            obs_text = '{"status":"error","message":"Không parse được Action."}'
            observations.append({"tool_name": "parser", "args": [], "raw": obs_text})
            steps.append({
                "step": step,
                "thought": thought,
                "action": "unknown",
                "observation": obs_text,
                "toolName": "parser",
                "toolStatus": "error"
            })
            continue

        tool_name, args = parsed
        action_key = (tool_name, tuple(args))

        if action_key in action_history:
            steps.append({
                "step": step,
                "thought": "🛡️ Guardrail: Agent bị lặp lại cùng Action.",
                "final": "Mình đang bị kẹt ở cùng một bước xử lý, nên sẽ dừng an toàn."
            })
            finished = True
            break

        action_history.add(action_key)
        obs_text = execute_tool(tool_name, args)
        obs_data = safe_json_loads(obs_text)
        status = obs_data.get("status", "success") if isinstance(obs_data, dict) else "success"

        observations.append({
            "tool_name": tool_name,
            "args": args,
            "raw": obs_text,
            "data": obs_data
        })

        steps.append({
            "step": step,
            "thought": thought,
            "action": f"{tool_name}{args}",
            "observation": obs_text,
            "toolName": tool_name,
            "toolStatus": status
        })

    if not finished and len(steps) < MAX_ITERATIONS:
        steps.append({
            "step": MAX_ITERATIONS,
            "thought": "Đã đạt tối đa bước xử lý.",
            "final": "Mình chưa thể hoàn tất yêu cầu trong giới hạn xử lý an toàn."
        })

    return {
        "provider": provider_info,
        "is_mock": is_mock,
        "query": user_query,
        "iterations_used": len([s for s in steps if "action" in s]) + (1 if any("final" in s for s in steps) else 0),
        "steps": steps
    }


class LiveHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        if self.path == "/api/info":
            load_dotenv(override=True)
            p = get_llm_provider()
            info = f"{p.__class__.__name__} ({getattr(p, 'model_name', 'Offline Mock Mode')})"
            res = json.dumps({"provider": info, "is_mock": isinstance(p, MockProvider)}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(res)))
            self.end_headers()
            self.wfile.write(res)
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == "/api/chat":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            try:
                data = json.loads(body)
                query = data.get("query", "")
                result = run_live_agent_api(query)
                res_bytes = json.dumps(result, ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(res_bytes)))
                self.end_headers()
                self.wfile.write(res_bytes)
            except Exception as e:
                err_res = json.dumps({"error": str(e)}).encode("utf-8")
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(err_res)
        else:
            self.send_response(404)
            self.end_headers()


if __name__ == "__main__":
    url = f"http://localhost:{PORT}"
    print("==================================================")
    print("🚀 ĐANG KHỞI CHẠY GIAO DIỆN SMART RETURN ASSISTANT UI")
    print("==================================================")
    print(f"🔗 Mở trình duyệt tại: {url}")
    print("Press Ctrl+C to stop the web server.\n")

    try:
        webbrowser.open(url)
    except Exception:
        pass

    with socketserver.TCPServer(("", PORT), LiveHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Đã dừng Web Server.")
            sys.exit(0)
