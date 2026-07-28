"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool & Spec Engineer)
Nơi khai báo tất cả các "món đồ nghề" mà ReAct Agent có thể gọi.
"""


def search_home_info(location: str, rent_duration: str,  budget: float, room_info) -> str:
    """
    Tìm kiếm thông tin nhà ở phù hợp với yêu cầu của người dùng.
    """
    return f"Thông tin nhà ở phù hợp với yêu cầu của người dùng: {location}, {rent_duration}, {budget}, {room_info}"
    

def get_calendar(): 
    """
    Lấy lịch của người dùng.
    """
    return f"Lịch của người dùng: {calendar_info}"


def send_msg(destination): 
    """
    Gửi tin nhắn đến người dùng qua zalo.
    
    Args:
        msg (str): Tin nhắn cần gửi
    """
    return f"Tin nhắn đã được gửi: {msg}"

# Danh sách các tool được đăng ký để Agent sử dụng
AVAILABLE_TOOLS = {
    "search_home_info": search_home_info,
    "get_calendar": get_calendar,
    "send_msg": send_msg,
}
