"""
🛠️ TOOL REGISTRY & SCHEMAS - CUPID AGENT (Dành cho Role 2: Tool Engineer)
Khai báo các công cụ tra cứu hoàng đạo, MBTI và địa điểm hẹn hò cho Cupid Agent.
"""

def check_horoscope_compatibility(sign1: str, sign2: str) -> str:
    """
    Tra cứu độ tương thích tình yêu giữa 2 cung hoàng đạo.
    
    Args:
        sign1 (str): Cung hoàng đạo thứ 1 (Ví dụ: 'Cự Giải', 'Bọ Cạp', 'Bạch Dương')
        sign2 (str): Cung hoàng đạo thứ 2 (Ví dụ: 'Bọ Cạp', 'Song Ngư', 'Kim Ngưu')
        
    Returns:
        str: Kết quả phân tích độ hợp và chỉ số % tương thích
    """
    s1, s2 = sign1.lower().strip(), sign2.lower().strip()
    
    # Danh sách 12 cung hợp lệ
    valid_signs = ["bạch dương", "kim ngưu", "song tử", "cự giải", "sư tử", "xử nữ", 
                   "thiên bình", "bọ cạp", "thần nông", "nhân mã", "ma kết", "bảo bình", "song ngư"]
    
    if not any(v in s1 for v in valid_signs) or not any(v in s2 for v in valid_signs):
        return f"LỖI: Cung hoàng đạo '{sign1}' hoặc '{sign2}' không hợp lệ. Vui lòng nhập 1 trong 12 cung hoàng đạo chuẩn."
        
    if ("cự giải" in s1 and "bọ cạp" in s2) or ("bọ cạp" in s1 and "cự giải" in s2):
        return "💘 Độ tương thích Cự Giải & Bọ Cạp: 95% (Cùng hệ Thủy - Cặp đôi trời sinh, thấu hiểu và gắn kết sâu sắc!)."
    elif ("kim ngưu" in s1 and "xử nữ" in s2) or ("xử nữ" in s1 and "kim ngưu" in s2):
        return "💘 Độ tương thích Kim Ngưu & Xử Nữ: 90% (Cùng hệ Đất - Cặp đôi bền vững, thực tế và tin tưởng lẫn nhau)."
    else:
        return f"💘 Độ tương thích giữa {sign1} và {sign2}: 80% (Cặp đôi tiềm năng, cần học cách lắng nghe và chia sẻ)."


def calculate_mbti_compatibility(mbti1: str, mbti2: str) -> str:
    """
    Phân tích chỉ số tương thích giữa 2 nhóm tính cách MBTI.
    
    Args:
        mbti1 (str): Nhóm MBTI thứ 1 (Ví dụ: 'INTJ', 'ENFP')
        mbti2 (str): Nhóm MBTI thứ 2 (Ví dụ: 'ENFP', 'INFJ')
        
    Returns:
        str: Điểm tương thích MBTI và đánh giá phong cách giao tiếp
    """
    m1, m2 = mbti1.upper().strip(), mbti2.upper().strip()
    
    if (m1 == "INTJ" and m2 == "ENFP") or (m1 == "ENFP" and m2 == "INTJ"):
        return "🧩 Tương thích MBTI INTJ & ENFP: 92% (Âm dương hút nhau: INTJ logic, điềm tĩnh bù trừ hoàn hảo cho ENFP sáng tạo, năng động!)."
    else:
        return f"🧩 Tương thích MBTI {m1} & {m2}: 85% (Hai tính cách hòa hợp tốt, dễ tạo dựng tiếng nói chung trong tình cảm)."


def search_date_ideas(location: str, vibe: str, budget: str = "vừa phải") -> str:
    """
    Gợi ý địa điểm và ý tưởng hẹn hò theo khu vực, không khí (vibe) và ngân sách.
    
    Args:
        location (str): Thành phố/Khu vực (Ví dụ: 'Hà Nội', 'TP.HCM')
        vibe (str): Phong cách buổi hẹn (Ví dụ: 'lãng mạn', 'sôi động', 'nhẹ nhàng', 'nghệ thuật')
        budget (str): Ngân sách ('tiết kiệm', 'vừa phải', 'sang trọng')
        
    Returns:
        str: Gợi ý 2 địa điểm và kịch bản buổi hẹn
    """
    loc_lower = location.lower()
    if "hà nội" in loc_lower:
        return (
            f"📍 Gợi ý hẹn hò tại Hà Nội (Vibe: {vibe}, Ngân sách: {budget}):\n"
            f"1. Cà phê xem phim/ngắm hoàng hôn Hồ Tây (Trill Rooftop / TAYTA Cafe) - Không gian lãng mạn, ấm cúng.\n"
            f"2. Đi dạo phố cổ & thưởng thức ẩm thực đêm Phố Phùng Hưng - Vừa đi dạo vừa trò chuyện thoải mái."
        )
    elif "hồ chí minh" in loc_lower or "tp.hcm" in loc_lower or "hcm" in loc_lower:
        return (
            f"📍 Gợi ý hẹn hò tại TP.HCM (Vibe: {vibe}, Ngân sách: {budget}):\n"
            f"1. Ngắm sài gòn từ Waterbus Bến Bạch Đằng ➔ Ăn tối tại Thảo Điền.\n"
            f"2. Quán Workshop làm đồ gốm/vẽ tranh cặp đôi tại Quận 1."
        )
    else:
        return f"📍 Gợi ý hẹn hò tại {location}: Ghé quán cà phê acoustics lãng mạn kết hợp dạo phố vào ban đêm."


# Danh sách các tool đăng ký cho Agent
AVAILABLE_TOOLS = {
    "check_horoscope_compatibility": check_horoscope_compatibility,
    "calculate_mbti_compatibility": calculate_mbti_compatibility,
    "search_date_ideas": search_date_ideas,
}
