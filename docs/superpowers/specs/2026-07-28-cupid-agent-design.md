# Cupid Agent Design

## 1. Mục tiêu

Cupid Agent là trợ lý ghép đôi và phân tích độ tương thích dùng dữ liệu mô phỏng. Người dùng chọn một hồ sơ có sẵn, yêu cầu agent tìm ứng viên phù hợp, xem phân tích chi tiết và tạo lời mở đầu tôn trọng dựa trên điểm chung.

Sản phẩm dùng ReAct để LLM lựa chọn tool, nhưng mọi thao tác lọc và chấm điểm phải deterministic. LLM chỉ điều phối tool và diễn đạt kết quả; không tự tính điểm hoặc tự suy luận thông tin hồ sơ.

## 2. Phạm vi

### Bao gồm

- 12 hồ sơ mock, tất cả từ 18 tuổi trở lên.
- Lọc sở thích giới tính tương thích hai chiều.
- Loại ứng viên vi phạm deal-breaker của một trong hai phía.
- Xếp hạng top 3 theo công thức trọng số cố định.
- Phân tích chi tiết một cặp hồ sơ.
- Tạo lời mở đầu từ điểm chung.
- ReAct executor dùng LLM thật và có mock fallback.
- Flask web UI gồm chat, bảng kết quả, phân tích và trace tool calls.
- Kiểm thử tool, parser, executor và Flask API bằng `unittest`.

### Không bao gồm

- Dữ liệu người dùng thật, tài khoản, đăng nhập hoặc database.
- Chỉnh sửa hay tạo hồ sơ qua giao diện.
- Lưu lịch sử trò chuyện phía server.
- Nhắn tin thật hoặc tích hợp nền tảng hẹn hò.
- Mô hình machine learning để dự đoán độ tương thích.
- Tuyên bố điểm số có giá trị khoa học hoặc bảo đảm thành công quan hệ.

## 3. Bố trí thư mục

```text
project/
├── cupid_web/                 # Flask web UI mới
│   ├── app.py
│   ├── templates/
│   │   └── index.html
│   └── static/
│       ├── app.js
│       └── style.css
├── cupid_data/                # dữ liệu mock mới
│   └── profiles.json
├── tests/                     # kiểm thử mới
├── src/
│   ├── tools.py               # Cupid tools và registry
│   ├── app.py                 # ReAct executor độc lập với UI
│   ├── prompts.py             # Cupid prompt và guardrails
│   └── providers.py           # provider hiện có, mock fallback khi cần
└── requirements.txt           # thêm Flask
```

Luồng phụ thuộc một chiều:

```text
cupid_web -> src/app.py -> src/tools.py -> cupid_data/profiles.json
                     \-> src/providers.py
```

Web UI và dữ liệu mock được đặt trong các thư mục mới. Agent và tool tiếp tục dùng các file `src/` hiện có để phù hợp scaffold của lab.

## 4. Dữ liệu mock

`cupid_data/profiles.json` chứa đúng 12 hồ sơ. Mỗi ID là duy nhất và mọi hồ sơ đều từ 18 tuổi trở lên.

Schema logic:

```json
{
  "id": "U001",
  "name": "An",
  "age": 26,
  "gender": "female",
  "interested_in": ["male"],
  "location": "Hà Nội",
  "interests": ["du lịch", "nhiếp ảnh", "cà phê"],
  "values": ["gia đình", "trung thực", "phát triển bản thân"],
  "relationship_goal": "long_term",
  "attributes": {
    "smoking": false,
    "drinking": "social"
  },
  "deal_breakers": {
    "smoking": true
  }
}
```

Bộ dữ liệu phải tạo được các tình huống sau:

- Một hồ sơ có ít nhất ba ứng viên hợp lệ.
- Một cặp không tương thích về `interested_in` hai chiều.
- Một cặp bị loại vì deal-breaker từ phía người tìm.
- Một cặp bị loại vì deal-breaker từ phía ứng viên.
- Một hồ sơ không có ứng viên hợp lệ.
- Một cặp có nhiều sở thích và giá trị chung để minh họa điểm cao.

Không đặt số điện thoại, email, địa chỉ cụ thể hoặc dữ liệu nhận dạng thật trong hồ sơ.

