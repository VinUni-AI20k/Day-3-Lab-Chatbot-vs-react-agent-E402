# Frontend demo - Mèo Hồng

Giao diện chat tĩnh, có mô phỏng luồng thu thập hồ sơ người nhận quà trong `docs/PROJECT_CONTEXT_GIFT_ASSISTANT.md`.

Chạy từ thư mục gốc dự án:

```bash
python3 -m http.server 8080 --directory frontend
```

Sau đó mở `http://localhost:8080`.

Frontend hiện không gọi API. Phần JavaScript chỉ mô phỏng việc thu thập 4 thông tin tối thiểu: quan hệ, dịp, sở thích và ngân sách. Khi ghép agent thật, thay `submitMessage()` bằng lời gọi backend, giữ nguyên cấu trúc dữ liệu và trạng thái UI.
