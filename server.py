"""
🚀 WEB APP SERVER FOR SMART RETURN ASSISTANT
File này dùng để khởi chạy giao diện UI trên trình duyệt: python server.py
"""

import http.server
import socketserver
import webbrowser
import os
import sys

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

PORT = 8000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)


if __name__ == "__main__":
    url = f"http://localhost:{PORT}"
    print("==================================================")
    print("🚀 ĐANG KHỞI CHẠY GIAO DIỆN SMART RETURN ASSISTANT UI")
    print("==================================================")
    print(f"🔗 Mở trình duyệt tại: {url}")
    print("Press Ctrl+C to stop the web server.\n")

    # Tự động mở trình duyệt web
    try:
        webbrowser.open(url)
    except Exception:
        pass

    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Đã dừng Web Server.")
            sys.exit(0)