## 5. Quy tắc đủ điều kiện

Một cặp chỉ được chấm điểm khi thỏa cả hai điều kiện:

1. Giới tính của mỗi người nằm trong `interested_in` của người còn lại.
2. Không ai vi phạm `deal_breakers` của người kia.

Deal-breaker được đánh giá hai chiều và là điều kiện loại tuyệt đối. Ứng viên không đủ điều kiện không xuất hiện trong top 3, bất kể điểm ở các tiêu chí khác.

## 6. Công thức tương thích

Điểm tổng nằm trong khoảng 0–100 và dùng trọng số cố định:

| Tiêu chí | Trọng số | Quy tắc |
|---|---:|---|
| Mục tiêu quan hệ | 35% | 100 nếu giống nhau, ngược lại 0 |
| Giá trị sống | 30% | Tỷ lệ giao nhau trên hợp của hai tập giá trị |
| Sở thích | 20% | Tỷ lệ giao nhau trên hợp của hai tập sở thích |
| Vị trí | 15% | 100 nếu cùng vị trí, ngược lại 0 |

Với tiêu chí dạng tập, dùng Jaccard similarity:

```text
score(A, B) = |A ∩ B| / |A ∪ B| * 100
```

Điểm tổng:

```text
total = goal * 0.35 + values * 0.30 + interests * 0.20 + location * 0.15
```

Làm tròn điểm hiển thị đến một chữ số thập phân. Xếp hạng giảm dần theo điểm tổng; nếu bằng điểm, sắp xếp tăng dần theo candidate ID để đầu ra deterministic.

## 7. Tool contracts

Mọi tool trả một trong hai cấu trúc:

```python
{"ok": True, "data": {"user_id": "U001"}}
{"ok": False, "error": {"code": "PROFILE_NOT_FOUND", "message": "Không tìm thấy hồ sơ U999"}}
```

Tool không ném exception cho lỗi nghiệp vụ dự kiến. Lỗi đọc hoặc parse file dữ liệu vẫn được ghi nhận là lỗi hệ thống bởi caller.

### 7.1 `get_user_profile(user_id)`

**Mục đích:** Lấy hồ sơ mock theo ID.

**Input:**

```python
{"user_id": "U001"}
```

**Output thành công:** Hồ sơ phù hợp cho agent và UI. Không thêm thuộc tính ngoài dữ liệu nguồn.

**Lỗi:**

- `INVALID_INPUT`: `user_id` thiếu hoặc sai kiểu.
- `PROFILE_NOT_FOUND`: ID không tồn tại.

### 7.2 `find_candidate_matches(user_id, limit=3)`

**Mục đích:** Lọc và xếp hạng ứng viên hợp lệ.

**Input:**

```python
{"user_id": "U001", "limit": 3}
```

`limit` là số nguyên từ 1 đến 3.

**Output thành công:** Danh sách tối đa `limit` phần tử, mỗi phần tử gồm:

- `candidate_id`
- `name`
- `score`
- `reasons`: tối đa ba lý do ngắn dựa trên tiêu chí đã tính

**Lỗi:**

- `INVALID_INPUT`
- `PROFILE_NOT_FOUND`
- `NO_MATCHES`

### 7.3 `calculate_compatibility(user_id, candidate_id)`

**Mục đích:** Phân tích chi tiết một cặp.

**Input:**

```python
{"user_id": "U001", "candidate_id": "U002"}
```

**Output thành công:**

- `eligible: true`
- `total_score`
- `breakdown`: điểm mục tiêu, giá trị, sở thích và vị trí
- `shared_interests`
- `shared_values`
- `reasons`

**Lỗi:**

- `INVALID_INPUT`
- `PROFILE_NOT_FOUND`
- `INELIGIBLE_MATCH`: nêu loại điều kiện không đạt nhưng không tiết lộ quá mức dữ liệu riêng của bên kia.

### 7.4 `suggest_first_message(user_id, candidate_id)`

**Mục đích:** Tạo một lời mở đầu deterministic, tôn trọng và dựa trên điểm chung.

**Input:**

```python
{"user_id": "U001", "candidate_id": "U002"}
```

