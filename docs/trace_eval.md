# 📊 BÁO CÁO GIÁM SÁT & ĐÁNH GIÁ TRACE

Người phụ trách TV1: Product + Data/Test Designer

Dự án: **Trợ Lý Tư Vấn Khóa Học Sinh Viên**

---

## 1. Bảng Chấm Điểm Agentic Fit

| Tiêu chí | Điểm (1-5) | Lý do đánh giá |
| :--- | :---: | :--- |
| **Multi-step Reasoning** | `5/5` | Cần kết hợp ngành học, môn đã học, môn tiên quyết, tín chỉ và mục tiêu nghề nghiệp. |
| **Tool Interaction** | `5/5` | Cần tra cứu danh sách môn, kiểm tra tiên quyết và tính workload từ dữ liệu có cấu trúc. |
| **Dynamic Decision** | `4/5` | Kết quả kiểm tra tiên quyết quyết định môn nào được gợi ý hoặc bị loại. |
| **Long Horizon** | `4/5` | Có thể mở rộng thành kế hoạch nhiều học kỳ, nhưng bản lab chỉ cần tư vấn học kỳ tới. |
| **Tổng điểm fit** | **18/20** | **Kết luận: Bài toán rất phù hợp để dùng ReAct Agent.** |

---

## 2. Bộ Test Cases

| ID | Loại case | Mục tiêu kiểm thử | Tool kỳ vọng |
| :---: | :--- | :--- | :--- |
| 1 | Đơn giản | Tư vấn kỹ năng nền tảng cho sinh viên muốn học AI | Không cần tool |
| 2 | Đơn giản | Giải thích khái niệm môn tiên quyết | Không cần tool |
| 3 | Multi-step | Kiểm tra sinh viên có đủ điều kiện học CS201 không | `check_prerequisites` |
| 4 | Multi-tool | Gợi ý 3 môn Data Science trong giới hạn 9 tín chỉ | `search_courses`, `check_prerequisites`, `estimate_workload` |
| 5 | Workload | Đánh giá kế hoạch CS201, DS201, AI301 có quá nặng không | `estimate_workload` |
| 6 | Thiếu thông tin | Kiểm tra agent có hỏi lại thay vì đoán bừa không | Không cần tool |
| 7 | Edge case | Môn không tồn tại và yêu cầu ép đăng ký sai | `search_courses`, `check_prerequisites` |

---

## 3. So Sánh Chatbot Baseline Vs ReAct Agent

### Test Case #4

**Câu hỏi**: "Em học ngành Công nghệ thông tin, GPA 3.2, đã hoàn thành CS101 và MATH101, học kỳ tới muốn học tối đa 9 tín chỉ và định hướng Data Science. Hãy gợi ý 3 môn phù hợp."

### Chatbot Baseline

- **Phản hồi kỳ vọng**: Có thể gợi ý chung các môn như Data Structures, Statistics, Machine Learning.
- **Vấn đề**: Không biết môn nào thật sự có trong dữ liệu, không kiểm tra được tiên quyết, dễ vượt giới hạn 9 tín chỉ.
- **Đánh giá**: Trả lời nghe hợp lý nhưng thiếu bằng chứng.

### ReAct Agent

- **Thought 1**: Cần tìm các môn liên quan Data Science.
- **Action 1**: `search_courses['Data Science']`
- **Observation 1**: Danh sách môn phù hợp, ví dụ `DS201`, `STAT201`, `AI301`.
- **Thought 2**: Cần kiểm tra sinh viên đã đủ tiên quyết cho từng môn.
- **Action 2**: `check_prerequisites['DS201', 'CS101,MATH101']`
- **Observation 2**: Sinh viên đủ điều kiện hoặc còn thiếu môn tiên quyết.
- **Thought 3**: Cần kiểm tra tổng tín chỉ không vượt 9.
- **Action 3**: `estimate_workload['DS201,STAT201,AI301']`
- **Observation 3**: Tổng tín chỉ và mức workload.
- **Final Answer kỳ vọng**: Gợi ý danh sách môn hợp lệ, nêu lý do, cảnh báo môn chưa đủ tiên quyết nếu có.
- **Đánh giá**: Tốt hơn baseline vì có kiểm tra dữ liệu trước khi tư vấn.

---

## 4. Tiêu Chí Pass/Fail Cho TV1

- Pass nếu `config/test_cases.json` là JSON hợp lệ.
- Pass nếu có ít nhất 5 test cases đúng đề tài tư vấn khóa học.
- Pass nếu có đủ case đơn giản, multi-step, thiếu thông tin và edge case.
- Pass nếu `docs/trace_eval.md` nêu rõ vì sao bài toán cần Agent.
- Fail nếu test cases vẫn còn chủ đề thời tiết/chuyến bay.
- Fail nếu expected behavior yêu cầu agent đoán dữ liệu không có tool.

