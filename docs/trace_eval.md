# Báo cáo Trace Eval: Baseline LLM-only vs ReAct Agent

Thời điểm chạy: 2026-07-28  
Môi trường: conda env `py3.10`  
Provider: `OpenAIProvider`  
Model: `gpt-4o-mini`  
Lệnh chạy kiểm thử:

```powershell
$env:PYTHONIOENCODING='utf-8'
conda run --no-capture-output -n py3.10 python -c "import sys; sys.path.append('src'); from app import load_test_cases, run_baseline_chatbot, run_react_agent; from providers import get_llm_provider; p=get_llm_provider('openai'); [(print('\n' + '='*80), print('TEST CASE', t.get('id'), ':', t.get('question')), print('='*80), print('\n--- BASELINE LLM ONLY ---'), run_baseline_chatbot(t['question'], p), print('\n--- REACT AGENT ---'), run_react_agent(t['question'], p)) for t in load_test_cases()[:5]]"
```

## 1. Scoring Matrix: Agentic Fit

| Tiêu chí | Điểm | Lý do |
| :--- | :---: | :--- |
| Multi-step Reasoning | 5/5 | Bài toán tìm và đặt lịch xem phòng cần hiểu ngân sách, khu vực, loại phòng, tình trạng phòng, lịch xem và thông tin liên hệ. |
| Tool Interaction | 5/5 | Agent cần gọi tool tìm phòng, xem chi tiết, kiểm tra lịch và đặt lịch xem phòng. |
| Dynamic Decision | 5/5 | Kết quả bước trước quyết định bước sau: không có phòng thì mở rộng khu vực, sai cú pháp tool thì sửa, thiếu số điện thoại thì hỏi lại. |
| Long Horizon | 4/5 | Workflow gồm nhiều bước từ tư vấn, tìm kiếm, lọc, xác nhận đến đặt lịch. Chưa phải workflow kéo dài nhiều ngày. |
| Tổng điểm fit | 19/20 | Bài toán rất phù hợp với ReAct Agent vì cần kết hợp reasoning và tool execution. |

## 2. Kết quả chạy 5 test case

### Test case 1

Câu hỏi: “Lần đầu thuê phòng trọ, tôi cần chuẩn bị những giấy tờ gì?”

#### Baseline LLM-only

Baseline trả lời trực tiếp bằng kiến thức chung, không gọi tool:

> Khi thuê phòng trọ lần đầu, bạn thường cần chuẩn bị: CCCD/CMND, sổ hộ khẩu nếu chủ nhà yêu cầu, giấy xác nhận sinh viên nếu là sinh viên, giấy bảo lãnh nếu cần. Ngoài ra nên chuẩn bị tiền đặt cọc, tiền thuê tháng đầu và kiểm tra kỹ hợp đồng thuê.

Nhận xét: Phù hợp với câu hỏi kiến thức chung. Không cần tool.

#### ReAct Agent

Agent không gọi tool và trả lời trực tiếp:

```text
Final Answer:
Khi thuê phòng trọ lần đầu, bạn thường cần chuẩn bị:
1. Giấy tờ tùy thân: CMND/CCCD.
2. Hộ khẩu hoặc xác nhận cư trú nếu cần.
3. Giấy tờ chứng minh công việc hoặc xác nhận sinh viên nếu có.
4. Tiền cọc theo yêu cầu chủ nhà.
5. Đọc và ký hợp đồng thuê.
```

Nhận xét: Agent xử lý đúng vì câu này không cần gọi công cụ.

---

### Test case 2

Câu hỏi: “Tiền cọc phòng trọ ở Việt Nam thường bằng bao nhiêu tháng tiền nhà?”

#### Baseline LLM-only

Baseline trả lời trực tiếp:

> Tiền cọc phòng trọ ở Việt Nam thường dao động từ 1 đến 3 tháng tiền nhà, tùy chủ nhà và khu vực. Phổ biến là 1-2 tháng, một số nơi có thể yêu cầu 2 tháng.

Nhận xét: Đúng vai trò LLM-only, trả lời bằng kiến thức chung.

#### ReAct Agent

Agent không gọi tool:

```text
Final Answer:
Tiền cọc phòng trọ ở Việt Nam thường dao động từ 1 đến 3 tháng tiền thuê nhà, tùy vào thỏa thuận giữa người thuê và chủ nhà.
```

Nhận xét: Đúng. Đây là câu hỏi đơn giản, không cần tool.

---

### Test case 3

Câu hỏi: “Tìm giúp tôi phòng trọ dưới 4 triệu/tháng ở Gia Lâm, Hà Nội.”

#### Baseline LLM-only

Baseline không có quyền truy cập database thời gian thực nên chỉ trả lời định hướng:

> Với mức giá dưới 4 triệu/tháng, bạn có thể tìm thấy phòng trọ sinh viên hoặc người lao động ở Gia Lâm. Giá thuê thường khoảng 2-4 triệu tùy diện tích và tiện nghi. Nếu cần thông tin chi tiết, hãy cung cấp thêm yêu cầu.