**Output thành công:**

- `message`
- `based_on`: sở thích hoặc giá trị chung đã dùng

Tool ưu tiên sở thích chung đầu tiên theo thứ tự ổn định; nếu không có sở thích chung thì dùng giá trị chung. Nếu không có điểm chung phù hợp, trả lời chào trung tính thay vì bịa thông tin.

**Lỗi:**

- `INVALID_INPUT`
- `PROFILE_NOT_FOUND`
- `INELIGIBLE_MATCH`

### 7.5 Registry

Bốn tool được đăng ký trong `AVAILABLE_TOOLS`. ReAct executor chỉ được gọi tên có trong registry; không dùng `eval` hoặc dynamic import từ output của LLM.

## 8. ReAct executor

`src/app.py` cung cấp API nội bộ độc lập với Flask:

```python
run_react_agent(user_query, provider, user_id=None) -> {
    "answer": str,
    "matches": list[dict],
    "compatibility": dict | None,
    "opener": dict | None,
    "trace": list[dict],
}
```

### 8.1 Chu trình

Mỗi vòng:

1. Gửi system prompt, user context và các observation trước đó cho provider.
2. Parse output thành một action hoặc final answer.
3. Kiểm tra tên tool và JSON input.
4. Bổ sung `user_id` đã chọn nếu action cần trường này và model không cung cấp.
5. Gọi tool từ registry.
6. Lưu action, input và observation vào trace.
7. Đưa observation lại cho provider.

Dừng khi nhận `Final Answer` hoặc sau tối đa năm vòng.

### 8.2 Định dạng model output

Action:

```text
Action: find_candidate_matches
Action Input: {"user_id": "U001", "limit": 3}
```

Hoặc kết thúc:

```text
Final Answer: Mình đã tìm thấy ba ứng viên phù hợp nhất cho hồ sơ U001.
```

Parser chỉ chấp nhận JSON object ở `Action Input`. Output sai định dạng trả `INVALID_ACTION`; tool không tồn tại trả `UNKNOWN_TOOL`.

### 8.3 Trace

Trace công khai cho UI chỉ chứa:

- số vòng
- tên action
- action input đã được kiểm tra
- observation có cấu trúc
- trạng thái lỗi nếu có

Không hiển thị hoặc lưu chain-of-thought chi tiết. Prompt có thể yêu cầu model suy luận nội bộ nhưng response contract chỉ dùng action hoặc final answer.

### 8.4 Provider và fallback

- Ưu tiên provider thật đã chọn qua cấu hình hiện có.
- Mock provider tạo action deterministic cho các luồng demo chuẩn.
- Fallback sang mock chỉ xảy ra khi chế độ fallback được bật rõ trong cấu hình và provider thật không khả dụng.
- UI phải gắn nhãn khi response đến từ mock fallback.

## 9. Prompt và guardrails

System prompt mô tả:

- Vai trò trợ lý ghép đôi trên dữ liệu mô phỏng.
- Danh sách tool và schema input.
- Yêu cầu dùng tool thay vì tự tính điểm hoặc bịa hồ sơ.
- Yêu cầu chỉ trả action hoặc final answer đúng định dạng.
- Tối đa năm vòng.

Guardrails:

- Chỉ xử lý hồ sơ người trưởng thành trong bộ mock.
- Không suy luận thuộc tính nhạy cảm không có trong dữ liệu.
- Không hỗ trợ theo dõi, thao túng, quấy rối hoặc hành vi thiếu đồng thuận.
- Không tạo nội dung tình dục hoặc gây áp lực trong lời mở đầu.
- Không trình bày điểm tương thích như kết luận khoa học.
- Không tiết lộ toàn bộ deal-breaker riêng tư của ứng viên trong thông báo lỗi.

## 10. Flask web UI

### 10.1 Routes

`GET /`

- Render trang chính.
- Cung cấp danh sách ID và tên hiển thị của 12 profile mock.

`POST /api/chat`

Request:

```json
{
  "message": "Hãy tìm người phù hợp với tôi",
  "user_id": "U001"
}
```

Response thành công:

