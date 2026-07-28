"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool & Spec Engineer)
Nơi khai báo tất cả các "món đồ nghề" mà ReAct Agent có thể gọi.
"""

# ==============================================================================
# 📦 CƠ SỞ DỮ LIỆU QUÀ TẶNG (GIFT_DATABASE - 20 Mục)
# ==============================================================================
GIFT_DATABASE = [
    {
        "id": 1,
        "name": "Giày chạy bộ Nike Pegasus / Adidas Ultraboost",
        "category": "Thời trang / Thể thao",
        "gender": ["nam", "nữ", "tất cả"],
        "character": ["năng động", "trẻ trung", "khỏe khoắn"],
        "favor": ["thể thao", "chạy bộ", "tập gym"],
        "color": ["đen", "trắng", "xanh", "đỏ"],
        "intimacy": ["bạn bè", "người yêu", "thân thiết"],
        "event": ["sinh nhật", "kỷ niệm", "giáng sinh"],
        "price": "2,500,000 VNĐ"
    },
    {
        "id": 2,
        "name": "Bình giữ nhiệt Lock&Lock 800ml inox 304",
        "category": "Gia dụng / Tiện ích",
        "gender": ["nam", "nữ", "tất cả"],
        "character": ["thực tế", "năng động", "chu đáo"],
        "favor": ["thể thao", "du lịch", "đi học", "đi làm"],
        "color": ["đen", "xanh", "xám", "bạc"],
        "intimacy": ["bạn bè", "đồng nghiệp"],
        "event": ["sinh nhật", "giáng sinh", "kỷ niệm"],
        "price": "450,000 VNĐ"
    },
    {
        "id": 3,
        "name": "Máy đọc sách Kindle Paperwhite 5",
        "category": "Công nghệ / Tri thức",
        "gender": ["nam", "nữ", "tất cả"],
        "character": ["trầm tính", "lịch sự", "tinh tế"],
        "favor": ["đọc sách", "học tập", "công nghệ"],
        "color": ["đen", "xanh"],
        "intimacy": ["người yêu", "bạn bè", "thân thiết"],
        "event": ["sinh nhật", "tốt nghiệp", "kỷ niệm"],
        "price": "3,200,000 VNĐ"
    },
    {
        "id": 4,
        "name": "Ví da bò cao cấp Pedro / Lethnic",
        "category": "Thời trang / Phụ kiện",
        "gender": ["nam"],
        "character": ["lịch sự", "trưởng thành", "tinh tế"],
        "favor": ["thời trang", "công sở"],
        "color": ["đen", "nâu"],
        "intimacy": ["người yêu", "bạn bè", "đồng nghiệp"],
        "event": ["sinh nhật", "kỷ niệm", "thăng chức"],
        "price": "850,000 VNĐ"
    },
    {
        "id": 5,
        "name": "Son môi Dior Addict Lip Glow",
        "category": "Mỹ phẩm / Làm đẹp",
        "gender": ["nữ"],
        "character": ["bánh bèo", "điệu đà", "trẻ trung", "tinh tế"],
        "favor": ["làm đẹp", "thời trang", "mỹ phẩm"],
        "color": ["hồng", "đỏ", "cam"],
        "intimacy": ["người yêu", "bạn bè"],
        "event": ["sinh nhật", "kỷ niệm", "8/3", "20/10", "valentin"],
        "price": "980,000 VNĐ"
    },
    {
        "id": 6,
        "name": "Nến thơm tinh dầu Agaya / Yankee Candle",
        "category": "Decor / Thư giãn",
        "gender": ["nữ", "nam", "tất cả"],
        "character": ["lãng mạn", "tinh tế", "thư thái", "bánh bèo"],
        "favor": ["decor", "thư giãn", "âm nhạc", "đọc sách"],
        "color": ["trắng", "hồng", "vàng"],
        "intimacy": ["bạn bè", "người yêu", "đồng nghiệp"],
        "event": ["sinh nhật", "tân gia", "giáng sinh", "kỷ niệm"],
        "price": "350,000 VNĐ"
    },
    {
        "id": 7,
        "name": "Đồng hồ đeo tay Casio / Seiko Minimalist",
        "category": "Phụ kiện thời trang",
        "gender": ["nam", "nữ", "tất cả"],
        "character": ["lịch sự", "đúng giờ", "trưởng thành"],
        "favor": ["thời trang", "công nghệ"],
        "color": ["đen", "bạc", "vàng"],
        "intimacy": ["người yêu", "thân thiết"],
        "event": ["sinh nhật", "tốt nghiệp", "kỷ niệm"],
        "price": "1,800,000 VNĐ"
    },
    {
        "id": 8,
        "name": "Tai nghe Bluetooth chống ồn Sony WH-1000XM5",
        "category": "Công nghệ / Âm nhạc",
        "gender": ["nam", "nữ", "tất cả"],
        "character": ["hiện đại", "năng động", "công nghệ"],
        "favor": ["nghe nhạc", "công nghệ", "xem phim", "thể thao"],
        "color": ["đen", "bạc", "xanh"],
        "intimacy": ["người yêu", "thân thiết"],
        "event": ["sinh nhật", "kỷ niệm", "tốt nghiệp"],
        "price": "6,500,000 VNĐ"
    },
    {
        "id": 9,
        "name": "Bộ cọ trang điểm Real Techniques 5 món",
        "category": "Mỹ phẩm / Làm đẹp",
        "gender": ["nữ"],
        "character": ["bánh bèo", "điệu đà", "chu đáo"],
        "favor": ["làm đẹp", "trang điểm", "thời trang"],
        "color": ["hồng", "vàng", "tím"],
        "intimacy": ["bạn bè", "người yêu"],
        "event": ["sinh nhật", "8/3", "20/10"],
        "price": "550,000 VNĐ"
    },
    {
        "id": 10,
        "name": "Mô hình Lego Architecture / Speed Champions",
        "category": "Giải trí / Đồ chơi sáng tạo",
        "gender": ["nam", "nữ", "tất cả"],
        "character": ["sáng tạo", "kiên nhẫn", "trẻ trung", "năng động"],
        "favor": ["lego", "mô hình", "game", "sáng tạo"],
        "color": ["đen", "đỏ", "vàng", "trắng"],
        "intimacy": ["bạn bè", "người yêu"],
        "event": ["sinh nhật", "giáng sinh", "kỷ niệm"],
        "price": "1,200,000 VNĐ"
    },
    {
        "id": 11,
        "name": "Bút ký cao cấp Parker đính kim loại",
        "category": "Văn phòng phẩm cao cấp",
        "gender": ["nam", "nữ", "tất cả"],
        "character": ["lịch sự", "trưởng thành", "công sở"],
        "favor": ["đọc sách", "viết lách", "công việc"],
        "color": ["đen", "vàng", "bạc"],
        "intimacy": ["đồng nghiệp", "sếp", "bạn bè"],
        "event": ["thăng chức", "tốt nghiệp", "sinh nhật"],
        "price": "600,000 VNĐ"
    },
    {
        "id": 12,
        "name": "Áo khoác Blazer / Cardigan thời trang",
        "category": "Thời trang",
        "gender": ["nam", "nữ", "tất cả"],
        "character": ["lịch sự", "thời trang", "nhã nhặn"],
        "favor": ["thời trang", "chụp ảnh"],
        "color": ["đen", "trắng", "xám", "kem"],
        "intimacy": ["người yêu", "thân thiết"],
        "event": ["sinh nhật", "kỷ niệm"],
        "price": "1,100,000 VNĐ"
    },
    {
        "id": 13,
        "name": "Loa Bluetooth Divoom Retro / Marshall Emberton",
        "category": "Công nghệ / Decor",
        "gender": ["nam", "nữ", "tất cả"],
        "character": ["chill", "nghệ sĩ", "trẻ trung", "năng động"],
        "favor": ["nghe nhạc", "decor", "du lịch"],
        "color": ["đen", "kem", "xanh"],
        "intimacy": ["bạn bè", "người yêu"],
        "event": ["sinh nhật", "tân gia", "giáng sinh"],
        "price": "2,800,000 VNĐ"
    },
    {
        "id": 14,
        "name": "Bộ ấm trà gốm sứ Bát Tràng tráng men cao cấp",
        "category": "Gia dụng / Decor",
        "gender": ["nam", "nữ", "tất cả"],
        "character": ["trầm tính", "truyền thống", "tinh tế"],
        "favor": ["thưởng trà", "decor"],
        "color": ["trắng", "xanh", "nâu"],
        "intimacy": ["đồng nghiệp", "người thân", "sếp"],
        "event": ["tân gia", "tết", "đám cưới"],
        "price": "750,000 VNĐ"
    },
    {
        "id": 15,
        "name": "Chậu cây cảnh để bàn phong thủy (Kim Tiền / Ngũ Gia Bì)",
        "category": "Cây cảnh / Phong thủy",
        "gender": ["nam", "nữ", "tất cả"],
        "character": ["yêu thiên nhiên", "thực tế", "lịch sự"],
        "favor": ["trồng cây", "decor", "thiên nhiên"],
        "color": ["xanh", "trắng"],
        "intimacy": ["đồng nghiệp", "bạn bè"],
        "event": ["tân gia", "thăng chức", "sinh nhật"],
        "price": "200,000 VNĐ"
    },
    {
        "id": 16,
        "name": "Bộ dụng cụ pha cà phê Pour-over V60 / French Press",
        "category": "Đồ uống / Tiện ích",
        "gender": ["nam", "nữ", "tất cả"],
        "character": ["tinh tế", "chill", "sáng tạo"],
        "favor": ["cà phê", "thưởng thức"],
        "color": ["đen", "bạc", "trắng"],
        "intimacy": ["bạn bè", "đồng nghiệp"],
        "event": ["sinh nhật", "giáng sinh"],
        "price": "650,000 VNĐ"
    },
    {
        "id": 17,
        "name": "Vòng tay / Dây chuyền bạc Pandora",
        "category": "Trang sức",
        "gender": ["nữ"],
        "character": ["bánh bèo", "lãng mạn", "tinh tế", "điệu đà"],
        "favor": ["thời trang", "trang sức", "làm đẹp"],
        "color": ["bạc", "hồng", "trắng"],
        "intimacy": ["người yêu", "thân thiết"],
        "event": ["kỷ niệm", "sinh nhật", "8/3", "valentin"],
        "price": "1,500,000 VNĐ"
    },
    {
        "id": 18,
        "name": "Bàn phím cơ không dây NuPhy / Keychron",
        "category": "Công nghệ / Văn phòng",
        "gender": ["nam", "nữ", "tất cả"],
        "character": ["công nghệ", "hiện đại", "năng động"],
        "favor": ["công nghệ", "game", "lập trình", "viết lách"],
        "color": ["xám", "trắng", "đen"],
        "intimacy": ["bạn bè", "người yêu"],
        "event": ["sinh nhật", "tốt nghiệp"],
        "price": "2,200,000 VNĐ"
    },
    {
        "id": 19,
        "name": "Balo du lịch chống nước đa năng Mark Ryden",
        "category": "Phụ kiện / Du lịch",
        "gender": ["nam", "nữ", "tất cả"],
        "character": ["năng động", "thực tế", "khỏe khoắn"],
        "favor": ["du lịch", "thể thao", "dã ngoại"],
        "color": ["đen", "xám"],
        "intimacy": ["bạn bè", "đồng nghiệp"],
        "event": ["sinh nhật", "tốt nghiệp"],
        "price": "700,000 VNĐ"
    },
    {
        "id": 20,
        "name": "Nước hoa Bleu de Chanel / Miss Dior 50ml",
        "category": "Mỹ phẩm / Sang trọng",
        "gender": ["nam", "nữ", "tất cả"],
        "character": ["lịch sự", "quyến rũ", "sang trọng", "tinh tế"],
        "favor": ["thời trang", "làm đẹp", "nước hoa"],
        "color": ["xanh", "hồng", "đen"],
        "intimacy": ["người yêu", "thân thiết"],
        "event": ["kỷ niệm", "sinh nhật", "valentin", "đám cưới"],
        "price": "3,100,000 VNĐ"
    }
]

# ==============================================================================
# 🎁 BỘ 3 HÀM TƯ VẤN QUÀ TẶNG (check_infor, ask_infor, recommend_gift)
# ==============================================================================

def check_infor(
    gender: str = "",
    character: str = "",
    favor: str = "",
    color: str = "",
    intimacy: str = "",
    event: str = ""
) -> tuple[bool, list[str]]:
    """
    Kiểm tra các thông tin đầu vào xem đã đầy đủ 6 thông tin quan trọng chưa.
    
    Returns:
        tuple[bool, list[str]]: (Trạng thái đủ/thiếu, Danh sách tên các trường còn thiếu)
    """
    missing_fields = []
    fields = {
        "giới tính": gender,
        "tính cách": character,
        "sở thích": favor,
        "màu sắc": color,
        "độ thân thiết": intimacy,
        "sự kiện": event,
    }
    for field_name, value in fields.items():
        if not value or not str(value).strip():
            missing_fields.append(field_name)
            
    is_sufficient = (len(missing_fields) == 0)
    return is_sufficient, missing_fields


def ask_infor(
    check_result: tuple[bool, list[str]] = None,
    gender: str = "",
    character: str = "",
    favor: str = "",
    color: str = "",
    intimacy: str = "",
    event: str = ""
) -> str:
    """
    Hỏi bổ sung thông tin nếu người dùng chưa nhập đủ.
    Đầu ra của check_infor (check_result) có thể được truyền trực tiếp làm đầu vào cho hàm này.
    """
    if check_result is None:
        check_result = check_infor(
            gender=gender,
            character=character,
            favor=favor,
            color=color,
            intimacy=intimacy,
            event=event
        )
        
    is_sufficient, missing = check_result
    
    if not is_sufficient:
        missing_str = ", ".join(missing)
        return (
            f"⚠️ THÔNG TIN CHƯA ĐỦ: Hệ thống còn thiếu các thông tin sau để chọn quà: [{missing_str}].\n"
            f"🤖 Vui lòng hỏi người dùng để bổ sung các thông tin này trước khi thực hiện gợi ý!"
        )
    return "✅ Đã nhận đủ tất cả 6 thông tin cần thiết."


def recommend_gift(
    gender: str = "",
    character: str = "",
    favor: str = "",
    color: str = "",
    intimacy: str = "",
    event: str = ""
) -> str:
    """
    Gợi ý món quà phù hợp nhất bằng cách:
    1. Gọi check_infor để kiểm tra đầu vào.
    2. Nếu chưa đủ thông tin, truyền kết quả check_infor vào ask_infor để phản hồi hỏi thông tin.
    3. Nếu đã đủ thông tin, tìm kiếm và chấm điểm các món quà khớp nhất từ GIFT_DATABASE (20 món).
    """
    # 1. Kiểm tra thông tin đầu vào
    check_res = check_infor(
        gender=gender,
        character=character,
        favor=favor,
        color=color,
        intimacy=intimacy,
        event=event
    )
    is_sufficient, _ = check_res
    
    # 2. Nếu thiếu thông tin -> Dùng ask_infor để hỏi
    if not is_sufficient:
        return ask_infor(check_result=check_res)
        
    # 3. Đã đủ thông tin -> Truy vấn và chấm điểm từ DATABASE
    g_req = gender.lower().strip()
    c_req = character.lower().strip()
    f_req = favor.lower().strip()
    col_req = color.lower().strip()
    i_req = intimacy.lower().strip()
    e_req = event.lower().strip()
    
    scored_gifts = []
    for gift in GIFT_DATABASE:
        score = 0
        
        if any(g_req in g for g in gift["gender"]) or "tất cả" in gift["gender"]:
            score += 2
        if any(c in c_req or c_req in c for c in gift["character"]):
            score += 2
        if any(f in f_req or f_req in f for f in gift["favor"]):
            score += 3
        if any(c in col_req or col_req in c for c in gift["color"]):
            score += 2
        if any(i in i_req or i_req in i for i in gift["intimacy"]):
            score += 1
        if any(e in e_req or e_req in e for e in gift["event"]):
            score += 2
            
        scored_gifts.append((score, gift))
        
    # Sắp xếp quà theo điểm phù hợp giảm dần
    scored_gifts.sort(key=lambda x: x[0], reverse=True)
    top_gifts = scored_gifts[:4]
    
    lines = [
        f"🎁 [HỆ THỐNG GỢI Ý QUÀ TẶNG - DỮ LIỆU DATABASE]",
        f"📋 Thông tin người nhận: Giới tính={gender} | Tính cách={character} | Sở thích={favor} | Màu={color} | Thân thiết={intimacy} | Dịp={event}",
        f"--------------------------------------------------------------------------------",
        f"Top món quà phù hợp nhất được trích xuất từ CSDL:"
    ]
    
    for idx, (score, gift) in enumerate(top_gifts, 1):
        lines.append(
            f"{idx}. {gift['name']} (Giá: {gift['price']})\n"
            f"   - Phân loại: {gift['category']}\n"
            f"   - Độ tương thích: {score}/12 điểm\n"
            f"   - Lý do gợi ý: Phù hợp người nhận {gender}, màu {color}, sở thích {favor} nhân dịp {event}."
        )
        
    lines.append("--------------------------------------------------------------------------------")
    lines.append(f"💡 Mẹo nhỏ: Hãy đóng gói quà theo tông màu chủ đạo là '{color}' để món quà thêm phần tinh tế!")
    
    return "\n".join(lines)


AVAILABLE_TOOLS = {
    "check_infor": check_infor,
    "ask_infor": ask_infor,
    "recommend_gift": recommend_gift,
}