Nhận xét: An toàn nhưng không giải quyết được yêu cầu tìm listing cụ thể.

#### ReAct Agent

Trace thực tế:

```text
Thought: Tôi sẽ tiến hành tìm kiếm các phòng trọ dưới 4 triệu/tháng ở khu vực Gia Lâm, Hà Nội.
Action: search_rentals[area='Gia Lâm', max_price=4000000, room_type='phòng trọ']

Observation:
Tim thay 2 listing phu hop:
- PT001 | phong tro | Gia Lam | 3.500.000 VND/thang | 22m2 | con trong | Ngo 68 Xuan Thuy, Gia Lam, Ha Noi | Tien ich: gac xep, dieu hoa, wifi, cho de xe
- PT003 | phong tro | Gia Lam | 3.800.000 VND/thang | 20m2 | da het phong | Pho Dich Vong Hau, Gia Lam, Ha Noi | Tien ich: wifi, tu lanh, khep kin
```

Sau đó agent thử gọi sai tool:

```text
Action: get_property_details[property_id='PT001']
Observation:
LOI: Công cụ 'get_property_details' không tồn tại. Các công cụ khả dụng: search_rentals, get_listing_detail, check_availability, book_viewing, compare_listings
```

Agent tự sửa:

```text
Action: get_listing_detail[property_id='PT001']
```

Final Answer:

> Có phòng PT001 giá 3.500.000 VND/tháng, diện tích 22m2, địa chỉ Ngõ 68 Xuân Thủy, Gia Lâm, Hà Nội, tiện ích gồm gác xếp, điều hòa, wifi, chỗ để xe. Agent hỏi người dùng có muốn đặt lịch xem phòng không.

Nhận xét: Agent tìm được listing thật từ tool và phục hồi sau lỗi gọi sai tool. Tuy nhiên `MAX_ITERATIONS = 3`, nên sau khi hoàn thành vẫn in thêm guardrail do điều kiện `step >= MAX_ITERATIONS`. Đây là lỗi nhỏ về logging/điều kiện in guardrail trong `app.py`, không phải lỗi tool.

---

### Test case 4

Câu hỏi: “Tìm căn hộ cho thuê ở Gia Lâm dưới 8 triệu/tháng, sau đó đặt lịch xem phòng mã CH002 vào thứ 7 tuần này lúc 10:00, tên liên hệ Trần Minh Đức.”

#### Baseline LLM-only

Baseline trả lời:

> Không có khả năng truy cập cơ sở dữ liệu thời gian thực để tìm căn hộ cụ thể. Cũng không thể đặt lịch xem phòng mã CH002. Người dùng nên liên hệ trực tiếp bên cho thuê.

Nhận xét: Baseline an toàn, nhưng không hoàn thành tác vụ.

#### ReAct Agent

Trace thực tế:

```text
Thought: Tôi sẽ bắt đầu bằng cách tìm kiếm danh sách căn hộ cho thuê ở Gia Lâm với mức giá dưới 8 triệu đồng mỗi tháng.
Action: search_rentals[GIA LÂM, 8000000, 'căn hộ']

Observation:
LOI khi chạy công cụ: invalid syntax. Perhaps you forgot a comma?
```

Agent tự sửa cú pháp:

```text
Action: search_rentals['Gia Lâm', 8000000, 'căn hộ']

Observation:
Tim thay 2 listing phu hop:
- CH002 | can ho | Gia Lam | 7.500.000 VND/thang | 45m2 | con trong | Pho Chua Boc, Gia Lam, Ha Noi | Tien ich: 1 phong ngu, ban cong, may giat, gan truong dai hoc
- CH003 | can ho | Gia Lam | 6.800.000 VND/thang | 38m2 | con trong | Pho Nguyen Trai, Gia Lam, Ha Noi | Tien ich: studio, thang may, bep rieng
```

Final Answer:

> Agent yêu cầu người dùng cung cấp số điện thoại để tiến hành đặt lịch xem phòng CH002 vào thứ 7 tuần này lúc 10:00.

Nhận xét: Agent đã tìm đúng căn hộ CH002 nhưng chưa gọi `book_viewing` vì prompt yêu cầu cần số điện thoại trước khi đặt lịch. Đây là hành vi an toàn theo guardrail, dù test case ban đầu kỳ vọng đặt lịch ngay. Nếu muốn đặt được ngay, cần thêm số điện thoại vào input hoặc sửa guardrail cho phép đặt lịch không cần số điện thoại.

---

### Test case 5

Câu hỏi: “Tôi cần một phòng trọ ở Trâu Quý hoặc Gia Lâm, có wifi và điều hòa, ngân sách dưới 4,5 triệu/tháng, diện tích tối thiểu 20m2.”

#### Baseline LLM-only

Baseline trả lời định hướng:

