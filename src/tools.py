"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool & Spec Engineer)
Nơi khai báo tất cả các "món đồ nghề" mà ReAct Agent có thể gọi.
"""

import json
import uuid
from pathlib import Path
from langchain_core.tools import tool

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_FILE = BASE_DIR / "config" / "movies_cache.json"
def load_movies():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
def save_movies(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
        
        
@tool
def search_theater(location: str):
    """
    Tìm rạp CGV theo tên hoặc khu vực.
    """
    movies = load_movies()
    cinemas = set()
    for movie in movies:
        for show in movie["showtimes"]:
            cinema = show["cinema"]
            if location.lower() in cinema.lower():
                cinemas.add(cinema)
    return sorted(list(cinemas))

@tool
def search_movie(movie_name: str):
    """
    Tìm thông tin phim.
    """
    movies = load_movies()
    for movie in movies:
        if movie_name.lower() in movie["film_name"].lower():
            return {
                "film_name": movie["film_name"],
                "genre": movie["genre"],
                "duration": movie["duration_min"],
                "rating": movie["rating"],
                "poster": movie["poster_path"],
                "synopsis": movie["synopsis"]
            }
    return "Không tìm thấy phim."

@tool
def search_showtime(
    movie_name: str,
    cinema: str,
    date: str
):
    """
    Tìm suất chiếu.
    """
    movies = load_movies()
    result = []
    for movie in movies:
        if movie_name.lower() not in movie["film_name"].lower():
            continue
        for show in movie["showtimes"]:
            if (
                cinema.lower() in show["cinema"].lower()
                and show["date"] == date
            ):
                result.append(
                    {
                        "time": show["time"],
                        "seats_available": show["seats_available"]
                    }
                )
    return result

@tool
def get_available_seats(
    movie_name: str,
    cinema: str,
    date: str,
    time: str
):
    """
    Lấy danh sách ghế còn trống.
    """
    movies = load_movies()
    for movie in movies:
        if movie_name.lower() not in movie["film_name"].lower():
            continue
        for show in movie["showtimes"]:
            if (
                show["cinema"] == cinema
                and show["date"] == date
                and show["time"] == time
            ):
                seat_map = show["seat_map"]
                if seat_map is None:
                    return []
                booked = set(seat_map["booked_seats"])
                available = []
                for row in seat_map["rows"]:
                    for col in range(
                        1,
                        seat_map["cols_per_row"] + 1
                    ):
                        seat = f"{row}{col}"

                        if seat not in booked:
                            available.append(seat)
                return available
    return []

@tool
def book_seats(
    movie_name: str,
    cinema: str,
    date: str,
    time: str,
    seats: list[str],
    customer_name: str
):
    """
    Đặt ghế.
    """
    movies = load_movies()
    for movie in movies:
        if movie_name.lower() not in movie["film_name"].lower():
            continue
        for show in movie["showtimes"]:
            if (
                show["cinema"] == cinema
                and show["date"] == date
                and show["time"] == time
            ):
                seat_map = show["seat_map"]
                if seat_map is None:
                    return {
                        "status": "FAILED",
                        "message": "Không có sơ đồ ghế."
                    }
                booked = seat_map["booked_seats"]
                for seat in seats:
                    if seat in booked:
                        return {
                            "status": "FAILED",
                            "message": f"Ghế {seat} đã được đặt."
                        }
                booked.extend(seats)
                show["seats_available"] -= len(seats)
                save_movies(movies)
                booking_id = str(uuid.uuid4())
                return {
                    "status": "SUCCESS",
                    "booking_id": booking_id,
                    "customer": customer_name,
                    "movie": movie["film_name"],
                    "cinema": cinema,
                    "date": date,
                    "time": time,
                    "seats": seats
                }
    return {
        "status": "FAILED",
        "message": "Không tìm thấy suất chiếu."
    }
    
@tool
def generate_ticket(
    booking_id: str,
    customer_name: str,
    movie_name: str,
    cinema: str,
    date: str,
    time: str,
    seats: list[str]
):
    """
    Sinh vé điện tử.
    """
    ticket_id = f"CGV-{uuid.uuid4().hex[:8].upper()}"
    return {
        "ticket_id": ticket_id,
        "booking_id": booking_id,
        "customer": customer_name,
        "movie": movie_name,
        "cinema": cinema,
        "date": date,
        "time": time,
        "seats": seats,
        "status": "CONFIRMED"
    }

# Danh sách các tool được đăng ký để Agent sử dụng
AVAILABLE_TOOLS = [
    search_theater,
    search_movie,
    search_showtime,
    get_available_seats,
    book_seats,
    generate_ticket
]





if __name__ == "__main__":
    print(
        search_movie.invoke(
        {
            "movie_name": "Conan"
        }
        )
    )
    print(
        search_theater.invoke(
            {
                "location": "Bà Triệu"
            }
        )
    )
    print(
        get_available_seats.invoke(
            {
                "movie_name": "Conan",
                "cinema": "CGV Vincom Bà Triệu",
                "date": "2026-07-28",
                "time": "19:00"
            }
        )
    )
    booking = book_seats.invoke(
        {
            "movie_name": "Conan",
            "cinema": "CGV Vincom Bà Triệu",
            "date": "2026-07-28",
            "time": "19:00",
            "seats": ["A1", "A2"],
            "customer_name": "Trường"
        }
    )
    print(booking)

    if booking.get("status") == "SUCCESS":
        ticket = generate_ticket.invoke(
            {
                "booking_id": booking["booking_id"],
                "customer_name": booking["customer"],
                "movie_name": booking["movie"],
                "cinema": booking["cinema"],
                "date": booking["date"],
                "time": booking["time"],
                "seats": booking["seats"]
            }
        )
        print(ticket)
    else:
        print("Ticket generation skipped because booking failed.")
