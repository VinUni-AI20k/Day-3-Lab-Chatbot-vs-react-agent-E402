"""
🔌 MULTI-PROVIDER LLM ADAPTER (OpenAI, Gemini, Anthropic, OpenRouter & Offline Mock)
Hỗ trợ chuyển đổi linh hoạt giữa các nhà cung cấp AI chỉ bằng cách đổi biến môi trường LLM_PROVIDER.
"""

import os
import sys
import re
import ast
import json
import requests
from dotenv import load_dotenv

# Đảm bảo in ra Tiếng Việt và Emojis không bị lỗi trên Windows Console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()

class BaseLLMProvider:
    """Interface cơ sở cho tất cả các LLM Provider"""
    def generate(self, prompt: str, system_prompt: str = "", stop_sequences: list = None) -> str:
        raise NotImplementedError


class GeminiProvider(BaseLLMProvider):
    """Google Gemini Provider"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gemini-2.5-flash"

    def generate(self, prompt: str, system_prompt: str = "", stop_sequences: list = None) -> str:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            return "[Gemini Error]: Chưa cấu hình GEMINI_API_KEY trong file .env!"
        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=self.api_key)
            contents = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            config = types.GenerateContentConfig(stop_sequences=stop_sequences) if stop_sequences else None
            response = client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config,
            )
            return response.text
        except Exception as e:
            return f"[Gemini Exception]: {str(e)}"


class OpenAIProvider(BaseLLMProvider):
    """OpenAI Provider (GPT-4o, GPT-3.5-turbo, etc.)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gpt-4o-mini"
        
    def generate(self, prompt: str, system_prompt: str = "", stop_sequences: list = None) -> str:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            return "[OpenAI Error]: Chưa cấu hình OPENAI_API_KEY trong file .env!"
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            kwargs = {"model": self.model_name, "messages": messages}
            if stop_sequences:
                kwargs["stop"] = stop_sequences

            response = client.chat.completions.create(**kwargs)
            return response.choices[0].message.content
        except Exception as e:
            return f"[OpenAI Exception]: {str(e)}"


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude Provider (Claude 3.5 Sonnet, Claude 3 Haiku)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "claude-3-haiku-20240307"
        
    def generate(self, prompt: str, system_prompt: str = "", stop_sequences: list = None) -> str:
        if not self.api_key or self.api_key == "your_anthropic_api_key_here":
            return "[Anthropic Error]: Chưa cấu hình ANTHROPIC_API_KEY trong file .env!"
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)
            kwargs = {
                "model": self.model_name,
                "max_tokens": 1000,
                "messages": [{"role": "user", "content": prompt}]
            }
            if system_prompt:
                kwargs["system"] = system_prompt
            if stop_sequences:
                kwargs["stop_sequences"] = stop_sequences

            response = client.messages.create(**kwargs)
            return response.content[0].text
        except Exception as e:
            return f"[Anthropic Exception]: {str(e)}"


