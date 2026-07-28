"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Agent Developer)
File chính ghép nối tất cả các thành phần: Tools + Prompts + Test Cases + Multi-Provider.
"""

import ast
import json
import os
import re
import sys
from dotenv import load_dotenv

# Đảm bảo import các module cùng thư mục src/ hoạt động mượt mà
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Đảm bảo in ra Tiếng Việt và Emojis không bị lỗi trên Windows Console
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Import các thành phần từ file của Role 2, Role 3 & Multi-Provider Adapter
from tools import AVAILABLE_TOOLS
from prompts import CHATBOT_BASELINE_PROMPT, REACT_SYSTEM_PROMPT, MAX_ITERATIONS
from providers import get_llm_provider

load_dotenv()


def load_test_cases():
    """Đọc bộ test cases từ config/test_cases.json của Role 1"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")

    # Fallback kiểm tra nếu file ở thư mục hiện tại
    if not os.path.exists(config_path):
        config_path = "test_cases.json"

    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_baseline_chatbot(user_query: str, provider):
    """
    Dựng Chatbot gốc (Baseline) không có công cụ.
    """
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    print(f"⚙️ System Prompt: {CHATBOT_BASELINE_PROMPT.strip()}")

    # Gọi LLM Provider thực hiện sinh câu trả lời
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"🤖 Chatbot trả lời:\n{response}")


def parse_action(model_output: str):
    """
    Parse dòng Action theo dạng: Action: tool_name['arg1', 'arg2']

    Returns:
        tuple[str, list] | None: Tên tool và danh sách tham số nếu parse được.
    """
    match = re.search(r"Action:\s*(\w+)\[(.*)\]", model_output, re.DOTALL)
    if not match:
        return None

    tool_name = match.group(1)
    raw_args = match.group(2).strip()
    if not raw_args:
        return tool_name, []

    try:
        parsed_args = ast.literal_eval(f"[{raw_args}]")
    except (SyntaxError, ValueError):
        return None

    return tool_name, parsed_args


def execute_tool(tool_name: str, args: list) -> str:
    """
    Gọi tool đã đăng ký trong AVAILABLE_TOOLS và biến mọi lỗi thành Observation.
    """
    tool = AVAILABLE_TOOLS.get(tool_name)
    if tool is None:
        valid_tools = ", ".join(AVAILABLE_TOOLS)
        return f"LỖI: Tool '{tool_name}' không tồn tại. Tool hợp lệ: {valid_tools}."

    try:
        return tool(*args)
    except TypeError as exc:
        return f"LỖI: Sai tham số khi gọi {tool_name}: {exc}."
    except Exception as exc:
        return f"LỖI: Tool {tool_name} gặp lỗi không mong muốn: {exc}."


def extract_order_id(user_query: str) -> str | None:
    match = re.search(r"\bORD\d+\b", user_query.upper())
    return match.group(0) if match else None


def infer_item_id(user_query: str) -> str | None:
    text = user_query.lower()
    if "hoodie" in text or "áo" in text or "ao" in text:
        return "ITEM-AO-HOODIE"
    if "tất" in text or "tat" in text:
        return "ITEM-TAT-SET"
    if "balo" in text:
        return "ITEM-BALO"
    if "giày" in text or "giay" in text:
        return "ITEM-GIAY"
    if "unknown" in text:
        return "ITEM-UNKNOWN"
    return None


def infer_reason(user_query: str) -> str:
    text = user_query.lower()
    if "sai size" in text:
        return "sai size"
    if "hoàn tiền" in text or "hoan tien" in text:
        return "hoàn tiền"
    if "lỗi" in text or "loi" in text:
        return "sản phẩm lỗi"
    return "khách hàng yêu cầu đổi trả"


def safe_json_loads(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"status": "raw", "message": text}


