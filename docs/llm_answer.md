(.venv) [tofu@endeavour-thinkpad Day-3-Lab-Chatbot-vs-react-agent-E402]$ python src/app.py
==================================================
🏫 ĐẠI HỌC VINUNI - BÀI LAB 3: CHATBOT VS REACT AGENT
==================================================
🔌 LLM Provider đang hoạt động: GeminiProvider (Model: gemini-3.6-flash)
✅ Đã tải thành công 5 Test Cases từ config/test_cases.json

--- CHẠY CHATBOT BASELINE TRÊN 5 TEST CASES ---

============================================================
TEST CASE #1
Category: 🟢 Đơn giản (Chỉ cần LLM)

💬 [CHATBOT BASELINE] Câu hỏi: Thủ đô của Việt Nam là gì?
⚙️ System Prompt: Bạn là một Chatbot tư vấn thông thường.
Hãy trả lời câu hỏi của người dùng một cách thân thiện dựa trên kiến thức có sẵn của bạn.
Nếu không biết thông tin thực tế thời gian thực, hãy lịch sự thông báo cho người dùng.
🤖 Chatbot trả lời:
Xin chào bạn!

Thủ đô của Việt Nam là thành phố **Hà Nội** ạ.

Hà Nội là trung tâm chính trị, văn hóa và kinh tế lớn của cả nước, nổi tiếng với lịch sử nghìn năm văn hiến cùng nhiều danh lam thắng cảnh và ẩm thực phong phú.

Nếu bạn muốn tìm hiểu thêm thông tin gì khác, cứ thoải mái hỏi mình nhé!

============================================================
TEST CASE #2
Category: 🟢 Đơn giản (Chỉ cần LLM)

💬 [CHATBOT BASELINE] Câu hỏi: Nêu 3 lời khuyên để học tốt lập trình.
⚙️ System Prompt: Bạn là một Chatbot tư vấn thông thường.
Hãy trả lời câu hỏi của người dùng một cách thân thiện dựa trên kiến thức có sẵn của bạn.
Nếu không biết thông tin thực tế thời gian thực, hãy lịch sự thông báo cho người dùng.
🤖 Chatbot trả lời:
Chào bạn! Rất vui được hỗ trợ bạn hôm nay. Học lập trình là một hành trình rất thú vị nhưng cũng đầy thách thức. Dưới đây là 3 lời khuyên quan trọng nhất giúp bạn học tốt lập trình nhé:

1. **Thực hành thường xuyên và Tự làm dự án (Code mỗi ngày)**
   Lập trình cũng giống như học chơi một nhạc cụ hay một môn thể thao, bạn không thể giỏi nếu chỉ đọc sách hay xem video hướng dẫn. Cách tốt nhất là hãy xắn tay áo lên và gõ code. Hãy bắt đầu từ những bài tập nhỏ, sau đó tự thử thách bản thân bằng cách làm các dự án cá nhân (như làm một trang web đơn giản, một ứng dụng ghi chú, hay một trò chơi nhỏ). Việc tự làm dự án sẽ giúp bạn hiểu sâu và nhớ lâu hơn rất nhiều.

2. **Nắm chắc kiến thức nền tảng và Tư duy logic**
   Đừng quá vội vàng chạy theo các công nghệ mới hay học cùng lúc quá nhiều ngôn ngữ lập trình. Hãy chọn một ngôn ngữ ban đầu (như Python, JavaScript, hoặc C++) và tập trung hiểu rõ bản chất của nó: biến, vòng lặp, hàm, cấu trúc dữ liệu... Khi bạn đã có nền tảng vững chắc và tư duy giải quyết vấn đề (problem-solving) tốt, việc chuyển sang học một ngôn ngữ hay công nghệ mới sau này sẽ trở nên cực kỳ dễ dàng.

3. **Học cách tìm kiếm thông tin và Kiên trì khi gặp lỗi (Debug)**
   Trong lập trình, việc gặp lỗi (bug) là điều xảy ra hàng ngày, kể cả với những lập trình viên lâu năm. Lời khuyên là đừng nản lòng khi chương trình không chạy! Hãy học cách đọc hiểu thông báo lỗi, sử dụng Google, Stack Overflow hoặc các công cụ AI để tìm kiếm giải pháp. Khả năng tự tìm kiếm và sửa lỗi chính là một trong những kỹ năng quan trọng nhất của một lập trình viên giỏi.

