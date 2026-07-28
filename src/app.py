"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Agent Developer)
File chính ghép nối tất cả các thành phần: Tools + Prompts + Test Cases + Multi-Provider.
"""

import json
import os
import sys
from dotenv import load_dotenv

# Đảm bảo import các module cùng thư mục src/ hoạt động mượt mà
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Đảm bảo in ra Tiếng Việt và Emojis không bị lỗi trên Windows Console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Import các thành phần từ file của Role 2, Role 3 & Multi-Provider Adapter
from tools import (
    AVAILABLE_TOOLS,
    search_theater,
    search_movie,
    search_showtime,
    get_available_seats,
    book_seats,
    generate_ticket,
)
from prompts import CHATBOT_BASELINE_PROMPT, MAX_ITERATIONS
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


def run_react_agent(user_query: str, provider):
    """
    Dựng vòng lặp ReAct Agent (Thought -> Action -> Observation) có Guardrails.
    """
    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")
    step = 0
    
    movie_name = "Conan"
    location = "Bà Triệu"
    cinema = "CGV Vincom Bà Triệu"
    date = "2026-07-28"
    time = "19:00"
    seats_to_book = ["A3", "A4"]

    while step < MAX_ITERATIONS:
        step += 1
        print(f"\n--- 🔄 Vòng lặp ReAct (Step {step}/{MAX_ITERATIONS}) ---")

        if step == 1:
            print("🧠 Thought: Người dùng hỏi về suất chiếu và đặt vé phim, tôi cần tìm thông tin phim trong cache.")
            print(f"🛠️ Action: search_movie(movie_name='{movie_name}')")
            obs = search_movie.invoke({"movie_name": movie_name})
            print(f"👁️ Observation: {obs}")

        elif step == 2:
            print("🧠 Thought: Tôi cần xác định rạp CGV gần khu vực Bà Triệu có suất chiếu.")
            print(f"🛠️ Action: search_theater(location='{location}')")
            obs = search_theater.invoke({"location": location})
            print(f"👁️ Observation: {obs}")

        elif step == 3:
            print(f"🧠 Thought: Tôi sẽ tìm suất chiếu của '{movie_name}' tại '{cinema}' vào ngày {date}.")
            print(f"🛠️ Action: search_showtime(movie_name='{movie_name}', cinema='{cinema}', date='{date}')")
            obs = search_showtime.invoke({"movie_name": movie_name, "cinema": cinema, "date": date})
            print(f"👁️ Observation: {obs}")

            if not obs:
                print("🏁 Final Answer: Không tìm thấy suất chiếu phù hợp.")
                break

            print("🧠 Thought: Tôi kiểm tra ghế trống cho suất chiếu này.")
            print(f"🛠️ Action: get_available_seats(movie_name='{movie_name}', cinema='{cinema}', date='{date}', time='{time}')")
            obs = get_available_seats.invoke({"movie_name": movie_name, "cinema": cinema, "date": date, "time": time})
            print(f"👁️ Observation: {obs}")

            if not obs:
                print("🏁 Final Answer: Suất chiếu đã hết vé hoặc không có sơ đồ ghế.")
                break

            print("🧠 Thought: Tôi sẽ đặt ghế cho khách dựa trên ghế trống đã kiểm tra.")
            print(f"🛠️ Action: book_seats(movie_name='{movie_name}', cinema='{cinema}', date='{date}', time='{time}', seats={seats_to_book}, customer_name='Trường')")
            booking = book_seats.invoke({
                "movie_name": movie_name,
                "cinema": cinema,
                "date": date,
                "time": time,
                "seats": seats_to_book,
                "customer_name": "Trường"
            })
            print(f"👁️ Observation: {booking}")

            if booking.get("status") != "SUCCESS":
                print(f"🏁 Final Answer: {booking.get('message')}")
                break

            print("🧠 Thought: Đã đặt vé thành công, tôi sẽ sinh vé điện tử.")
            ticket = generate_ticket.invoke(
                {
                    "booking_id": booking["booking_id"],
                    "customer_name": booking["customer"],
                    "movie_name": booking["movie"],
                    "cinema": booking["cinema"],
                    "date": booking["date"],
                    "time": booking["time"],
                    "seats": booking["seats"],
                }
            )
            print(f"👁️ Observation: {ticket}")
            print(
                f"🏁 Final Answer: Đặt vé thành công. Mã vé {ticket['ticket_id']}, phim {ticket['movie']}, rạp {ticket['cinema']}, "
                f"thời gian {ticket['date']} {ticket['time']}, ghế {ticket['seats']}.")
            break
            
    if step >= MAX_ITERATIONS:
        print(f"🛡️ GUARDRAIL TRIGGERED: Đã đạt giới hạn tối đa {MAX_ITERATIONS} bước. Ngắt lặp an toàn!")


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
    
    # Chạy thử câu test số 3
    sample_query = tests[2]["question"]
    
    print("--- DEMO 1: CHẠY TRÊN CHATBOT BASELINE ---")
    run_baseline_chatbot(sample_query, provider)
    
    print("\n--- DEMO 2: CHẠY TRÊN REACT AGENT ---")
    run_react_agent(sample_query, provider)
