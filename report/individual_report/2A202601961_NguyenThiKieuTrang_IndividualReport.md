# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nguyễn Thị Kiều Trang
- **Student ID**: 2A202601961
- **Role**: Role 5 — Observability / Trace Analyst
- **Project**: AI Recruitment Screening & Interview Scheduling Assistant
- **Date**: 28/07/2026

---

## I. Technical Contribution (15 Points)

### 1. Phạm vi công việc

Trong nhóm, tôi đảm nhiệm **Role 5 — Observability**. Trách nhiệm chính của tôi là
theo dõi toàn bộ hành trình xử lý của Agent, đối chiếu kết quả thực tế với kết quả
kỳ vọng và ghi lại bằng chứng để nhóm có thể phát hiện lỗi thay vì chỉ nhìn vào câu
trả lời cuối cùng.

Các phần việc đã thực hiện:

- Xây dựng bảng **Agentic Fit Scoring Matrix** cho đề tài số 9 theo bốn tiêu chí:
  Multi-step Reasoning, Tool Interaction, Dynamic Decision và Long Horizon.
- Chấm tổng điểm phù hợp **15/20**, từ đó kết luận bài toán phù hợp để thử nghiệm
  ReAct Agent.
- Ghi lại trace theo chuỗi `Thought -> Action -> Observation -> Final Answer` cho
  các luồng sàng lọc và đặt lịch phỏng vấn.
- Chạy, quan sát và tổng hợp kết quả của 10 test case từ TC001 đến TC010.
- Đối chiếu từng trường trong `expected`, bao gồm status, score, kỹ năng còn thiếu,
  trạng thái lịch, đặt lịch và tạo email.
- Phân tích failed trace, thực hiện Root Cause Analysis và ghi nhận biện pháp phòng
  thủ của Agent V2.
- Thực hiện cross-audit cho prompt injection, dữ liệu rỗng, kinh nghiệm phi thực tế,
  gọi sai tool, lặp action và đặt lịch khi chưa có xác nhận của HR.
- Ghi nhận kiểm thử PDF-to-JSON cho cả Job Description và Candidate CV.

### 2. Modules/Artifacts Implemented

- [`docs/trace_eval.md`](docs/trace_eval.md): báo cáo chính của Role 5, bao gồm
  Scoring Matrix, trace, RCA, bảng kết quả kiểm thử, cross-audit và hybrid decision.
- [`config/test_cases.json`](config/test_cases.json): nguồn dữ liệu được sử dụng để
  quan sát và đánh giá TC001–TC010.
- [`docs/hybrid_flowchart.mermaid`](docs/hybrid_flowchart.mermaid): bằng chứng về
  luồng lựa chọn Chatbot, ReAct Agent và Guardrail.

### 3. Code and Trace Highlights

Trace multi-step TC004 được theo dõi theo đúng thứ tự:

```text
Thought: Cần xác nhận ứng viên đạt ngưỡng.
Action: screen_candidate[JD, CV]
Observation: {"status":"PASS","score":100.0,"schedule_interview":true}

Thought: Ứng viên PASS nên kiểm tra lịch.
Action: check_interviewer_calendar["available"]
Observation: {"calendar_checked":true,"available_slots":[...]}

Action: book_interview["Pham Minh D","2026-07-30 09:00","CONFIRMED"]
Observation: {"status":"BOOKED","interview_booked":true}

Action: generate_invitation_email[...]
Observation: {"email_generated":true,"sent":false}
```

Kết quả quan sát cuối cùng:

| Nhóm test | Số lượng | Kết quả |
|---|---:|---:|
| Simple | 3 | 3/3 PASS |
| Multi-Step | 2 | 2/2 PASS |
| Trap/Guardrail | 5 | 5/5 PASS |
| **Tổng** | **10** | **10/10 PASS (100%)** |

Trace không chỉ dùng để trình bày. Mỗi `Observation` là kết quả thực do application
chèn vào sau khi gọi tool. Agent sử dụng Observation đó để quyết định bước tiếp
theo; model không được tự tạo dữ liệu lịch hoặc kết quả chấm CV.

---

## II. Debugging Case Study (10 Points)

### 1. Problem Description