```json
{
  "ok": true,
  "data": {
    "answer": "Mình đã tìm thấy ba ứng viên phù hợp nhất.",
    "matches": [],
    "compatibility": null,
    "opener": null,
    "trace": [],
    "provider_mode": "live"
  }
}
```

API kiểm tra `user_id`, message không rỗng và giới hạn message tối đa 1000 ký tự.

### 10.2 Giao diện

Trang chính gồm:

- Dropdown chọn profile mock.
- Khung chat.
- Bảng top 3 với tên, điểm và lý do.
- Panel điểm chi tiết theo tiêu chí.
- Nút yêu cầu lời mở đầu.
- Panel tool trace có thể thu gọn.
- Nhãn “Dữ liệu mô phỏng — kết quả chỉ nhằm mục đích minh họa”.
- Nhãn `live` hoặc `mock fallback` cho provider.

JavaScript chỉ gửi request, render dữ liệu có cấu trúc và quản lý trạng thái hiện tại trong browser. Logic lọc, tính điểm và tạo lời mở đầu không nằm trong JavaScript.

Nội dung động phải được gán bằng API DOM an toàn như `textContent`, không chèn trực tiếp bằng `innerHTML` từ response của LLM.

## 11. Xử lý lỗi

Các mã lỗi nghiệp vụ:

- `PROFILE_NOT_FOUND`
- `INVALID_INPUT`
- `INELIGIBLE_MATCH`
- `NO_MATCHES`
- `UNKNOWN_TOOL`
- `INVALID_ACTION`
- `MAX_ITERATIONS`
- `PROVIDER_ERROR`

Ánh xạ HTTP:

| Trường hợp | HTTP |
|---|---:|
| Input request sai | 400 |
| Profile không tồn tại | 404 |
| Provider upstream lỗi | 502 |
| Lỗi hệ thống không dự kiến | 500 |

Tool error trong một chu trình ReAct được đưa vào observation để model có thể điều chỉnh action. Flask không trả stack trace, API key hoặc nội dung cấu hình cho client.

## 12. Kiểm thử

Dùng `unittest` của Python stdlib.

### Tool tests

- Lấy profile hợp lệ và ID không tồn tại.
- Lọc `interested_in` tương thích hai chiều.
- Loại ứng viên khi một trong hai phía vi phạm deal-breaker.
- Điểm từng tiêu chí và tổng điểm đúng công thức.
- Điểm luôn trong khoảng 0–100.
- Top 3 có thứ tự ổn định khi bằng điểm.
- Phân tích cặp không đủ điều kiện.
- Lời mở đầu chỉ dùng điểm chung hoặc lời chào trung tính.

### Parser và executor tests

- Parse action và JSON input hợp lệ.
- Từ chối JSON lỗi.
- Từ chối unknown tool.
- Chuyển observation giữa các vòng.
- Dừng khi có final answer.
- Dừng với `MAX_ITERATIONS` sau năm vòng.
- Mock provider hoàn thành các luồng demo deterministic.

### Flask API tests

- Request hợp lệ.
- Thiếu hoặc rỗng message.
- Message vượt 1000 ký tự.
- User ID không tồn tại.
- Response tuân thủ schema.

### Happy path tích hợp

Một test thực hiện luồng:

```text
chọn profile -> tìm top 3 -> phân tích candidate -> tạo lời mở đầu
```

Không kiểm thử wording chính xác hoặc chain-of-thought của LLM thật. Chỉ kiểm thử contract, tool calls và output có cấu trúc.

## 13. Tiêu chí hoàn thành

- Web UI khởi động bằng Flask và hiển thị đủ 12 profile mock.
- Người dùng chọn profile, yêu cầu ghép đôi và nhận top 3 hợp lệ.
- Điểm trong UI khớp hoàn toàn với kết quả tool.
- Có thể phân tích một candidate và tạo lời mở đầu.
- Panel trace cho thấy action, input và observation mà không lộ chain-of-thought.
- Demo chạy với provider thật khi có cấu hình và chạy deterministic bằng mock fallback khi được bật.
- Toàn bộ test `unittest` đạt.
- Không có dữ liệu thật, database hoặc side effect ra dịch vụ bên ngoài ngoài lời gọi LLM đã cấu hình.
