"""
🔌 MULTI-PROVIDER LLM ADAPTER (OpenAI, Gemini, Anthropic, OpenRouter & Offline Mock)
Hỗ trợ chuyển đổi linh hoạt giữa các nhà cung cấp AI chỉ bằng cách đổi biến môi trường LLM_PROVIDER.
"""

import os
import sys
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
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        raise NotImplementedError


class GeminiProvider(BaseLLMProvider):
    """Google Gemini Provider"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gemini-2.0-flash"
        
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
    """
    Offline Mock Provider — Mô phỏng luồng ReAct Agent 3 bước
    cho chủ đề định hướng nghề nghiệp (không cần API key).

    Step 1: assess_user_profile
    Step 2: search_careers
    Step 3: Final Answer
    """

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        p = prompt.lower()

        # Nếu đã có Observation từ search_careers → Final Answer
        if "search_careers" in p and "observation" in p:
            return (
                "Thought: Tôi đã có kết quả tìm kiếm nghề nghiệp phù hợp. "
                "Tôi đủ thông tin để đưa ra câu trả lời cuối cùng.\n"
                "Final Answer: Dựa trên hồ sơ của bạn (tốt nghiệp CNTT, "
                "biết Python và Excel, thích dữ liệu và logic), các nghề phù hợp nhất là:\n"
                "1. 📊 Data Analyst — Phân tích dữ liệu, xây dựng báo cáo và dashboard.\n"
                "2. 💻 Software Developer — Lập trình xây dựng ứng dụng, phù hợp tư duy logic.\n"
                "3. 🔬 Data Scientist — Xây dựng mô hình ML, cần nền tảng toán tốt hơn.\n\n"
                "Kỹ năng cần học thêm cho Data Analyst: SQL, Thống kê, Trực quan hóa dữ liệu (Power BI/Tableau).\n"
                "Bước tiếp theo: Hoàn thiện một dự án portfolio nhỏ bằng Python + SQL, nộp thực tập Data Analyst."
            )

        # Nếu đã có Observation từ assess_user_profile → gọi search_careers
        if "assess_user_profile" in p and "observation" in p:
            return (
                'Thought: Tôi đã có hồ sơ người dùng chuẩn hóa. '
                'Bước tiếp theo là tìm kiếm nghề phù hợp theo sở thích và kỹ năng.\n'
                'Action: search_careers[{"interests": ["dữ liệu", "logic", "công nghệ"], '
                '"skills": ["Python", "Excel"]}]'
            )

        # Bước đầu: gọi assess_user_profile
        return (
            "Thought: Người dùng cung cấp thông tin về nền tảng học vấn, "
            "kỹ năng và sở thích. Tôi cần chuẩn hóa hồ sơ trước khi tìm kiếm nghề phù hợp.\n"
            'Action: assess_user_profile[{"education": "Cử nhân Công nghệ Thông tin", '
            '"skills": ["Python", "Excel"], '
            '"interests": ["dữ liệu", "logic", "công nghệ"], '
            '"personality": "Thích làm việc với dữ liệu và logic", '
            '"goals": "Tìm nghề phù hợp và lộ trình phát triển kỹ năng"}]'
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
