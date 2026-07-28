"""Cupid tools available to the ReAct agent."""

import json
from pathlib import Path
from typing import Any


DATA_FILE = Path(__file__).resolve().parents[1] / "cupid_data" / "profiles.json"


def _load_profiles() -> dict[str, dict]:
    with DATA_FILE.open(encoding="utf-8") as file:
        profiles = json.load(file)
    return {profile["id"]: profile for profile in profiles}


def _success(data: dict) -> dict:
    return {"ok": True, "data": data}


def _error(code: str, message: str) -> dict:
    return {"ok": False, "error": {"code": code, "message": message}}


def _profile(user_id: str) -> tuple[dict | None, dict | None]:
    if not isinstance(user_id, str) or not user_id.strip():
        return None, _error("INVALID_INPUT", "user_id phải là chuỗi không rỗng")
    profile = _load_profiles().get(user_id)
    if profile is None:
        return None, _error("PROFILE_NOT_FOUND", f"Không tìm thấy hồ sơ {user_id}")
    return profile, None


def get_user_profile(user_id: Any) -> dict:
    """Lấy một hồ sơ mock theo ID.

    Args:
        user_id: ID hồ sơ, ví dụ ``U001``.

    Returns:
        Dict success chứa profile hoặc error với mã ``INVALID_INPUT`` hay
        ``PROFILE_NOT_FOUND``. Lỗi nghiệp vụ không được raise.
    """
    profile, error = _profile(user_id)
    if error:
        return error
    assert profile is not None
    return _success(profile)


def _eligibility_reason(first: dict, second: dict) -> str | None:
    if (
        second["gender"] not in first["interested_in"]
        or first["gender"] not in second["interested_in"]
    ):
        return "Hai hồ sơ không phù hợp tiêu chí kết nối hai chiều"
    for owner, candidate in ((first, second), (second, first)):
        for attribute, blocked_value in owner.get("deal_breakers", {}).items():
            if candidate.get("attributes", {}).get(attribute) == blocked_value:
                return "Hai hồ sơ không đáp ứng điều kiện ghép đôi"
    return None


def _jaccard(left: list[str], right: list[str]) -> float:
    union = set(left) | set(right)
    return 100.0 if not union else len(set(left) & set(right)) / len(union) * 100


def _compatibility(first: dict, second: dict) -> dict:
    breakdown = {
        "relationship_goal": (
            100.0 if first["relationship_goal"] == second["relationship_goal"] else 0.0
        ),
        "values": _jaccard(first["values"], second["values"]),
        "interests": _jaccard(first["interests"], second["interests"]),
        "location": 100.0 if first["location"] == second["location"] else 0.0,
    }
    total = (
        breakdown["relationship_goal"] * 0.35
        + breakdown["values"] * 0.30
        + breakdown["interests"] * 0.20
        + breakdown["location"] * 0.15
    )
    return {
        "eligible": True,
        "total_score": round(total, 1),
        "breakdown": {key: round(value, 1) for key, value in breakdown.items()},
        "shared_interests": sorted(set(first["interests"]) & set(second["interests"])),
        "shared_values": sorted(set(first["values"]) & set(second["values"])),
    }


def calculate_compatibility(user_id: Any, candidate_id: Any) -> dict:
    """Phân tích điểm tương thích của hai hồ sơ đủ điều kiện.

    Args:
        user_id: ID người đang tìm kết nối.
        candidate_id: ID ứng viên cần phân tích.

    Returns:
        Dict success gồm tổng điểm, breakdown và điểm chung; hoặc error
        ``INVALID_INPUT``, ``PROFILE_NOT_FOUND`` hay ``INELIGIBLE_MATCH``.
    """
    user, error = _profile(user_id)
    if error:
        return error
    candidate, error = _profile(candidate_id)
    if error:
        return error
    assert user is not None and candidate is not None
    if user_id == candidate_id:
        return _error("INELIGIBLE_MATCH", "Không thể ghép một hồ sơ với chính nó")
    reason = _eligibility_reason(user, candidate)
    if reason:
        return _error("INELIGIBLE_MATCH", reason)
    return _success(_compatibility(user, candidate))


def _reasons(result: dict, user: dict, candidate: dict) -> list[str]:
    reasons = []
    if result["shared_values"]:
        reasons.append("Cùng giá trị: " + ", ".join(result["shared_values"][:2]))
    if result["shared_interests"]:
        reasons.append("Cùng sở thích: " + ", ".join(result["shared_interests"][:2]))
    if user["relationship_goal"] == candidate["relationship_goal"]:
        reasons.append("Cùng mục tiêu mối quan hệ")
    if user["location"] == candidate["location"]:
        reasons.append("Cùng khu vực")
    return reasons[:3]


def find_candidate_matches(user_id: Any, limit: Any = 3) -> dict:
    """Tìm tối đa ba ứng viên hợp lệ và xếp hạng deterministic.

    Args:
        user_id: ID hồ sơ cần tìm ứng viên.
        limit: Số kết quả từ 1 đến 3.

    Returns:
        Dict success chứa ``matches`` hoặc error ``INVALID_INPUT``,
        ``PROFILE_NOT_FOUND`` hay ``NO_MATCHES``.
    """
    user, error = _profile(user_id)
    if error:
        return error
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 3:
        return _error("INVALID_INPUT", "limit phải là số nguyên từ 1 đến 3")
    assert user is not None

    matches = []
    for candidate_id, candidate in _load_profiles().items():
        if candidate_id == user_id or _eligibility_reason(user, candidate):
            continue
        result = _compatibility(user, candidate)
        matches.append(
            {
                "candidate_id": candidate_id,
                "name": candidate["name"],
                "score": result["total_score"],
                "reasons": _reasons(result, user, candidate),
            }
        )

    if not matches:
        return _error("NO_MATCHES", f"Không có ứng viên phù hợp cho {user_id}")
    matches.sort(key=lambda item: (-item["score"], item["candidate_id"]))
    return _success({"matches": matches[:limit]})


