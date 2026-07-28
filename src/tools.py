"""Deterministic tools for the Mèo Hồng gift-selection agent.

All tools return data (including failures) instead of raising user-facing errors,
so the agent can make a safe, explainable next decision.
"""

from __future__ import annotations

import re
from typing import Any


GIFT_CATALOG = [
    {"id": "coffee-kit", "name": "Bộ cà phê drip thủ công", "price": 320000, "category": "Đồ uống", "tags": ["cà phê", "tối giản", "thực dụng"], "personalization": False, "delivery": "nội thành 1 ngày"},
    {"id": "reading-light", "name": "Đèn đọc sách kẹp bàn", "price": 280000, "category": "Sách", "tags": ["đọc sách", "tối giản", "thực dụng"], "personalization": False, "delivery": "nội thành 1 ngày"},
    {"id": "book-coffee-box", "name": "Hộp quà sách & cà phê", "price": 650000, "category": "Combo", "tags": ["đọc sách", "cà phê", "sinh nhật", "cá nhân hóa"], "personalization": True, "delivery": "2–3 ngày"},
    {"id": "game-card", "name": "Thẻ quà tặng game", "price": 500000, "category": "Giải trí", "tags": ["game", "trải nghiệm", "sinh nhật"], "personalization": False, "delivery": "gửi mã ngay"},
    {"id": "desk-kit", "name": "Bộ phụ kiện bàn làm việc", "price": 450000, "category": "Văn phòng", "tags": ["đồng nghiệp", "tối giản", "thực dụng"], "personalization": False, "delivery": "nội thành 1 ngày"},
    {"id": "ceramic-workshop", "name": "Voucher workshop làm gốm", "price": 750000, "category": "Trải nghiệm", "tags": ["trải nghiệm", "sáng tạo", "kỷ niệm"], "personalization": False, "delivery": "mã điện tử ngay"},
    {"id": "skincare-set", "name": "Bộ chăm sóc da mini", "price": 480000, "category": "Làm đẹp", "tags": ["làm đẹp", "thư giãn", "sinh nhật"], "personalization": False, "delivery": "2–3 ngày"},
    {"id": "cooking-class", "name": "Voucher lớp nấu ăn", "price": 690000, "category": "Trải nghiệm", "tags": ["nấu ăn", "trải nghiệm", "kỷ niệm"], "personalization": False, "delivery": "mã điện tử ngay"},
]


REQUIRED_FIELDS = ("relationship", "occasion", "interests", "budget_max")


def get_profile_completeness(profile: dict[str, Any]) -> dict[str, Any]:
    """Return the missing mandatory profile fields and the next question topic."""
    missing = [field for field in REQUIRED_FIELDS if not profile.get(field)]
    labels = {"relationship": "mối quan hệ", "occasion": "dịp tặng", "interests": "sở thích", "budget_max": "ngân sách"}
    return {
        "ok": True,
        "is_complete": not missing,
        "missing_fields": missing,
        "next_question_topic": labels[missing[0]] if missing else None,
    }


def search_gifts(profile: dict[str, Any]) -> dict[str, Any]:
    """Filter the offline demo catalog by the recipient's budget and interests."""
    completeness = get_profile_completeness(profile)
    if not completeness["is_complete"]:
        return {"ok": False, "error": "PROFILE_INCOMPLETE", "gifts": [], "missing_fields": completeness["missing_fields"]}

    maximum = profile["budget_max"]
    interests = {item.lower() for item in profile.get("interests", [])}
    avoid = {item.lower() for item in profile.get("dislikes", [])}
    matches = []
    for gift in GIFT_CATALOG:
        tags = {tag.lower() for tag in gift["tags"]}
        if gift["price"] > maximum or tags.intersection(avoid):
            continue
        if tags.intersection(interests) or gift["category"] == "Combo":
            matches.append(gift.copy())
    return {"ok": True, "gifts": matches, "catalog": "offline demo catalog"}


