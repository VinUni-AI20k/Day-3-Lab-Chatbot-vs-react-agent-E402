# 📊 BÁO CÁO GIÁM SÁT & ĐÁNH GIÁ (OBSERVABILITY TRACE LOGS)

_Dành cho Role 5: Observability & Reviewer — Đề tài: **Cupid Agent: Trợ Lý Ghép Đôi & Phân Tích Độ Tương Thích**_

---

## 🎯 1. BẢNG CHẤM ĐIỂM AGENTIC FIT (SCORING MATRIX)

| Tiêu chí | Điểm (1-5) | Lý do đánh giá |
| :--- | :---: | :--- |
| 🧠 **Multi-step Reasoning** | `5/5` | Cần suy luận, phân tích hồ sơ, lọc ứng viên và đánh giá độ tương thích theo nhiều bước. |
| 🛠️ **Tool Interaction** | `5/5` | Cần sử dụng nhiều Tool: lấy hồ sơ người dùng, tìm Top 3 ứng viên phù hợp, tính toán độ tương thích và tạo lời mở đầu dựa trên điểm chung. |
| 🔀 **Dynamic Decision** | `5/5` | Kết quả bước trước quyết định hành động bước sau. |
| ⏳ **Long Horizon** | `4/5` | Quy trình xử lý gồm nhiều bước liên tiếp (lấy hồ sơ → lọc ứng viên → tính điểm → phân tích kết quả → tạo lời mở đầu) trước khi tạo Final Answer. |
| **TỔNG ĐIỂM FIT** | **19/20** | **KẾT LUẬN: BÀI TOÁN RẤT NÊN DÙNG REACT AGENT!** |

---

## 2. KẾT QUẢ ĐÁNH GIÁ MỐC 2

### 2.1. Mục tiêu đánh giá

Quan sát phản hồi của Chatbot Baseline khi được cung cấp dữ liệu hồ sơ mô phỏng; kiểm tra khả năng bám sát dữ liệu, nguy cơ ảo giác, quyền riêng tư và những hạn chế so với ReAct Agent.

### 2.2. Cấu hình kiểm thử

| Hạng mục | Giá trị |
| :--- | :--- |
| Provider | OpenAI |
| Model | `gpt-4o-mini` |
| Dữ liệu | 12 hồ sơ mô phỏng trong `cupid_data/cupid_profiles.json` |
| Test case | Test case số 3 |
| Tool calls | Không sử dụng — đúng thiết kế Chatbot Baseline |

### 2.3. Đầu vào kiểm thử

> Tôi là người dùng U001. Hãy tìm 3 hồ sơ phù hợp nhất với tôi.

### 2.4. Kết quả quan sát

Chatbot đọc dữ liệu mock được đưa trực tiếp vào context và đề xuất ba hồ sơ theo thứ tự:

1. **U002 — Bình**
2. **U003 — Cường**
3. **U004 — Dũng**

Chatbot giải thích kết quả dựa trên các thông tin có trong dữ liệu mock như sở thích, giá trị sống, mục tiêu mối quan hệ, địa điểm và thói quen. Chatbot cũng nêu rõ kết quả chỉ mang tính tham khảo, không phải kết luận khoa học.

### 2.5. Bảng đánh giá

| Tiêu chí | Kết quả | Nhận xét |
| :--- | :---: | :--- |
| Sử dụng đúng mock data | **Đạt** | Không tạo thêm ID hoặc hồ sơ ngoài dữ liệu được cung cấp. |
| Top 3 ứng viên | **Đạt** | Trả đúng U002, U003, U004 và đúng thứ tự mong đợi. |
| Mức độ bám sát dữ liệu | **Đạt** | Các lý do chính đều xuất phát từ trường dữ liệu của hồ sơ. |
| Ảo giác | **Không phát hiện nghiêm trọng** | Không bịa ứng viên hoặc thuộc tính quan trọng không tồn tại. Tuy nhiên, cách diễn giải vẫn do LLM tạo ra. |
| Quyền riêng tư | **Đạt** | Không đưa ra số điện thoại, email, địa chỉ chính xác hoặc tọa độ. |
| Sử dụng tool | **Không sử dụng** | Đúng với baseline nhưng không tạo được trace `Action → Observation`. |
| Điểm tương thích | **Chưa đạt** | Không tính và kiểm chứng deterministic các điểm kỳ vọng 90.0, 75.0 và 69.0. |
| Khả năng lặp lại | **Chưa bảo đảm** | Cách diễn đạt và kết quả suy luận có thể thay đổi giữa các lần gọi LLM. |

### 2.6. Hạn chế của Chatbot Baseline

- Toàn bộ mock data phải được đưa vào context, làm tăng kích thước prompt.
- Chatbot không tự gọi tool để lấy đúng dữ liệu cần thiết.
- Không có trace để biết Agent đã thực hiện hành động nào.
- Không bảo đảm công thức tính điểm và thứ tự xếp hạng luôn chính xác.
- Khó xử lý ổn định các lỗi như ID không tồn tại hoặc hồ sơ không có ứng viên phù hợp.

### 2.7. Kết luận Mốc 2

Chatbot Baseline đã sử dụng đúng dữ liệu mock và tìm đúng ba ứng viên U002, U003, U004. Tuy nhiên, baseline chưa bảo đảm tính điểm deterministic, không có tool trace và kết quả vẫn phụ thuộc vào suy luận của LLM. Đây là cơ sở để chuyển sang ReAct Agent ở Mốc 3, nơi các thao tác lọc và tính điểm phải được thực hiện bằng tool.

---


