"""
🔌 MULTI-PROVIDER LLM ADAPTER (OpenAI, Gemini, Anthropic, OpenRouter & Offline Mock)
Hỗ trợ chuyển đổi linh hoạt giữa các nhà cung cấp AI chỉ bằng cách đổi biến môi trường LLM_PROVIDER.
"""

import os
import sys
import json
import re
import unicodedata
import requests
from dotenv import load_dotenv

# Đảm bảo in ra Tiếng Việt và Emojis không bị lỗi trên Windows Console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()


def _fold_text(value: str) -> str:
    """Lowercase and remove Vietnamese accents for keyword guardrails."""
    decomposed = unicodedata.normalize("NFD", value.casefold())
    without_marks = "".join(
        char for char in decomposed if unicodedata.category(char) != "Mn"
    )
    return without_marks.replace("đ", "d")


class BaseLLMProvider:
    """Interface cơ sở cho tất cả các LLM Provider"""
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        raise NotImplementedError


class GeminiProvider(BaseLLMProvider):
    """Google Gemini Provider"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gemini-2.5-flash"
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            return "[Gemini Error]: Chưa cấu hình GEMINI_API_KEY trong file .env!"
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            contents = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            response = client.models.generate_content(
                model=self.model_name,
                contents=contents
            )
            return response.text
        except Exception as e:
            return f"[Gemini Exception]: {str(e)}"


class OpenAIProvider(BaseLLMProvider):
    """OpenAI Provider (GPT-4o, GPT-3.5-turbo, etc.)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gpt-4o-mini"
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            return "[OpenAI Error]: Chưa cấu hình OPENAI_API_KEY trong file .env!"
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"[OpenAI Exception]: {str(e)}"


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude Provider (Claude 3.5 Sonnet, Claude 3 Haiku)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "claude-3-haiku-20240307"
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
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
                
            response = client.messages.create(**kwargs)
            return response.content[0].text
        except Exception as e:
            return f"[Anthropic Exception]: {str(e)}"


class OpenRouterProvider(BaseLLMProvider):
    """OpenRouter Provider (Hỗ trợ gọi mọi model qua OpenRouter API)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "google/gemini-2.5-flash"
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
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
            res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=30)
            if res.status_code == 200:
                data = res.json()
                return data["choices"][0]["message"]["content"]
            else:
                return f"[OpenRouter API Error {res.status_code}]: {res.text}"
        except Exception as e:
            return f"[OpenRouter Exception]: {str(e)}"


class MockProvider(BaseLLMProvider):
    """Offline deterministic provider for the recruitment test cases."""
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        text = prompt.casefold()
        normalized_text = _fold_text(prompt)
        baseline = system_prompt.casefold()

        if "không có khả năng truy cập cơ sở dữ liệu" in baseline:
            return (
                "Tôi có thể tư vấn chung về tuyển dụng, nhưng không thể xác nhận "
                "dữ liệu JobID, UserID hoặc điểm phù hợp khi chưa được cấp tool."
            )

        if "gioi tinh" in normalized_text or "gender" in normalized_text or "tuoi" in normalized_text:
            return (
                "Thought: Yêu cầu dùng thuộc tính nhạy cảm không phù hợp.\n"
                "Final Answer: Tôi không thể chấm hoặc xếp hạng theo giới tính hay tuổi. "
                "Tôi có thể đánh giá theo kỹ năng, kinh nghiệm, ngành và địa điểm."
            )

        score_request = re.search(r"userid\s+(\d+).*?jobid\s+(\d+)", text)
        if score_request:
            user_id, job_id = score_request.groups()
            if "observation: lỗi:" in text:
                return (
                    "Thought: Dữ liệu đầu vào không hợp lệ.\n"
                    "Final Answer: Tôi không thể chấm điểm vì không tìm thấy JobID hoặc UserID. "
                    "Vui lòng kiểm tra lại mã dữ liệu."
                )
            if f"observation: job [{job_id}]" not in text:
                return f"Thought: Cần đọc yêu cầu công việc trước.\nAction: get_job_description[{job_id}]"
            if f"observation: ứng viên [{user_id}]" not in text:
                return f"Thought: Cần đọc hồ sơ ứng viên trước khi chấm.\nAction: get_candidate_profile[{user_id}]"
            if "observation: đánh giá hỗ trợ hr" not in text:
                return f"Thought: Đã có JD và hồ sơ, cần chấm mức phù hợp.\nAction: score_candidate[{job_id}, {user_id}]"
            return (
                "Thought: Đã có kết quả chấm từ dữ liệu.\n"
                f"Final Answer: Tôi đã chấm điểm UserID {user_id} theo JobID {job_id}. "
                "HR cần xem hồ sơ gốc trước quyết định."
            )

        job_request = re.search(r"jobid\s+(\d+)", text)
        if job_request:
            job_id = job_request.group(1)
            if f"observation: job [{job_id}]" not in text:
                return f"Thought: Cần tra cứu JobID được yêu cầu.\nAction: get_job_description[{job_id}]"
            return (
                "Thought: Đã có mô tả công việc.\n"
                f"Final Answer: Tôi đã lấy thông tin chi tiết của công việc JobID {job_id} từ dữ liệu."
            )

        return (
            "Thought: Câu hỏi này không cần tra cứu dữ liệu.\n"
            "Final Answer: Hãy trình bày kinh nghiệm, kỹ năng liên quan và thành tựu cụ thể; "
            "đồng thời chuẩn bị ví dụ thực tế trước buổi phỏng vấn."
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
