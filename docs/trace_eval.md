# 📊 BÁO CÁO GIÁM SÁT & ĐÁNH GIÁ (OBSERVABILITY TRACE LOGS)

*Dành cho Role 5: Observability & Reviewer*

---

## 🎯 1. BẢNG CHẤM ĐIỂM AGENTIC FIT (SCORING MATRIX)


| Tiêu chí                    | Điểm (1-5) | Lý do đánh giá                                                                                                                                                                                                                                          |
| --------------------------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 🧠 **Multi-step Reasoning** | `4/5`      | Cần thực hiện qua các step như: 1 - Tìm thông tin từ các trang web như [facbeook](http://facebook.com) và [batdongsan.com.vn](http://batdongsan.com.vn)- So sánh độ phù hợp của sản phẩm được list với hồ sơ của người dùng- Chốt lịch với người dùng |
| 🛠️ **Tool Interaction**    | `5/5`      | Cần tra cứu facebook với trang web [batdongsan.com.vn](http://batdongsan.com.vn) , google calendar, [https://phongtro123.com/](https://phongtro123.com/), [https://www.nhatot.com/,](https://www.nhatot.com/) zalo api                                 |
| 🔀 **Dynamic Decision**     | `4/5`      | Kết quả bước trước quyết định hành động bước sau.                                                                                                                                                                                                       |
| ⏳ **Long Horizon**          | `4/5`      | Cần có vì quá trình đặt lịch gồm nhiều bước và nhiều ngày                                                                                                                                                                                               |
| **TỔNG ĐIỂM FIT**           | **17/20**  | **KẾT LUẬN: BÀI TOÁN RẤT NÊN DÙNG REACT AGENT!**                                                                                                                                                                                                        |


---



## 🔍 2. SO SÁNH PHẢN HỒI (TEST CASE #3)

**Mốc 2:** 



==================================================

🏫 ĐẠI HỌC VINUNI - BÀI LAB 3: CHATBOT VS REACT AGENT

==================================================

🔌 LLM Provider đang hoạt động: MockProvider (Model: Offline Mock Mode)

✅ Đã tải thành công 5 Test Cases từ config/test_cases.json

--- DEMO 1: CHẠY TRÊN CHATBOT BASELINE ---

💬 [CHATBOT BASELINE] Câu hỏi: Mình cần thuê studio ở Quận 7 trong 6 tháng, ngân sách 7 triệu. Tìm giúp mình vài chỗ phù hợp và hỏi chủ nhà còn phòng không.

⚙️ System Prompt: Bạn là chatbot tư vấn thuê trọ/căn hộ.

Hãy trả lời thân thiện, rõ ràng, dựa trên kiến thức sẵn có.

Nếu người dùng yêu cầu dữ liệu thời gian thực (bài đăng đang còn, số điện thoại thật, phản hồi chủ nhà),

hãy nói rõ bạn không thể tự xác minh trực tiếp trong chế độ baseline.

🤖 Chatbot trả lời:

🤖 [Mock Provider]: Phản hồi giả lập offline cho bài test.

--- DEMO 2: CHẠY TRÊN REACT AGENT ---

🤖 [REACT AGENT] Câu hỏi: Mình cần thuê studio ở Quận 7 trong 6 tháng, ngânsách 7 triệu. Tìm giúp mình vài chỗ phù hợp và hỏi chủ nhà còn phòng không.

--- 🔄 Vòng lặp ReAct (Step 1/3) ---

🧠 Thought: Cần tìm danh sách bài đăng phù hợp yêu cầu user.

🛠️ Action: search_home_info['Quận 7', '6 tháng', 7000000, 'studio']

👁️ Observation: Kết quả tìm kiếm theo yêu cầu (location=Quận 7, rent_duration=6 tháng, budget=7000000, room_info=studio):

- Studio full nội thất gần ĐH Tôn Đức Thắng | 6.5 triệu/tháng | Nguồn: Facebook Group: Phòng trọ Quận 7 | Liên hệ: Nguyễn Minh (0909123456) | Profile: facebook.com/minh.nguyen.rent

- Căn hộ 1PN Sunrise Cityview | 9.8 triệu/tháng | Nguồn: Batdongsan | Liên hệ: Trần Thu Hà (0911222333) | Profile: batdongsan.vn/ha-tran

--- 🔄 Vòng lặp ReAct (Step 2/3) ---

🧠 Thought: Cần xác nhận tình trạng còn phòng với chủ nhà phù hợp nhất.

🛠️ Action: send_msg['0909123456', 'Anh/chị còn phòng studio ở Quận 7 không ạ?']

👁️ Observation: Đã gửi Zalo tới 0909123456: 'Anh/chị còn phòng studio ở Quận7 không ạ?'. Phản hồi: Còn phòng, có thể dọn vào từ tuần sau.

--- 🔄 Vòng lặp ReAct (Step 3/3) ---

🧠 Thought: Nếu còn phòng, lấy lịch rảnh user để đề xuất lịch xem nhà.

🛠️ Action: get_calendar[]

👁️ Observation: Lịch rảnh gợi ý: Thứ 4 (19:00-20:30), Thứ 6 (18:30-20:00), Chủ nhật (09:00-11:00).

