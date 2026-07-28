"""
💘 AI MATCHMAKING AGENT - GRADIO WEB FRONTEND (`src/web_ui.py`)
Giao diện Web UI hiện đại cho Bà Mối AI tương thích Gradio 6.0+,
hỗ trợ quản lý Session State, tự động reset lịch sử hội thoại 100% sạch sẽ khi bấm nút Xóa.
"""

import os
import sys
import json
import gradio as gr
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from providers import get_llm_provider
from tools import MOCK_CANDIDATE_DB
from agent import MatchmakingAgent
from ai_levels.level1_rule_based import rule_based_bot
from ai_levels.level2_llm_chatbot import llm_chatbot
from ai_levels.level4_autonomous_agent import AutonomousMatchmakerAgent

load_dotenv()

provider = get_llm_provider()


def chat_fn(message: str, history, agent_state, level_choice: str):
    """Xử lý hội thoại độc lập theo Session State với phanh reset sạch sẽ"""
    if not message or not str(message).strip():
        return "", history, agent_state

    if history is None:
        history = []
    if agent_state is None:
        agent_state = MatchmakingAgent(provider_name="gemini")

    user_text = str(message).strip()

    if "Cấp 3" in level_choice:
        bot_response = agent_state.process_message(user_text)
    elif "Cấp 4" in level_choice:
        auto_agent = AutonomousMatchmakerAgent(goal=user_text, provider=provider)
        auto_agent.execute()
        memory_str = "\n".join([f"• Step {m['step']} [{m.get('task', '')}]: {m.get('observation', m.get('result', ''))}" for m in auto_agent.memory])
        final_ans = getattr(auto_agent, 'final_answer', '') or "✨ **Đề xuất hoàn tất!**"
        bot_response = f"🚀 **[CẤP 4 - AUTONOMOUS AGENT GOAL COMPLETION]**\n\n🎯 **Mục tiêu**: {user_text}\n\n📋 **Nhật ký Bộ nhớ Execution Memory**:\n{memory_str}\n\n---\n\n{final_ans}"
    elif "Cấp 2" in level_choice:
        bot_response = llm_chatbot(user_text, provider)
    else:
        bot_response = rule_based_bot(user_text)

    history.append({"role": "user", "content": user_text})
    history.append({"role": "assistant", "content": bot_response})
    return "", history, agent_state


def reset_chat_fn():
    """Tạo lại phiên Agent mới 100% sạch sẽ khi bấm Xóa lịch sử"""
    fresh_agent = MatchmakingAgent(provider_name="gemini")
    return [], fresh_agent


def get_candidate_db_markdown():
    """Tạo bảng xem trước Mock Database hồ sơ"""
    lines = ["| ID | Tên & Tuổi | Vị trí | Nghề nghiệp | Sở thích tiêu biểu |", "|:---:|:---:|:---:|:---:|:---|"]
    for c in MOCK_CANDIDATE_DB:
        lines.append(f"| `{c['id']}` | **{c['name']}** ({c['age']}t) | {c['location']} | {c['occupation']} | {c['interests']} |")
    return "\n".join(lines)


# Custom CSS Theme Styling
custom_css = """
.container { max-width: 1100px; margin: 0 auto; }
.header-box { text-align: center; padding: 20px; background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 99%, #feada6 100%); border-radius: 15px; margin-bottom: 20px; color: #4a154b; }
.header-box h1 { font-size: 2.2rem; font-weight: 700; margin-bottom: 5px; }
.header-box p { font-size: 1.1rem; opacity: 0.9; }
"""

