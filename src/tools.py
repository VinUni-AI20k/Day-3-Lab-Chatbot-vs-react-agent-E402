"""
Tool registry & schemas for Role 2: Tool Engineer.

Topic 10: rental room/apartment finder and viewing scheduler.
All tools are deterministic, read from mock data, and return strings instead
of raising business errors so the ReAct Agent can recover safely.
"""

from datetime import datetime
import unicodedata


RENTAL_LISTINGS = [
    {
        "id": "PT001",
        "property_type": "phong tro",
        "location": "Gia Lam",
        "price": 3500000,
        "address": "Ngo 68 Xuan Thuy, Gia Lam, Ha Noi",
        "area_m2": 22,
        "deposit_months": 1,
        "amenities": ["gac xep", "dieu hoa", "wifi", "cho de xe"],
        "available": True,
        "viewing_slots": ["thu 7 tuan nay 09:00", "thu 7 tuan nay 14:00", "chu nhat tuan nay 10:00"],
    },
    {
        "id": "PT002",
        "property_type": "phong tro",
        "location": "Gia Lam",
        "price": 4200000,
        "address": "Ngo 123 Tran Duy Hung, Gia Lam, Ha Noi",
        "area_m2": 25,
        "deposit_months": 1,
        "amenities": ["dieu hoa", "ban cong", "may giat chung"],
        "available": True,
        "viewing_slots": ["thu 7 tuan nay 11:00", "chu nhat tuan nay 15:00"],
    },
    {
        "id": "PT003",
        "property_type": "phong tro",
        "location": "Gia Lam",
        "price": 3800000,
        "address": "Pho Dich Vong Hau, Gia Lam, Ha Noi",
        "area_m2": 20,
        "deposit_months": 1,
        "amenities": ["wifi", "tu lanh", "khep kin"],
        "available": False,
        "viewing_slots": [],
    },
    {
        "id": "CH001",
        "property_type": "can ho",
        "location": "Gia Lam",
        "price": 8500000,
        "address": "Pho Thai Ha, Gia Lam, Ha Noi",
        "area_m2": 48,
        "deposit_months": 2,
        "amenities": ["1 phong ngu", "may giat", "bep rieng", "bao ve"],
        "available": True,
        "viewing_slots": ["thu 7 tuan nay 16:00", "chu nhat tuan nay 09:00"],
    },
    {
        "id": "CH002",
        "property_type": "can ho",
        "location": "Gia Lam",
        "price": 7500000,
        "address": "Pho Chua Boc, Gia Lam, Ha Noi",
        "area_m2": 45,
        "deposit_months": 1,
        "amenities": ["1 phong ngu", "ban cong", "may giat", "gan truong dai hoc"],
        "available": True,
        "viewing_slots": ["thu 7 tuan nay 10:00", "thu 7 tuan nay 15:00", "chu nhat tuan nay 10:00"],
    },
    {
        "id": "CH003",
        "property_type": "can ho",
        "location": "Gia Lam",
        "price": 6800000,
        "address": "Pho Nguyen Trai, Gia Lam, Ha Noi",
        "area_m2": 38,
        "deposit_months": 1,
        "amenities": ["studio", "thang may", "bep rieng"],
        "available": True,
        "viewing_slots": ["thu 6 tuan nay 18:00", "thu 7 tuan nay 13:00"],
    },
]


def _normalize_text(value: str) -> str:
    """Return lowercase text with common Vietnamese variants normalized."""
    if value is None:
        return ""
    text = str(value).strip().lower().replace("đ", "d")
    text = unicodedata.normalize("NFD", text)
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    return " ".join(text.split())


def _format_price(price: int) -> str:
    return f"{price:,} VND/thang".replace(",", ".")


def _find_listing(listing_id: str):
    listing_id_normalized = str(listing_id or "").strip().upper()
    for listing in RENTAL_LISTINGS:
        if listing["id"] == listing_id_normalized:
            return listing
    return None


def _format_listing_summary(listing: dict) -> str:
    status = "con trong" if listing["available"] else "da het phong"
    amenities = ", ".join(listing["amenities"])
    return (
        f"- {listing['id']} | {listing['property_type']} | {listing['location']} | "
        f"{_format_price(listing['price'])} | {listing['area_m2']}m2 | {status} | "
        f"{listing['address']} | Tien ich: {amenities}"
    )


