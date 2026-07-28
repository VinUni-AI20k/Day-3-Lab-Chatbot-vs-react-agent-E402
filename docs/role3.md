# 🛡️ PHÂN TÍCH LỖI VÀ NGUYÊN TẮC AN TOÀN CHO TOOL (TOOL FAILURE ANALYSIS & GUARDRAILS)

> **Chủ đề**: Trợ Lý Tra Cứu Đơn Hàng & Xử Lý Đổi Trả  
> **Đảm nhận**: Role 3 - Prompt Engineer & Guardrail Analyst  
> **Tài liệu tham chiếu**: [`docs/MO_TA_TOOLS.md`](file:///Users/keeee22/ai20k_3/DAY03_2A202601117_DANGHOANGHAI/docs/MO_TA_TOOLS.md) & [`src/tools.py`](file:///Users/keeee22/ai20k_3/DAY03_2A202601117_DANGHOANGHAI/src/tools.py)

---

## 📌 1. CHI TIẾT PHÂN TÍCH LỖI CÁC CÔNG CỤ (TOOL FAILURE MODES)

### 1️⃣ `get_order_info(order_id: str)`
* **Mục đích**: Tra cứu chi tiết thông tin đơn hàng theo mã đơn (trạng thái, ngày nhận hàng, ngành hàng, điều kiện đổi trả).
* **Các lỗi có thể xảy ra (`Failure Modes`)**:
  * `EMPTY_ORDER_ID`: Mã đơn hàng rỗng hoặc chỉ chứa khoảng trắng. Trả về: `"LỖI: Mã đơn hàng không được để trống."`
  * `ORDER_NOT_FOUND`: Không tìm thấy mã đơn hàng trên hệ thống.
  * `UNAUTHORIZED`: Không có quyền truy cập thông tin đơn hàng của người dùng khác.
  * `TIMEOUT / SERVICE_UNAVAILABLE`: API hệ thống phản hồi chậm hoặc tạm thời gián đoạn.
* **Quy tắc xử lý & Khắc phục**:
  * Đã chuẩn hóa: Xóa khoảng trắng dư thừa (`.strip()`) và viết hoa (`.upper()`).
  * Phanh an toàn (`Graceful Error Handling`): Trả về chuỗi thông báo lỗi có tiền tố `"LỖI: ..."` thay vì `raise Exception`.
  * Không suy đoán (Hallucinate) thông tin đơn hàng nếu tool báo lỗi hoặc chưa gọi tool.

---

### 2️⃣ `check_return_policy(category: str, days_since_purchase: int)`
* **Mục đích**: Đánh giá điều kiện & quy định đổi trả theo ngành hàng và số ngày kể từ khi nhận hàng.
* **Các lỗi có thể xảy ra (`Failure Modes`)**:
  * `INVALID_CATEGORY`: Ngành hàng không hợp lệ hoặc không có trong danh mục hỗ trợ.
  * `INVALID_DAYS`: Số ngày kể từ khi mua âm (`days_since_purchase < 0`) hoặc sai kiểu dữ liệu.
  * `NON_RETURNABLE_CATEGORY`: Sản phẩm thuộc ngành hàng không hỗ trợ đổi trả (Thực phẩm tươi sống, đồ ăn, đông lạnh...).
  * `EXCEEDED_RETURN_PERIOD`: Số ngày quá thời hạn đổi trả cho phép (Điện tử/Gia dụng: quá 7 ngày; Thời trang/Phụ kiện: quá 14 ngày).
* **Quy tắc xử lý & Khắc phục**:
  * Validate đầu vào trước khi đối soát chính sách.
  * Kiểm tra đúng khung thời gian của từng ngành hàng:
    * **Thực phẩm / Tươi sống**: KHÔNG áp dụng đổi trả.
    * **Điện tử / Gia dụng**: Tối đa 7 ngày (yêu cầu nguyên tem, vỏ hộp).
    * **Thời trang / Phụ kiện**: Tối đa 14 ngày (yêu cầu nguyên tag mác, chưa qua sử dụng).
  * Nếu không đủ điều kiện hoặc quá thời hạn, trả về lý do từ chối rõ ràng cho người dùng.

---

### 3️⃣ `calculate_refund_amount(order_id: str, product_price: float, reason: str)`
* **Mục đích**: Tính toán chi tiết số tiền hoàn trả dự kiến dựa trên giá trị sản phẩm và lý do đổi trả.
* **Các lỗi có thể xảy ra (`Failure Modes`)**:
  * `INVALID_PRODUCT_PRICE`: Giá trị sản phẩm không hợp lệ (`product_price <= 0` hoặc sai định dạng số).
  * `MISSING_REASON`: Lý do đổi trả trống, khiến hệ thống không xác định được chi phí vận chuyển thu hồi.
  * `INVALID_ORDER_ID`: Mã đơn hàng không hợp lệ.
* **Quy tắc xử lý & Khắc phục**:
  * Quy tắc khấu trừ phí thu hồi:
    * **Lỗi từ shop/sản phẩm** (lỗi, hỏng, sai, vỡ, kém, tì vết): Miễn 100% phí thu hồi (hoàn lại 100% giá trị sản phẩm).
    * **Lỗi cá nhân/khách đổi ý**: Trừ 30,000 VNĐ phí vận chuyển thu hồi.
  * Chỉ trả về **số tiền hoàn dự kiến**, ghi rõ chi tiết khấu trừ, không cam kết số tiền hoàn cố định tuyệt đối nếu chưa qua kiểm định thực tế.

---

### 4️⃣ `create_return_request(order_id: str, items_to_return: str, reason: str, bank_account: str)`
* **Mục đích**: Khởi tạo yêu cầu đổi/trả hàng chính thức trên hệ thống, cấp mã RMA và mã vận đơn thu hồi hàng.
* **Các lỗi có thể xảy ra (`Failure Modes`)**:
  * `INVALID_ORDER_ID`: Mã đơn hàng rỗng hoặc không hợp lệ. Trả về: `"LỖI: Mã đơn hàng không hợp lệ."`
  * `MISSING_REQUIRED_PARAMS`: Thiếu sản phẩm cần trả (`items_to_return`), lý do (`reason`), hoặc tài khoản ngân hàng (`bank_account`).
  * `RETURN_NOT_ELIGIBLE`: Khởi tạo yêu cầu khi đơn hàng chưa qua bước kiểm tra điều kiện hoặc không đủ điều kiện đổi trả.
  * `DUPLICATE_RETURN_REQUEST`: Đơn hàng đã có yêu cầu RMA được khởi tạo trước đó.
* **Quy tắc xử lý & Khắc phục**:
  * Ép tuân thủ quy trình ReAct nghiêm ngặt: Chỉ được gọi `create_return_request` sau khi đã hoàn thành các bước tra cứu, kiểm tra điều kiện, tính tiền hoàn và được người dùng xác nhận.
  * Bảo mật thông tin: Không ghi log dữ liệu tài khoản ngân hàng (`bank_account`) vào hệ thống logging công khai để tránh rò rỉ PII.

---

### 5️⃣ `track_shipping_status(tracking_number: str)`
* **Mục đích**: Tra cứu hành trình vận chuyển thực tế của bưu kiện giao đi hoặc bưu kiện thu hồi đổi trả.
* **Các lỗi có thể xảy ra (`Failure Modes`)**:
  * `EMPTY_TRACKING_NUMBER`: Mã vận đơn rỗng. Trả về: `"LỖI: Mã vận đơn không được để trống."`
  * `TRACKING_NOT_FOUND`: Mã vận đơn không tồn tại trên hệ thống vận chuyển.
  * `TRACKING_DATA_DELAYED`: Dữ liệu quét mã bưu cục chưa cập nhật kịp thời.
* **Quy tắc xử lý & Khắc phục**:
  * Đã chuẩn hóa mã vận đơn (`.strip()`, `.upper()`).
  * Không suy đoán vị trí bưu kiện nếu chưa có kết quả từ tool.

---

## 🛡️ 2. NGUYÊN TẮC BẢO VỆ AN TOÀN (GUARDRAILS & FAILURE MODES)

1. **Chuẩn hóa đầu vào (`Input Normalization`)**:  
   Tất cả mã đơn hàng (`order_id`) và mã vận đơn (`tracking_number`) đều được tự động làm sạch khoảng trắng dư thừa (`.strip()`) và chuyển thành chữ hoa (`.upper()`).

2. **Phanh an toàn (`Graceful Error Handling`)**:  
   Khi tham số rỗng hoặc gặp lỗi, các hàm trong `src/tools.py` không tung ngoại lệ (`raise Exception`), mà trả về chuỗi văn bản bắt đầu với tiền tố `"LỖI: ..."` giúp Agent nhận biết qua `Observation` để điều chỉnh hành vi phù hợp trong vòng lặp ReAct.

3. **Bắt buộc Quy trình Xử lý Đổi trả (Strict Return Workflow)**:  
   Agent phải thực hiện đúng thứ tự các bước bên dưới, không được nhảy bước:

```text
Get Order (get_order_info)
    ↓
Check Policy (check_return_policy)
    ↓
Calculate Refund (calculate_refund_amount)
    ↓
User Confirmation (Người dùng đồng ý & cung cấp STK)
    ↓
Create Return Request (create_return_request)
```

4. **Chống Ảo Giác & Suy Đoán (Anti-Hallucination Guardrail)**:  
   * Agent chỉ được sử dụng dữ liệu quan sát (`Observation`) nhận về từ Tool.
   * Không tự bịa ra trạng thái đơn hàng, số tiền hoàn trả hay mã RMA khi chưa gọi Tool tương ứng.

5. **Bảo mật dữ liệu cá nhân (PII Protection)**:  
   * Tài khoản ngân hàng (`bank_account`) chỉ dùng làm tham số khởi tạo đơn đổi trả, tuyệt đối không lưu trữ trong log hệ thống hoặc hiển thị bất hợp lý.

