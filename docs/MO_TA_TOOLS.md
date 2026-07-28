# 🛠️ DANH SÁCH & BẢNG MÔ TẢ CÁC CÔNG CỤ (TOOL SPECS)

> **Chủ đề**: Trợ Lý Tra Cứu Đơn Hàng & Xử Lý Đổi Trả  
> **Đảm nhận**: Role 2 - Tool & Spec Engineer  
> **File mã nguồn**: [`src/tools.py`](file:///d:/AI20K/LABS/DAY03_2A202601117_DANGHOANGHAI/src/tools.py)

---

## 📌 1. TỔNG QUAN HỆ THỐNG CÔNG CỤ (TOOLS OVERVIEW)

ReAct Agent sử dụng bộ 5 công cụ trong `src/tools.py` để thực hiện các thao tác suy luận (`Thought -> Action -> Observation`) nhằm giải quyết các yêu cầu phức tạp từ khách hàng liên quan đến tra cứu đơn hàng, đánh giá chính sách đổi trả, tính tiền hoàn và tạo đơn đổi trả.

| STT | Tên Tool (`Function Name`) | Tham số chính (`Arguments`) | Mục đích sử dụng |
| :---: | :--- | :--- | :--- |
| 1 | `get_order_info` | `order_id: str` | Tra cứu chi tiết thông tin đơn hàng theo mã đơn. |
| 2 | `check_return_policy` | `category: str, days_since_purchase: int` | Đánh giá điều kiện & quy định đổi trả theo ngành hàng và số ngày. |
| 3 | `calculate_refund_amount` | `order_id: str, product_price: float, reason: str` | Tính toán số tiền hoàn trả dự kiến sau khi trừ phí vận chuyển (nếu có). |
| 4 | `create_return_request` | `order_id: str, items_to_return: str, reason: str, bank_account: str` | Khởi tạo đơn đổi trả chính thức và cấp mã RMA / mã thu hồi. |
| 5 | `track_shipping_status` | `tracking_number: str` | Tra cứu hành trình vận chuyển kiện hàng giao đi hoặc kiện thu hồi. |

---

## 🔍 2. CHI TIẾT MÔ TẢ CÁC CÔNG CỤ (DETAILED SPECS)

### 1️⃣ `get_order_info`
* **Mô tả**: Tra cứu trạng thái, ngày nhận hàng, ngành hàng và điều kiện đổi trả của một đơn hàng.
* **Tham số**:
  * `order_id` (`str`): Mã đơn hàng cần tra cứu (VD: `'ORD-123'`, `'HD98765'`).
* **Kết quả trả về (`str`)**:
  ```text
  📦 THÔNG TIN ĐƠN HÀNG [ORD-123]:
  - Trạng thái: Đã giao hàng thành công
  - Ngày nhận hàng: 3 ngày trước
  - Ngành hàng: Thiết bị điện tử / Thời trang
  - Tình trạng đổi trả: Trong thời hạn hỗ trợ đổi trả (dưới 7 ngày)
  ```

---

### 2️⃣ `check_return_policy`
* **Mô tả**: Tra cứu điều kiện và chính sách đổi trả sản phẩm dựa vào ngành hàng và thời gian nhận hàng.
* **Tham số**:
  * `category` (`str`): Ngành hàng (`'Điện tử'`, `'Thời trang'`, `'Thực phẩm tươi sống'`,...).
  * `days_since_purchase` (`int`): Số ngày kể từ khi khách nhận được sản phẩm.
* **Quy tắc xử lý**:
  * **Thực phẩm / Tươi sống**: Không áp dụng đổi trả.
  * **Điện tử / Gia dụng**: Tối đa 7 ngày (Yêu cầu nguyên tem, vỏ hộp).
  * **Thời trang / Phụ kiện**: Tối đa 14 ngày (Yêu cầu nguyên tag mác).
* **Kết quả trả về (`str`)**:
  ```text
  ✅ ĐỦ ĐIỀU KIỆN: Ngành 'Điện tử' cho phép đổi trả trong 7 ngày. Đơn hàng (3 ngày) ĐỦ ĐIỀU KIỆN (Yêu cầu nguyên tem, vỏ hộp).
  ```

---

### 3️⃣ `calculate_refund_amount`
* **Mô tả**: Tính toán chi tiết số tiền khách hàng nhận lại sau khi cấn trừ chi phí thu hồi (nếu có).
* **Tham số**:
  * `order_id` (`str`): Mã đơn hàng.
  * `product_price` (`float`): Giá trị sản phẩm (VNĐ).
  * `reason` (`str`): Lý do đổi trả (`'Lỗi nhà sản xuất'`, `'Đổi ý không thích'`,...).
* **Quy tắc khấu trừ**:
  * **Lỗi từ phía shop/sản phẩm**: Miễn 100% phí thu hồi (Hoàn lại đúng giá trị sản phẩm).
  * **Lỗi cá nhân/khách đổi ý**: Trừ 30,000 VNĐ phí vận chuyển thu hồi.
* **Kết quả trả về (`str`)**:
  ```text
  💰 BẢNG TÍNH TIỀN HOÀN DỰ KIẾN [ORD-123]:
  - Giá trị sản phẩm: 500,000 VNĐ
  - Lý do đổi trả: Lỗi nhà sản xuất
  - Chi phí vận chuyển: Miễn phí vận chuyển thu hồi (Lỗi do nhà bán/sản phẩm).
  👉 TỔNG TIỀN HOÀN LẠI DỰ KIẾN: 500,000 VNĐ
  ```

---

### 4️⃣ `create_return_request`
* **Mô tả**: Khởi tạo yêu cầu đổi/trả hàng chính thức trên hệ thống và tạo mã vận đơn gửi hàng về kho.
* **Tham số**:
  * `order_id` (`str`): Mã đơn hàng.
  * `items_to_return` (`str`): Tên sản phẩm muốn trả.
  * `reason` (`str`): Lý do đổi trả.
  * `bank_account` (`str`): Tài khoản ngân hàng nhận lại tiền hoàn.
* **Kết quả trả về (`str`)**:
  ```text
  🎉 THÀNH CÔNG: Đã khởi tạo yêu cầu đổi trả cho đơn hàng [ORD-123]!
  - Mã Yêu Cầu (RMA): RMA-ORD-123
  - Sản phẩm trả: Tai nghe Bluetooth Sony
  - Lý do: Lỗi kết nối âm thanh
  - Tài khoản nhận hoàn tiền: MBBank - 0987654321 - NGUYEN VAN A
  - Mã vận đơn thu hồi hàng: RET-GHN-ORD-123
  📌 Hướng dẫn: Đóng gói sản phẩm, dán mã RMA-ORD-123 bên ngoài kiện hàng. Shipper sẽ liên hệ lấy hàng trong 24h.
  ```

---

### 5️⃣ `track_shipping_status`
* **Mô tả**: Tra cứu trạng thái vận chuyển bưu kiện thực tế theo mã vận đơn.
* **Tham số**:
  * `tracking_number` (`str`): Mã vận đơn giao hàng hoặc mã vận đơn thu hồi (`'GHN987654'`, `'RET-GHN-ORD-123'`).
* **Kết quả trả về (`str`)**:
  ```text
  🚚 HÀNH TRÌNH VẬN CHUYỂN [GHN987654]:
  - Trạng thái: Đang trong tiến trình luân chuyển bưu kiện.
  - Cập nhật mới nhất: Bưu kiện đã rời Kho tổng Tân Bình, đang chuyển sang Bưu cục Giao nhận.
  ```

---

## 🛡️ 3. NGUYÊN TẮC CHỊU LỖI & PHANH AN TOÀN (FAILURE MODES)

1. **Chuẩn hóa đầu vào (`Input Normalization`)**: Tất cả mã đơn hàng, mã vận đơn đều được tự động xóa khoảng trắng dư thừa (`.strip()`) và viết hoa (`.upper()`).
2. **Không crash mã nguồn (`Graceful Error Handling`)**: Khi tham số rỗng hoặc gặp lỗi bất ngờ, các hàm luôn trả về chuỗi văn bản chứa tiền tố `"LỖI: ..."` chứ không `raise Exception`, giúp Agent nhận biết thất bại qua `Observation` và đưa ra hướng xử lý phù hợp.
3. **Phù hợp ReAct Loop**: Mọi hàm đều có Docstring định dạng chuẩn với mô tả rõ ràng mục đích, tham số (`Args`) và kết quả trả về (`Returns`) để LLM hiểu và tự động trích xuất tham số chính xác.
