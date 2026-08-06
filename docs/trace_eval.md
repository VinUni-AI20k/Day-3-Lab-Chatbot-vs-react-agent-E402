BÁO CÁO ĐÁNH GIÁ AGENT
Dự án: Text-to-SQL ReAct Agent (Goodreads Books)

1. ĐÁNH GIÁ MỨC ĐỘ PHÙ HỢP CỦA AGENT (AGENTIC FIT)

Chúng tôi đánh giá mức độ phù hợp của bài toán Text-to-SQL trên cơ sở dữ liệu
Goodreads đối với kiến trúc ReAct Agent:

| Tiêu chí                                        | Điểm (1-5) | Lý do đánh giá chi tiết                                                                                                                                                                                                                                |
| :---------------------------------------------- | :--------: | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Suy luận đa bước** | **5/5**    | Người dùng thường đặt các câu hỏi mơ hồ (ví dụ: "sách hay", "tương tự Harry Potter"). Agent bắt buộc phải suy luận nhiều bước: Tra cứu schema $\rightarrow$ Thử nghiệm câu truy vấn SQL $\rightarrow$ Đọc kết quả $\rightarrow$ Định dạng câu trả lời. |
| **Tương tác công cụ**   | **5/5**    | Agent cần tương tác trực tiếp với cơ sở dữ liệu thông qua các công cụ thực thi SQL động. LLM không thể tự lưu trữ hoặc đoán dữ liệu của hàng nghìn đầu sách.                                                                                           |
| **Quyết định động**      | **4/5**    | Kết quả từ các bước truy vấn trước (ví dụ: phát hiện lỗi sai tên cột ở Test \#7) bắt buộc Agent phải thay đổi chiến thuật truy vấn ở bước tiếp theo.                                                                                                   |
| **Quy trình dài hạn**        | **3/5**    | Tác vụ tương đối ngắn hạn, thường xoay quanh 3-6 bước suy luận (Iterations) cho mỗi câu hỏi từ phía người dùng.                                                                                                                                        |
| **TỔNG ĐIỂM FIT**                               | **17/20**  | **KẾT LUẬN: BÀI TOÁN RẤT PHÙ HỢP ĐỂ TRIỂN KHAI REACT AGENT\!**                                                                                                                                                                                         |

2. PHÂN TÍCH LOG THỰC TẾ (TEST CASE #1)

Yêu cầu người dùng (Query): "Database sách này có bao nhiêu cuốn và cấu trúc
bảng ra sao?"

  - Kỳ vọng: Agent gọi `describe_table('books')` để xem schema và trả
    lời tổng quan.
  - Thực tế hệ thống chạy:
      - Thought: Nhận diện đúng cần gọi describe_table.
      - Hành động: Gọi describe_table[books].
      - Observation: Hệ thống trả về lỗi kết nối cơ sở dữ liệu describe failed:
        unable to open database file.
      - Xử lý lỗi: Thay vì dừng lại hoặc báo lỗi thân thiện, Agent tự sinh ra
        các bước giả lập (ảo tưởng công cụ list_tables và tự bịa ra dữ liệu phản
        hồi) để đưa ra câu trả lời cuối cùng chứa các ký tự giữ chỗ đại diện:
        "Bảng books có ... dòng và cấu trúc như sau: ..."

3. PHÂN TÍCH CÁC LỖI HỆ THỐNG

Qua phân tích log chạy thực tế từ hệ thống, chúng tôi phát hiện 4 vấn đề kỹ
thuật nghiêm trọng cần được khắc phục:

**Lỗi 1: Lỗi kết nối cơ sở dữ liệu SQLite (`unable to open database file`)**

  - **Dấu hiệu**: Xuất hiện ở hầu hết các test case khi gọi `describe_table` hoặc `execute_select_query`.
  - **Nguyên nhân**: Đường dẫn tương đối đến file `books.db` trong `src/tools.py` hoặc `src/app.py` đang bị sai lệch so với thư mục làm việc hiện tại của terminal.

**Lỗi 2: Hiện tượng ảo tưởng công cụ (Tool Hallucination)**

  - **Dấu hiệu**: Agent tự gọi các tool không tồn tại như `validate_sql`, `get_table_sample`, `search_schema`.
  - **Nguyên nhân**: Prompt hệ thống chưa đủ chặt chẽ để giới hạn LLM chỉ được dùng các tool đã khai báo. Khi gặp lỗi (ví dụ lỗi kết nối DB), LLM tự "sáng tạo" ra tool để giải quyết.

**Lỗi 3: Lỗi phân tích cú pháp (Parser Leak) & Tự giả lập môi trường**

  - **Dấu hiệu**: LLM tự sinh ra cả phần `Observation:` và `Thought:` tiếp theo trong cùng một lượt trả lời. Bộ phân tích (parser) trong `app.py` không xử lý được, dẫn đến lỗi.
  - **Nguyên nhân**: Thiếu `stop token` khi gọi API, khiến LLM không biết khi nào cần dừng lại.

**Lỗi 4: Giới hạn tần suất gọi API (Groq Rate Limit Exceeded - 429)**

  - **Dấu hiệu**: API trả về lỗi `429 - Rate limit reached`.
  - **Nguyên nhân**: Agent thực hiện nhiều vòng lặp suy luận liên tục trong thời gian ngắn, vượt ngưỡng giới hạn TPM/RPM của tài khoản miễn phí.

4. PHƯƠNG ÁN KHẮC PHỤC VÀ NÂNG CẤP

Để nâng cao tính ổn định của Agent, chúng tôi đề xuất các giải pháp kỹ thuật sau:

**1. Sửa lỗi kết nối Database**

Trong `src/tools.py`, chuyển từ đường dẫn tương đối sang đường dẫn tuyệt đối dựa trên vị trí của file mã nguồn.

import os
import sqlite3

# Xác định đường dẫn tuyệt đối đến file DB nằm cùng cấp hoặc trong thư mục dự án
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "books.db")  # Đường dẫn đúng tới file DB

def get_db_connection():
    # Sử dụng URI mode hoặc kiểm tra sự tồn tại của file trước khi kết nối
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Không tìm thấy file database tại: {DB_PATH}")
    # Kết nối ở chế độ read-only để tăng cường bảo mật
    return sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)

