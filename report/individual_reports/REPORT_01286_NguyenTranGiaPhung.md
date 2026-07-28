# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nguyễn Trần Gia Phụng
- **Student ID**: 01286
- **Date**: 2026-07-28

---

## I. Technical Contribution (15 Points)

Tôi đảm nhận **Role 1 - Build Test Case** cho dự án **AI Matchmaking Agent ("Bà Mối AI")**.

- **Module phụ trách**: [`config/test_cases.json`](../../config/test_cases.json)
- **Nội dung đóng góp**: Xây dựng 5 test case để so sánh bốn cấp độ AI và kiểm tra các nhánh chính của hệ thống.

| Test | Nội dung trong dự án | Hành vi mong đợi |
| :---: | :--- | :--- |
| 1 | Hỏi tiêu chuẩn của một mối quan hệ lành mạnh | Rule-Based không xử lý được; LLM trả lời trực tiếp, không cần tool. |
| 2 | Tìm bạn gái 22–28 tuổi tại Hà Nội, thích nhạc indie, vẽ tranh và cà phê | ReAct Agent gọi `search_candidates` và che thông tin cá nhân. |
| 3 | Chỉ yêu cầu “tìm bạn gái để hẹn hò” | Agent phát hiện thiếu tuổi, vị trí, sở thích; hỏi bổ sung và không gọi tool. |
| 4 | Tính tương thích giữa người dùng và Khánh Linh trong cơ sở dữ liệu | Autonomous Agent tìm Khánh Linh, gọi `calculate_compatibility` rồi tổng hợp kết quả. |
| 5 | Tìm bạn gái 18–20 tuổi tại Cà Mau, thích leo núi tuyết | Không có kết quả khớp cứng; hệ thống kích hoạt Relaxed Search. |

### Code Highlights

Test case kiểm tra Guardrail khi thiếu thông tin:

```json
{
  "id": 3,
  "question": "Tôi muốn tìm bạn gái để tìm hiểu hẹn hò.",
  "expected_behavior": "Agent phát hiện THIẾU vị trí, độ tuổi và sở thích mong muốn. KHÔNG GỌI TOOL, đưa ra câu hỏi bổ sung nhẹ nhàng."
}
```

Test case kiểm tra Relaxed Search:

```json
{
  "id": 5,
  "question": "Tìm giúp tôi bạn gái 18 đến 20 tuổi ở thành phố Cà Mau thích đi leo núi tuyết.",
  "expected_behavior": "Tool search_candidates không tìm thấy kết quả khớp cứng, kích hoạt Relaxed Search nới lỏng bán kính và cảnh báo an toàn."
}
```

### Documentation

`src/app.py` dùng hàm `load_test_cases()` để đọc file của Role 1. `src/test_ai_levels.py` chạy lần lượt từng test qua:

1. Rule-Based Bot;
2. LLM Chatbot;
3. Reactive Agent;
4. Autonomous Agent.

Các trường `gap_analysis` và `expected_behavior` trong mỗi test là căn cứ để nhóm đối chiếu kết quả và ghi trace tại `docs/trace_eval.md`.

---

## II. Debugging Case Study (10 Points)

- **Problem Description**: Test case #5 sử dụng địa danh “Cà Mau”. Đường parse CSV dự phòng trong Agent phụ thuộc vào whitelist địa danh, nên có nguy cơ không truyền đúng `location` vào `search_candidates`.

- **Log Source**: Phần **TEST CASE #5 — Edge Case** và phát hiện **F3** trong [`docs/trace_eval.md`](../../docs/trace_eval.md).

```text
Action: search_candidates[{
  "target_gender": "Nữ",
  "min_age": 18,
  "max_age": 20,
  "location": "Cà Mau",
  "query_interests": "thích đi leo núi tuyết"
}]

Observation:
  total_found = 3
  is_relaxed_search = true
```

- **Diagnosis**: Đường gọi tool bằng JSON giữ nguyên địa danh “Cà Mau”, trong khi đường CSV dự phòng có thể bỏ sót địa danh ngoài whitelist. Lỗi thuộc bước chuyển tham số từ phản hồi LLM sang tool.

- **Solution**: Luồng chính sử dụng Action dạng JSON nên truyền đúng tham số. Kết quả kiểm tra thực tế trả về ba ứng viên nới lỏng, `is_relaxed_search=true` và số điện thoại được che, ví dụ `0987***321`. Dự án nên tiếp tục chuẩn hóa tool call bằng JSON và bỏ whitelist địa danh cứng.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

1. **Reasoning**: Với test #2, Chatbot chỉ có thể tư vấn chung vì không truy cập cơ sở dữ liệu. ReAct Agent phân tích yêu cầu rồi chọn `search_candidates`. Với test #3, Agent nhận ra thiếu dữ liệu và hỏi lại thay vì gọi tool sai.

2. **Reliability**: Ở test #1, Chatbot phù hợp hơn vì câu hỏi chỉ cần kiến thức chung. ReAct Agent không tạo thêm giá trị nếu gọi tool cho trường hợp này. Agent cũng phụ thuộc vào định dạng Action và kết quả trả về từ tool.

3. **Observation**: Trong test #5, Observation cho biết không có kết quả khớp cứng và `is_relaxed_search=true`. Thông tin này giúp Agent cảnh báo người dùng và đưa ra các ứng viên gần nhất thay vì trả về danh sách rỗng.

---

## IV. Future Improvements (5 Points)

- **Scalability**: Chuyển 5 test case hiện tại thành test tự động chạy qua cả bốn cấp độ AI.
- **Safety**: Bổ sung assertion kiểm tra Agent không gọi tool ở test #3 và luôn che số điện thoại ở test #2, #5.
- **Performance**: Dùng Mock Provider cho kiểm thử lặp lại; chỉ gọi Gemini API khi chạy đánh giá tích hợp.
- **Maintainability**: Chọn test theo trường `id` thay vì vị trí trong mảng. Hiện `src/app.py` ghi “TEST CASE #3 - COMPATIBILITY”, nhưng test #3 trong `config/test_cases.json` là Slot Filling.

---

> [!NOTE]
> Báo cáo được viết theo đúng phạm vi Role 1 và các artifact hiện có trong dự án.
