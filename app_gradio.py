"""
🚀 GRADIO WEB UI LAUNCHER (`app_gradio.py`)
Khởi chạy giao diện Web UI Gradio cho AI Matchmaking Agent với tự động chọn cổng khả dụng.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.abspath(__file__), "src"))

from src.web_ui import launch_server

if __name__ == "__main__":
    print("==========================================================")
    print("💖 BẮT ĐẦU KHỞI CHẠY GRADIO WEB UI FRONTEND 💖")
    print("==========================================================")
    launch_server()
