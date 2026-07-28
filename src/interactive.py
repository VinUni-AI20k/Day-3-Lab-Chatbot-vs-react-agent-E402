"""
Interactive CLI cho ReAct Agent.
Cho phép người dùng nhập câu hỏi tùy ý liên tục để chat với Agent.
"""

import sys
import os

# Đảm bảo import các module từ thư mục src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import run_react_agent
from providers import get_llm_provider

def main():
    print("================================================================")
    print("🤖 CHÀO MỪNG ĐẾN VỚI TRỢ LÝ TÌM KIẾM NHÀ TRỌ (INTERACTIVE MODE)")
    print("================================================================")
    
    # Khởi tạo LLM Provider
    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print(f"🔌 Đang sử dụng Provider: {provider.__class__.__name__} (Model: {model_name})")
    print("💡 Mẹo: Nhập 'exit', 'quit' hoặc 'q' để thoát khỏi chương trình.")
    
    while True:
        try:
            query = input("\n👤 Bạn: ").strip()
            if not query:
                continue
                
            if query.lower() in ("exit", "quit", "q"):
                print("👋 Tạm biệt! Hẹn gặp lại bạn lần sau.")
                break
                
            # Gọi ReAct Agent để xử lý
            run_react_agent(query, provider)
            
        except KeyboardInterrupt:
            print("\n👋 Đã ngắt kết nối. Tạm biệt!")
            break
        except Exception as e:
            print(f"\n❌ Đã xảy ra lỗi: {e}")

if __name__ == "__main__":
    main()
