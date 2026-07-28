#!/usr/bin/env python3
"""Tạo goodreads_books_clean.csv từ goodreads_books_raw.csv."""

import csv
import re
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parent
INPUT_FILE = DATA_DIR / "goodreads_books_raw.csv"
OUTPUT_FILE = DATA_DIR / "goodreads_books_clean.csv"

GENRE_BOILERPLATE = [
    "Art", "Biography", "Business", "Children's", "Christian", "Classics",
    "Comics", "Cookbooks", "Ebooks", "Fantasy", "Fiction", "Graphic Novels",
    "Historical Fiction", "History", "Horror", "Memoir", "Music", "Mystery",
    "Nonfiction", "Poetry", "Psychology", "Romance", "Science",
    "Science Fiction", "Self Help", "Sports", "Thriller", "Travel",
    "Young Adult",
]


def clean_text(value):
    return re.sub(r"\s+", " ", value or "").strip()


def clean_genres(value):
    genres = [clean_text(item) for item in (value or "").split(",")]
    genres = [item for item in genres if item]

    prefix_size = len(GENRE_BOILERPLATE)
    while genres[:prefix_size] == GENRE_BOILERPLATE:
        genres = genres[prefix_size:]

    result = []
    seen = set()
    for genre in genres:
        key = genre.casefold()
        if key not in seen:
            seen.add(key)
            result.append(genre)
    return "|".join(result)


def clean_number(value, positive=False):
    value = clean_text(value)
    if not value:
        return ""
    try:
        number = float(value)
    except ValueError:
        return ""
    if positive and number <= 0:
        return ""
    return str(int(number)) if number.is_integer() else format(number, "g")


def main():
    with INPUT_FILE.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        fieldnames = [name for name in reader.fieldnames if name]
        rows = []
        seen_book_ids = set()

        for raw in reader:
            row = {
                key: clean_text(value)
                for key, value in raw.items()
                if key
            }

            if not row.get("title") or not row.get("author"):
                continue

            book_id = row.get("bookId")
            if book_id and book_id in seen_book_ids:
                continue
            if book_id:
                seen_book_ids.add(book_id)

            row["genres"] = clean_genres(row.get("genres"))
            row["num_pages"] = clean_number(row.get("num_pages"), positive=True)
            row["avg_rating"] = clean_number(row.get("avg_rating"))

            for field in (
                "num_ratings", "num_reviews", "rated_1", "rated_2",
                "rated_3", "rated_4", "rated_5",
            ):
                row[field] = clean_number(row.get(field))

            rows.append(row)

    with OUTPUT_FILE.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Đã tạo {OUTPUT_FILE.name}: {len(rows)} dòng")


if __name__ == "__main__":
    main()
