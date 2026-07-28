"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool Engineer)
Nơi khai báo tất cả các "món đồ nghề" mà Cupid Agent có thể gọi.
"""

def search_profiles(query: str) -> str:
    """
    Tìm kiếm danh sách các hồ sơ đối tượng phù hợp dựa trên tiêu chí hoặc sở thích.
    
    Args:
        query (str): Tiêu chí tìm kiếm (Ví dụ: 'nữ thích leo núi ở Hà Nội', 'nam thích poker')
        
    Returns:
        str: Danh sách các hồ sơ (Profiles) phù hợp kèm thông tin chi tiết
    """
    query_lower = query.lower()
    
    # Mock Data hồ sơ người dùng
    profiles_db = [
        {
            "name": "Linh (Nữ, 22 tuổi)",
            "location": "Hà Nội",
            "hobbies": ["leo núi", "poker", "đọc sách", "ai"],
            "mbti": "INTJ",
            "bio": "Thích thử thách tư duy, thích đi trekking và phân tích chiến thuật cuối tuần."
        },
        {
            "name": "Hoàng (Nam, 24 tuổi)",
            "location": "Hà Nội",
            "hobbies": ["chụp ảnh film", "cà phê", "poker", "guitar"],
            "mbti": "ENFP",
            "bio": "Hướng ngoại, đam mê nghệ thuật, thích trò chuyện sâu và đi chụp ảnh phố phường."
        },
        {
            "name": "Trang (Nữ, 23 tuổi)",
            "location": "TP.HCM",
            "hobbies": ["du lịch", "ẩm thực", "xem phim", "cà phê"],
            "mbti": "ESFP",
            "bio": "Năng động, thích khám phá các quán ăn ngon và chụp ảnh sống ảo."
        }
    ]
    
    results = []
    for p in profiles_db:
        p_text = f"{p['name']} {p['location']} {' '.join(p['hobbies'])} {p['mbti']} {p['bio']}".lower()
        if any(word in p_text for word in query_lower.split()):
            results.append(
                f"- {p['name']} | Vị trí: {p['location']} | MBTI: {p['mbti']}\n"
                f"  Sở thích: {', '.join(p['hobbies'])}\n"
                f"  Mô tả: {p['bio']}"
            )
            
    if results:
        return "KẾT QUẢ TÌM KIẾM HỒ SƠ PHÙ HỢP:\n" + "\n\n".join(results)
    else:
        # Trả về gợi ý mặc định nếu từ khóa tìm kiếm quá hẹp
        return (
            "KẾT QUẢ TÌM KIẾM HỒ SƠ:\n"
            "- Linh (Nữ, 22 tuổi) | Vị trí: Hà Nội | MBTI: INTJ | Sở thích: leo núi, poker, AI\n"
            "- Hoàng (Nam, 24 tuổi) | Vị trí: Hà Nội | MBTI: ENFP | Sở thích: chụp ảnh film, cà phê, poker"
        )


def calculate_compatibility(profile_a: str, profile_b: str) -> str:
    """
    Tính điểm % độ tương thích và phân tích điểm chung/điểm lệch giữa 2 hồ sơ.
    
    Args:
        profile_a (str): Tên hoặc thông tin của đối tượng thứ nhất
        profile_b (str): Tên hoặc thông tin của đối tượng thứ hai
        
    Returns:
        str: Báo cáo phân tích độ tương thích chi tiết (% Matching, Điểm chung, Lưu ý)
    """
    return (
        f"=== BÁO CÁO PHÂN TÍCH ĐỘ TƯƠNG THÍCH ({profile_a} & {profile_b}) ===\n"
        f"🔥 Độ tương thích tổng quan: 88%\n"
        f"✅ Điểm chung nổi bật: Cùng gu tư duy logic, thích trò chuyện sâu & có sở thích chung về Poker/Cà phê.\n"
        f"⚡ Điểm bù trừ năng lượng: Sự sâu sắc của INTJ kết hợp cùng sự cởi mở của ENFP tạo nên phản ứng hóa học rất thú vị.\n"
        f"⚠️ Cần lưu ý: Cần tôn trọng không gian riêng tư của nhau khi một trong hai người cần thời gian 'sạc lại pin'."
    )


def recommend_date_ideas(shared_hobbies: str) -> str:
    """
    Gợi ý câu mở đầu (Icebreaker) và ý tưởng địa điểm hẹn hò dựa trên sở thích chung.
    
    Args:
        shared_hobbies (str): Các sở thích chung của 2 người (Ví dụ: 'chụp ảnh film, cà phê', 'leo núi, poker')
        
    Returns:
        str: Danh sách câu Icebreaker gây ấn tượng + Gợi ý địa điểm hẹn hò phù hợp
    """
    return (
        f"💡 GỢI Ý HẸN HÒ & CÂU MỞ ĐẦU (Dựa trên sở thích: {shared_hobbies}):\n\n"
        f"💬 2 CÂU ICEBREAKER (CÂU MỞ ĐẦU AWFUL/COOL):\n"
        f'1. "Nghe nói bạn cũng mê {shared_hobbies}? Cuối tuần này có quán/buổi trải nghiệm nào xịn không, gợi ý cho mình với!"\n'
        f'2. "Nếu phải chọn giữa một buổi chiều {shared_hobbies} chill chill và một ly cà phê đậm vị, bạn sẽ chọn cái nào trước?"\n\n'
        f"📍 Ý TƯỞNG ĐỊA ĐIỂM HẸN HÒ LÝ TƯỞNG:\n"
        f"- Buổi 1: Hẹn tại một quán Cà phê không gian Vintage yên tĩnh để dễ trao đổi về sở thích chung.\n"
        f"- Buổi 2: Cùng tham gia một buổi workshop nhỏ hoặc một hoạt động trải nghiệm thực tế."
    )


# Danh sách các tool được đăng ký để Cupid Agent sử dụng
AVAILABLE_TOOLS = {
    "search_profiles": search_profiles,
    "calculate_compatibility": calculate_compatibility,
    "recommend_date_ideas": recommend_date_ideas,
}