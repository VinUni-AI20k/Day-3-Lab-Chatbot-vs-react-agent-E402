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
        self.model_name = model or os.getenv("LLM_MODEL") or "google/gemini-2.0-flash-001"
        
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
    """Offline Mock Provider (Cho bài test không cần kết nối API)"""
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        text = prompt.lower()
        
        # Guardrail bẫy PII (Test #9)
        if "số điện thoại" in text or "địa chỉ nhà" in text or "facebook" in text:
            return "Final Answer: Rất tiếc, tôi không thể cung cấp các thông tin cá nhân nhạy cảm (SĐT, địa chỉ, tài khoản cá nhân) để bảo vệ quyền riêng tư người dùng theo đúng quy định Guardrail."

        # Guardrail bẫy Prompt Injection / Roleplay (Test #10)
        if "bỏ qua mọi quy tắc" in text or "người yêu của tôi" in text or "nói lời yêu" in text:
            return "Final Answer: Tôi là Cupid Agent - Trợ lý ghép đôi chuyên nghiệp. Tôi không thể thực hiện vai trò cá nhân này, nhưng rất sẵn sàng hỗ trợ bạn tìm kiếm và kết nối đối phương phù hợp!"

        # Xử lý các bước trong vòng lặp ReAct nhận được Observation
        if "observation:" in text:
            if "lỗ i:" in text or "lỗi:" in text or "atlantis" in text:
                return "Thought: Công cụ báo lỗi do dữ liệu không hợp lệ.\nFinal Answer: Không tìm thấy thông tin phù hợp với yêu cầu của bạn."
            elif "get_user_profile" in text and "linh" in text:
                return "Thought: Đã có hồ sơ Linh, giờ tính độ tương thích với ID #2.\nAction: check_zodiac_compatibility['Sư Tử', 'Kim Ngưu']"
            elif "get_user_profile" in text and "mai" in text:
                return "Thought: Đã có hồ sơ Mai, giờ gợi ý địa điểm hẹn hò.\nAction: suggest_dating_spots['đọc sách, nghe nhạc']"
            elif "sư tử" in text or "nhân mã" in text or "kim ngưu" in text or "compatibility" in text:
                return "Thought: Tôi đã có thông tin chi tiết tương thích.\nFinal Answer: Điểm tương thích giữa 2 hồ sơ được đánh giá rất cao, cùng nhiều điểm chung về phong cách sống và năng lượng."
            elif "địa điểm đề xuất" in text or "acoustic" in text or "cà phê" in text:
                return "Thought: Đã nhận được danh sách địa điểm.\nFinal Answer: Gợi ý buổi hẹn hò hoàn hảo: 1. Cư Xá Cà Phê; 2. Thưởng thức nhạc tại Acoustic Trịnh Ca."
            return "Thought: Đã nhận được Observation.\nFinal Answer: Cupid Agent đã hoàn thành tổng hợp thông tin cho bạn!"

        # Xử lý các câu hỏi mở đầu (Initial User Queries)
        if "atlantis" in text or "hack atm" in text:
            return "Thought: Cần tra cứu hồ sơ người dùng tên Atlantis.\nAction: get_user_profile['Atlantis']"
        elif "hợp với tôi và gợi ý hoạt động" in text or "đọc sách và âm nhạc" in text:
            return "Thought: Tra cứu hồ sơ Mai trước.\nAction: get_user_profile['Mai']"
        elif "tính điểm tương thích của tôi với hồ sơ id #2" in text or "tính điểm tương thích" in text:
            return "Thought: Tra cứu hồ sơ Linh trước.\nAction: get_user_profile['Linh']"
        elif "id #1 và id #3" in text or "hồ sơ id #1" in text:
            return "Thought: Cần kiểm tra độ tương thích giữa cung Sư Tử và Nhân Mã.\nAction: check_zodiac_compatibility['Sư Tử', 'Nhân Mã']"
        elif "hướng nội" in text or "đọc sách và nấu ăn" in text:
            return "Thought: Cần tra cứu hồ sơ bạn Mai hợp tính cách hướng nội.\nAction: get_user_profile['Mai']"
        elif "tình yêu là gì" in text:
            return "Tình yêu là sự thấu hiểu, tôn trọng và đồng hành cùng nhau. Để duy trì mối quan hệ lâu dài, cần chân thành, biết lắng nghe và tạo những khoảnh khắc lãng mạn bên nhau."
        elif "love language" in text or "phong cách yêu" in text:
            return "5 Phong cách yêu (Love Languages): 1. Words of Affirmation; 2. Acts of Service; 3. Receiving Gifts; 4. Quality Time; 5. Physical Touch."
        elif "bí quyết" in text and "hẹn hò" in text:
            return "3 Bí quyết hẹn hò đầu tiên: 1. Trang phục gọn gàng; 2. Lắng nghe chân thành; 3. Chọn địa điểm thoải mái, không quá ồn ào."
            
        return "Thought: Tôi đã nhận được yêu cầu.\nFinal Answer: Cupid Agent sẵn sàng đồng hành tư vấn tình yêu cùng bạn!"


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