def build_final_answer(user_query: str, observations: list[dict]) -> str:
    last = observations[-1]["data"] if observations else {}
    order_id = extract_order_id(user_query)

    if last.get("status") == "error":
        message = last.get("message") or last.get("reason") or "Không thể hoàn tất yêu cầu."
        return f"Final Answer: Mình chưa thể xử lý yêu cầu này. {message} Vui lòng kiểm tra lại mã đơn hoặc mã sản phẩm."

    if "order" in last:
        order = last["order"]
        status_map = {
            "delivered": "đã giao",
            "shipping": "đang vận chuyển",
        }
        status = status_map.get(order["status"], order["status"])
        return f"Final Answer: Đơn {order['order_id']} hiện {status}. Mình tìm thấy {len(order['items'])} sản phẩm trong đơn."

    if "eligible" in last:
        if last["eligible"]:
            return (
                f"Final Answer: Đơn {order_id} đủ điều kiện đổi/trả. "
                f"Lý do: {last['reason']} Hạn cuối xử lý là {last.get('deadline')}."
            )
        return f"Final Answer: Đơn {order_id} chưa đủ điều kiện đổi/trả. Lý do: {last['reason']}"

    if "return_request_id" in last:
        return f"Final Answer: Đã tạo yêu cầu đổi/trả {last['return_request_id']}. {last['next_step']}"

    if "refund_amount" in last:
        return (
            f"Final Answer: Số tiền hoàn dự kiến cho {last['item_name']} là "
            f"{last['refund_amount']:,} {last['currency']} sau phí {last['deduction_fee']:,} {last['currency']}."
        )

    return "Final Answer: Mình đã xử lý xong các bước có thể thực hiện với dữ liệu hiện có."


def plan_next_step(user_query: str, observations: list[dict]) -> str:
    """
    Planner deterministic cho lab: tạo output đúng format ReAct để parser/executor xử lý.
    Cách này giúp demo ổn định khi không có API key hoặc model trả lời không đúng format.
    """
    order_id = extract_order_id(user_query)
    item_id = infer_item_id(user_query)
    reason = infer_reason(user_query)
    text = user_query.lower()

    if not order_id:
        return (
            "Thought: Tôi thiếu mã đơn hàng nên không thể tra cứu dữ liệu cụ thể.\n"
            "Final Answer: Bạn vui lòng cung cấp mã đơn hàng dạng ORDxxxx để mình kiểm tra."
        )

    if not observations:
        return (
            "Thought: Cần tra cứu đơn hàng trước khi kết luận hoặc tạo yêu cầu đổi/trả.\n"
            f"Action: lookup_order['{order_id}']"
        )

    last = observations[-1]["data"]
    if last.get("status") == "error":
        return (
            "Thought: Tool trả lỗi nên tôi không có đủ bằng chứng để tiếp tục.\n"
            f"{build_final_answer(user_query, observations)}"
        )

    if "order" in last:
        order = last["order"]
        if "đã giao chưa" in text or "da giao chua" in text or "trạng thái" in text or "trang thai" in text:
            return (
                "Thought: Tôi đã có trạng thái đơn hàng nên có thể trả lời.\n"
                f"{build_final_answer(user_query, observations)}"
            )

        if not item_id:
            return (
                "Thought: Người dùng muốn xử lý đổi/trả nhưng chưa nêu rõ sản phẩm.\n"
                "Final Answer: Mình đã tìm thấy đơn hàng, nhưng bạn vui lòng cho biết sản phẩm cần đổi/trả."
            )

        if "hoàn tiền" in text or "hoan tien" in text:
            return (
                "Thought: Cần ước tính số tiền hoàn trước khi trả lời.\n"
                f"Action: estimate_refund['{order_id}', '{item_id}']"
            )

        return (
            "Thought: Đã có đơn hàng, cần kiểm tra chính sách đổi/trả cho sản phẩm cụ thể.\n"
            f"Action: check_return_policy['{order_id}', '{item_id}', '{reason}']"
        )

    if "eligible" in last:
        if last["eligible"] and ("tạo" in text or "tao" in text):
            return (
                "Thought: Policy hợp lệ và người dùng muốn tạo yêu cầu đổi/trả.\n"
                f"Action: create_return_request['{order_id}', '{item_id}', '{reason}']"
            )
        return (
            "Thought: Tôi đã có kết quả policy nên có thể trả lời cuối cùng.\n"
            f"{build_final_answer(user_query, observations)}"
        )

    return (
        "Thought: Tôi đã có đủ thông tin từ Observation gần nhất.\n"
        f"{build_final_answer(user_query, observations)}"
    )


