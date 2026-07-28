"""
🔌 MULTI-PROVIDER LLM ADAPTER — LangChain Edition
Trả về LangChain ChatModel qua init_chat_model. API keys tự đọc từ biến môi trường.
"""

import os
import warnings

# Bỏ qua DeprecationWarning từ các package upstream (vd: google-genai trên Python 3.14)
warnings.filterwarnings("ignore", category=DeprecationWarning)

from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage


# ── Alias provider → init_chat_model model_provider ─────────────────────────
# Các provider có thể dùng alias ngắn gọn; init_chat_model tự xử lý env key tương ứng:
#   Gemini      → google-genai (key: GOOGLE_API_KEY)
#   OpenAI      → openai       (key: OPENAI_API_KEY)
#   Anthropic   → anthropic    (key: ANTHROPIC_API_KEY)
#   OpenRouter  → openai-compat via OpenRouter endpoint (key: OPENROUTER_API_KEY)

PROVIDER_ALIASES = {
    "gemini": {"model_provider": "google_genai"},
    "google_genai": {"model_provider": "google_genai"},
    "openai": {"model_provider": "openai"},
    "anthropic": {"model_provider": "anthropic"},
    "openrouter": {
        "model_provider": "openai",
        "base_url": "https://openrouter.ai/api/v1",
        "_api_key_env": "OPENROUTER_API_KEY",
    },
}


def get_llm_provider(model: str = None, provider: str = None, **extra_kwargs):
    """
    Trả về LangChain ChatModel qua init_chat_model.
    API keys tự đọc từ biến môi trường tương ứng.

    Args:
        model: Tên model (vd: "gemini-2.5-flash", "gpt-4o-mini", "claude-3-haiku-20240307").
               Mặc định đọc từ biến môi trường LLM_MODEL.
        provider: "gemini" | "google_genai" | "openai" | "anthropic" | "openrouter".
                  Mặc định đọc từ biến môi trường LLM_PROVIDER.
        **extra_kwargs: Tham số truyền thêm cho init_chat_model (vd: temperature, max_tokens, thinking=...)

    Returns:
        LangChain BaseChatModel — gọi .invoke(messages) để sử dụng.

    Raises:
        ValueError: Nếu chưa cấu hình API key cho provider tương ứng.

    Ví dụ:
        >>> llm = get_llm_provider("gemini-2.5-flash", "gemini")
        >>> response = llm.invoke([HumanMessage(content="Xin chào!")])
        >>> print(response.content)
    """
    # 1. Resolve model + provider từ env hoặc param truyền vào
    model = model or os.getenv("LLM_MODEL") or "gpt-4o-mini"
    provider_name = (provider or os.getenv("LLM_PROVIDER") or "openai").lower().strip()

    # 2. Xử lý provider "mock" (không phải init_chat_model provider) → FakeListChatModel
    if provider_name == "mock":
        from langchain_core.language_models import FakeListChatModel

        llm = FakeListChatModel(
            responses=[
                "[Mock Mode]: Chưa cấu hình API key. Set LLM_PROVIDER để dùng model thật."
            ]
        )
        object.__setattr__(llm, "model_name", "mock")
        object.__setattr__(llm, "_provider_name", "mock")
        return llm

    # 3. Lấy cấu hình provider từ alias map (hỗ trợ cả alias "gemini" → "google_genai")
    config = PROVIDER_ALIASES.get(provider_name, {"model_provider": provider_name})

    # 4. Build kwargs cho init_chat_model
    init_kwargs = {"model": model, "model_provider": config["model_provider"]}

    # Copy các key còn lại (vd: base_url) trừ _api_key_env (key đặc biệt cho map env → openai_api_key)
    api_key_env = config.get("_api_key_env")
    for key, value in config.items():
        if not key.startswith("_"):
            init_kwargs[key] = value

    # 5. Với provider cần key env variable riêng (vd: OpenRouter dùng OPENROUTER_API_KEY thay vì OPENAI_API_KEY)
    if api_key_env:
        env_key = os.getenv(api_key_env)
        if not env_key:
            raise ValueError(
                f"Biến môi trường {api_key_env} chưa được thiết lập. "
                f"Vui lòng set {api_key_env} trong .env hoặc export trong terminal."
            )
        # OpenRouter dùng OpenAI-compat → cần openai_api_key
        init_kwargs["openai_api_key"] = env_key

    # 6. Merge kwargs truyền thêm từ caller (vd: thinking, temperature, ...)
    init_kwargs.update(extra_kwargs)

    # 7. Khởi tạo ChatModel qua LangChain init_chat_model
    try:
        llm = init_chat_model(**init_kwargs)
    except (ValueError, ImportError) as e:
        raise ValueError(
            f"Không thể khởi tạo model '{model}' với provider '{provider_name}'. Lỗi: {e}"
        ) from e

    # 8. Gắn metadata để app.py có thể đọc tên model + provider dễ dàng
    llm._provider_name = provider_name  # type: ignore[attr-defined]
    return llm


# ── Demo nhanh (không bắt buộc) ──────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 55)
    print("  🔌 providers.py — get_llm_provider() Demo")
    print("=" * 55)

    try:
        llm = get_llm_provider(
            model="google/gemma-4-31b-it",
            provider="openrouter",
        )
    except ValueError as e:
        print(f"\n⚠️  {e}")
        print("💡 Thiết lập biến môi trường rồi chạy lại:")
        print('   export LLM_PROVIDER="openai"')
        print('   export OPENAI_API_KEY="sk-..."')
        # Fallback: chạy mock test
        print("\n🧪 Đang chạy mock test (không cần API key)...")
        llm = get_llm_provider(provider="mock")

    model_id = getattr(llm, "model_name", None) or getattr(llm, "model", "?")
    print(f"\n📡 Provider : {getattr(llm, '_provider_name', '?')}")
    print(f"🤖 Class    : {llm.__class__.__name__}")
    print(f"🔧 Model ID : {model_id}")

    # Test invoke đơn giản
    print("\n" + "─" * 55)
    print("  💬 Test invoke:")
    print("─" * 55)
    try:
        response = llm.invoke(
            [HumanMessage(content="Xin chào, nói một câu tiếng Việt!")]
        )
        print(f"\n👤 User: Xin chào, nói một câu tiếng Việt!")
        print(f"🤖 Bot :\n{response.content}")
    except Exception as e:
        print(f"\n❌ Invoke failed: {e}")
        print("   (Đây là test mock — cấu hình API key thật rồi chạy lại.)")