class OpenRouterProvider(BaseLLMProvider):
    """OpenRouter Provider (Hỗ trợ gọi mọi model qua OpenRouter API)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "google/gemini-2.5-flash"
        
    def generate(self, prompt: str, system_prompt: str = "", stop_sequences: list = None) -> str:
        if not self.api_key or self.api_key == "your_openrouter_api_key_here":
            return "[OpenRouter Error]: Chưa cấu hình OPENROUTER_API_KEY trong file .env!"
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            payload = {
                "model": self.model_name,
                "messages": messages
            }
            if stop_sequences:
                payload["stop"] = stop_sequences
            res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=30)
            if res.status_code == 200:
                data = res.json()
                return data["choices"][0]["message"]["content"]
            else:
                return f"[OpenRouter API Error {res.status_code}]: {res.text}"
        except Exception as e:
            return f"[OpenRouter Exception]: {str(e)}"


class MockProvider(BaseLLMProvider):
    """Offline Mock Provider (Cho bài test không cần kết nối API / không tốn phí)

    LƯU Ý: Đây KHÔNG phải một LLM thật, chỉ là một "kịch bản" (scripted policy)
    được viết cứng dựa theo Business Flow Guardrails trong prompts.py, đủ để
    Role 4 và cả nhóm chạy thử TOÀN BỘ vòng lặp ReAct (Thought -> Action ->
    Observation) và các Guardrails ở app.py mà không cần API key. Khi chấm
    điểm/demo thật, hãy đổi LLM_PROVIDER sang gemini/openai/anthropic/openrouter.
    """

    def generate(self, prompt: str, system_prompt: str = "", stop_sequences: list = None) -> str:
        if "Action:" in system_prompt or "Final Answer" in system_prompt:
            text = self._react_step(prompt)
        else:
            text = self._baseline_reply(prompt)
        return self._apply_stop(text, stop_sequences)

    @staticmethod
    def _apply_stop(text: str, stop_sequences) -> str:
        if not stop_sequences:
            return text
        cut_at = len(text)
        for seq in stop_sequences:
            idx = text.find(seq)
            if idx != -1:
                cut_at = min(cut_at, idx)
        return text[:cut_at]

    @staticmethod
    def _baseline_reply(prompt: str) -> str:
        looks_like_person_name = re.search(
            r"[A-ZÀ-Ỹ][a-zà-ỹ]+(?:\s+[A-ZÀ-Ỹ][a-zà-ỹ]+)+", prompt
        )
        if "tính cách" in prompt.lower() and looks_like_person_name:
            return (
                f"Mình không có quyền truy cập dữ liệu trắc nghiệm tính cách thật của "
                f"'{looks_like_person_name.group(0)}', nên không thể khẳng định tính cách "
                "của bạn ấy là gì. Nếu bạn mô tả sở thích/tính cách trực tiếp, mình có thể "
                "gợi ý quà chung chung dựa trên đó."
            )
        if re.search(r"gift_\d+", prompt.lower()) or "tồn kho" in prompt.lower():
            return (
                "Mình không có dữ liệu tồn kho/giá thời gian thực nên không thể xác nhận "
                "chính xác. Bạn nên tra cứu trực tiếp trên hệ thống cửa hàng."
            )
        return (
            "Khi chọn quà, bạn nên ưu tiên theo sở thích cá nhân của người nhận, cân đối "
            "với ngân sách, và lưu ý một số điều kiêng kỵ nếu tặng vào dịp lễ/văn hóa đặc "
            "thù. Một món quà nhỏ nhưng đúng gu thường ý nghĩa hơn món đắt tiền nhưng vô cảm."
        )

    _ACTION_LOG_RE = re.compile(
        r"Action:\s*([A-Za-z_][A-Za-z0-9_]*)\[(.*?)\]\s*\nObservation:\s*(.*?)(?=\n\n|\Z)",
        re.DOTALL,
    )

    @staticmethod
    def _format_action(thought: str, tool: str, args: dict) -> str:
        # Luôn build args qua json.dumps để đảm bảo JSON hợp lệ (KHÔNG f-string
        # tay từng phần), vì repr() của list/dict Python dùng dấu nháy đơn ' '
        # chứ không phải JSON hợp lệ (dấu nháy kép) — dễ gây lỗi parse ở app.py.
        return f"Thought: {thought}\nAction: {tool}[{json.dumps(args, ensure_ascii=False)}]"

    def _react_step(self, prompt: str) -> str:
        history = self._ACTION_LOG_RE.findall(prompt)
        done = {tool: obs.strip() for tool, _args, obs in history}

        question_match = re.search(r"Question:\s*(.*?)\n", prompt)
        question = question_match.group(1) if question_match else prompt

        person = self._extract_person(question)
        occasion = self._extract_occasion(question)
        culture = self._extract_culture(question)
        budget = self._extract_budget(question)
        so_nguoi_gop = self._extract_group_size(question)
        explicit_gift_id = re.search(r"GIFT_\d+", question)

        # 1) Có nhắc người cụ thể -> tra cứu tính cách trước tiên.
        if person and "get_personality_profile" not in done:
            return self._format_action(
                f'Câu hỏi nhắc tới "{person}", cần tra cứu tính cách trước.',
                "get_personality_profile",
                {"person_name": person},
            )

        # 2) Có nhắc dịp lễ -> tra quy tắc trước khi tìm quà.
        if occasion and "tra_cuu_quy_tac_dip" not in done:
            args = {"dip": occasion}
            if culture:
                args["van_hoa"] = culture
            return self._format_action(
                f"Câu hỏi nhắc dịp {occasion}, cần tra quy tắc kiêng kỵ trước khi tìm quà.",
                "tra_cuu_quy_tac_dip",
                args,
            )

        # 3) Tìm quà: ưu tiên suggest_gift_by_personality nếu đã có personality_type.
        if "search_gift_catalog" not in done and "suggest_gift_by_personality" not in done:
            budget_value = budget if budget is not None else -1
            exclude = self._extract_exclusions(done.get("tra_cuu_quy_tac_dip", ""))
            personality_obs = done.get("get_personality_profile", "")
            type_match = re.search(r"nhóm tính cách '([^']+)'", personality_obs)
            if type_match:
                return self._format_action(
                    f"Đã biết nhóm tính cách '{type_match.group(1)}', dùng để gợi ý quà nhanh "
                    "(kèm loại trừ kiêng kỵ nếu có).",
                    "suggest_gift_by_personality",
                    {"personality_type": type_match.group(1), "budget": budget_value, "loai_tru": exclude},
                )
            return self._format_action(
                "Chưa có nhóm tính cách cụ thể, tìm quà theo ngân sách và loại trừ kiêng kỵ (nếu có).",
                "search_gift_catalog",
                {"so_thich": [], "budget": budget_value, "loai_tru": exclude},
            )

        # 4) Kiểm tra tồn kho cho món quà vừa tìm được (hoặc mã được nhắc thẳng trong câu hỏi).
        if "check_gift_availability" not in done:
            gift_id = None
            if explicit_gift_id:
                gift_id = explicit_gift_id.group(0)
            else:
                catalog_obs = done.get("search_gift_catalog") or done.get("suggest_gift_by_personality") or ""
                found = re.search(r"(GIFT_\d+):", catalog_obs)
                if found:
                    gift_id = found.group(1)
            if gift_id:
                return self._format_action(
                    "Cần xác nhận còn hàng trước khi chốt quà.",
                    "check_gift_availability",
                    {"gift_id": gift_id},
                )

        # 5) Nếu là quà góp chung nhiều người -> chia ngân sách.
        if so_nguoi_gop and "tinh_ngan_sach_gop" not in done:
            price_match = re.search(r"giá\s*([\d\.]+)\s*VNĐ", done.get("check_gift_availability", ""))
            gia_tien = int(price_match.group(1).replace(".", "")) if price_match else (budget or 0)
            if gia_tien > 0:
                return self._format_action(
                    f"Nhóm {so_nguoi_gop} người cùng góp, cần chia đều ngân sách.",
                    "tinh_ngan_sach_gop",
                    {"gia_tien": gia_tien, "so_nguoi_gop": so_nguoi_gop},
                )

        # 6) Đã đủ căn cứ (hoặc hết hướng đi hợp lệ) -> tổng hợp Final Answer.
        return self._compose_final_answer(done)

    _PERSON_NAME_RE = re.compile(
        r"(?:cho|của|tên)\s+['\"]?([A-ZÀ-Ỹ][\wÀ-ỹ]*(?:\s+[A-ZÀ-Ỹ][\wÀ-ỹ]*){0,3})"
    )

    @classmethod
    def _extract_person(cls, question: str):
        match = cls._PERSON_NAME_RE.search(question)
        if not match:
            return None
        return match.group(1).strip().rstrip(",.'\"")

    @staticmethod
    def _extract_occasion(question: str):
        text = question.lower()
        for keyword, label in [
            ("halloween", "Halloween"),
            ("giáng sinh", "Giáng Sinh"),
            ("noel", "Giáng Sinh"),
            ("trung thu", "Trung Thu"),
            ("tết", "Tết"),
        ]:
            if keyword in text:
                return label
        return None

    @staticmethod
    def _extract_culture(question: str):
        text = question.lower()
        for keyword, label in [
            ("nhật", "Nhật Bản"),
            ("trung quốc", "Trung Quốc"),
            ("hàn quốc", "Hàn Quốc"),
        ]:
            if keyword in text:
                return label
        return None

    @staticmethod
    def _extract_budget(question: str):
        # Cách nói tắt kiểu Việt Nam "1 triệu 5" = 1,5 triệu = 1.500.000, cần
        # bắt riêng trước vì chữ số lẻ theo sau "triệu" không có đơn vị đi kèm.
        colloquial = re.search(r"ngân sách\s*(-?\d+)\s*triệu\s+(\d)(?!\d)", question, re.IGNORECASE)
        if colloquial:
            sign = -1 if colloquial.group(1).startswith("-") else 1
            whole = abs(int(colloquial.group(1)))
            tenth = int(colloquial.group(2))
            return sign * (whole * 1_000_000 + tenth * 100_000)

        match = re.search(r"ngân sách\s*(-?[\d\.,]+)\s*(triệu|ngàn|nghìn|đồng|vnđ)?", question, re.IGNORECASE)
        if not match:
            return None
        raw, unit = match.group(1), (match.group(2) or "").lower()
        number = float(raw.replace(".", "").replace(",", "."))
        if unit == "triệu":
            return int(number * 1_000_000)
        if unit in ("ngàn", "nghìn"):
            return int(number * 1_000)
        return int(number)

    @staticmethod
    def _extract_group_size(question: str):
        match = re.search(r"(\d+)\s*người", question)
        return int(match.group(1)) if match else None

    @staticmethod
    def _extract_exclusions(rule_observation: str) -> list:
        match = re.search(r"loại_trừ gợi ý dùng cho search_gift_catalog:\s*(\[.*?\])", rule_observation)
        if not match:
            return []
        try:
            return ast.literal_eval(match.group(1))
        except (ValueError, SyntaxError):
            return []

    @staticmethod
    def _compose_final_answer(done: dict) -> str:
        errors = [obs for obs in done.values() if obs.startswith("LỖI")]
        if errors or not done:
            return (
                "Thought: Một số bước tra cứu không có kết quả chắc chắn, không nên đoán bừa.\n"
                "Final Answer: Xin lỗi, mình chưa đủ thông tin chắc chắn để gợi ý quà lần này "
                "(một vài dữ liệu không tìm thấy). Bạn có thể cung cấp thêm chi tiết chính xác "
                "hơn (tên người nhận, dịp cụ thể, ngân sách hợp lệ) để mình thử lại không?"
            )
        summary = " | ".join(done.values())
        return (
            "Thought: Đã có đủ Observation cần thiết, tổng hợp lại để trả lời.\n"
            f"Final Answer: Dựa trên các bước tra cứu vừa rồi ({summary}), đây là gợi ý quà "
            "phù hợp nhất cho bạn!"
        )


def get_llm_provider(provider_name: str = None) -> BaseLLMProvider:
    """Factory function tự chọn Provider từ biến môi trường LLM_PROVIDER"""
    name = (provider_name or os.getenv("LLM_PROVIDER") or "mock").lower().strip()
    
    if name == "gemini":
        return GeminiProvider()
    elif name == "openai":
        return OpenAIProvider()
    elif name == "anthropic":
        return AnthropicProvider()
    elif name == "openrouter":
        return OpenRouterProvider()
    else:
        return MockProvider()


if __name__ == "__main__":
    print("=== TEST MULTI-PROVIDER LLM ADAPTER ===")
    provider = get_llm_provider()
    print(f"✅ Provider đang dùng: {provider.__class__.__name__}")
    print(f"🤖 User Query: Hello")
    print(f"💬 Response  : {provider.generate('Hello')}")