**2. Chặn ảo tưởng công cụ trong Prompt**

Cập nhật prompt hệ thống trong `src/prompts.py` để ra lệnh nghiêm ngặt cho LLM:

BẠN CHỈ ĐƯỢC PHÉP SỬ DỤNG CÁC CÔNG CỤ SAU:
1. describe_table
2. execute_select_query
 
NGHIÊM CẤM tự ý tạo ra các công cụ mới (ví dụ: list_tables, get_table_sample, validate_sql) hoặc tự đóng giả vai trò của hệ thống bằng cách viết phần 'Observation:'. 
Nếu các công cụ được cung cấp báo lỗi, bạn phải sử dụng thông tin lỗi đó trong phần 'Thought' tiếp theo để sửa đổi câu truy vấn, hoặc đưa ra 'Final Answer' thông báo lỗi cho người dùng.

**3. Cải tiến Parser và cài đặt Stop Words**

Trong `src/app.py`, khi gửi yêu cầu đến API, hãy thiết lập tham số `stop` để mô hình dừng sinh văn bản ngay khi gặp từ khóa của hệ thống (ví dụ: `Observation:`).

# Ví dụ cấu hình stop words khi gọi API
completion = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=...,
    stop=["Observation:", "OBSERVATION:"], # Ngăn chặn LLM tự viết kết quả của Tool
    temperature=0.0 # Giảm nhiệt độ xuống 0 để Agent suy luận chính xác, không sáng tạo tùy tiện
)

**4. Tích hợp cơ chế chờ để chống lỗi 429 (Rate Limit Backoff)**

Thêm một khoảng trễ nhỏ (ví dụ: `time.sleep(2)`) giữa các test case trong `src/app.py` để tránh làm quá tải API.

import time

# Trong vòng lặp chạy các Test Cases
for test in test_cases:
    # ... thực thi test case ...
    time.sleep(3.0)  # Nghỉ 3 giây giữa các Test Cases để hồi phục giới hạn TPM