Khi tải JD `[FSOFT] Fresher Embedded.pdf` và CV `CV_DAOVANDAT_2026.pdf`, Agent từng
trả về trace sau:

```text
Step 1 | Thought: Cần đối chiếu JD với CV bằng tiêu chí công việc.
Step 2 | Action: screen_candidate[JD JSON, CV JSON]
Step 3 | Observation: {"status":"ERROR","message":"Job experience requirement is invalid."}
Step 4 | Final Answer: Kết quả là hỗ trợ ra quyết định; HR review kết luận cuối.
```

Trong lúc đọc PDF, thư viện còn in các cảnh báo dạng:

```text
Ignoring wrong pointing object 8 0 (offset 0)
Ignoring wrong pointing object 10 0 (offset 0)
```

### 2. Log Source

- Failed trace và RCA: [`docs/trace_eval.md`](docs/trace_eval.md)
- Kiểm tra tiêu chí experience: [`src/tools.py`](src/tools.py)
- Trace loop và repeated-action guardrail: [`src/app.py`](src/app.py)
- Giới hạn vòng lặp: [`src/prompts.py`](src/prompts.py)

### 3. Diagnosis

Nguyên nhân chính không phải là các dòng `wrong pointing object`. Đây là cảnh báo
khôi phục cấu trúc tham chiếu nội bộ của PDF từ `pypdf`; tài liệu vẫn có thể trích
xuất text.

Lỗi thực sự nằm ở dữ liệu JD sau bước PDF-to-JSON. JD Fresher không đưa ra số năm
kinh nghiệm cụ thể, nhưng trường `experience` từng được đưa sang tool dưới dạng giá
trị không phải số. `screen_candidate` chỉ chấp nhận số năm hợp lệ; vì vậy tool trả
structured error `Job experience requirement is invalid.` thay vì tự đoán yêu cầu.

Trace đã giúp tách rõ ba lớp:

1. `Thought` và `Action` của Agent là hợp lý vì đúng tool được chọn.
2. `Observation` chứng minh lỗi xảy ra trong dữ liệu/tool contract, không phải do
   Agent chọn sai workflow.
3. Cảnh báo PDF chỉ là nhiễu log và không phải root cause của kết quả ERROR.

### 4. Solution and Verification

Giải pháp được áp dụng:

- PDF parser trả `None`/không áp dụng tiêu chí khi JD không nêu số năm kinh nghiệm.
- `screen_candidate` dùng cờ `has_experience_criterion`; chỉ kiểm tra và chấm kinh
  nghiệm khi JD thực sự chứa giá trị.
- Giá trị có nhưng sai kiểu vẫn trả ERROR để tránh Agent tự bịa dữ liệu.
- Hạ mức log `pypdf` cho các cảnh báo cấu trúc có thể phục hồi, nhưng vẫn giữ lỗi
  thật như PDF rỗng, mã hóa, quá 10 MB, quá 20 trang hoặc không có text.

Kết quả sau sửa với đúng hai PDF:

```json
{
  "position": "Fresher Embedded",
  "required_skills": ["C++", "C"],
  "job_experience": null,
  "status": "REVIEW",
  "score": 79.0
}
```

Ngoài lỗi trên, tôi cũng kiểm tra failure mode lặp action. Agent V2 lưu chữ ký
`(tool_name, args)` trong `seen_actions`; nếu model gọi lại cùng action, ứng dụng
dừng trước lần gọi tool thứ hai. Hệ thống còn có `MAX_ITERATIONS = 6`, timeout 10
giây, parser `ast.literal_eval`, unknown-tool fallback và exception isolation.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

### 1. Reasoning

`Thought` giúp Agent thể hiện mục tiêu của từng bước và lý do chọn tool. Với TC004,
Agent không thể chuyển thẳng từ CV sang email mời. Nó phải lần lượt chấm CV, kiểm tra
lịch, đặt lịch có xác nhận rồi mới tạo email nháp. Nhờ đó người kiểm thử có thể xác
định chính xác quyết định sai xuất hiện ở bước nào.

