# Tool Failure Analysis

## 1. `get_order_info(order_id)`

**Mục đích:** Tra cứu thông tin đơn hàng.

### Có thể xảy ra lỗi

* `ORDER_NOT_FOUND`: Không tìm thấy đơn hàng.
* `UNAUTHORIZED`: Không có quyền truy cập.
* `DATA_NOT_SYNCED`: Dữ liệu chưa đồng bộ.
* `TIMEOUT`: API phản hồi quá chậm.
* `SERVICE_UNAVAILABLE`: Hệ thống không khả dụng.

**Xử lý**

* Kiểm tra định dạng `order_id`.
* Retry khi timeout.
* Không suy đoán trạng thái đơn hàng nếu tool lỗi.

---

## 2. `check_return_policy(category, days_since_purchase)`

**Mục đích:** Kiểm tra điều kiện đổi trả.

### Có thể xảy ra lỗi

* `INVALID_CATEGORY`
* `INVALID_DAYS`
* `POLICY_NOT_FOUND`
* `POLICY_VERSION_MISMATCH`

**Xử lý**

* Validate đầu vào.
* Nếu không tìm thấy chính sách thì chuyển cho nhân viên hỗ trợ.

---

## 3. `calculate_refund_amount(order_id, items_to_return, reason)`

**Mục đích:** Tính số tiền hoàn dự kiến.

### Có thể xảy ra lỗi

* `ITEM_NOT_IN_ORDER`
* `ITEM_ALREADY_REFUNDED`
* `INVALID_RETURN_REASON`
* `PROMOTION_CALCULATION_FAILED`

**Xử lý**

* Chỉ trả về **số tiền hoàn dự kiến**.
* Không cam kết số tiền hoàn cuối cùng.

---

## 4. `create_return_request(...)`

**Mục đích:** Tạo yêu cầu đổi/trả hàng.

### Có thể xảy ra lỗi

* `RETURN_NOT_ELIGIBLE`
* `DUPLICATE_RETURN_REQUEST`
* `INVALID_BANK_ACCOUNT`
* `RMA_CREATION_FAILED`

**Xử lý**

Chỉ tạo yêu cầu khi đã:

1. Tra cứu đơn hàng.
2. Kiểm tra điều kiện đổi trả.
3. Tính hoàn tiền.
4. Người dùng xác nhận.

Không lưu thông tin tài khoản ngân hàng trong log.

---

## 5. `track_shipping_status(tracking_number)`

**Mục đích:** Theo dõi trạng thái vận chuyển.

### Có thể xảy ra lỗi

* `TRACKING_NOT_FOUND`
* `NO_SCAN_EVENT_YET`
* `TRACKING_DATA_DELAYED`
* `CARRIER_NOT_SUPPORTED`

**Xử lý**

* Retry nếu timeout.
* Không suy đoán vị trí kiện hàng.

---

# Common Errors

* Input không hợp lệ.
* API timeout hoặc service unavailable.
* Gọi tool sai thứ tự.
* Hallucination (LLM tự trả lời khi chưa gọi tool).
* Rò rỉ dữ liệu nhạy cảm (PII).

## Guardrails

* Validate input trước khi gọi tool.
* Chỉ sử dụng dữ liệu từ tool.
* Retry tối đa 2 lần khi timeout.
* Mask thông tin nhạy cảm trong log.
* Bắt buộc workflow:

```
Get Order
    ↓
Check Policy
    ↓
Calculate Refund
    ↓
User Confirmation
    ↓
Create Return Request
```
