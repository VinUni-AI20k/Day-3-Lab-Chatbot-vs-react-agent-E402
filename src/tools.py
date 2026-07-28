"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool & Spec Engineer)
Nơi định nghĩa các công cụ (Tools) phục vụ cho Cupid Agent - Trợ lý ghép đôi & tư vấn hẹn hò.
"""

import json

# Giả lập cơ sở dữ liệu người dùng (Profile Database)
USER_DATABASE = {
    "anh": {
        "name": "Anh",
        "gender": "Nam",
        "birth_year": 1999,
        "zodiac": "Sư Tử",
        "hobbies": ["đá bóng", "nghe nhạc", "cafe"]
    },
    "mai": {
        "name": "Mai",
        "gender": "Nữ",
        "birth_year": 2001,
        "zodiac": "Nhân Mã",
        "hobbies": ["nấu ăn", "nghe nhạc", "đọc sách"]
    },
    "linh": {
        "name": "Linh",
        "gender": "Nữ",
        "birth_year": 1998,
        "zodiac": "Kim Ngưu",
        "hobbies": ["đi phượt", "xem phim", "nhiếp ảnh"]
    },
    "vy": {
        "name": "Vy",
        "gender": "Nữ",
        "birth_year": 2000,
        "zodiac": "Song Tử",
        "hobbies": ["mua sắm", "xem phim", "ăn uống"]
    }
}

# Danh sách nguyên tố của 12 cung hoàng đạo dùng để tính toán độ tương thích
ZODIAC_ELEMENTS = {
    "bạch dương": "Lửa", "sư tử": "Lửa", "nhân mã": "Lửa",
    "kim ngưu": "Đất", "xử nữ": "Đất", "ma kết": "Đất",
    "song tử": "Khí", "thiên bình": "Khí", "bảo bình": "Khí",
    "cự giải": "Nước", "thiên yết": "Nước", "song ngư": "Nước"
}

# Giả lập danh mục địa điểm hẹn hò dựa trên sở thích
DATING_SPOTS_CATALOG = {
    "nghe nhạc": [
        "Phòng trà Acoustic Trịnh Ca - Thưởng thức nhạc Trịnh mộc mạc.",
        "Bình Minh Jazz Club - Không gian lãng mạn, nhạc Jazz sống động."
    ],
    "xem phim": [
        "Rạp chiếu phim giường nằm L'amour CGV - Riêng tư và sang trọng.",
        "Rạp chiếu phim ngoài trời trên tầng thượng (Skyline Cinema)."
    ],
    "đi phượt": [
        "Camping tại Đồng Cao hoặc Hàm Lợn - Gần gũi thiên nhiên, cùng dựng lều cắm trại.",
        "Chuyến đi phượt ngắn ngày bằng xe máy lên Ba Vì ngắm hoa dã quỳ."
    ],
    "nấu ăn": [
        "Lớp học làm bánh ngọt hoặc làm gốm cùng nhau tại Bát Tràng.",
        "Workshop nấu ăn món Ý tự làm tại gia."
    ],
    "cafe": [
        "Cư Xá Cà Phê - Không gian hoài cổ, yên tĩnh thích hợp trò chuyện.",
        "Top of Hanoi - Quán cafe rooftop ngắm toàn cảnh thành phố lung linh."
    ],
    "đá bóng": [
        "Cùng nhau đi xem một trận bóng đá trực tiếp tại sân vận động Hàng Đẫy.",
        "Quán cafe thể thao náo nhiệt xem trận đấu lớn."
    ]
}

# Giả lập lịch trình bận rộn để kiểm tra xung đột thời gian hẹn hò
BUSY_SCHEDULES = [
    "tối thứ bảy", "tối thứ 7", "19:00 thứ bảy", "20:00 thứ bảy",
    "chiều chủ nhật", "15:00 chủ nhật", "sáng thứ hai", "sáng thứ 2"
]

# Danh sách câu thả thính theo sở thích
PICKUP_LINES = {
    "nghe nhạc": [
        "Gu âm nhạc của em thật đỉnh, nhưng gu chọn người yêu của em còn đỉnh hơn nếu có anh!",
        "Anh không giỏi chơi nhạc cụ, nhưng anh giỏi nhịp đập trái tim cùng em."
    ],
    "xem phim": [
        "Em thích xem phim bom tấn à? Anh không phải diễn viên nhưng cuộc đời anh sẽ là bộ phim hay nhất nếu có em làm nữ chính.",
        "Xem phim ma thì sợ, xem phim tình cảm thì sến, thôi thì quay sang xem anh này!"
    ],
    "đi phượt": [
        "Em thích đi phượt xa xôi, còn anh chỉ muốn đi phượt vào sâu trong tim em.",
        "Đồng hành đi phượt cần bản đồ, còn hành trình đi tìm hạnh phúc của anh chỉ cần em dẫn lối."
    ],
    "nấu ăn": [
        "Món ăn em nấu có thể hơi mặn hoặc hơi nhạt, nhưng tình yêu anh dành cho em thì lúc nào cũng vừa vặn ngọt ngào.",
        "Anh không biết nấu ăn ngon, nhưng anh hứa sẽ làm người rửa bát chăm chỉ nhất đời em."
    ],
    "cafe": [
        "Cà phê phin phải đợi từng giọt, còn anh thì sẵn sàng chờ đợi cái gật đầu của em suốt cả đời.",
        "Em thích cafe sữa hay bạc xỉu? Anh thì thích 'bạc đầu' cùng em cơ."
    ],
    "đá bóng": [
        "Em có muốn làm trọng tài không? Để mỗi lần anh phạm lỗi, em lại phạt anh bằng một nụ hôn.",
        "Anh có thể sút hụt bóng trên sân cỏ, nhưng chưa bao giờ sút trượt tình yêu của em."
    ]
}

def get_user_profile(name: str) -> str:
    """
    Tra cứu thông tin hồ sơ chi tiết của một người dùng trong hệ thống.
    
    Args:
        name (str): Tên của người cần tra cứu (ví dụ: 'Anh', 'Mai', 'Linh', 'Vy')
        
    Returns:
        str: Chuỗi JSON chứa thông tin hồ sơ (nếu thành công) hoặc chuỗi thông báo lỗi (bắt đầu bằng LỖI:).
    """
    try:
        # Kiểm tra kiểu dữ liệu đầu vào chống crash
        if not isinstance(name, str):
            return f"LỖI: Tham số 'name' truyền vào phải là chuỗi văn bản (string), nhận được kiểu {type(name).__name__}."
            
        if not name.strip():
            return "LỖI: Tên người dùng không được để trống."
            
        key = name.strip().lower()
        if key in USER_DATABASE:
            return json.dumps(USER_DATABASE[key], ensure_ascii=False)
            
        return f"LỖI: Không tìm thấy hồ sơ của người dùng '{name}' trong hệ thống."
    except Exception as e:
        return f"LỖI: Đã xảy ra lỗi hệ thống khi xử lý get_user_profile: {str(e)}."


def check_zodiac_compatibility(sign1: str, sign2: str) -> str:
    """
    Kiểm tra mức độ tương hợp giữa hai cung hoàng đạo.
    
    Args:
        sign1 (str): Tên cung hoàng đạo thứ nhất (ví dụ: 'Sư Tử', 'Kim Ngưu')
        sign2 (str): Tên cung hoàng đạo thứ hai (ví dụ: 'Nhân Mã', 'Song Tử')
        
    Returns:
        str: Chuỗi JSON chứa điểm số tương thích (%), nhận xét và các thông tin nguyên tố liên quan.
    """
    try:
        # Kiểm tra kiểu dữ liệu đầu vào chống crash
        if not isinstance(sign1, str) or not isinstance(sign2, str):
            t1 = type(sign1).__name__
            t2 = type(sign2).__name__
            return f"LỖI: Tham số cung hoàng đạo phải là chuỗi văn bản (string). Nhận được: sign1={t1}, sign2={t2}."
            
        if not sign1.strip() or not sign2.strip():
            return "LỖI: Cung hoàng đạo không được để trống."
            
        s1 = sign1.strip().lower()
        s2 = sign2.strip().lower()
        
        if s1 not in ZODIAC_ELEMENTS or s2 not in ZODIAC_ELEMENTS:
            invalid = []
            if s1 not in ZODIAC_ELEMENTS:
                invalid.append(sign1)
            if s2 not in ZODIAC_ELEMENTS:
                invalid.append(sign2)
            return f"LỖI: Cung hoàng đạo không tồn tại hoặc sai chính tả: {', '.join(invalid)}."
            
        # Các cặp đôi đặc biệt được chấm điểm chi tiết
        special_pairs = {
            ("sư tử", "nhân mã"): (95, "Cặp đôi hoàn hảo! Cả hai thuộc nguyên tố Lửa, cùng tần số năng động, đam mê và thấu hiểu nhau."),
            ("sư tử", "song tử"): (85, "Cực kỳ ăn ý. Song Tử linh hoạt kết hợp với Sư Tử quyết đoán tạo nên mối quan hệ đầy tiếng cười."),
            ("kim ngưu", "nhân mã"): (45, "Khó hòa hợp. Kim Ngưu cần sự an toàn ổn định, trong khi Nhân Mã thích phiêu lưu và tự do."),
            ("kim ngưu", "song tử"): (50, "Cần nhiều nỗ lực. Sự thay đổi nhanh chóng của Song Tử dễ khiến Kim Ngưu cảm thấy bất an.")
        }
        
        pair = (s1, s2)
        rev_pair = (s2, s1)
        
        if pair in special_pairs:
            score, comment = special_pairs[pair]
        elif rev_pair in special_pairs:
            score, comment = special_pairs[rev_pair]
        else:
            e1 = ZODIAC_ELEMENTS[s1]
            e2 = ZODIAC_ELEMENTS[s2]
            
            if e1 == e2:
                score = 90
                comment = f"Cùng thuộc nhóm nguyên tố {e1}. Sự thấu hiểu cao, chia sẻ chung nhiều giá trị sống."
            elif (e1 == "Lửa" and e2 == "Khí") or (e1 == "Khí" and e2 == "Lửa"):
                score = 80
                comment = "Lửa gặp Gió. Đôi bên kích thích tư duy, truyền cảm hứng và giúp nhau cùng tiến bộ."
            elif (e1 == "Đất" and e2 == "Nước") or (e1 == "Nước" and e2 == "Đất"):
                score = 80
                comment = "Nước tưới mát đất. Mối quan hệ nuôi dưỡng, bình yên và mang tính xây dựng lâu bền."
            else:
                score = 60
                comment = "Tương thích trung bình. Cần thấu hiểu và tôn trọng sự khác biệt của đối phương để hòa hợp."
                
        result = {
            "compatibility_score": f"{score}%",
            "comment": comment,
            "sign1_element": ZODIAC_ELEMENTS[s1],
            "sign2_element": ZODIAC_ELEMENTS[s2]
        }
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return f"LỖI: Đã xảy ra lỗi hệ thống khi xử lý check_zodiac_compatibility: {str(e)}."


def suggest_dating_spots(*hobbies_args) -> str:
    """
    Gợi ý các địa điểm hẹn hò lý tưởng dựa trên danh sách sở thích chung của hai người.
    
    Args:
        *hobbies_args: Các sở thích (ví dụ: 'nghe nhạc, xem phim' hoặc 'nghe nhạc', 'xem phim')
        
    Returns:
        str: Chuỗi văn bản chứa danh sách các địa điểm hẹn hò gợi ý cụ thể.
    """
    try:
        if len(hobbies_args) == 1:
            hobbies_list_str = hobbies_args[0]
        else:
            hobbies_list_str = hobbies_args
            
        # Nếu Agent truyền vào list thay vì string, tự động gộp thành chuỗi chống crash
        if isinstance(hobbies_list_str, (list, tuple)):
            hobbies_list_str = ", ".join([str(item) for item in hobbies_list_str])
            
        if not isinstance(hobbies_list_str, str):
            return f"LỖI: Tham số 'hobbies_list_str' phải là chuỗi văn bản (string), nhận được kiểu {type(hobbies_list_str).__name__}."
            
        if not hobbies_list_str.strip():
            return "Gợi ý chung: Một buổi tối cùng đi dạo Hồ Gươm và trò chuyện nhẹ nhàng."
            
        hobbies = [h.strip().lower() for h in hobbies_list_str.split(",") if h.strip()]
        suggestions = []
        
        for hobby in hobbies:
            for catalog_hobby, spots in DATING_SPOTS_CATALOG.items():
                if catalog_hobby in hobby or hobby in catalog_hobby:
                    suggestions.extend(spots)
                    break
                    
        suggestions = list(set(suggestions))
        
        if not suggestions:
            return "Gợi ý chung: Một buổi hẹn tại quán cà phê ấm cúng ven hồ hoặc cùng đi dạo phố cổ."
            
        response_text = "Các địa điểm đề xuất cho buổi hẹn hò dựa trên sở thích chung:\n"
        for i, spot in enumerate(suggestions[:3], 1):
            response_text += f"{i}. {spot}\n"
            
        return response_text.strip()
    except Exception as e:
        return f"LỖI: Đã xảy ra lỗi hệ thống khi xử lý suggest_dating_spots: {str(e)}."


def calculate_love_fortune(name1: str, name2: str) -> str:
    """
    Tính toán quẻ bói tình duyên (thần số học vui vẻ) hôm nay giữa hai người dựa trên tên của họ.
    
    Args:
        name1 (str): Tên người thứ nhất.
        name2 (str): Tên người thứ hai.
        
    Returns:
        str: Điểm số vận mệnh hôm nay và lời khuyên hẹn hò hài hước.
    """
    try:
        if not isinstance(name1, str) or not isinstance(name2, str):
            t1 = type(name1).__name__
            t2 = type(name2).__name__
            return f"LỖI: Tên của cả hai người phải là chuỗi văn bản (string). Nhận được: name1={t1}, name2={t2}."
            
        if not name1.strip() or not name2.strip():
            return "LỖI: Tên của cả hai người không được để trống."
            
        n1 = name1.strip()
        n2 = name2.strip()
        
        # Tạo điểm số giả lập deterministic dựa trên tổng số ký tự trong tên để luôn ra cùng kết quả
        total_len = len(n1) + len(n2)
        score = (total_len * 7) % 41 + 60  # Điểm dao động từ 60% đến 100%
        
        advice_list = [
            "Hôm nay là thời điểm vàng để chủ động nhắn tin! Tỷ lệ phản hồi cực kỳ cao.",
            "Tránh nói về người yêu cũ hoặc vấn đề tài chính trong ngày hôm nay nhé.",
            "Một món quà nhỏ bất ngờ (như ly trà sữa) sẽ khiến đối phương rung động mạnh.",
            "Cơ hội hẹn hò ngoài trời rất tốt. Hãy rủ đối phương đi dạo ngay tối nay.",
            "Sự im lặng ấm áp đôi khi tốt hơn ngàn lời nói. Hãy lắng nghe đối phương nhiều hơn."
        ]
        
        selected_advice = advice_list[total_len % len(advice_list)]
        
        fortune_result = {
            "daily_love_score": f"{score}/100",
            "fortune_comment": f"Quẻ bói tình duyên hôm nay cho {n1} & {n2}: {selected_advice}"
        }
        return json.dumps(fortune_result, ensure_ascii=False)
    except Exception as e:
        return f"LỖI: Đã xảy ra lỗi hệ thống khi xử lý calculate_love_fortune: {str(e)}."


def generate_pickup_line(hobby: str) -> str:
    """
    Tạo một câu thả thính (pickup line) siêu ngọt ngào hoặc hài hước dựa trên sở thích của đối phương.
    
    Args:
        hobby (str): Sở thích cụ thể để tạo câu thả thính (ví dụ: 'nghe nhạc', 'xem phim', 'đi phượt', 'nấu ăn')
        
    Returns:
        str: Câu thả thính được cá nhân hóa tương ứng với sở thích đó.
    """
    try:
        if not isinstance(hobby, str):
            return f"LỖI: Sở thích 'hobby' truyền vào phải là chuỗi văn bản (string), nhận được kiểu {type(hobby).__name__}."
            
        if not hobby.strip():
            return "LỖI: Sở thích không được để trống."
            
        h_lower = hobby.strip().lower()
        
        # Tìm kiếm sở thích khớp trong danh mục thả thính
        matched_key = None
        for key in PICKUP_LINES.keys():
            if key in h_lower or h_lower in key:
                matched_key = key
                break
                
        if matched_key:
            lines = PICKUP_LINES[matched_key]
            # Sử dụng deterministic selection dựa trên độ dài chuỗi để chạy test ổn định
            selected_line = lines[len(h_lower) % len(lines)]
            return f"Câu thả thính gợi ý cho sở thích '{hobby}': \"{selected_line}\""
            
        return f"Câu thả thính gợi ý: \"Anh/Em có tin vào tình yêu sét đánh không, hay để anh/em đi qua lại lần nữa nhé?\""
    except Exception as e:
        return f"LỖI: Đã xảy ra lỗi hệ thống khi xử lý generate_pickup_line: {str(e)}."


def check_dating_schedule_conflict(date_time_str: str) -> str:
    """
    Kiểm tra xem thời gian đề xuất hẹn hò có bị trùng lặp với lịch trình bận rộn giả lập nào không.
    
    Args:
        date_time_str (str): Thời gian hẹn hò dự kiến (ví dụ: 'Tối thứ bảy', 'Chiều chủ nhật')
        
    Returns:
        str: Kết quả kiểm tra lịch hẹn trống hay bị trùng lịch (xung đột).
    """
    try:
        if not isinstance(date_time_str, str):
            return f"LỖI: Thời gian 'date_time_str' phải là chuỗi văn bản (string), nhận được kiểu {type(date_time_str).__name__}."
            
        if not date_time_str.strip():
            return "LỖI: Thời gian hẹn hò dự kiến không được để trống."
            
        dt_lower = date_time_str.strip().lower()
        
        for busy_time in BUSY_SCHEDULES:
            if busy_time in dt_lower or dt_lower in busy_time:
                return f"XUNG ĐỘT: Thời gian '{date_time_str}' bị trùng lịch bận ({busy_time}). Vui lòng chọn thời gian khác!"
                
        return f"LỊCH TRỐNG: Thời gian '{date_time_str}' hoàn toàn trống lịch. Có thể tiến hành lên lịch hẹn hò!"
    except Exception as e:
        return f"LỖI: Đã xảy ra lỗi hệ thống khi xử lý check_dating_schedule_conflict: {str(e)}."


# Đăng ký danh sách công cụ hoạt động với Agent
AVAILABLE_TOOLS = {
    "get_user_profile": get_user_profile,
    "check_zodiac_compatibility": check_zodiac_compatibility,
    "suggest_dating_spots": suggest_dating_spots,
    "calculate_love_fortune": calculate_love_fortune,
    "generate_pickup_line": generate_pickup_line,
    "check_dating_schedule_conflict": check_dating_schedule_conflict
}