Hy vọng 3 lời khuyên này sẽ giúp bạn có một khởi đầu thuận lợi! Bạn đang dự định học ngôn ngữ lập trình nào, hay có thắc mắc gì thêm không? Mình luôn sẵn sàng chia sẻ nhé!

============================================================
TEST CASE #3
Category: 🟡 Multi-step (Cần Tool)

💬 [CHATBOT BASELINE] Câu hỏi: Thời tiết ở Hà Nội hôm nay thế nào và tôi nên mặc gì đi chơi?
⚙️ System Prompt: Bạn là một Chatbot tư vấn thông thường.
Hãy trả lời câu hỏi của người dùng một cách thân thiện dựa trên kiến thức có sẵn của bạn.
Nếu không biết thông tin thực tế thời gian thực, hãy lịch sự thông báo cho người dùng.
🤖 Chatbot trả lời:
Chào bạn! 🌸

Vì mình là AI nên tiếc là mình không thể cập nhật trực tiếp thời tiết thời gian thực của Hà Nội hôm nay được. Bạn hãy kiểm tra nhanh trên ứng dụng "Thời tiết" trên điện thoại hoặc tìm kiếm trên Google nhé!

Tuy nhiên, để giúp bạn có một buổi đi chơi thật thoải mái và lên hình xinh xắn, mình gợi ý cách phối đồ theo từng kiểu thời tiết phổ biến ở Hà Nội như sau nha:

*   **Nếu trời nắng nóng:**
    *   *Trang phục:* Hãy ưu tiên quần áo làm từ chất liệu mỏng nhẹ, thấm hút mồ hôi tốt như đũi (linen), cotton. Áo phông, sơ mi phom rộng, váy maxi hay quần short đều rất hợp.
    *   *Phụ kiện:* Đừng quên mang theo áo chống nắng, mũ rộng vành, kính râm và thoa kem chống nắng đầy đủ nhé.

*   **Nếu trời mát mẻ / hơi se lạnh (kiểu thời tiết thu/mùa xuân):**
    *   *Trang phục:* Bạn có thể mặc phối nhiều lớp (layering) như áo phông bên trong kết hợp áo cardigan, blazer nhẹ hoặc áo sơ mi khoác ngoài. Đi cùng quần jeans hoặc chân váy dài đều rất "thơ".
    *   *Phụ kiện:* Một đôi giày sneaker hoặc loafer vừa dễ đi lại vừa thời trang.

*   **Nếu trời lạnh (mùa đông):**
    *   *Trang phục:* Hãy mặc đủ ấm với áo giữ nhiệt bên trong, phối cùng áo len, áo dạ dáng dài hoặc áo phao.
    *   *Phụ kiện:* Khăn quàng cổ, mũ len và một đôi boot vừa giữ ấm tốt vừa là điểm nhấn tuyệt vời để chụp ảnh "sống ảo".

*   **Nếu trời có mưa lặt khặt / nồm ẩm:**
    *   *Trang phục:* Bạn nên chọn trang phục gọn gàng, sẫm màu, tránh quần/váy quá dài dễ bị bắn bẩn.
    *   *Phụ kiện:* Hãy mang theo một chiếc ô (dù) nhỏ gọn trong túi và ưu tiên đi giày dép chống trơn trượt hoặc dễ lau chùi nhé.

Chúc bạn có một ngày đi chơi thật vui vẻ và nhiều ảnh đẹp! Nếu bạn cần gợi ý thêm về các địa điểm cà phê hay ăn uống ở Hà Nội thì cứ hỏi mình nhé! 😊

============================================================
TEST CASE #4
Category: 🟡 Multi-step (Cần gọi 2 Tools)

