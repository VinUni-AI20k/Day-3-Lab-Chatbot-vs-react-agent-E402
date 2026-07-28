"""
🧠 CẤP ĐỘ 3: REACTIVE AGENT (ReAct Agent - Thought -> Action -> Observation)
Agent suy luận đa bước, kiểm soát thông tin thiếu (Information Gathering Loop),
PII Masking, phanh an toàn Guardrails và tự động gọi công cụ.
"""

import os
import sys
import json
import re
from typing import Dict, Any, List, Tuple

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.tools import calculate_compatibility, search_candidates, AVAILABLE_TOOLS, MOCK_CANDIDATE_DB
from src.prompts import REACT_SYSTEM_PROMPT, MAX_INFO_GATHERING_TURNS, MAX_TOOL_CALLS_PER_TURN, MAX_ITERATIONS
from src.providers import get_llm_provider


def parse_and_execute_tool(tool_name: str, args_raw: str) -> Any:
    """
    Trình phân tích & thực thi công cụ linh hoạt cho LLM ReAct Agent.
    Hỗ trợ JSON dict, Kwargs (key=value), và Positional parameters (CSV).
    """
    tool_fn = AVAILABLE_TOOLS.get(tool_name)
    if not tool_fn:
        return {"error": f"Không tìm thấy công cụ '{tool_name}'"}

    args_str = args_raw.strip()

    # 1. Thử giải mã JSON Dict
    if args_str.startswith("{") and args_str.endswith("}"):
        try:
            kwargs = json.loads(args_str)
            return tool_fn(**kwargs)
        except Exception:
            pass

    # 2. Thử phân tích dạng Kwargs key=val: target_gender="Nữ", min_age=18...
    if "=" in args_str:
        try:
            kwargs = {}
            pairs = re.findall(r'([a-zA-Z0-9_]+)\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|([^,\]\)\s]+))', args_str)
            for key, val_dq, val_sq, val_raw in pairs:
                val = val_dq or val_sq or val_raw
                val = val.strip()
                if val.isdigit():
                    val = int(val)
                elif val.lower() == "true":
                    val = True
                elif val.lower() == "false":
                    val = False
                kwargs[key] = val
            if kwargs:
                return tool_fn(**kwargs)
        except Exception:
            pass

    # 3. Phân tách danh sách các tham số vị trí (Positional tokens)
    clean_str = args_str.strip("[]()")
    raw_tokens = [t.strip().strip('"\'') for t in clean_str.split(",") if t.strip()]

    if tool_name == "search_candidates":
        kwargs = {}
        for token in raw_tokens:
            if token.isdigit():
                val = int(token)
                if val < 35 and "min_age" not in kwargs:
                    kwargs["min_age"] = val
                elif "max_age" not in kwargs:
                    kwargs["max_age"] = val
            elif token.lower() in ["nam", "nữ", "male", "female"]:
                kwargs["target_gender"] = "Nam" if token.lower() in ["nam", "male"] else "Nữ"
            elif any(loc in token.lower() for loc in ["hà nội", "hcm", "hồ chí minh", "đà nẵng", "hải phòng", "bắc ninh", "cần thơ"]):
                kwargs["location"] = token
            else:
                if "query_interests" in kwargs:
                    kwargs["query_interests"] += f" {token}"
                else:
                    kwargs["query_interests"] = token
        
        # Guardrail: KHÔNG tự điền giá trị mặc định / fallback khi thiếu thông tin
        missing_kwargs = []
        if not kwargs.get("target_gender"):
            missing_kwargs.append("Giới tính đối tượng (Nam/Nữ)")
        if not kwargs.get("location"):
            missing_kwargs.append("Vị trí địa lý (Tỉnh/Thành phố)")
        if not kwargs.get("query_interests"):
            missing_kwargs.append("Mô tả sở thích/gu mong muốn")
        if "min_age" not in kwargs or "max_age" not in kwargs:
            missing_kwargs.append("Khoảng độ tuổi (min_age, max_age)")
        
        if missing_kwargs:
            return {"error": f"THIẾU DỮ LIỆU BẮT BUỘC: Chưa có đủ các tham số [{', '.join(missing_kwargs)}]. Vui lòng hỏi lại người dùng để bổ sung thông tin, KHÔNG ĐƯỢC tự đoán hay fallback."}
            
        return tool_fn(**kwargs)

    elif tool_name == "calculate_compatibility":
        # Thử giải mã JSON / Python Dict trong args_raw
        dict_matches = re.findall(r'\{[^{}]*\}', args_raw)
        if len(dict_matches) >= 2:
            try:
                import ast
                def parse_dict(s):
                    try:
                        return json.loads(s)
                    except Exception:
                        return ast.literal_eval(s)

                p1 = parse_dict(dict_matches[0])
                p2 = parse_dict(dict_matches[1])

                if isinstance(p1.get("interests"), list):
                    p1["interests"] = ", ".join(p1["interests"])
                if isinstance(p2.get("interests"), list):
                    p2["interests"] = ", ".join(p2["interests"])

                # Kiểm tra thông tin bắt buộc của từng người
                missing_p1 = [f for f in ["gender", "age", "location", "interests"] if not p1.get(f)]
                missing_p2 = [f for f in ["gender", "age", "location", "interests"] if not p2.get(f)]

                if missing_p1 or missing_p2:
                    err_msg = "THIẾU DỮ LIỆU THÔNG TIN HỒ SƠ: "
                    if missing_p1:
                        err_msg += f"Người 1 thiếu {missing_p1}; "
                    if missing_p2:
                        err_msg += f"Người 2 thiếu {missing_p2}. "
                    err_msg += "Vui lòng hỏi lại người dùng để bổ sung đầy đủ thông tin, KHÔNG ĐƯỢC tự đoán hoặc fallback."
                    return {"error": err_msg}

                p1.setdefault("id", "CUSTOM_A")
                p1.setdefault("name", p1.get("name", "Bạn Nam" if p1.get("gender") == "Nam" else "Bạn Nữ"))
                p1.setdefault("phone", "0900000001")
                p1.setdefault("height_cm", int(p1.get("height_cm", 175 if p1.get("gender") == "Nam" else 165)))
                p1.setdefault("education", p1.get("education", "Đại học"))
                p1.setdefault("occupation", p1.get("occupation", "Tự do"))

                p2.setdefault("id", "CUSTOM_B")
                p2.setdefault("name", p2.get("name", "Bạn Nữ" if p2.get("gender") == "Nữ" else "Bạn Nam"))
                p2.setdefault("phone", "0900000002")
                p2.setdefault("height_cm", int(p2.get("height_cm", 165 if p2.get("gender") == "Nữ" else 175)))
                p2.setdefault("education", p2.get("education", "Đại học"))
                p2.setdefault("occupation", p2.get("occupation", "Tự do"))

                return tool_fn(p1, p2)
            except Exception:
                pass

        # Tìm theo ID chính xác hoặc tên cụ thể trong MOCK_CANDIDATE_DB
        found_persons = []
        for token in raw_tokens:
            token_clean = token.strip().lower()
            if not token_clean:
                continue
            for cand in MOCK_CANDIDATE_DB:
                if cand["id"].lower() == token_clean or token_clean in cand["name"].lower():
                    if cand not in found_persons:
                        found_persons.append(cand)
                        break
        if len(found_persons) >= 2:
            return tool_fn(found_persons[0], found_persons[1])

        return {
            "error": "THIẾU DỮ LIỆU: Không tìm thấy đủ thông tin chi tiết (Giới tính, Tuổi, Vị trí, Sở thích) của cả 2 đối tượng trong yêu cầu. Hãy hỏi lại người dùng để cung cấp đầy đủ thông tin trước khi tính độ tương thích."
        }

    try:
        return tool_fn(args_raw)
    except Exception as e:
        return {"error": f"Lỗi thực thi tool '{tool_name}': {str(e)}"}


