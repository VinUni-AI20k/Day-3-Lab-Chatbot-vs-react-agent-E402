"""Web UI thân thiện cho RentalFlow — chạy bằng Streamlit."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from langgraph_agent import run_rental_graph
from tools import RENTAL_LISTINGS


st.set_page_config(
    page_title="RentalFlow · Tìm nhà dễ hơn",
    page_icon="🏡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
:root { --ink:#10233f; --muted:#64748b; --mint:#16b89a; --cream:#f7faf8; --line:#e6eef0; }
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp { background: #f7faf8; color: var(--ink); }
[data-testid="stSidebar"] { background: #10233f; }
[data-testid="stSidebar"] * { color: #f5fbfa !important; }
[data-testid="stSidebar"] .stCaption { color: #b6c8d4 !important; }
h1, h2, h3 { font-family: 'Space Grotesk', sans-serif; letter-spacing: -0.03em; }
.hero { background: linear-gradient(120deg,#10233f 0%,#183b54 62%,#0e897c 100%); border-radius: 24px; padding: 34px 38px; color:white; margin: 8px 0 28px; box-shadow: 0 14px 35px rgba(16,35,63,.14); }
.hero h1 { color:#fff; font-size:42px; margin:0 0 10px; }
.hero p { color:#d6f1ea; font-size:17px; margin:0; max-width:690px; }
.eyebrow { color:#8fe9d1; text-transform:uppercase; letter-spacing:.14em; font-size:12px; font-weight:700; margin-bottom:10px; }
.metric { background:white; border:1px solid var(--line); border-radius:18px; padding:18px 20px; }
.metric strong { display:block; font-family:'Space Grotesk'; font-size:25px; color:var(--ink); }
.metric span { color:var(--muted); font-size:13px; }
.listing { background:#fff; border:1px solid var(--line); border-radius:20px; padding:20px; min-height:220px; box-shadow:0 5px 14px rgba(16,35,63,.04); }
.listing .emoji { font-size:34px; }
.listing h3 { margin:7px 0 5px; font-size:20px; }
.listing .location { color:var(--muted); font-size:14px; }
.price { color:#0b9c85; font-size:21px; font-weight:700; margin-top:15px; }
.tag { display:inline-block; color:#197765; background:#e7f8f3; border-radius:20px; padding:5px 10px; font-size:12px; font-weight:600; margin:5px 4px 0 0; }
.trace { background:#10233f; color:#d5e7ea; border-radius:14px; padding:14px 17px; font-family:monospace; font-size:12px; line-height:1.65; }
.success { background:#e7f8f3; border:1px solid #a9e7d6; border-radius:14px; padding:14px 18px; color:#126b5b; }
.muted { color:var(--muted); }
button[kind="primary"] { background:#16b89a; border-color:#16b89a; }
</style>
""",
    unsafe_allow_html=True,
)


def format_price(value: int) -> str:
    return f"{value:,.0f} đ/tháng".replace(",", ".")


def reset_search() -> None:
    for key in ("graph_state", "selected_listing_id", "selected_slot"):
        st.session_state.pop(key, None)


if "graph_state" not in st.session_state:
    st.session_state.graph_state = None

with st.sidebar:
    st.markdown("## 🏡 RentalFlow")
    st.caption("Trợ lý tìm nhà có dữ liệu và có phanh an toàn")
    st.divider()
    st.markdown("### Bộ lọc tìm kiếm")
    location = st.selectbox(
        "Khu vực",
        ["Tất cả khu vực", "Cầu Giấy", "Bình Thạnh", "Đà Nẵng"],
    )
    max_price = st.slider("Ngân sách tối đa / tháng", 2_000_000, 20_000_000, 10_000_000, 500_000)
    bedrooms_label = st.selectbox("Số phòng ngủ", ["Không quan trọng", "Studio", "1 phòng ngủ", "2 phòng ngủ"])
    pet_allowed = st.checkbox("Cho phép nuôi thú cưng", value=False)
    furnished = st.checkbox("Có nội thất", value=True)
    st.divider()
    st.caption("🔒 Booking chỉ được thực thi sau khi bạn chọn slot và xác nhận rõ ràng.")

bedrooms = {"Không quan trọng": None, "Studio": 0, "1 phòng ngủ": 1, "2 phòng ngủ": 2}[bedrooms_label]
location_value = "" if location == "Tất cả khu vực" else location
filters = {
    "location": location_value,
    "max_price": max_price,
    "bedrooms": bedrooms,
    "pet_allowed": True if pet_allowed else None,
    "furnished": True if furnished else None,
}

st.markdown(
    """
<div class="hero">
  <div class="eyebrow">AI-powered home search</div>
  <h1>Tìm một nơi<br>thật sự hợp với bạn.</h1>
  <p>Khám phá căn hộ phù hợp, xem lịch trống và đặt lịch xem nhà trong vài bước — minh bạch, dễ dùng, không bịa dữ liệu.</p>
</div>
""",
    unsafe_allow_html=True,
)

