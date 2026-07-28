"""Deterministic tools for the Mèo Hồng gift-selection agent.

All tools return data (including failures) instead of raising user-facing errors,
so the agent can make a safe, explainable next decision.
"""

from __future__ import annotations

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


AVAILABLE_TOOLS = {"get_profile_completeness": get_profile_completeness, "search_gifts": search_gifts, "rank_gifts": rank_gifts}