def rank_gifts(profile: dict[str, Any], gifts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Rank gifts predictably and attach a concise, user-visible reason."""
    interests = {item.lower() for item in profile.get("interests", [])}
    occasion = str(profile.get("occasion", "")).lower()
    ranked = []
    for gift in gifts:
        tags = {tag.lower() for tag in gift["tags"]}
        score = len(tags.intersection(interests)) * 3 + int(occasion in tags)
        if profile.get("deadline") and "ngày mai" in profile["deadline"].lower() and "ngày" not in gift["delivery"]:
            score += 2
        reasons = [f"hợp sở thích {', '.join(sorted(tags.intersection(interests)))}"] if tags.intersection(interests) else ["nằm trong ngân sách và dễ tặng"]
        if gift["price"] <= profile["budget_max"]:
            reasons.append(f"giá {gift['price']:,}đ trong mức bạn đặt ra".replace(",", "."))
        ranked.append({**gift, "score": score, "reason": "; ".join(reasons)})
    return sorted(ranked, key=lambda item: (-item["score"], item["price"]))[:5]


def extract_gift_profile(prompt: str) -> str:
    """Extract recipient, age, occasion and interests from a Vietnamese request."""
    text = prompt.lower()
    recipient_map = {
        "mẹ": ["mẹ", "má"], "bố": ["bố", "ba", "cha"],
        "bạn gái": ["bạn gái", "người yêu nữ"], "bạn trai": ["bạn trai", "người yêu nam"],
        "vợ": ["vợ"], "chồng": ["chồng"], "sếp": ["sếp"],
        "đồng nghiệp": ["đồng nghiệp"], "con": ["con trai", "con gái"],
        "bạn thân": ["bạn thân", "bạn bè", "bạn"],
    }
    occasion_map = {
        "sinh nhật": ["sinh nhật"], "Giáng sinh": ["giáng sinh", "noel"],
        "Valentine": ["valentine", "lễ tình nhân"], "Tết": ["tết", "năm mới"],
        "kỷ niệm ngày cưới": ["kỷ niệm ngày cưới", "kỷ niệm"], "20/10": ["20/10"],
        "8/3": ["8/3"], "tốt nghiệp": ["tốt nghiệp", "ra trường"],
    }
    interest_map = {
        "đọc sách": ["đọc sách", "sách"], "nấu ăn": ["nấu ăn", "nấu nướng", "ẩm thực"],
        "du lịch": ["du lịch", "phượt"], "công nghệ": ["công nghệ", "gadget", "điện tử"],
        "thể thao": ["thể thao", "gym", "bóng đá", "chạy bộ"], "âm nhạc": ["âm nhạc", "nghe nhạc", "guitar"],
        "làm đẹp": ["làm đẹp", "skincare", "mỹ phẩm"], "thời trang": ["thời trang", "quần áo"],
        "chơi game": ["chơi game", "game thủ"],
    }
    recipient = next((name for name, words in recipient_map.items() if any(word in text for word in words)), "Không xác định")
    occasion = next((name for name, words in occasion_map.items() if any(word in text for word in words)), "Không xác định")
    interests = [name for name, words in interest_map.items() if any(word in text for word in words)]
    age_match = re.search(r"(\d{1,3})\s*tuổi", text)
    age = f"{age_match.group(1)} tuổi" if age_match else "Không xác định"
    return "\n".join((
        "Hồ sơ tặng quà:", f"- Đối tượng: {recipient}", f"- Độ tuổi: {age}",
        f"- Dịp lễ: {occasion}", f"- Sở thích: {', '.join(interests) if interests else 'Không xác định'}",
    ))


def search_gift_api(gift_description: str) -> str:
    """Return a clearly labelled mock store/link for a gift category; no live lookup."""
    description = gift_description.lower()
    stores = (
        (("sách", "sach"), "Tiki - Nhà sách trực tuyến", "https://tiki.vn/nha-sach-tiki"),
        (("công nghệ", "gadget", "điện tử"), "FPT Shop - Đồ công nghệ", "https://fptshop.com.vn"),
        (("nấu ăn", "ẩm thực"), "Shopee - Đồ dùng nhà bếp", "https://shopee.vn"),
        (("làm đẹp", "skincare", "mỹ phẩm"), "Hasaki - Mỹ phẩm & làm đẹp", "https://hasaki.vn"),
        (("thời trang", "quần áo"), "Lazada - Thời trang", "https://www.lazada.vn"),
        (("thể thao", "gym"), "Decathlon - Đồ thể thao", "https://www.decathlon.vn"),
        (("du lịch", "phượt"), "Travelgear - Phụ kiện du lịch", "https://travelgear.vn"),
        (("chơi game", "game thủ"), "GearVN - Gaming Gear", "https://gearvn.com"),
        (("âm nhạc", "guitar"), "Việt Thương Music - Nhạc cụ", "https://vietthuong.vn"),
    )
    for keywords, store, link in stores:
        if any(keyword in description for keyword in keywords):
            return f"Dữ liệu mock — Cửa hàng: {store}. Link: {link}"
    return f"LỖI: Không tìm thấy cửa hàng phù hợp cho món quà '{gift_description}'."


AVAILABLE_TOOLS = {
    "get_profile_completeness": get_profile_completeness,
    "search_gifts": search_gifts,
    "rank_gifts": rank_gifts,
    "extract_gift_profile": extract_gift_profile,
    "search_gift_api": search_gift_api,
}