# Build Gradio Interface
with gr.Blocks(title="Bà Mối AI - AI Matchmaking Agent") as demo:
    
    # Session State cho từng người dùng
    agent_state = gr.State(lambda: MatchmakingAgent(provider_name="gemini"))

    gr.HTML("""
    <div class="header-box">
        <h1>💘 AI MATCHMAKING AGENT - BÀ MỐI AI</h1>
        <p>Trợ lý ghép đôi thông minh • Đánh giá tương thích • Tự động lập kế hoạch hẹn hò hợp gu</p>
    </div>
    """)

    with gr.Tabs():
        with gr.TabItem("💬 Trò Chuyện & Ghép Đôi"):
            with gr.Row():
                with gr.Column(scale=3):
                    chatbot = gr.Chatbot(
                        height=520,
                        avatar_images=("https://cdn-icons-png.flaticon.com/512/4140/4140048.png", "https://cdn-icons-png.flaticon.com/512/6997/6997662.png")
                    )
                    
                    with gr.Row():
                        msg = gr.Textbox(
                            placeholder="Nhập yêu cầu ghép đôi (VD: 'Tìm bạn gái 22-26 tuổi ở Hà Nội thích nhạc indie')...",
                            container=False,
                            scale=7
                        )
                        send_btn = gr.Button("Gửi 💘", scale=1, variant="primary")
                    
                    with gr.Row():
                        clear_btn = gr.Button("🔄 Xóa sạch lịch sử", variant="secondary", size="sm")

                with gr.Column(scale=1):
                    gr.Markdown("### ⚙️ Cấu Hình Hệ Thống")
                    level_selector = gr.Radio(
                        choices=[
                            "🧠 Cấp 3: ReAct Agent (Bà Mối AI)",
                            "🚀 Cấp 4: Autonomous Agent (Goal & Planning)",
                            "🤖 Cấp 2: LLM Chatbot (Gemini Baseline)",
                            "🤖 Cấp 1: Rule-Based Bot (Keyword)"
                        ],
                        value="🧠 Cấp 3: ReAct Agent (Bà Mối AI)",
                        label="Chọn Cấp Độ AI System"
                    )
                    
                    gr.Markdown("### 💡 Gợi Ý Câu Hỏi Mẫu")
                    ex1 = gr.Button("1. 🌸 Tìm bạn gái Hà Nội (Search Tool)")
                    ex2 = gr.Button("2. 📊 Đánh giá tương thích C001 & C002")
                    ex3 = gr.Button("3. 💬 Tìm bạn gái (Test Slot Filling)")
                    ex4 = gr.Button("4. 🎯 Goal Cấp 4: Tìm bạn & lập lịch hẹn")

                    gr.Markdown(f"**🔌 Provider**: `Google Gemini`\n**🤖 Model**: `gemini-3.5-flash-lite`")

        with gr.TabItem("📋 Danh Sách Hồ Sơ Ứng Viên Mẫu (Mock DB)"):
            gr.Markdown("### 🏢 Cơ Sở Dữ Liệu Hồ Sơ Ứng Viên (Mock Candidate Database)")
            gr.Markdown(get_candidate_db_markdown())

    # Event Handlers với gr.State quản lý phiên
    msg.submit(chat_fn, [msg, chatbot, agent_state, level_selector], [msg, chatbot, agent_state])
    send_btn.click(chat_fn, [msg, chatbot, agent_state, level_selector], [msg, chatbot, agent_state])
    clear_btn.click(reset_chat_fn, None, [chatbot, agent_state])

    # Example Quick Buttons
    ex1.click(lambda: "Tôi là Nam 26 tuổi ở Hà Nội, hãy tìm cho tôi bạn gái khoảng 22 đến 26 tuổi ở Hà Nội thích nghe nhạc indie, vẽ tranh và đi cà phê.", None, msg)
    ex2.click(lambda: "Hãy đánh giá độ tương thích giữa hồ sơ C001 (Nguyễn Văn Tuấn) và C002 (Trần Thị Ngọc Bích).", None, msg)
    ex3.click(lambda: "Tôi muốn tìm bạn gái để tìm hiểu hẹn hò.", None, msg)
    ex4.click(lambda: "Tìm giúp tôi bạn gái phù hợp tại Hà Nội và lập kịch bản buổi hẹn hò đầu tiên lãng mạn cho 2 người.", None, msg)


def launch_server():
    for p in range(7860, 7875):
        try:
            print(f"📌 Thử nghiệm khởi chạy tại port: {p}")
            demo.queue().launch(
                server_name="127.0.0.1",
                server_port=p,
                theme=gr.themes.Soft(primary_hue="pink", secondary_hue="rose"),
                css=custom_css,
                share=False,
                inbrowser=False
            )
            print(f"🚀 Máy chủ Web UI đã chạy thành công tại địa chỉ: http://127.0.0.1:{p}")
            break
        except OSError:
            continue


if __name__ == "__main__":
    launch_server()
