"""LangGraph orchestration for the rental search and viewing workflow."""

from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from tools import book_viewing, get_viewing_slots, search_rentals


class RentalState(TypedDict, total=False):
    query: str
    filters: dict[str, Any]
    results: list[dict[str, Any]]
    selected_listing_id: str
    requested_date_range: str
    slots: list[str]
    selected_slot: str
    user_confirmed: bool
    booking: dict[str, Any]
    response: str
    trace: list[dict[str, Any]]
    needs_confirmation: bool


def _trace(state: RentalState, node: str, detail: str) -> list[dict[str, Any]]:
    return [*state.get("trace", []), {"node": node, "detail": detail}]


def parse_request(state: RentalState) -> dict[str, Any]:
    filters = dict(state.get("filters") or {})
    query = state.get("query", "")
    if "cầu giấy" in query.casefold():
        filters.setdefault("location", "Cầu Giấy")
    elif "bình thạnh" in query.casefold():
        filters.setdefault("location", "Bình Thạnh")
    elif "đà nẵng" in query.casefold() or "hải châu" in query.casefold():
        filters.setdefault("location", "Đà Nẵng")
    return {
        "filters": filters,
        "trace": _trace(state, "parse_request", f"filters={filters}"),
    }


def search_node(state: RentalState) -> dict[str, Any]:
    filters = state.get("filters") or {}
    results = search_rentals(**filters)
    selected = state.get("selected_listing_id")
    if selected:
        results = [item for item in results if item["listing_id"] == selected]
    return {
        "results": results,
        "selected_listing_id": selected or (results[0]["listing_id"] if results else ""),
        "trace": _trace(
            state,
            "search_rentals",
            f"{len(results)} listing(s) matched",
        ),
    }


def slots_node(state: RentalState) -> dict[str, Any]:
    listing_id = state.get("selected_listing_id", "")
    if not listing_id:
        return {
            "slots": [],
            "trace": _trace(state, "get_viewing_slots", "skipped: no listing"),
        }
    schedule = get_viewing_slots(
        listing_id,
        state.get("requested_date_range", ""),
    )
    return {
        "slots": schedule.get("slots", []),
        "trace": _trace(
            state,
            "get_viewing_slots",
            f"{listing_id}: {len(schedule.get('slots', []))} slot(s)",
        ),
    }


def booking_guard_node(state: RentalState) -> dict[str, Any]:
    selected_slot = state.get("selected_slot", "")
    listing_id = state.get("selected_listing_id", "")
    if not selected_slot or not listing_id:
        return {
            "needs_confirmation": False,
            "trace": _trace(state, "booking_guard", "skipped: no slot selected"),
        }
    if not state.get("user_confirmed", False):
        return {
            "needs_confirmation": True,
            "trace": _trace(state, "booking_guard", "confirmation required"),
        }
    booking = book_viewing(listing_id, selected_slot, user_confirmed=True)
    return {
        "booking": booking,
        "needs_confirmation": False,
        "trace": _trace(state, "book_viewing", booking.get("status", "error")),
    }


def finalize_node(state: RentalState) -> dict[str, Any]:
    results = state.get("results", [])
    slots = state.get("slots", [])
    booking = state.get("booking") or {}
    if booking.get("status") == "confirmed":
        response = (
            f"Đã đặt lịch thành công cho {booking['listing_id']} vào "
            f"{booking['slot']}. Mã xác nhận: {booking['confirmation_code']}."
        )
    elif state.get("needs_confirmation"):
        response = "Bạn hãy chọn một khung giờ và bấm “Xác nhận đặt lịch” để tiếp tục."
    elif not results:
        response = (
            "Mình chưa tìm thấy căn phù hợp với bộ lọc hiện tại. "
            "Bạn có thể nới ngân sách hoặc mở rộng khu vực."
        )
    elif slots:
        response = (
            f"Đã tìm thấy {len(results)} căn phù hợp. "
            f"Căn {state.get('selected_listing_id')} đang có "
            f"{len(slots)} khung giờ xem nhà."
        )
    else:
        response = f"Đã tìm thấy {len(results)} căn phù hợp với tiêu chí của bạn."
    return {
        "response": response,
        "trace": _trace(state, "finalize", response),
    }


def build_rental_graph():
    """Build a compiled LangGraph workflow."""
    graph = StateGraph(RentalState)
    graph.add_node("parse_request", parse_request)
    graph.add_node("search_rentals", search_node)
    graph.add_node("get_viewing_slots", slots_node)
    graph.add_node("booking_guard", booking_guard_node)
    graph.add_node("finalize", finalize_node)
    graph.set_entry_point("parse_request")
    graph.add_edge("parse_request", "search_rentals")
    graph.add_edge("search_rentals", "get_viewing_slots")
    graph.add_edge("get_viewing_slots", "booking_guard")
    graph.add_edge("booking_guard", "finalize")
    graph.add_edge("finalize", END)
    return graph.compile()


RENTAL_GRAPH = build_rental_graph()


def run_rental_graph(**kwargs: Any) -> RentalState:
    """Invoke graph with UI-friendly defaults."""
    return RENTAL_GRAPH.invoke(
        {
            "query": kwargs.get("query", ""),
            "filters": kwargs.get("filters", {}),
            "selected_listing_id": kwargs.get("selected_listing_id", ""),
            "requested_date_range": kwargs.get("requested_date_range", ""),
            "selected_slot": kwargs.get("selected_slot", ""),
            "user_confirmed": kwargs.get("user_confirmed", False),
            "trace": [],
        }
    )
