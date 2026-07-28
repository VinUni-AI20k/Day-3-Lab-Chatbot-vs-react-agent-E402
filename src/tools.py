"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool & Spec Engineer)
Nơi khai báo tất cả các "món đồ nghề" mà ReAct Agent sử dụng trong đề tài:
"Trợ Lý Khai Quật Nhân Cách Thứ 2 & Tư Vấn Tâm Lý"
"""

def analyze_personality_traits(user_answers: str) -> str:
    """
    Phân tích các đặc trưng tính cách nổi bật và xu hướng cảm xúc dựa trên câu trả lời hoặc mô tả của người dùng.
    
    Args:
        user_answers (str): Đoạn văn bản mô tả suy nghĩ, thói quen, cách ứng xử hoặc câu trả lời bài test của người dùng.
        
    Returns:
        str: Kết quả phân tích các nét tính cách chủ đạo, độ nhạy cảm và xu hướng ứng xử.
    """
    if not user_answers or len(user_answers.strip()) < 5:
        return "LỖI: Mô tả quá ngắn hoặc trống. Vui lòng cung cấp thêm thông tin về suy nghĩ hoặc phản ứng của bạn."
    
    text = user_answers.lower()
    traits = []
    
    if any(w in text for w in ["im lặng", "một mình", "nội tâm", "ít nói", "khép kín"]):
        traits.append("Hướng nội sâu sắc (Introverted) - Thường tích tụ năng lượng khi ở một mình.")
    if any(w in text for w in ["lo lắng", "sợ", "áp lực", "căng thẳng", "stress", "mệt mỏi"]):
        traits.append("Độ nhạy cảm cảm xúc cao (Highly Sensitive) - Dễ bị ảnh hưởng bởi môi trường xung quanh.")
    if any(w in text for w in ["hoàn hảo", "kỹ tính", "tiêu chuẩn", "đúng giờ", "nghiêm túc"]):
        traits.append("Xu hướng cầu toàn (Perfectionist) - Đặt kỳ vọng cao vào bản thân và công việc.")
    if any(w in text for w in ["tự do", "nổi loạn", "khác biệt", "sáng tạo", "phá cách"]):
        traits.append("Tâm hồn tự do & Sáng tạo (Creative Rebel) - Ghét sự gò bó, thích tìm đường đi riêng.")

    if not traits:
        traits.append("Tính cách cân bằng, linh hoạt - Khả năng thích nghi tốt trong nhiều hoàn cảnh.")

    result = "📊 PHÂN TÍCH TÍNH CÁCH CHỦ ĐẠO:\n" + "\n".join(f"- {t}" for t in traits)
    return result


def get_psychological_archetype(trait_keywords: str) -> str:
    """
    Khai quật "Nhân cách thứ 2" (Shadow Archetype) - khía cạnh ẩn giấu trong tiềm thức của người dùng.
    
    Args:
        trait_keywords (str): Từ khóa hoặc chủ đề đại diện cho nỗi sợ, ước mơ ẩn giấu hoặc thói quen đêm khuya (ví dụ: 'đêm', 'cô đơn', 'nổi loạn', 'sáng tạo', 'bảo vệ').
        
    Returns:
        str: Hồ sơ hình mẫu "Nhân cách thứ 2", bao gồm tên hình mẫu, đặc điểm tiềm thức và lời khuyên hòa giải nội tâm.
    """
    if not trait_keywords:
        return "LỖI: Chưa cung cấp từ khóa tính cách để khai quật hình mẫu."
        
    kw = trait_keywords.lower()
    
    if any(w in kw for w in ["nổi loạn", "tự do", "phá cách", "khác biệt"]):
        return (
            "🎭 NHÂN CÁCH THỨ 2: KẺ NỔI LOẠN ẨN MÌNH (The Hidden Rebel)\n"
            "- Đặc điểm tiềm thức: Bên ngoài bạn có thể tuân thủ quy tắc, nhưng sâu bên trong là khao khát bứt phá và khẳng định cái tôi duy nhất.\n"
            "- Điểm mạnh tiềm ẩn: Bật nhảy tư duy đột phá, không sợ đi ngược đám đông.\n"
            "- Lời khuyên hòa giải: Hãy tạo cho mình những 'khoảng không tự do' an toàn để sáng tạo mà không sợ bị phán xét."
        )
    elif any(w in kw for w in ["đêm", "triết học", "suy ngẫm", "cô đơn", "sâu sắc"]):
        return (
            "🎭 NHÂN CÁCH THỨ 2: NHÀ TRIẾT HỌC ĐÊM KHUYA (The Midnight Philosopher)\n"
            "- Đặc điểm tiềm thức: Bạn thường che giấu những trăn trở sâu sắc về bản thể và cuộc đời đằng sau nụ cười thường ngày.\n"
            "- Điểm mạnh tiềm ẩn: Thấu cảm sâu sắc, khả năng quan sát và thấu hiểu bản chất vấn đề.\n"
            "- Lời khuyên hòa giải: Đừng ôm giữ mọi suy nghĩ một mình, hãy viết journaling hoặc chia sẻ với người tri kỷ."
        )
    elif any(w in kw for w in ["bảo vệ", "hy sinh", "gánh vác", "lắng nghe", "chăm sóc"]):
        return (
            "🎭 NHÂN CÁCH THỨ 2: NGƯỜI BẢO VỆ THẦM LẶNG (The Silent Guardian)\n"
            "- Đặc điểm tiềm thức: Bạn luôn mong muốn che chở người khác nhưng đôi khi quên mất việc chăm sóc chính đứa trẻ bên trong mình.\n"
            "- Điểm mạnh tiềm ẩn: Trái tim ấm áp, đáng tin cậy và kiên cường.\n"
            "- Lời khuyên hòa giải: Học cách nói 'Không' và ưu tiên chữa lành cho bản thân trước."
        )
    else:
        return (
            "🎭 NHÂN CÁCH THỨ 2: KẺ TÌM KIẾM ẨN MÌNH (The Mystic Seeker)\n"
            "- Đặc điểm tiềm thức: Bạn đang trong hành trình khám phá những khía cạnh mới chưa từng bộc lộ của bản thân.\n"
            "- Điểm mạnh tiềm ẩn: Tò mò, sẵn sàng mở lòng với những trải nghiệm tâm lý mới.\n"
            "- Lời khuyên hòa giải: Hãy tiếp tục lắng nghe tín hiệu từ cảm xúc hàng ngày để hiểu rõ mình hơn."
        )


def search_mental_health_resources(topic: str) -> str:
    """
    Tra cứu tài nguyên tư vấn tâm lý, kỹ thuật tự chữa lành (Mindfulness, CBT), hoặc hotline hỗ trợ khẩn cấp.
    
    Args:
        topic (str): Chủ đề cần tư vấn hoặc tình trạng tâm lý (ví dụ: 'stress', 'lo âu', 'trầm cảm', 'mất ngủ', 'khủng hoảng', 'hotline').
        
    Returns:
        str: Danh sách tài liệu, kỹ thuật thực hành hoặc thông tin liên hệ hỗ trợ khẩn cấp.
    """
    if not topic:
        return "LỖI: Vui lòng nhập chủ đề cần tra cứu tài nguyên tư vấn."
        
    t = topic.lower()
    
    # Kiểm tra tín hiệu khủng hoảng khẩn cấp (Safeguard / Crisis Guardrail)
    if any(w in t for w in ["tự sát", "tự hại", "muốn chết", "khủng hoảng", "hotline", "khẩn cấp"]):
        return (
            "🆘 TÀI NGUYÊN HỖ TRỢ TÂM LÝ KHẨN CẤP:\n"
            "- Hotline Ngày Mới (Hỗ trợ tâm lý & Khủng hoảng): 0963 061 414\n"
            "- Tổng đài Quốc gia Bảo vệ Trẻ em & Tâm lý: 111\n"
            "- Viện Sức khỏe Tâm thần - Bệnh viện Bạch Mai: (024) 3576 5344\n"
            "💡 Lời nhắn: Bạn không một mình. Hãy liên hệ ngay với chuyên gia hoặc người thân đáng tin cậy để được hỗ trợ kịp thời!"
        )
    elif any(w in t for w in ["stress", "căng thẳng", "áp lực", "lo âu"]):
        return (
            "🧘 BÀI TẬP VÀ KỸ THUẬT XOA DỊU STRESS & LO ÂU:\n"
            "1. Kỹ thuật thở 4-7-8: Hít vào 4s -> Giữ thở 7s -> Thở ra từ từ qua miệng 8s (Lặp lại 4 lần).\n"
            "2. Phương pháp Nối đất 5-4-3-2-1: Nhìn 5 vật xung quanh, Chạm 4 thứ, Nghe 3 âm thanh, Ngửi 2 mùi, Nếm 1 vị.\n"
            "3. Sách khuyên đọc: 'Hiểu Về Trái Tim' (Thích Nhất Hạnh), 'Được Mới Mất' (Pema Chödrön)."
        )
    elif any(w in t for w in ["mất ngủ", "khó ngủ", "đêm"]):
        return (
            "🌙 KỸ THUẬT VỆ SINH GIẤC NGỦ (SLEEP HYGIENE):\n"
            "1. Tắt toàn bộ thiết bị điện tử trước khi ngủ 30 phút.\n"
            "2. Thực hành phương pháp Quét cơ thể (Body Scan Meditation) từ ngón chân lên đỉnh đầu.\n"
            "3. Nghe nhạc tần số 432Hz hoặc tiếng mưa rơi tự nhiên."
        )
    else:
        return (
            f"📚 TÀI NGUYÊN TƯ VẤN TÂM LÝ CHỦ ĐỀ '{topic}':\n"
            "- Kỹ thuật Viết tự do (Journaling): Dành 10 phút mỗi ngày viết ra mọi cảm xúc mà không phán xét.\n"
            "- Nguyên lý CBT (Liệu pháp Nhận thức Hành vi): Nhận diện suy nghĩ tiêu cực -> Thách thức tính thực tế -> Thay bằng suy nghĩ cân bằng.\n"
            "- Khuyên dùng: Tham vấn chuyên gia tâm lý nếu tình trạng kéo dài trên 2 tuần."
        )


def check_counselor_schedule(counselor_name: str) -> str:
    """
    Tra cứu lịch làm việc trống của chuyên gia tư vấn tâm lý để hỗ trợ đặt lịch hẹn.
    
    Args:
        counselor_name (str): Tên chuyên gia tư vấn hoặc từ khóa 'tất cả' / 'bất kỳ'.
        
    Returns:
        str: Thông tin các ca tư vấn còn trống trong tuần.
    """
    schedules = {
        "nguyễn văn a": "TS. Nguyễn Văn A (Chuyên gia Trị liệu Tâm lý Nhận thức):\n- Thứ 4: 09:00 - 11:00\n- Thứ 6: 14:00 - 16:00",
        "lê thị b": "Chuyên gia Lê Thị B (Tư vấn Hôn nhân & Mối quan hệ):\n- Thứ 3: 10:00 - 12:00\n- Thứ 7: 15:00 - 17:00",
        "trần văn c": "ThS. Trần Văn C (Tư vấn Khủng hoảng Người trẻ & Định hướng):\n- Thứ 2: 13:30 - 15:30\n- Chủ Nhật: 08:30 - 10:30",
    }
    
    if not counselor_name or counselor_name.lower() in ["tất cả", "bat ky", "bất kỳ", "all"]:
        return "📅 LỊCH TRỐNG CỦA CÁC CHUYÊN GIA TƯ VẤN TRONG TUẦN:\n\n" + "\n\n".join(schedules.values())
        
    name_clean = counselor_name.lower()
    for key, val in schedules.items():
        if key in name_clean or name_clean in key:
            return f"📅 LỊCH TRỐNG CỦA CHUYÊN GIA:\n{val}"
            
    return (
        f"LỖI: Không tìm thấy thông tin chuyên gia '{counselor_name}'.\n"
        f"💡 Gợi ý chuyên gia hiện có: TS. Nguyễn Văn A, Chuyên gia Lê Thị B, ThS. Trần Văn C."
    )


# Danh sách các tool được đăng ký để ReAct Agent sử dụng
AVAILABLE_TOOLS = {
    "analyze_personality_traits": analyze_personality_traits,
    "get_psychological_archetype": get_psychological_archetype,
    "search_mental_health_resources": search_mental_health_resources,
    "check_counselor_schedule": check_counselor_schedule,
}
