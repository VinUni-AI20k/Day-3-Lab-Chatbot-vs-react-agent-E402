import os
import sys
from dotenv import load_dotenv

load_dotenv()

class GroqProvider:
    """Bộ chuyển đổi (Adapter) kết nối tới Groq Cloud API"""
    def __init__(self, model_name=None, api_key=None):
        try:
            from groq import Groq
        except ImportError:
            print("⚠️ Thư viện groq chưa được cài. Vui lòng chạy: pip install groq")
            sys.exit(1)
        
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("Không tìm thấy GROQ_API_KEY trong file .env!")
            
        self.client = Groq(api_key=self.api_key)
        # Sử dụng model được chỉ định hoặc mặc định là llama-3.3-70b-specdec
        self.model_name = model_name or os.getenv("LLM_MODEL") or "llama-3.3-70b-specdec"

    def generate(self, prompt: str, system_prompt: str = None) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.1,  # Nhiệt độ thấp giúp sinh SQL chuẩn xác, ít ngẫu nhiên
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"[Groq Exception]: {e}"


class GeminiProvider:
    """Bộ chuyển đổi (Adapter) kết nối tới Google Gemini API (Sử dụng SDK cũ ổn định)"""
    def __init__(self, model_name=None, api_key=None):
        try:
            import google.generativeai as genai
        except ImportError:
            print("⚠️ Thư viện google-generativeai chưa được cài. Vui lòng chạy: pip install google-generativeai")
            sys.exit(1)

        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("Không tìm thấy GEMINI_API_KEY hoặc GOOGLE_API_KEY trong file .env!")
            
        genai.configure(api_key=self.api_key)
        self.model_name = model_name or os.getenv("LLM_MODEL") or "gemini-2.0-flash"
        self.model = genai.GenerativeModel(self.model_name)

    def generate(self, prompt: str, system_prompt: str = None) -> str:
        try:
            # Nếu có system prompt, truyền vào phần cấu hình sinh nội dung
            config = {}
            if system_prompt:
                # Cú pháp truyền system instruction cho SDK google-generativeai
                self.model = genai.GenerativeModel(
                    model_name=self.model_name,
                    system_instruction=system_prompt
                )
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"[Gemini Exception]: {e}"


def get_llm_provider():
    """Hàm nhà máy (Factory function) khởi tạo Provider dựa theo cấu hình .env"""
    load_dotenv()
    provider_name = os.getenv("LLM_PROVIDER", "gemini").lower()
    model_name = os.getenv("LLM_MODEL")

    if provider_name == "groq":
        return GroqProvider(model_name=model_name)
    elif provider_name == "gemini":
        return GeminiProvider(model_name=model_name)
    else:
        # Dự phòng mặc định quay về Gemini nếu cấu hình sai tên
        print(f"⚠️ Không nhận diện được Provider '{provider_name}'. Tự động chuyển về Gemini.")
        return GeminiProvider(model_name=model_name)