📋 SỔ TAY PHÂN CÔNG & CHECKLIST THỰC HÀNH (ZERO-CONFLICT WORKFLOW)
💡 Hướng dẫn: Mỗi thành viên mở đúng file được phân công trong thư mục dự án và thực hiện checklist theo từng Mốc.
👥 1. BẢNG PHÂN VAI & FILE ĐẢM NHẬN
Vai trò (Role)	File đảm nhận	Nhiệm vụ chính	Người đảm nhận	Mã học viên
Role 1: Product Architect	config/test_cases.json	Định hướng bài toán, soạn bộ câu test case & bổ sung dữ liệu sạch (clean data) cho dự án	Đào Kiều Thịnh Quang	02A2202601014
Role 2: Tool Engineer	src/tools.py	Định nghĩa và xây dựng các công cụ (Tools) cho Agent	Nguyễn Hoàng Anh	2A2202601186
Role 3: Prompt Engineer	src/prompts.py	Viết ReAct System Prompt, thiết lập Guardrails & giải thích chi tiết quá trình hoạt động/suy luận	Trần Quang Minh	2A22026001210
Role 4: Core Developer / Integrator	src/app.py	Chỉ tập trung hoàn thiện file tích hợp chính (src/app.py) theo đúng các yêu cầu nghiệp vụ	Phạm Khắc Khương Duy	02A2202601982
Role 5: Observability	docs/trace_eval.md<br/>docs/hybrid_flowchart.mermaid	Lập bảng Scoring Matrix, Phân tích Trace Log, Vẽ sơ đồ Hybrid Flowchart, tìm kiếm dữ liệu (data) & hỗ trợ triển khai app	Ngô Văn Nam	02A2202601340
⏱️ 2. CHECKLIST THỰC HÀNH THEO 4 MỐC
📍 MỐC 1: Định hình & Đánh giá độ phù hợp (Agentic Fit) (20 phút)
Mục tiêu: Chứng minh bài toán này CẦN dùng Agent chứ không chỉ Chatbot.

Role 1 & Cả nhóm: Tự do lựa chọn 1 chủ đề bài toán thực tế (Dự án: Text-to-SQL Goodreads Books).

Role 5 (Ngô Văn Nam): Điền bảng Scoring Matrix và hỗ trợ tìm kiếm dữ liệu đầu vào.

Role 2 (Nguyễn Hoàng Anh): Liệt kê tên các công cụ sẽ tạo trong src/tools.py phù hợp với chủ đề nhóm đã chọn.

Role 3 (Trần Quang Minh): Xác định các trường hợp tool có thể bị lỗi (Failure Modes) và chuẩn bị giải thích quy trình.

Role 4 (Phạm Khắc Khương Duy): Mở Terminal gõ python src/app.py kiểm tra xem môi trường sẵn sàng chưa.

🤝 Cả nhóm: Gật đầu thống nhất bài toán trước khi sang Mốc 2.

🔄 Đồng bộ Git Mốc 1: Cả nhóm lưu file, đẩy code lên Git: git add . ➔ git commit -m "Moc 1: Scoring Matrix & Dinh hinh" ➔ git push.
📍 MỐC 2: Baseline Chatbot & Khai báo Tool Specs (30 phút)
Mục tiêu: Thấy rõ hạn chế của Chatbot gốc và chuẩn hóa công cụ cho Agent.

Role 1 (Đào Kiều Thịnh Quang): Viết bộ Test Cases và chuẩn bị tập dữ liệu sạch để thử nghiệm.

Role 2 (Nguyễn Hoàng Anh): Dùng AI bổ sung Docstring / Mô tả chuẩn cho các hàm trong src/tools.py.

Role 3 (Trần Quang Minh): Soạn CHATBOT_BASELINE_PROMPT trong file src/prompts.py.

Role 4 (Phạm Khắc Khương Duy): Gõ git pull để kéo file về máy ➔ Hoàn thiện file app.py chính để chạy thử nghiệm Baseline Chatbot.

Role 5 (Ngô Văn Nam): Ghi lại phản hồi của Chatbot gốc vào docs/trace_eval.md và hỗ trợ kiểm tra luồng dữ liệu.

🔄 Đồng bộ Git Mốc 2: Cả nhóm lưu file, đẩy code lên Git: git add . ➔ git commit -m "Moc 2: Chatbot Baseline & Tool Specs" ➔ git push.
📍 MỐC 3: ReAct Loop & Safeguards (60 phút)
Mục tiêu: Dựng ReAct Agent suy luận Thought -> Action và cài phanh an toàn.

Role 3 (Trần Quang Minh): Soạn REACT_SYSTEM_PROMPT, thiết lập MAX_ITERATIONS và viết phần giải thích quá trình suy luận chi tiết.

Role 2 (Nguyễn Hoàng Anh): Đảm bảo các hàm trong src/tools.py khi gặp lỗi sẽ trả về chuỗi thông báo lỗi chứ không crash code.

Role 4 (Phạm Khắc Khương Duy): Gõ git pull kéo toàn bộ code mới nhất ➔ Hoàn thiện phần tích hợp vòng lặp ReAct trong file src/app.py.

Role 5 (Ngô Văn Nam): Trích xuất chuỗi Thought -> Action -> Observation, hỗ trợ triển khai chạy thử app và dán log vào docs/trace_eval.md.

Role 1 (Đào Kiều Thịnh Quang): Kiểm tra xem Agent có vượt qua được câu bẫy (Edge Case) bằng phanh Guardrail hay không.

🔄 Đồng bộ Git Mốc 3: Cả nhóm lưu file, đẩy code lên Git: git add . ➔ git commit -m "Moc 3: ReAct Agent Loop & Safeguards" ➔ git push.
📍 MỐC 4: Tương tác liên nhóm & Hybrid Flowchart (40 phút)
Mục tiêu: Thử thách khả năng chịu lỗi trước đòn tấn công từ nhóm khác & Chấm chéo linh hoạt.

⚔️ Đội Tấn Công: Mang các câu test case của nhóm mình sang "xả" vào Agent của Nhóm bạn để kiểm thử khả năng chịu lỗi.

🛡️ Đội Phòng Thủ: Quan sát Agent nhóm mình phản ứng trước câu hỏi của nhóm bạn. Kiểm tra xem Guardrail bảo vệ an toàn không.

📊 Role 5 (Ngô Văn Nam): Vẽ sơ đồ Hybrid Flowchart vào file docs/hybrid_flowchart.mermaid.

🔄 Đồng bộ Git Mốc 4 (Hoàn thành): Cả nhóm lưu file, đẩy bản hoàn chỉnh lên Git: git add . ➔ git commit -m "Moc 4: Cross Audit & Hybrid Flowchart Hoan thanh" ➔ git push.