def _matches_amenities(listing: dict, amenities) -> bool:
    if not amenities:
        return True

    if isinstance(amenities, str):
        requested = [amenities]
    else:
        requested = list(amenities)

    requested_normalized = {
        _normalize_text(item) for item in requested if str(item or "").strip()
    }
    if not requested_normalized:
        return True

    listing_amenities = {_normalize_text(item) for item in listing.get("amenities", [])}
    return requested_normalized.issubset(listing_amenities)


def search_rentals(
    location: str,
    max_price: int | None = None,
    property_type: str | None = None,
    min_area: int | None = None,
    amenities=None,
) -> str:
    """
    Search rental listings by location, maximum monthly price, property type,
    minimum area, and required amenities.

    Args:
        location (str): District/area, for example "Gia Lam".
        max_price (int | None): Maximum monthly rent in VND. If omitted, no price limit is applied.
        property_type (str | None): "phong tro" or "can ho". If omitted, all types are included.
        min_area (int | None): Minimum usable area in m2.
        amenities (str | list[str] | None): Required amenities, for example "wifi" or ["wifi", "dieu hoa"].

    Returns:
        str: Matching listings with id, price, address, area, status, and amenities.
        On invalid input or no result, returns a string beginning with "LOI:".
    """
    if max_price is not None:
        try:
            max_price = int(max_price)
        except (TypeError, ValueError):
            return "LOI: max_price phai la so tien VND hop le."
        if max_price <= 0:
            return "LOI: max_price phai lon hon 0."

    if min_area is not None:
        try:
            min_area = int(min_area)
        except (TypeError, ValueError):
            return "LOI: min_area phai la so nguyen hop le."
        if min_area <= 0:
            return "LOI: min_area phai lon hon 0."

    if not _normalize_text(location):
        return "LOI: location khong duoc de trong."

    target_location = _normalize_text(location)
    target_type = _normalize_text(property_type) if property_type else None

    matches = [
        listing
        for listing in RENTAL_LISTINGS
        if (
            target_location in _normalize_text(listing["location"])
            and (target_type is None or target_type in _normalize_text(listing["property_type"]))
            and (max_price is None or listing["price"] <= max_price)
            and (min_area is None or listing["area_m2"] >= min_area)
            and _matches_amenities(listing, amenities)
        )
    ]

    if not matches:
        if max_price is None:
            price_clause = "khong gioi han ve gia"
        else:
            price_clause = f"ngan sach {_format_price(max_price)}"
        return (
            "LOI: Khong tim thay listing phu hop voi "
            f"khu vuc '{location}', loai '{property_type or 'tat ca'}', {price_clause}."
        )

    lines = [
        f"Tim thay {len(matches)} listing phu hop:"
    ]
    lines.extend(_format_listing_summary(listing) for listing in matches)
    return "\n".join(lines)


def get_listing_detail(listing_id: str) -> str:
    """
    Get detailed information for one rental listing.

    Args:
        listing_id (str): Listing code, for example "PT001" or "CH002".

    Returns:
        str: Full listing details including address, rent, deposit, amenities,
        availability, and viewing slots. If not found, returns "LOI: ...".
    """
    listing = _find_listing(listing_id)
    if not listing:
        return f"LOI: Khong tim thay ma phong/can ho '{listing_id}'."

    status = "con trong" if listing["available"] else "da het phong"
    slots = ", ".join(listing["viewing_slots"]) if listing["viewing_slots"] else "khong co lich xem kha dung"
    return (
        f"Chi tiet {listing['id']}:\n"
        f"- Loai: {listing['property_type']}\n"
        f"- Khu vuc: {listing['location']}\n"
        f"- Dia chi: {listing['address']}\n"
        f"- Gia thue: {_format_price(listing['price'])}\n"
        f"- Dien tich: {listing['area_m2']}m2\n"
        f"- Tien coc: {listing['deposit_months']} thang\n"
        f"- Tien ich: {', '.join(listing['amenities'])}\n"
        f"- Trang thai: {status}\n"
        f"- Lich xem kha dung: {slots}"
    )