Chatbot baseline chỉ thực hiện một model call. Nó có thể tạo câu trả lời nghe hợp lý,
nhưng không có bằng chứng rằng điểm CV hoặc lịch phỏng vấn là dữ liệu thật. ReAct
Agent tốn nhiều bước hơn nhưng mỗi kết luận quan trọng đều được grounded bằng
Observation từ tool.

### 2. Reliability

Agent không luôn tốt hơn Chatbot. Với câu hỏi lý thuyết hoặc hướng dẫn tĩnh không
cần dữ liệu ngoài, Chatbot nhanh hơn, rẻ hơn và ít có nguy cơ lỗi parser/tool.

Agent có thể làm kém hơn khi:

- Tool contract không rõ hoặc dữ liệu đầu vào sai kiểu.
- Model gọi sai tên tool, sai số lượng tham số hoặc lặp cùng action.
- Workflow nhiều bước làm tăng độ trễ và số lần gọi model.
- Observation quá dài khiến context phức tạp hơn.

Vì vậy dự án sử dụng hybrid decision: Q&A tĩnh đi theo Chatbot path; sàng lọc CV,
kiểm tra lịch và thao tác có side effect đi theo ReAct path; input nguy hiểm đi thẳng
vào Guardrail.

### 3. Observation

Observation là phần biến suy luận của model thành quy trình có thể kiểm chứng. Ví dụ:

- `screen_candidate -> REVIEW` khiến Agent không tự động đặt lịch.
- `available_slots = []` khiến Agent gọi `suggest_new_slots` thay vì bịa thời gian.
- `CV is empty.` khiến workflow dừng an toàn.
- Prompt injection bị chặn trước khi gọi bất kỳ tool nào.
- Booking chỉ thành công khi có `CONFIRMED`, duy trì human-in-the-loop.

Bài học lớn nhất của tôi là không nên đánh giá Agent chỉ bằng câu trả lời cuối. Cần
đánh giá đồng thời Action, tham số, Observation, số tool call, guardrail status và
side effect đã xảy ra hay chưa.

---

## IV. Future Improvements (5 Points)

### Scalability

- Lưu trace dưới dạng JSON Lines/OpenTelemetry thay vì chỉ hiển thị trên giao diện.
- Gắn `trace_id`, `candidate_id`, thời gian xử lý và latency cho từng tool call.
- Dùng async queue cho PDF parsing, batch screening và tác vụ email/lịch.
- Tách calendar/email adapter khỏi mock tool để dễ kết nối hệ thống doanh nghiệp.

### Safety

- Thêm policy engine độc lập để kiểm tra Action trước khi tool có side effect chạy.
- Yêu cầu HR phê duyệt rõ ràng trước mọi thao tác đặt hoặc đổi lịch.
- Mã hóa dữ liệu, phân quyền truy cập và tự động che PII trong log.
- Kiểm tra thiên lệch; không đưa tuổi, giới tính, ảnh, địa chỉ hoặc thuộc tính nhạy
  cảm vào điểm tuyển dụng.
- Dùng schema validation nghiêm ngặt và antivirus/OCR sandbox cho file tải lên.

### Performance and Evaluation

- Cache kết quả trích xuất PDF theo checksum và cache dữ liệu JD dùng chung.
- Chỉ gọi ReAct Agent khi câu hỏi thật sự cần tool; câu hỏi tĩnh dùng Chatbot.
- Mở rộng bộ test với CV song ngữ, PDF scan, dữ liệu thiếu, lịch đổi nhiều lần và
  lỗi provider/calendar thực tế.
- Theo dõi precision, recall, false rejection rate, latency, token cost và tỉ lệ HR
  override thay vì chỉ đo số test case PASS.
- Dùng evaluation dataset đã được HR gán nhãn và kiểm thử hồi quy sau mỗi thay đổi.

---

## Conclusion

Role 5 giúp biến một demo có đầu ra thành hệ thống có bằng chứng kiểm thử. Qua Scoring
Matrix, trace log, failed-trace RCA và cross-audit, tôi xác nhận ReAct Agent phù hợp
với phần sàng lọc và hẹn phỏng vấn nhiều bước, nhưng vẫn cần hybrid routing,
guardrails và HR chịu trách nhiệm quyết định cuối cùng.
