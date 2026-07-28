"""
🔌 MULTI-PROVIDER LLM ADAPTER (OpenAI, Gemini, Anthropic, OpenRouter & Offline Mock)
Hỗ trợ chuyển đổi linh hoạt giữa các nhà cung cấp AI chỉ bằng cách đổi biến môi trường LLM_PROVIDER.
"""

import os
import re
import sys

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv():
        """Cho phép MockProvider chạy khi chưa cài python-dotenv."""


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
            import requests

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

    @staticmethod
    def _extract_react_parts(prompt: str):
        match = re.search(
            r"USER QUESTION:\s*(.*?)\s*TRACE SO FAR:\s*(.*)",
            prompt,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if not match:
            return prompt.lower(), ""
        return match.group(1).strip().lower(), match.group(2).lower()

    def _generate_react(self, prompt: str) -> str:
        question, trace = self._extract_react_parts(prompt)

        if "3 cách" in question and "bắt đầu cuộc trò chuyện" in question:
            return (
                "Thought: Đây là câu hỏi tư vấn chung, không cần dữ liệu hệ thống.\n"
                "Final Answer: Bạn có thể chào hỏi tự nhiên, hỏi một câu mở dựa "
                "trên hoàn cảnh chung và lắng nghe chân thành. Hãy tôn trọng ranh "
                "giới của người đối diện."
            )

        if "mối quan hệ nghiêm túc" in question and "yếu tố" in question:
            return (
                "Thought: Đây là câu hỏi kiến thức chung, không cần gọi tool.\n"
                "Final Answer: Một mối quan hệ nghiêm túc cần sự tôn trọng, giao "
                "tiếp trung thực, tin cậy, đồng thuận về kỳ vọng và khả năng cùng "
                "giải quyết bất đồng."
            )

        if "quick sort" in question:
            return (
                "Thought: Yêu cầu lập trình nằm ngoài phạm vi Cupid Agent.\n"
                "Final Answer: Yêu cầu này ngoài phạm vi Cupid Agent. Bạn nên sử "
                "dụng một trợ lý lập trình để được hỗ trợ phù hợp hơn."
            )

        if "thời tiết" in question:
            return (
                "Thought: Yêu cầu thời tiết nằm ngoài phạm vi và không có tool phù hợp.\n"
                "Final Answer: Cupid Agent không hỗ trợ tra cứu thời tiết. Bạn vui "
                "lòng sử dụng một dịch vụ dự báo thời tiết."
            )

        if "một ứng viên phù hợp" in question:
            return (
                "Thought: Yêu cầu chưa có tên hoặc MSSV để xác định hồ sơ.\n"
                "Final Answer: Bạn cần cung cấp tên hoặc MSSV của ứng viên cần xem "
                "để tôi truy xuất đúng hồ sơ."
            )

        if "piano" in question and "đan len" in question:
            if "action: search_candidate_profiles" not in trace:
                return (
                    "Thought: Cần tìm ứng viên theo đầy đủ các tiêu chí đã nêu.\n"
                    'Action: search_candidate_profiles["bạn nam chơi piano, '
                    'biết nấu ăn và đan len"]'
                )
            return (
                "Thought: Observation cho biết không có ứng viên phù hợp, nên phải "
                "dừng an toàn và không bịa hồ sơ.\n"
                "Final Answer: Hiện không tìm thấy ứng viên nào đáp ứng đầy đủ các "
                "tiêu chí. Bạn có thể mở rộng hoặc ưu tiên lại một vài tiêu chí."
            )

        if "so sánh phương" in question:
            if "action: get_user_profile" not in trace:
                return (
                    "Thought: Cần lấy hồ sơ hiện tại làm cơ sở so sánh.\n"
                    'Action: get_user_profile["current_user"]'
                )
            if "action: calculate_compatibility" not in trace:
                return (
                    "Thought: Đã có hồ sơ người dùng, cần tính điểm cho Phương và Lan.\n"
                    'Action: calculate_compatibility["current_user", '
                    '["Phương", "Lan"]]'
                )
            if "action: synthesize_recommendation" not in trace:
                return (
                    "Thought: Observation xếp Phương cao hơn Lan, cần tổng hợp cặp "
                    "đứng đầu.\n"
                    'Action: synthesize_recommendation["current_user", "Phương"]'
                )
            return (
                "Thought: Đã có điểm và gói tổng hợp làm bằng chứng.\n"
                "Final Answer: Phương phù hợp hơn với Minh: Phương đạt 94/100, "
                "còn Lan đạt 88/100. Phương cùng mục tiêu nghiêm túc và cùng thích "
                "đọc sách. Điểm số chỉ mang tính tham khảo; hai bạn vẫn nên trò "
                "chuyện để kiểm chứng sự phù hợp."
            )

        if "3 người phù hợp nhất" in question or "phù hợp nhất" in question:
            if "action: get_user_profile" not in trace:
                return (
                    "Thought: Cần lấy hồ sơ hiện tại trước khi tìm người phù hợp.\n"
                    'Action: get_user_profile["current_user"]'
                )
            if "action: search_candidate_profiles" not in trace:
                return (
                    "Thought: Hồ sơ cho biết mục tiêu nghiêm túc, cần lọc ứng viên "
                    "cùng mục tiêu.\n"
                    'Action: search_candidate_profiles["mối quan hệ nghiêm túc"]'
                )
            if "action: calculate_compatibility" not in trace:
                return (
                    "Thought: Đã tìm thấy Mai, Lan và Phương; cần tính và xếp hạng.\n"
                    'Action: calculate_compatibility["current_user", '
                    '["Mai", "Lan", "Phương"]]'
                )
            if "action: synthesize_recommendation" not in trace:
                return (
                    "Thought: Mai có điểm cao nhất trong Observation, cần tổng hợp "
                    "khuyến nghị cuối.\n"
                    'Action: synthesize_recommendation["current_user", "Mai"]'
                )
            return (
                "Thought: Đã có đủ Observation để trả lời có căn cứ.\n"
                "Final Answer: Ba ứng viên phù hợp nhất là Mai 98/100, Phương "
                "94/100 và Lan 88/100. Mai đứng đầu vì cùng mục tiêu nghiêm túc "
                "và cùng thích đọc sách với Minh. Điểm cần lưu ý là dữ liệu chỉ "
                "hỗ trợ tham khảo. Gợi ý mở đầu: \"Chào Mai, gần đây bạn đọc cuốn "
                "sách nào khiến bạn ấn tượng nhất?\""
            )

        return (
            "Thought: Yêu cầu chưa đủ rõ để chọn tool an toàn.\n"
            "Final Answer: Bạn vui lòng cung cấp thêm tên, MSSV hoặc tiêu chí cụ thể."
        )

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if "QUY TẮC REACT" in system_prompt and "AVAILABLE TOOLS" in system_prompt:
            return self._generate_react(prompt)

        text = prompt.lower()
        if "3 cách" in text and "bắt đầu cuộc trò chuyện" in text:
            return (
                "Bạn có thể: (1) chào hỏi và giới thiệu ngắn gọn, "
                "(2) hỏi một câu mở dựa trên hoàn cảnh chung, "
                "(3) lắng nghe và phản hồi chân thành. "
                "Hãy giữ thái độ tự nhiên và tôn trọng ranh giới của đối phương."
            )
        if "mối quan hệ nghiêm túc" in text and "yếu tố" in text:
            return (
                "Một mối quan hệ nghiêm túc thường cần sự tôn trọng, giao tiếp "
                "trung thực, tin cậy, đồng thuận về kỳ vọng và khả năng cùng giải "
                "quyết bất đồng."
            )
        if "phù hợp nhất" in text or "so sánh phương" in text:
            return (
                "Tôi chưa thể đưa ra kết luận vì chatbot thông thường không có "
                "quyền truy cập hồ sơ đã lưu hoặc công cụ tính độ tương thích. "
                "Bạn có thể cung cấp thông tin của từng người để tôi nhận xét sơ bộ."
            )
        if "hãy tìm cho tôi" in text:
            return (
                "Tôi không thể kiểm tra danh sách ứng viên vì không có quyền truy "
                "cập cơ sở dữ liệu. Tôi sẽ không tự tạo hồ sơ không có căn cứ."
            )
        return (
            "Tôi có thể tư vấn dựa trên thông tin bạn cung cấp, nhưng không thể "
            "truy cập hồ sơ hoặc dữ liệu hệ thống."
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
