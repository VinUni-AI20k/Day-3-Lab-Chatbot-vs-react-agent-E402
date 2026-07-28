"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool & Spec Engineer)
Nơi khai báo tất cả các "món đồ nghề" mà ReAct Agent có thể gọi.
"""


from typing import Dict, List


def search_home_info(location: str, rent_duration: str, budget: float, room_info: str) -> str:
    """
    Tìm danh sách bài đăng cho thuê phù hợp với nhu cầu người dùng.

    Args:
        location (str): Khu vực muốn thuê (ví dụ: "Q7, TP.HCM").
        rent_duration (str): Thời gian thuê dự kiến (ví dụ: "6 tháng").
        budget (float): Ngân sách tối đa mỗi tháng (VND).
        room_info (str): Nhu cầu số phòng/loại phòng.

    Returns:
        str: Danh sách gợi ý gồm nguồn đăng, liên hệ và giá.
    """
    try:
        mock_posts: List[Dict[str, str]] = [
            {
                "title": "Studio full nội thất gần ĐH Tôn Đức Thắng",
                "source": "Facebook Group: Phòng trọ Quận 7",
                "price": "6.5 triệu/tháng",
                "contact_name": "Nguyễn Minh",
                "phone": "0909123456",
                "profile": "facebook.com/minh.nguyen.rent",
            },
            {
                "title": "Căn hộ 1PN Sunrise Cityview",
                "source": "Batdongsan",
                "price": "9.8 triệu/tháng",
                "contact_name": "Trần Thu Hà",
                "phone": "0911222333",
                "profile": "batdongsan.vn/ha-tran",
            },
        ]

        summary_lines = [
            (
                f"- {item['title']} | {item['price']} | Nguồn: {item['source']} | "
                f"Liên hệ: {item['contact_name']} ({item['phone']}) | Profile: {item['profile']}"
            )
            for item in mock_posts
        ]
        return (
            "Kết quả tìm kiếm theo yêu cầu "
            f"(location={location}, rent_duration={rent_duration}, budget={budget}, room_info={room_info}):\n"
            + "\n".join(summary_lines)
        )
    except Exception as e:
        return f"Lỗi khi tìm kiếm nhà: {str(e)}"


def get_calendar() -> str:
    """
    Lấy các khung giờ rảnh của người dùng để đề xuất lịch đi xem nhà.

    Returns:
        str: Các mốc giờ khả dụng trong 7 ngày tới.
    """
    try:
        return (
            "Lịch rảnh gợi ý: "
            "Thứ 4 (19:00-20:30), Thứ 6 (18:30-20:00), Chủ nhật (09:00-11:00)."
        )
    except Exception as e:
        return f"Lỗi khi lấy lịch rảnh: {str(e)}"


def send_msg(destination: str, msg: str) -> str:
    """
    Gửi tin nhắn qua Zalo (mô phỏng).
    Hàm này cũng được dùng để nhắn chủ nhà kiểm tra availability.

    Args:
        destination (str): Người nhận. Ví dụ: số điện thoại chủ nhà hoặc "user_zalo".
        msg (str): Nội dung tin nhắn cần gửi.

    Returns:
        str: Trạng thái gửi và phản hồi mô phỏng.
    """
    try:
        if "còn phòng" in msg.lower():
            if destination.endswith("56"):
                return (
                    f"Đã gửi Zalo tới {destination}: '{msg}'. "
                    "Phản hồi: Còn phòng, có thể dọn vào từ tuần sau."
                )
            return (
                f"Đã gửi Zalo tới {destination}: '{msg}'. "
                "Phản hồi: Hiện đã hết phòng, có thể liên hệ lại đầu tháng sau."
            )
        return f"Đã gửi Zalo tới {destination}: {msg}"
    except Exception as e:
        return f"Lỗi khi gửi tin nhắn: {str(e)}"

# Danh sách các tool được đăng ký để Agent sử dụng
AVAILABLE_TOOLS = {
    "search_home_info": search_home_info,
    "get_calendar": get_calendar,
    "send_msg": send_msg,
}