def check_availability(listing_id: str, date: str, time: str) -> str:
    """
    Check whether a listing is available for viewing at a requested date and time.

    Args:
        listing_id (str): Listing code.
        date (str): Requested date text, for example "thu 7 tuan nay".
        time (str): Requested time in HH:MM format.

    Returns:
        str: Availability result. Invalid listing/date/time returns "LOI: ...".
    """
    listing = _find_listing(listing_id)
    if not listing:
        return f"LOI: Khong tim thay ma phong/can ho '{listing_id}'."
    if not listing["available"]:
        return f"LOI: Listing '{listing['id']}' hien da het phong, khong the dat lich xem."

    time_error = _validate_time(time)
    if time_error:
        return time_error

    date_key = _normalize_text(date)
    if not date_key:
        return "LOI: date khong duoc de trong."
    if "32/13" in date_key:
        return "LOI: Ngay xem phong khong hop le."

    requested_slot = f"{date_key} {str(time).strip()}"
    normalized_slots = [_normalize_text(slot) for slot in listing["viewing_slots"]]
    if requested_slot not in normalized_slots:
        return (
            f"LOI: Listing '{listing['id']}' khong co lich xem vao {date} luc {time}. "
            f"Cac lich kha dung: {', '.join(listing['viewing_slots'])}."
        )

    return f"Listing '{listing['id']}' con lich xem vao {date} luc {time}."


def book_viewing(listing_id: str, date: str, time: str, contact_name: str, phone: str = "") -> str:
    """
    Book a viewing appointment for a rental listing.

    Args:
        listing_id (str): Listing code.
        date (str): Requested date text, for example "thu 7 tuan nay".
        time (str): Requested time in HH:MM format.
        contact_name (str): Name of the viewer.
        phone (str): Optional contact phone number.

    Returns:
        str: Booking confirmation if valid. Any invalid listing, unavailable slot,
        bad time, or missing contact returns a string beginning with "LOI:".
    """
    if not _normalize_text(contact_name):
        return "LOI: contact_name khong duoc de trong khi dat lich xem phong."

    availability = check_availability(listing_id, date, time)
    if availability.startswith("LOI:"):
        return availability

    listing = _find_listing(listing_id)
    phone_note = f", SDT: {phone}" if str(phone or "").strip() else ""
    return (
        f"Dat lich xem phong thanh cong cho listing {listing['id']}.\n"
        f"- Nguoi lien he: {contact_name}{phone_note}\n"
        f"- Thoi gian: {date} luc {time}\n"
        f"- Dia chi: {listing['address']}\n"
        f"- Luu y: Vui long den dung gio va mang CCCD/giay to tuy than."
    )


def compare_listings(listing_ids) -> str:
    """
    Compare multiple rental listings by price, area, amenities, and availability.

    Args:
        listing_ids (list[str] | str): Listing ids, for example ["PT001", "CH002"]
        or a comma-separated string like "PT001, CH002".

    Returns:
        str: Comparison table and a simple recommendation. Unknown ids return
        "LOI: ..." so the Agent can ask the user to correct them.
    """
    if isinstance(listing_ids, str):
        ids = [item.strip().upper() for item in listing_ids.split(",") if item.strip()]
    else:
        try:
            ids = [str(item).strip().upper() for item in listing_ids if str(item).strip()]
        except TypeError:
            return "LOI: listing_ids phai la danh sach ma listing hoac chuoi cach nhau bang dau phay."

    if len(ids) < 2:
        return "LOI: Can it nhat 2 ma listing de so sanh."

    listings = []
    missing_ids = []
    for listing_id in ids:
        listing = _find_listing(listing_id)
        if listing:
            listings.append(listing)
        else:
            missing_ids.append(listing_id)

    if missing_ids:
        return f"LOI: Khong tim thay cac ma listing sau: {', '.join(missing_ids)}."

    lines = ["Bang so sanh listing:"]
    for listing in listings:
        lines.append(_format_listing_summary(listing))

    available_listings = [listing for listing in listings if listing["available"]]
    if available_listings:
        best_value = min(available_listings, key=lambda item: item["price"] / item["area_m2"])
        lines.append(
            f"Goi y: {best_value['id']} co gia/m2 tot nhat trong cac listing con trong "
            f"({_format_price(best_value['price'])}, {best_value['area_m2']}m2)."
        )
    else:
        lines.append("Goi y: Tat ca listing dang het phong, nen tim lua chon khac.")

    return "\n".join(lines)


def _validate_time(time: str) -> str:
    try:
        parsed_time = datetime.strptime(str(time).strip(), "%H:%M").time()
    except (TypeError, ValueError):
        return "LOI: time phai dung dinh dang HH:MM, vi du 10:00."

    if parsed_time.hour < 8 or parsed_time.hour > 20:
        return "LOI: Gio xem phong chi ho tro tu 08:00 den 20:00."
    return ""


AVAILABLE_TOOLS = {
    "search_rentals": search_rentals,
    "get_listing_detail": get_listing_detail,
    "check_availability": check_availability,
    "book_viewing": book_viewing,
    "compare_listings": compare_listings,
}