def run_react_agent(user_query: str, provider=None):
    """
    Dựng vòng lặp ReAct Agent (Thought -> Action -> Observation) có Guardrails.
    """
    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")
    observations = []
    action_history = set()
    finished = False

    for step in range(1, MAX_ITERATIONS + 1):
        print(f"\n--- 🔄 Vòng lặp ReAct (Step {step}/{MAX_ITERATIONS}) ---")

        agent_output = plan_next_step(user_query, observations)
        print(agent_output)

        if "Final Answer:" in agent_output:
            finished = True
            break

        parsed_action = parse_action(agent_output)
        if not parsed_action:
            observations.append({
                "tool_name": "parser",
                "args": [],
                "raw": "LỖI: Không parse được Action. Hãy dùng định dạng tool['arg1', 'arg2'].",
                "data": {
                    "status": "error",
                    "message": "Không parse được Action.",
                },
            })
            print(f"👁️ Observation: {observations[-1]['raw']}")
            continue

        tool_name, args = parsed_action
        action_key = (tool_name, tuple(args))
        if action_key in action_history:
            print("🛡️ GUARDRAIL TRIGGERED: Agent lặp lại cùng một Action với cùng tham số.")
            print("Final Answer: Mình đang bị kẹt ở cùng một bước xử lý, nên sẽ dừng an toàn. Vui lòng kiểm tra lại yêu cầu.")
            finished = True
            break

        action_history.add(action_key)
        observation_text = execute_tool(tool_name, args)
        observation_data = safe_json_loads(observation_text)
        observations.append({
            "tool_name": tool_name,
            "args": args,
            "raw": observation_text,
            "data": observation_data,
        })
        print(f"👁️ Observation: {observation_text}")

    if not finished:
        print(f"🛡️ GUARDRAIL TRIGGERED: Đã đạt giới hạn tối đa {MAX_ITERATIONS} bước. Ngắt lặp an toàn!")
        print("Final Answer: Mình chưa thể hoàn tất yêu cầu trong giới hạn xử lý an toàn. Vui lòng thử lại với thông tin rõ hơn.")


if __name__ == "__main__":
    print("==================================================")
    print("🏫 ĐẠI HỌC VINUNI - BÀI LAB 3: CHATBOT VS REACT AGENT")
    print("==================================================")

    # Khởi tạo Multi-Provider LLM Adapter (Đọc từ biến môi trường LLM_PROVIDER)
    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print(f"🔌 LLM Provider đang hoạt động: {provider.__class__.__name__} (Model: {model_name})")

    tests = load_test_cases()
    print(f"✅ Đã tải thành công {len(tests)} Test Cases từ config/test_cases.json\n")

    # Chạy thử câu test số 4: cần tra cứu đơn hàng và kiểm tra policy
    sample_query = tests[3]["question"]

    print("--- DEMO 1: CHẠY TRÊN CHATBOT BASELINE ---")
    run_baseline_chatbot(sample_query, provider)

    print("\n--- DEMO 2: CHẠY TRÊN REACT AGENT ---")
    run_react_agent(sample_query, provider)

    print("\n--- DEMO 3: EDGE CASE / SAFE FALLBACK ---")
    run_react_agent(tests[4]["question"], provider)

    print("\n" + "=" * 50)
    print("💬 CHẾ ĐỘ CHAT TƯƠNG TÁC TRỰC TIẾP (INTERACTIVE CLI MODE)")
    print("Gõ câu hỏi bất kỳ để chat trực tiếp với ReAct Agent, hoặc gõ 'exit' / 'quit' để thoát.")
    print("=" * 50)

    while True:
        try:
            user_input = input("\n👤 Khách hàng: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit", "thoat", "q"]:
                print("👋 Cảm ơn bạn đã sử dụng Trợ lý ReAct Agent!")
                break
            run_react_agent(user_input, provider)
        except (KeyboardInterrupt, EOFError):
            print("\n👋 Đã thoát chương trình.")
            break