> Với ngân sách dưới 4,5 triệu/tháng tại Trâu Quý hoặc Gia Lâm, có thể tìm được phòng trọ có wifi, điều hòa, diện tích tối thiểu 20m2. Nên tìm gần các trường đại học hoặc khu sinh viên.

Nhận xét: Không có listing cụ thể, không kiểm tra được dữ liệu thực tế.

#### ReAct Agent

Trace thực tế:

```text
Thought: Tôi sẽ tìm kiếm danh sách phòng trọ ở khu vực Trâu Quỳ hoặc Gia Lâm, với yêu cầu về wifi, điều hòa, ngân sách tối đa 4,5 triệu/tháng và diện tích tối thiểu 20m2.
Action: search_rentals["Trâu Quỳ", 4500000, "phòng trọ"]

Observation:
LOI: Khong tim thay listing phu hop voi khu vuc 'Trâu Quỳ', loai 'phòng trọ', ngan sach 4.500.000 VND/thang.
```

Agent mở rộng sang Gia Lâm:

```text
Action: search_rentals["Gia Lâm", 4500000, "phòng trọ"]

Observation:
Tim thay 3 listing phu hop:
- PT001 | phong tro | Gia Lam | 3.500.000 VND/thang | 22m2 | con trong | Ngo 68 Xuan Thuy, Gia Lam, Ha Noi | Tien ich: gac xep, dieu hoa, wifi, cho de xe
- PT002 | phong tro | Gia Lam | 4.200.000 VND/thang | 25m2 | con trong | Ngo 123 Tran Duy Hung, Gia Lam, Ha Noi | Tien ich: dieu hoa, ban cong, may giat chung
- PT003 | phong tro | Gia Lam | 3.800.000 VND/thang | 20m2 | da het phong | Pho Dich Vong Hau, Gia Lam, Ha Noi | Tien ich: wifi, tu lanh, khep kin
```

Final Answer:

> Agent đề xuất PT001 và PT002 là 2 phòng còn trống tại Gia Lâm. PT001 có wifi và điều hòa, giá 3.500.000 VND/tháng, diện tích 22m2. PT002 có điều hòa, giá 4.200.000 VND/tháng, diện tích 25m2, nhưng không có wifi trong dữ liệu tiện ích.

Nhận xét: Agent xử lý tốt bước mở rộng khu vực sau khi Trâu Quỳ không có kết quả. Tuy nhiên, agent chưa lọc chặt điều kiện “có wifi và điều hòa”: PT002 thiếu wifi trong dữ liệu tool nhưng vẫn được đề xuất. PT001 là lựa chọn khớp nhất.

## 3. Tổng kết so sánh

| Loại câu hỏi | Baseline LLM-only | ReAct Agent |
| :--- | :--- | :--- |
| Câu kiến thức chung | Trả lời tốt, ngắn gọn | Trả lời tốt, không cần tool |
| Câu cần dữ liệu listing | Chỉ tư vấn chung, không có kết quả cụ thể | Gọi `search_rentals` và trả về listing thật từ mock database |
| Câu nhiều bước | Không thể đặt lịch hoặc xác nhận mã phòng | Có thể tìm listing, sửa lỗi tool, hỏi thêm thông tin khi thiếu |
| Edge/guardrail | Không có cơ chế tool/guardrail | Có `MAX_ITERATIONS`, báo lỗi tool và tự phục hồi một phần |

## 4. Các lỗi/điểm cần cải thiện sau khi chạy thật

1. Prompt đang khai báo tool `get_property_details`, nhưng code thật chỉ có `get_listing_detail`. Điều này làm agent gọi sai tool ở test case 3.
2. Prompt khai báo `book_viewing_appointment`, nhưng code thật có `book_viewing`. Nên đồng bộ tên tool để agent đặt lịch tốt hơn.
3. Điều kiện in guardrail trong `run_react_agent()` hiện vẫn in guardrail nếu task hoàn thành đúng ở step cuối cùng. Nên thêm biến `completed = True` để chỉ in guardrail khi thật sự chưa có `Final Answer`.
4. Agent chưa lọc hậu xử lý theo tiện ích/diện tích thật chặt. Test case 5 cho thấy PT002 thiếu wifi nhưng vẫn được đề xuất.
5. Với test case đặt lịch, guardrail yêu cầu số điện thoại nên agent chưa gọi `book_viewing`. Nếu mục tiêu bài lab là đặt lịch luôn, cần thêm số điện thoại vào test case hoặc cho phép `phone` là optional trong prompt.

## 5. Kết luận

Kết quả chạy thật cho thấy baseline LLM-only phù hợp với câu hỏi kiến thức chung nhưng không thể xử lý tác vụ cần dữ liệu và hành động. ReAct Agent vượt trội ở các câu hỏi cần tìm listing, xử lý lỗi tool và điều phối nhiều bước, nhưng cần đồng bộ prompt-tool schema và cải thiện logic lọc kết quả để đạt trace eval tốt hơn.
