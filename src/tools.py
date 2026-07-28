"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool & Spec Engineer)
Nơi khai báo tất cả các "món đồ nghề" mà ReAct Agent sử dụng trong đề tài:
"Trợ Lý Khai Quật Nhân Cách Thứ 2 & Tư Vấn Tâm Lý"
"""

import json
import re
from typing import Union, List


def score_personality_profile(responses: Union[List[int], str]) -> str:
    """
    Tính điểm hồ sơ tính cách từ bộ đáp án tự đánh giá (thang điểm 1-5).
    
    Args:
        responses (Union[List[int], str]): Danh sách 10 câu trả lời tự đánh giá, ví dụ: [5, 4, 2, 4, 3, 5, 4, 2, 4, 3] hoặc chuỗi JSON "[5, 4, 2, 4, 3, 5, 4, 2, 4, 3]".
        
    Returns:
        str: Kết quả điểm số các chỉ số tính cách (openness, conscientiousness, extraversion, agreeableness, emotional_sensitivity) và giải thích xu hướng.
    """
    try:
        if isinstance(responses, str):
            try:
                parsed = json.loads(responses)
                if isinstance(parsed, list):
                    responses = parsed
            except Exception:
                numbers = re.findall(r'\d+', responses)
                responses = [int(n) for n in numbers]
        
        if not isinstance(responses, list) or len(responses) < 5:
            return "LỖI: Đầu vào phải là danh sách ít nhất 5 đến 10 điểm số tự đánh giá (thang 1-5)."

        nums = [float(x) for x in responses]

        if len(nums) == 10:
            openness = round((nums[0] + nums[5]) / 2.0, 1)
            conscientiousness = round((nums[1] + nums[6]) / 2.0, 1)
            extraversion = round((nums[2] + nums[7]) / 2.0, 1)
            agreeableness = round((nums[3] + nums[8]) / 2.0, 1)
            emotional_sensitivity = round((nums[4] + nums[9]) / 2.0, 1)
        else:
            openness = round(nums[0], 1)
            conscientiousness = round(nums[1], 1) if len(nums) > 1 else 3.0
            extraversion = round(nums[2], 1) if len(nums) > 2 else 3.0
            agreeableness = round(nums[3], 1) if len(nums) > 3 else 3.0
            emotional_sensitivity = round(nums[4], 1) if len(nums) > 4 else 3.0

        scores = {
            "openness": openness,
            "conscientiousness": conscientiousness,
            "extraversion": extraversion,
            "agreeableness": agreeableness,
            "emotional_sensitivity": emotional_sensitivity
        }

        json_str = json.dumps(scores, ensure_ascii=False)
        return (
            f"Kết quả điểm số hồ sơ tính cách: {json_str}\n"
            f"- Openness (Cởi mở): {openness}/5.0\n"
            f"- Conscientiousness (Tận tụy/Cầu toàn): {conscientiousness}/5.0\n"
            f"- Extraversion (Hướng ngoại): {extraversion}/5.0\n"
            f"- Agreeableness (Hòa đồng): {agreeableness}/5.0\n"
            f"- Emotional Sensitivity (Độ nhạy cảm cảm xúc): {emotional_sensitivity}/5.0\n"
            f"⚠️ LƯU Ý PHI LÂM SÀNG: Kết quả này chỉ mang tính tự tham khảo cá nhân, không phải là chẩn đoán y khoa hay tâm lý chính thức."
        )

    except Exception as e:
        return f"LỖI: Không thể tính điểm hồ sơ tính cách. Chi tiết: {str(e)}"


def get_wellbeing_exercise(emotional_state: str, intensity: Union[int, str] = 5) -> str:
    """
    Gợi ý bài tập hỗ trợ xoa dịu cảm xúc & thực hành tâm lý phù hợp với trạng thái và mức độ căng thẳng của người dùng.
    
    Args:
        emotional_state (str): Trạng thái cảm xúc (ví dụ: 'căng thẳng', 'lo âu', 'buồn bã', 'mệt mỏi', 'giận dữ').
        intensity (Union[int, str]): Mức độ cảm xúc trên thang điểm 1-10 (ví dụ: 7).
        
    Returns:
        str: Bài tập thực hành chi tiết (kỹ thuật thở, grounding, journaling) và lưu ý phi lâm sàng.
    """
    try:
        try:
            val_intensity = int(intensity)
        except (ValueError, TypeError):
            val_intensity = 5

        state_clean = str(emotional_state).lower()

        if "căng thẳng" in state_clean or "stress" in state_clean or "áp lực" in state_clean:
            exercise = (
                f"🧘 BÀI TẬP XOA DỊU CĂNG THẲNG (Trạng thái: '{emotional_state}', Mức độ: {val_intensity}/10):\n"
                f"1. Kỹ thuật thở nhịp nhàng 4-7-8: Hít vào bằng mũi trong 4s, giữ hơi 7s, thở ra từ từ qua miệng trong 8s. Lặp lại 5 vòng.\n"
                f"2. Phương pháp Nối đất (Grounding 5-4-3-2-1): Tìm 5 vật bạn nhìn thấy, 4 thứ bạn chạm vào được, 3 âm thanh xung quanh, 2 mùi hương và 1 vị trong miệng.\n"
                f"3. Dành 10 phút thả lỏng vai và nhắm mắt nghỉ ngơi."
            )
        elif "lo âu" in state_clean or "sợ" in state_clean or "bồn chồn" in state_clean:
            exercise = (
                f"🌿 BÀI TẬP GIẢM LO ÂU (Trạng thái: '{emotional_state}', Mức độ: {val_intensity}/10):\n"
                f"1. Kỹ thuật Thở Hộp (Box Breathing): Hít 4s - Giữ 4s - Thở 4s - Giữ 4s.\n"
                f"2. Viết nhật ký xả cảm xúc (Worry Journaling): Viết ra tất cả mối lo lên giấy, sau đó khoanh tròn những điều bạn CÓ THỂ kiểm soát."
            )
        else:
            exercise = (
                f"🌱 BÀI TẬP CÂN BẰNG TÂM TRÍ (Trạng thái: '{emotional_state}', Mức độ: {val_intensity}/10):\n"
                f"1. Quét cơ thể (Body Scan): Nhắm mắt và hướng sự chú ý lần lượt từ ngón chân lên đỉnh đầu trong 5 phút.\n"
                f"2. Ghi lại 3 điều bạn cảm thấy biết ơn trong ngày hôm nay."
            )

        return (
            f"{exercise}\n"
            f"⚠️ LƯU Ý PHI LÂM SÀNG: Bài tập mang tính chất hỗ trợ tự xoa dịu tinh thần, không thay thế cho tư vấn hoặc điều trị y khoa chuyên khoa."
        )

    except Exception as e:
        return f"LỖI: Không thể tra cứu bài tập hỗ trợ. Chi tiết: {str(e)}"


def get_psychological_archetype(trait_keywords: str) -> str:
    """
    Khai quật "Nhân cách thứ 2" (Shadow Archetype) - khía cạnh ẩn giấu trong tiềm thức của người dùng.
    
    Args:
        trait_keywords (str): Từ khóa đại diện cho nỗi sợ, ước mơ ẩn giấu hoặc thói quen đêm khuya (ví dụ: 'đêm', 'cô đơn', 'nổi loạn', 'sáng tạo', 'bảo vệ').
        
    Returns:
        str: Hồ sơ hình mẫu "Nhân cách thứ 2", bao gồm tên hình mẫu, đặc điểm tiềm thức và lời khuyên hòa giải nội tâm.
    """
    if not trait_keywords:
        return "LỖI: Chưa cung cấp từ khóa tính cách để khai quật hình mẫu."
        
    kw = str(trait_keywords).lower()
    
    if any(w in kw for w in ["nổi loạn", "tự do", "phá cách", "khác biệt"]):
        return (
            "🎭 NHÂN CÁCH THỨ 2: KẺ NỔI LOẠN ẨN MÌNH (The Hidden Rebel)\n"
            "- Đặc điểm tiềm thức: Bên ngoài bạn có thể tuân thủ quy tắc, nhưng sâu bên trong là khao khát bứt phá và khẳng định cái tôi duy nhất.\n"
            "- Điểm mạnh tiềm ẩn: Bật nhảy tư duy đột phá, không sợ đi ngược đám đông.\n"
            "- Lời khuyên hòa giải: Hãy tạo cho mình những 'khoảng không tự do' an toàn để sáng tạo mà không sợ bị phán xét.\n"
            "⚠️ Lưu ý: Thông tin mang tính tham khảo tự khám phá bản thân."
        )
    elif any(w in kw for w in ["đêm", "triết học", "suy ngẫm", "cô đơn", "sâu sắc"]):
        return (
            "🎭 NHÂN CÁCH THỨ 2: NHÀ TRIẾT HỌC ĐÊM KHUYA (The Midnight Philosopher)\n"
            "- Đặc điểm tiềm thức: Bạn thường che giấu những trăn trở sâu sắc về bản thể và cuộc đời đằng sau nụ cười thường ngày.\n"
            "- Điểm mạnh tiềm ẩn: Thấu cảm sâu sắc, khả năng quan sát và thấu hiểu bản chất vấn đề.\n"
            "- Lời khuyên hòa giải: Đừng ôm giữ mọi suy nghĩ một mình, hãy viết journaling hoặc chia sẻ với người tri kỷ.\n"
            "⚠️ Lưu ý: Thông tin mang tính tham khảo tự khám phá bản thân."
        )
    else:
        return (
            "🎭 NHÂN CÁCH THỨ 2: NGƯỜI BẢO VỆ THẦM LẶNG (The Silent Guardian)\n"
            "- Đặc điểm tiềm thức: Bạn luôn mong muốn che chở người khác nhưng đôi khi quên mất việc chăm sóc chính đứa trẻ bên trong mình.\n"
            "- Điểm mạnh tiềm ẩn: Trái tim ấm áp, đáng tin cậy và kiên cường.\n"
            "- Lời khuyên hòa giải: Học cách nói 'Không' và ưu tiên chữa lành cho bản thân trước.\n"
            "⚠️ Lưu ý: Thông tin mang tính tham khảo tự khám phá bản thân."
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
        
    t = str(topic).lower()
    
    if any(w in t for w in ["tự sát", "tự hại", "muốn chết", "khủng hoảng", "hotline", "khẩn cấp"]):
        return (
            "🆘 TÀI NGUYÊN HỖ TRỢ TÂM LÝ KHẨN CẤP:\n"
            "- Hotline Ngày Mới (Hỗ trợ tâm lý & Khủng hoảng): 0963 061 414\n"
            "- Tổng đài Quốc gia Bảo vệ Trẻ em & Tâm lý: 111\n"
            "- Viện Sức khỏe Tâm thần - Bệnh viện Bạch Mai: (024) 3576 5344\n"
            "💡 Lời nhắn: Bạn không một mình. Hãy liên hệ ngay với chuyên gia hoặc người thân đáng tin cậy để được hỗ trợ kịp thời!"
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
    }
    
    if not counselor_name or str(counselor_name).lower() in ["tất cả", "bat ky", "bất kỳ", "all"]:
        return "📅 LỊCH TRỐNG CỦA CÁC CHUYÊN GIA TƯ VẤN TRONG TUẦN:\n\n" + "\n\n".join(schedules.values())
        
    name_clean = str(counselor_name).lower()
    for key, val in schedules.items():
        if key in name_clean or name_clean in key:
            return f"📅 LỊCH TRỐNG CỦA CHUYÊN GIA:\n{val}"
            
    return f"LỖI: Không tìm thấy thông tin chuyên gia '{counselor_name}'."


# Danh sách các tool được đăng ký để ReAct Agent sử dụng
AVAILABLE_TOOLS = {
    "score_personality_profile": score_personality_profile,
    "get_wellbeing_exercise": get_wellbeing_exercise,
    "get_psychological_archetype": get_psychological_archetype,
    "search_mental_health_resources": search_mental_health_resources,
    "check_counselor_schedule": check_counselor_schedule,
}
