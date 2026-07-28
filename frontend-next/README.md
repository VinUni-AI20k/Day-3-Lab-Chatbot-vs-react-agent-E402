# Mèo Hồng - Next.js frontend

Giao diện chat hồng-trắng cho trợ lý chọn quà. Trang mô phỏng việc agent thu thập bốn tín hiệu cần thiết: mối quan hệ, dịp tặng, sở thích và ngân sách.

## Web search API

App gọi `POST /api/web-search` khi đã thu thập đủ thông tin chọn quà. API route này giữ key ở server và dùng Tavily Search; trình duyệt chỉ nhận tiêu đề, link và đoạn mô tả kết quả.

1. Tạo API key Tavily: https://app.tavily.com/home
2. Sao chép `.env.local.example` thành `.env.local`, sau đó điền `TAVILY_API_KEY`.

## Chạy local

```bash
npm run dev
```

Mở `http://localhost:3000` để xem giao diện.

## Kiểm tra production

```bash
npm run build
```

Trang hiện là demo client-side. Khi kết nối agent backend, thay phần mô phỏng trong `src/app/page.tsx` bằng API chat, giữ nguyên profile state và các trạng thái UI.