class MatchmakingAgent:
    """
    Core AI Matchmaking Agent Cấp 3 (ReAct Agent) quản lý hội thoại,
    trích xuất Intent & Slots, Slot Filling Loop và Guardrails.
    """

    def __init__(self, provider_name: str = None):
        self.provider = get_llm_provider(provider_name)
        self.reset_state()

    def reset_state(self):
        """Reset sạch sẽ toàn bộ trạng thái và lịch sử hội thoại"""
        self.conversation_history: List[Dict[str, str]] = []
        self.state: Dict[str, Any] = {
            "turn_count": 0,
            "intent": None,
            "is_task_complete": False,
            "search_slots": {
                "target_gender": None,
                "min_age": None,
                "max_age": None,
                "location": None,
                "query_interests": None
            },
            "compatibility_slots": {
                "person_a": None,
                "person_b": None
            }
        }

    def reset_current_task(self):
        """Reset các tham số slot cho câu prompt mới"""
        self.state["turn_count"] = 0
        self.state["intent"] = None
        self.state["is_task_complete"] = False
        self.state["search_slots"] = {
            "target_gender": None,
            "min_age": None,
            "max_age": None,
            "location": None,
            "query_interests": None
        }
        self.state["compatibility_slots"] = {
            "person_a": None,
            "person_b": None
        }

    def extract_intent_and_slots(self, user_input: str) -> Dict[str, Any]:
        """Trích xuất Intent (SEARCH / COMPATIBILITY) và tham số do người dùng cung cấp"""
        text = user_input.lower()
        
        if any(k in text for k in ["tương thích", "hợp nhau", "chấm điểm", "so sánh", "đánh giá 2 người", "đánh giá"]):
            self.state["intent"] = "COMPATIBILITY"
        elif any(k in text for k in ["tìm", "gợi ý", "ghép đôi", "kết bạn", "người yêu", "bạn gái", "bạn trai", "tìm nữ", "tìm nam"]):
            self.state["intent"] = "SEARCH"
        elif not self.state["intent"]:
            self.state["intent"] = "SEARCH"

        intent = self.state["intent"]

        if intent == "SEARCH":
            slots = self.state["search_slots"]
            
            if any(w in text for w in ["tìm nữ", "bạn gái", "nữ", "con gái", "chị", "em gái"]):
                slots["target_gender"] = "Nữ"
            elif any(w in text for w in ["tìm nam", "bạn trai", "nam", "con trai", "anh"]):
                slots["target_gender"] = "Nam"

            age_matches = re.findall(r'(\d{2})\s*(?:tới|-|đến)\s*(\d{2})\s*tuổi', text)
            if age_matches:
                slots["min_age"] = int(age_matches[0][0])
                slots["max_age"] = int(age_matches[0][1])
            else:
                single_age = re.findall(r'(\d{2})\s*tuổi', text)
                if single_age:
                    age = int(single_age[0])
                    slots["min_age"] = max(18, age - 3)
                    slots["max_age"] = age + 3

            locations = ["hà nội", "tp.hcm", "tphcm", "hồ chí minh", "đà nẵng", "hải phòng", "bắc ninh", "cần thơ"]
            for loc in locations:
                if loc in text:
                    slots["location"] = "Hà Nội" if "hà nội" in loc else ("TP.HCM" if "hcm" in loc else loc.title())
                    break

            interest_keywords = ["thích", "gu", "yêu", "đam mê", "sở thích", "phong cách", "lối sống"]
            for kw in interest_keywords:
                if kw in text:
                    idx = text.find(kw)
                    slots["query_interests"] = user_input[idx:].strip()
                    break
            if not slots["query_interests"] and len(user_input.split()) >= 4 and slots["location"]:
                slots["query_interests"] = user_input.strip()

        elif intent == "COMPATIBILITY":
            slots = self.state["compatibility_slots"]
            found = []
            for candidate in MOCK_CANDIDATE_DB:
                if candidate["id"].lower() in text or candidate["name"].lower() in text:
                    found.append(candidate)
            
            if len(found) >= 2:
                slots["person_a"] = found[0]
                slots["person_b"] = found[1]
            elif len(found) == 1:
                if not slots["person_a"]:
                    slots["person_a"] = found[0]
                elif slots["person_a"]["id"] != found[0]["id"]:
                    slots["person_b"] = found[0]

        return self.state

    def check_missing_parameters(self) -> Tuple[bool, List[str]]:
        """Kiểm tra tham số còn thiếu để kích hoạt Slot Filling Guardrail"""
        intent = self.state["intent"]
        missing = []

        if intent == "SEARCH":
            slots = self.state["search_slots"]
            if not slots["target_gender"]:
                missing.append("Giới tính đối tượng bạn muốn tìm (Nam hay Nữ)")
            if not slots["location"]:
                missing.append("Vị trí địa lý (Tỉnh/Thành phố hiện tại)")
            if not slots["query_interests"]:
                missing.append("Mô tả sở thích, phong cách sống hoặc gu người yêu mong muốn")
            if not slots["min_age"] or not slots["max_age"]:
                missing.append("Khoảng độ tuổi mong muốn (Ví dụ: từ 22 đến 28 tuổi)")

        elif intent == "COMPATIBILITY":
            slots = self.state["compatibility_slots"]
            if not slots["person_a"]:
                missing.append("Thông tin đầy đủ của Người thứ nhất (Tên/ID, Tuổi, Vị trí, Sở thích)")
            if not slots["person_b"]:
                missing.append("Thông tin đầy đủ của Người thứ hai (Tên/ID, Tuổi, Vị trí, Sở thích)")

        return (len(missing) > 0, missing)

    def process_message_llm_react(self, user_input: str) -> str:
        """Thực thi ReAct Loop qua LLM (Thought -> Action -> Observation -> Final Answer)"""
        prompt = f"Yêu cầu hiện tại của người dùng: {user_input}\n"
        if self.conversation_history:
            history_str = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in self.conversation_history[-4:]])
            prompt = f"Lịch sử hội thoại gần nhất:\n{history_str}\n\nYêu cầu hiện tại của người dùng: {user_input}"

        iterations = 0
        current_context = prompt
        execution_trace = []
        
        while iterations < MAX_ITERATIONS:
            iterations += 1
            llm_out = self.provider.generate(current_context, system_prompt=REACT_SYSTEM_PROMPT)
            
            if any(err in llm_out for err in ["[Groq Error]", "[Gemini Error]", "[OpenAI Error]", "[Anthropic Error]", "[OpenRouter Error]", "[Mock Provider]"]):
                return None
            
            action_match = re.search(r'Action:\s*`?([a-zA-Z0-9_]+)`?\s*\[(.*?)\]', llm_out, re.DOTALL)
            if not action_match:
                action_match = re.search(r'Action:\s*`?([a-zA-Z0-9_]+)`?\s*\((.*?)\)', llm_out, re.DOTALL)
                
            if action_match:
                tool_name = action_match.group(1).strip()
                args_raw = action_match.group(2).strip()
                
                action_end_idx = action_match.end()
                clean_llm_out = llm_out[:action_end_idx].strip()
                execution_trace.append(clean_llm_out)
                
                if tool_name in AVAILABLE_TOOLS:
                    obs = parse_and_execute_tool(tool_name, args_raw)
                    obs_str = json.dumps(obs, ensure_ascii=False, indent=2) if isinstance(obs, (dict, list)) else str(obs)
                    
                    obs_step = f"Observation (Kết quả Tool {tool_name}):\n{obs_str}"
                    execution_trace.append(obs_step)
                    
                    current_context += f"\n\n{clean_llm_out}\n{obs_step}\nHãy tiếp tục suy luận (Thought) và đưa ra Final Answer cho người dùng dựa trên Observation này."
                    continue
                elif tool_name.lower() in ["none", "không", "n/a"]:
                    break
                else:
                    err_step = f"Observation: Lỗi không tìm thấy tool '{tool_name}'."
                    execution_trace.append(err_step)
                    current_context += f"\n\n{llm_out}\n{err_step}"
                    continue
            
            execution_trace.append(llm_out.strip())
            break
            
        if not execution_trace:
            return None
            
        return "\n\n".join(execution_trace)

    def process_message(self, user_input: str) -> str:
        """Xử lý thông điệp người dùng qua 5 bước Workflow"""
        # Guardrail: Input validation
        if not user_input or not str(user_input).strip():
            return "Vui lòng nhập câu hỏi hoặc yêu cầu ghép đôi hợp lệ!"

        llm_response = self.process_message_llm_react(user_input)
        if llm_response:
            self.conversation_history.append({"role": "user", "content": user_input})
            self.conversation_history.append({"role": "assistant", "content": llm_response})
            self.state["is_task_complete"] = True
            return llm_response

        text = user_input.lower()
        has_new_intent_keywords = any(k in text for k in ["tìm", "gợi ý", "ghép đôi", "tương thích", "chấm điểm", "so sánh", "đánh giá"])
        if self.state.get("is_task_complete", False) or has_new_intent_keywords:
            self.reset_current_task()

        self.state["turn_count"] += 1
        turn_count = self.state["turn_count"]
        self.conversation_history.append({"role": "user", "content": user_input})

        self.extract_intent_and_slots(user_input)
        is_missing, missing_params = self.check_missing_parameters()

        # Guardrail: MAX_INFO_GATHERING_TURNS Limit
        if turn_count > MAX_INFO_GATHERING_TURNS:
            self.state["is_task_complete"] = True
            s = self.state["search_slots"]
            tool_res = search_candidates(
                target_gender=s["target_gender"] or "Nữ",
                min_age=s["min_age"] or 20,
                max_age=s["max_age"] or 30,
                location=s["location"] or "Hà Nội",
                query_interests=s["query_interests"] or "Thích âm nhạc, du lịch"
            )
            return self.format_persona_response("SEARCH", tool_res, is_max_turn_fallback=True)

        # Guardrail: Slot Filling Check -> Không gọi tool khi thiếu tham số
        if is_missing:
            ask_param = missing_params[0]
            response = f"Chào bạn! Bà Mối AI rất vui được hỗ trợ bạn nè.\n\nĐể tìm được đối tượng ghép đôi ưng ý nhất, bạn cho Bà Mối biết thêm thông tin về **{ask_param}** nhé?"
            self.conversation_history.append({"role": "assistant", "content": response})
            return response

        # Đủ parameters -> Gọi Tool với phanh an toàn MAX_TOOL_CALLS_PER_TURN
        tool_call_count = 0
        tool_res = None
        
        while tool_call_count < MAX_TOOL_CALLS_PER_TURN:
            tool_call_count += 1
            try:
                if self.state["intent"] == "SEARCH":
                    s = self.state["search_slots"]
                    tool_res = search_candidates(
                        target_gender=s["target_gender"],
                        min_age=s["min_age"],
                        max_age=s["max_age"],
                        location=s["location"],
                        query_interests=s["query_interests"]
                    )
                elif self.state["intent"] == "COMPATIBILITY":
                    s = self.state["compatibility_slots"]
                    tool_res = calculate_compatibility(s["person_a"], s["person_b"])
                break
            except Exception as e:
                if tool_call_count >= MAX_TOOL_CALLS_PER_TURN:
                    return f"[Fallback Error]: Đã thử gọi Tool {MAX_TOOL_CALLS_PER_TURN} lần nhưng không thành công ({str(e)}). Vui lòng thử lại sau!"

        final_answer = self.format_persona_response(self.state["intent"], tool_res)
        self.conversation_history.append({"role": "assistant", "content": final_answer})
        self.state["is_task_complete"] = True
        return final_answer

    def format_persona_response(self, intent: str, tool_res: Dict, is_max_turn_fallback: bool = False) -> str:
        """Đóng vai Bà Mối AI văn phong tự nhiên, ấm áp"""
        lines = []
        if is_max_turn_fallback:
            lines.append("*Bà Mối đã tổng hợp thông tin hiện có để gợi ý ngay cho bạn đây:*")

        if intent == "SEARCH":
            candidates = tool_res.get("candidates", [])
            note = tool_res.get("note")

            lines.append("**DANH SÁCH ỨNG VIÊN TIỀM NĂNG DÀNH CHO BẠN**\n")
            if note:
                lines.append(f"*Ghi chú từ Bà Mối*: {note}\n")

            if not candidates:
                lines.append("Bà Mối tiếc quá, hiện chưa tìm thấy hồ sơ nào khớp với mong muốn. Bạn thử thay đổi tiêu chí xem sao nhé!")
            else:
                for idx, c in enumerate(candidates, 1):
                    lines.append(f"**{idx}. {c['masked_name']}** ({c['age']} tuổi, {c['location']}) - *Match: {c['match_score']}%*")
                    lines.append(f"   • Nghề nghiệp: {c['occupation']} | Chiều cao: {c['height_cm']}cm")
                    lines.append(f"   • Sở thích & Lối sống: {c['interests_highlight']}")
                    lines.append(f"   • Liên hệ bảo mật: {c['masked_phone']}\n")

                lines.append("**Lời khuyên từ Bà Mối AI**: Hãy chọn hồ sơ bạn ấn tượng nhất để Bà Mối giúp hai bạn bắt đầu trò chuyện nhé! Chúc bạn sớm tìm được chân tình!")

        elif intent == "COMPATIBILITY":
            score = tool_res.get("total_score", 0)
            summary = tool_res.get("summary", "")
            strengths = tool_res.get("strengths", [])
            weaknesses = tool_res.get("weaknesses", [])

            lines.append(f"**KẾT QUẢ ĐÁNH GIÁ TƯƠNG THÍCH: {score}/100 ĐIỂM**\n")
            lines.append(f"**Nhận xét của Bà Mối AI**:\n\"{summary}\"\n")
            
            if strengths:
                lines.append("**Điểm cộng hòa hợp nhất**:")
                for s in strengths:
                    lines.append(f"   - {s}")
                lines.append("")

            if weaknesses:
                lines.append("**Điểm cần lưu ý & cảm thông**:")
                for w in weaknesses:
                    lines.append(f"   - {w}")
                lines.append("")

            lines.append("*Chúc hai bạn luôn lắng nghe và thấu hiểu lẫn nhau!*")

        return "\n".join(lines)


def reactive_agent_process(user_query: str, agent=None) -> str:
    """Wrapper function cho Cấp độ 3 ReAct Agent"""
    if agent is None:
        agent = MatchmakingAgent()
    
    print(f"User Goal: {user_query}")
    res = agent.process_message(user_query)
    return f"[Cấp 3 - ReAct Agent]:\n{res}"


if __name__ == "__main__":
    agent = MatchmakingAgent()
    q = "Đánh giá độ tương thích giữa hồ sơ C001 (Nguyễn Văn Tuấn) và C002 (Trần Thị Ngọc Bích)."
    print(reactive_agent_process(q, agent))