m1, m2, m3 = st.columns(3)
with m1:
    st.markdown('<div class="metric"><strong>5</strong><span>listing demo có sẵn</span></div>', unsafe_allow_html=True)
with m2:
    st.markdown('<div class="metric"><strong>3 bước</strong><span>tìm · chọn · xem lịch</span></div>', unsafe_allow_html=True)
with m3:
    st.markdown('<div class="metric"><strong>100%</strong><span>có xác nhận trước booking</span></div>', unsafe_allow_html=True)

st.markdown("## Bắt đầu tìm kiếm")
query = st.text_input(
    "Bạn đang tìm gì?",
    placeholder="Ví dụ: Căn 1 phòng ngủ ở Bình Thạnh, cuối tuần này...",
    label_visibility="collapsed",
)
c1, c2 = st.columns([1, 5])
with c1:
    search_clicked = st.button("🔎 Tìm căn phù hợp", type="primary", use_container_width=True)
with c2:
    if st.button("↺ Xóa bộ lọc", use_container_width=False):
        reset_search()
        st.rerun()

if search_clicked:
    with st.spinner("LangGraph đang tìm các căn phù hợp..."):
        st.session_state.graph_state = run_rental_graph(
            query=query or f"Tìm nhà ở {location_value or 'tất cả khu vực'}",
            filters=filters,
        )
        st.session_state.pop("selected_listing_id", None)
        st.session_state.pop("selected_slot", None)

state = st.session_state.graph_state
if state:
    st.markdown("## Căn phù hợp với bạn")
    if not state.get("results"):
        st.info(state.get("response", "Chưa có căn phù hợp."))
    else:
        cols = st.columns(min(3, len(state["results"])))
        for index, listing in enumerate(state["results"]):
            with cols[index % len(cols)]:
                st.markdown(
                    f"""
                    <div class="listing">
                      <div class="emoji">{listing['image']}</div>
                      <h3>{listing['title']}</h3>
                      <div class="location">📍 {listing['location']} · {listing['area_m2']} m²</div>
                      <div class="price">{format_price(listing['price'])}</div>
                      <span class="tag">{'🐾 Cho nuôi thú cưng' if listing['pet_allowed'] else 'Không nuôi thú cưng'}</span>
                      <span class="tag">{'Nội thất' if listing['furnished'] else 'Cơ bản'}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button("Xem lịch căn này", key=f"select_{listing['listing_id']}", use_container_width=True):
                    st.session_state.selected_listing_id = listing["listing_id"]
                    st.session_state.pop("selected_slot", None)
                    st.session_state.graph_state = run_rental_graph(
                        query=query or listing["title"],
                        filters=filters,
                        selected_listing_id=listing["listing_id"],
                        requested_date_range="cuối tuần này",
                    )
                    st.rerun()

selected_id = st.session_state.get("selected_listing_id")
if selected_id and state:
    selected = next((x for x in state.get("results", []) if x["listing_id"] == selected_id), None)
    st.markdown("---")
    st.markdown("## 📅 Chọn lịch xem nhà")
    if selected:
        st.markdown(f"**{selected['title']}** · {selected['location']}")
    slots = state.get("slots", [])
    if slots:
        selected_slot = st.radio("Khung giờ còn trống", slots, horizontal=True, key="slot_radio")
        st.session_state.selected_slot = selected_slot
        confirmed = st.checkbox("Tôi xác nhận muốn đặt lịch xem nhà này.", key="booking_confirm")
        if st.button("✅ Xác nhận đặt lịch", type="primary", disabled=not confirmed):
            with st.spinner("Đang xác nhận lịch..."):
                st.session_state.graph_state = run_rental_graph(
                    query=query or "",
                    filters=filters,
                    selected_listing_id=selected_id,
                    requested_date_range="cuối tuần này",
                    selected_slot=selected_slot,
                    user_confirmed=True,
                )
            st.success(st.session_state.graph_state["response"])
    else:
        st.warning("Căn này chưa có khung giờ phù hợp.")

with st.expander("🔍 Xem trace LangGraph"):
    if state and state.get("trace"):
        trace_text = "\n".join(
            f"[{item['node']}] {item['detail']}" for item in state["trace"]
        )
        st.markdown(f'<div class="trace">{trace_text}</div>', unsafe_allow_html=True)
    else:
        st.caption("Trace sẽ xuất hiện sau khi bạn chạy tìm kiếm.")

st.markdown(
    '<p class="muted" style="text-align:center;margin-top:40px;">RentalFlow · Demo LangGraph · Dữ liệu deterministic cho mục đích học tập</p>',
    unsafe_allow_html=True,
)
