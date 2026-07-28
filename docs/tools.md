Các tools sử dụng trong AI Agent:
search_theater()          # Tìm rạp CGV
search_movie()            # Tìm phim đang chiếu
search_showtime()         # Tìm suất chiếu
get_available_seats()     # Lấy danh sách ghế trống
book_seats()              # Đặt/giữ ghế
generate_ticket()         # Sinh vé điện tử


## search_theater()
Tìm rạp CGV
Mục đích:
    Tìm danh sách rạp CGV phù hợp với yêu cầu của người dùng.
Sử dụng để:
    Xác định rạp người dùng muốn xem.
    Lấy theater_id để tìm suất chiếu.
## search_movie()
Tìm phim đang chiếu / sắp chiếu
Mục đích:
    Tìm thông tin phim theo tên.
Sử dụng để:
    Kiểm tra phim có tồn tại không.
    Lấy ID phim.
    Biết trạng thái:
    Đang chiếu
    Sắp chiếu
    Đã hết suất
## search_showtime()
Tìm suất chiếu
Mục đích:
    Tìm thời gian chiếu của phim tại một rạp cụ thể.
Sử dụng để:
    Trả lời:
    "Phim Conan có suất nào?"
    hoặc:
    "Tối nay có chiếu lúc mấy giờ?"
## get_available_seats()
Lấy danh sách ghế trống
Mục đích:
    Kiểm tra những ghế nào còn có thể đặt.
## book_seats()
Đặt hoặc giữ ghế
Mục đích:
    Thực hiện hành động đặt vé.
Sử dụng để:
    Khóa ghế tránh người khác đặt.
    Tạo mã booking.
## generate_ticket()
Sinh vé điện tử
Mục đích:
    Tạo vé sau khi đặt thành công.
Sử dụng để:
    Hiển thị vé.