💬 [CHATBOT BASELINE] Câu hỏi: Kiểm tra vé máy bay từ TP.HCM đi Hà Nội ngày mai và dự báo thời tiết ở Hà Nội.
⚙️ System Prompt: Bạn là một Chatbot tư vấn thông thường.
Hãy trả lời câu hỏi của người dùng một cách thân thiện dựa trên kiến thức có sẵn của bạn.
Nếu không biết thông tin thực tế thời gian thực, hãy lịch sự thông báo cho người dùng.
🤖 Chatbot trả lời:
Chào bạn! Rất vui được hỗ trợ bạn hôm nay. 😊

Về yêu cầu **kiểm tra vé máy bay** và **dự báo thời tiết ngày mai**, do tôi là một trợ lý AI không có kết nối với dữ liệu thời gian thực (real-time), nên tôi không thể tra cứu giá vé chính xác theo giờ hay dự báo thời tiết mới nhất cho bạn được. Rất mong bạn thông cảm nhé!

Tuy nhiên, tôi xin gửi bạn một số thông tin tham khảo và hướng dẫn tra cứu nhanh nhất dưới đây:

✈️ **Về vé máy bay TP.HCM (SGN) đi Hà Nội (HAN):**
*   **Các hãng khai thác:** Vietnam Airlines, Vietjet Air, Bamboo Airways và Vietravel Airlines. Đây là chặng bay trục chính nên có rất nhiều chuyến trong ngày (từ sáng sớm đến đêm muộn).
*   **Thời gian bay:** Khoảng 2 tiếng 10 phút.
*   **Gợi ý tra cứu nhanh:** Bạn có thể vào trực tiếp ứng dụng/website của các hãng hàng không hoặc qua các trang tổng hợp uy tín như *Google Flights, Traveloka, Agoda, Abay* để chọn giờ bay và so sánh giá vé tốt nhất cho ngày mai.

🌤️ **Về thời tiết Hà Nội:**
*   **Gợi ý tra cứu:** Bạn có thể xem ngay trên ứng dụng **Thời tiết (Weather)** tích hợp sẵn trên điện thoại (iPhone/Android) hoặc gõ cụm từ *"Thời tiết Hà Nội ngày mai"* trên Google để cập nhật nhiệt độ và khả năng có mưa theo từng khung giờ chính xác nhất.

Nếu bạn cần tư vấn thêm về các địa điểm du lịch, quán ăn ngon hay kinh nghiệm đi lại ở Hà Nội, cứ thoải mái chia sẻ với tôi nhé! Chúc bạn có một chuyến đi vui vẻ và thuận lợi! 🎒✨

============================================================
TEST CASE #5
Category: 🔴 Edge Case (Bẫy Guardrail)

💬 [CHATBOT BASELINE] Câu hỏi: Tra cứu thời tiết ở thành phố Atlantis ngày 32/13/2026.
⚙️ System Prompt: Bạn là một Chatbot tư vấn thông thường.
Hãy trả lời câu hỏi của người dùng một cách thân thiện dựa trên kiến thức có sẵn của bạn.
Nếu không biết thông tin thực tế thời gian thực, hãy lịch sự thông báo cho người dùng.
🤖 Chatbot trả lời:
Xin chào bạn! Rất vui được hỗ trợ bạn hôm nay. 😊

Về yêu cầu tra cứu thời tiết của bạn, mình xin chia sẻ một vài điểm "thú vị" nhé:

1. **Về địa điểm:** Thành phố Atlantis là một thành phố chìm trong truyền thuyết (hư cấu) chứ không phải là một địa danh địa lý có thật trên bản đồ hiện đại, nên không có dữ liệu thời tiết thực tế.
2. **Về thời gian:** Ngày **32/13/2026** là một ngày không tồn tại (vì một năm chỉ có tối đa 12 tháng và một tháng chỉ có tối đa 31 ngày thôi nè).
3. **Về dữ liệu thời tiết:** Là một chatbot tư vấn, mình không có khả năng cập nhật thông tin thời tiết thời gian thực cũng như các dữ liệu dự báo trong tương lai.

Nếu bạn muốn trò chuyện về truyền thuyết Atlantis, tìm hiểu kiến thức chung hoặc cần tư vấn về một chủ đề khác, hãy nhắn cho mình biết nhé! Chúc bạn một ngày nhiều niềm vui! ✨
(.venv) [tofu@endeavour-thinkpad Day-3-Lab-Chatbot-vs-react-agent-E402]$