def suggest_first_message(user_id: Any, candidate_id: Any) -> dict:
    """Tạo lời mở đầu tôn trọng từ một điểm chung có trong dữ liệu.

    Args:
        user_id: ID người gửi.
        candidate_id: ID người nhận.

    Returns:
        Dict success chứa ``message`` và ``based_on``; hoặc error
        ``INVALID_INPUT``, ``PROFILE_NOT_FOUND`` hay ``INELIGIBLE_MATCH``.
    """
    user, error = _profile(user_id)
    if error:
        return error
    candidate, error = _profile(candidate_id)
    if error:
        return error
    assert user is not None and candidate is not None
    if user_id == candidate_id:
        return _error(
            "INELIGIBLE_MATCH", "Không thể tạo lời mở đầu cho cùng một hồ sơ"
        )
    reason = _eligibility_reason(user, candidate)
    if reason:
        return _error("INELIGIBLE_MATCH", reason)

    shared_interests = sorted(set(user["interests"]) & set(candidate["interests"]))
    shared_values = sorted(set(user["values"]) & set(candidate["values"]))
    if shared_interests:
        topic = shared_interests[0]
        message = (
            f"Chào {candidate['name']}, mình thấy chúng ta đều thích {topic}. "
            "Bạn thích điều gì nhất ở sở thích này?"
        )
        based_on = {"type": "interest", "value": topic}
    elif shared_values:
        topic = shared_values[0]
        message = (
            f"Chào {candidate['name']}, mình thấy chúng ta cùng coi trọng {topic}. "
            "Rất vui được làm quen với bạn!"
        )
        based_on = {"type": "value", "value": topic}
    else:
        message = (
            f"Chào {candidate['name']}, rất vui được làm quen với bạn. "
            "Dạo này bạn có trải nghiệm nào thú vị không?"
        )
        based_on = {"type": "neutral", "value": None}
    return _success({"message": message, "based_on": based_on})


AVAILABLE_TOOLS = {
    "get_user_profile": get_user_profile,
    "find_candidate_matches": find_candidate_matches,
    "calculate_compatibility": calculate_compatibility,
    "suggest_first_message": suggest_first_message,
}


if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as directory:
        DATA_FILE = Path(directory) / "profiles.json"
        DATA_FILE.write_text(
            json.dumps(
                [
                    {
                        "id": "U001",
                        "name": "An",
                        "age": 26,
                        "gender": "female",
                        "interested_in": ["male"],
                        "location": "Hà Nội",
                        "interests": ["cà phê", "du lịch"],
                        "values": ["gia đình", "trung thực"],
                        "relationship_goal": "long_term",
                        "attributes": {"smoking": False},
                        "deal_breakers": {"smoking": True},
                    },
                    {
                        "id": "U002",
                        "name": "Bình",
                        "age": 28,
                        "gender": "male",
                        "interested_in": ["female"],
                        "location": "Hà Nội",
                        "interests": ["cà phê", "đọc sách"],
                        "values": ["gia đình", "tôn trọng"],
                        "relationship_goal": "long_term",
                        "attributes": {"smoking": False},
                        "deal_breakers": {"smoking": True},
                    },
                    {
                        "id": "U003",
                        "name": "Chi",
                        "age": 25,
                        "gender": "female",
                        "interested_in": ["female"],
                        "location": "Đà Nẵng",
                        "interests": ["âm nhạc"],
                        "values": ["độc lập"],
                        "relationship_goal": "casual",
                        "attributes": {"smoking": False},
                        "deal_breakers": {},
                    }
                ],
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        assert get_user_profile("U001")["ok"] is True
        assert get_user_profile("U999")["error"]["code"] == "PROFILE_NOT_FOUND"
        assert get_user_profile(123)["error"]["code"] == "INVALID_INPUT"
        compatible = calculate_compatibility("U001", "U002")
        assert compatible["ok"] is True
        assert 0 <= compatible["data"]["total_score"] <= 100
        assert set(compatible["data"]["breakdown"]) == {
            "relationship_goal",
            "values",
            "interests",
            "location",
        }
        assert calculate_compatibility("U001", "U003")["error"]["code"] == "INELIGIBLE_MATCH"
        matches = find_candidate_matches("U001")
        assert matches["ok"] is True
        assert 1 <= len(matches["data"]["matches"]) <= 3
        ranking = [
            (item["score"], item["candidate_id"])
            for item in matches["data"]["matches"]
        ]
        assert ranking == sorted(ranking, key=lambda item: (-item[0], item[1]))
        assert find_candidate_matches("U001", 0)["error"]["code"] == "INVALID_INPUT"
        opener = suggest_first_message("U001", "U002")
        assert opener["ok"] is True
        assert opener["data"]["message"]
        assert set(AVAILABLE_TOOLS) == {
            "get_user_profile",
            "find_candidate_matches",
            "calculate_compatibility",
            "suggest_first_message",
        }
