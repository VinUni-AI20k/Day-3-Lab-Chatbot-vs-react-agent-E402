"""Runnable offline state-machine demo for Mèo Hồng."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from prompts import FOLLOW_UP_QUESTIONS, MAX_ITERATIONS
from tools import get_profile_completeness, rank_gifts, search_gifts


def empty_profile() -> dict[str, Any]:
    return {"relationship": "", "occasion": "", "interests": [], "dislikes": [], "budget_min": None, "budget_max": None, "deadline": ""}


def parse_money(text: str) -> tuple[int | None, int | None]:
    values = re.findall(r"(\d+(?:[.,]\d+)?)\s*(triệu|tr|nghìn|ngàn|k)?", text.lower())
    amounts = []
    for number, unit in values:
        amount = float(number.replace(",", "."))
        amounts.append(int(amount * (1_000_000 if unit in ("triệu", "tr") else 1_000 if unit in ("nghìn", "ngàn", "k") else 1)))
    if not amounts:
        return None, None
    return (min(amounts), max(amounts)) if len(amounts) > 1 else (None, amounts[0])


@dataclass
class GiftAgent:
    profile: dict[str, Any] = field(default_factory=empty_profile)
    iteration: int = 0
    trace: list[dict[str, Any]] = field(default_factory=list)

    def _extract(self, message: str) -> None:
        text = message.lower()
        relationships = {"bạn thân": "Bạn thân", "người yêu": "Người yêu", "đồng nghiệp": "Đồng nghiệp", "mẹ": "Mẹ", "bố": "Bố", "sếp": "Sếp"}
        occasions = {"sinh nhật": "Sinh nhật", "kỷ niệm": "Kỷ niệm", "cảm ơn": "Cảm ơn", "tri ân": "Tri ân", "giáng sinh": "Giáng sinh"}
        for token, value in relationships.items():
            if token in text:
                self.profile["relationship"] = value
                break
        for token, value in occasions.items():
            if token in text:
                self.profile["occasion"] = value
                break
        interests = {"cà phê": "cà phê", "đọc sách": "đọc sách", "sách": "đọc sách", "game": "game", "chơi game": "game", "làm đẹp": "làm đẹp", "skincare": "làm đẹp", "nấu ăn": "nấu ăn", "gốm": "sáng tạo", "du lịch": "trải nghiệm"}
        for token, value in interests.items():
            if token in text and value not in self.profile["interests"]:
                self.profile["interests"].append(value)
        minimum, maximum = parse_money(text)
        if maximum:
            self.profile["budget_min"], self.profile["budget_max"] = minimum, maximum
        if "ngày mai" in text:
            self.profile["deadline"] = "ngày mai"

    def handle_message(self, message: str) -> dict[str, Any]:
        self.iteration += 1
        self._extract(message)
        complete = get_profile_completeness(self.profile)
        event = {"iteration": self.iteration, "profile": self.profile.copy(), "tool_calls": ["get_profile_completeness"], "node": "collect_profile"}
        if self.iteration > MAX_ITERATIONS:
            reply = "Mình chưa muốn hỏi lan man. Bạn cho mình biết thêm " + complete["next_question_topic"] + " để chọn quà chính xác nhé."
            event.update(node="fallback", reply=reply)
        elif not complete["is_complete"]:
            reply = FOLLOW_UP_QUESTIONS[complete["missing_fields"][0]]
            event.update(reply=reply)
        else:
            result = search_gifts(self.profile)
            event["tool_calls"].append("search_gifts")
            if not result["gifts"]:
                reply = "Catalog demo chưa có món phù hợp với các điều kiện này. Bạn muốn nới một ràng buộc, ví dụ tăng ngân sách hoặc đổi loại quà, không?"
                event.update(node="fallback", reply=reply)
            else:
                gifts = rank_gifts(self.profile, result["gifts"])
                event["tool_calls"].append("rank_gifts")
                lines = [f"{index}. {gift['name']} — {gift['price']:,}đ: {gift['reason']}.".replace(",", ".") for index, gift in enumerate(gifts, 1)]
                reply = "Mình đã lọc từ catalog demo. Đây là các lựa chọn phù hợp nhất:\n" + "\n".join(lines)
                event.update(node="rank_and_explain", reply=reply, gifts=gifts)
        self.trace.append(event)
        return {"reply": reply, "profile": self.profile, "trace": event}


def load_test_cases() -> list[dict[str, Any]]:
    return json.loads((Path(__file__).parent.parent / "config" / "test_cases.json").read_text(encoding="utf-8"))


if __name__ == "__main__":
    agent = GiftAgent()
    print("Mèo Hồng (offline demo). Gõ 'thoát' để dừng.")
    while True:
        message = input("Bạn: ").strip()
        if message.lower() in {"thoát", "exit", "quit"}:
            break
        if message:
            print("Mèo Hồng:", agent.handle_message(message)["reply"])
