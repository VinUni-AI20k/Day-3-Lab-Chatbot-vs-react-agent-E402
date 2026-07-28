"""
🛠️ TOOL 2: SEARCH CANDIDATES (`tools/search.py`)
Tìm kiếm top K người phù hợp từ Mock Database bằng Hybrid Search (Hard Filter + Semantic Vector Search).
Tích hợp Guardrails: Masking PII & Relaxed Search khi không tìm thấy kết quả.
"""

import os
import sys
import importlib.util
from typing import List, Optional, Dict, Union
from pydantic import BaseModel, Field

# Dynamic import compatibility module without name collision
curr_dir = os.path.dirname(os.path.abspath(__file__))
comp_path = os.path.join(curr_dir, "compatibility.py")

spec = importlib.util.spec_from_file_location("tools_compatibility_mod", comp_path)
comp_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(comp_mod)

calculate_text_similarity = comp_mod.calculate_text_similarity
UserProfile = comp_mod.UserProfile


# Structured Output Models
class CandidateMatch(BaseModel):
    id: str
    masked_name: str
    masked_phone: str
    gender: str
    age: int
    location: str
    height_cm: int
    education: str
    occupation: str
    interests_highlight: str
    match_score: float


class SearchResponse(BaseModel):
    candidates: List[CandidateMatch]
    total_found: int
    is_relaxed_search: bool
    note: Optional[str] = None


# 🏢 MOCK DATABASE (18 Hồ sơ ứng viên đa dạng)
MOCK_CANDIDATE_DB: List[Dict] = [
    {
        "id": "C001", "name": "Nguyễn Văn Tuấn", "phone": "0912345678", "gender": "Nam",
        "age": 27, "location": "Hà Nội", "height_cm": 176, "education": "Đại học",
        "occupation": "Kỹ sư Phần mềm", "interests": "Đam mê công nghệ, chơi guitar, thích du lịch phượt và cà phê bệt"
    },
    {
        "id": "C002", "name": "Trần Thị Ngọc Bích", "phone": "0987654321", "gender": "Nữ",
        "age": 25, "location": "Hà Nội", "height_cm": 163, "education": "Thạc sĩ",
        "occupation": "UI/UX Designer", "interests": "Yêu nghệ thuật, vẽ tranh canvas, nghe nhạc indie, chụp ảnh film"
    },
    {
        "id": "C003", "name": "Lê Hoàng Minh", "phone": "0934567890", "gender": "Nam",
        "age": 29, "location": "TP.HCM", "height_cm": 180, "education": "Đại học",
        "occupation": "Quản lý Marketing", "interests": "Thích tập gym, chạy bộ Marathon, đọc sách kinh doanh, mê ẩm thực đường phố"
    },
    {
        "id": "C004", "name": "Phạm Mai Anh", "phone": "0901234567", "gender": "Nữ",
        "age": 24, "location": "TP.HCM", "height_cm": 160, "education": "Đại học",
        "occupation": "Content Creator", "interests": "Viết lách, làm vlog du lịch, yêu mèo, thích nấu ăn và làm bánh ngọt"
    },
    {
        "id": "C005", "name": "Đỗ Quang Hùng", "phone": "0978123456", "gender": "Nam",
        "age": 31, "location": "Đà Nẵng", "height_cm": 174, "education": "Đại học",
        "occupation": "Kiến trúc sư", "interests": "Đam mê thiết kế không gian sống, thích đi biển, lướt sóng và uống trà chiều"
    },
    {
        "id": "C006", "name": "Vũ Khánh Linh", "phone": "0965432187", "gender": "Nữ",
        "age": 26, "location": "Hà Nội", "height_cm": 165, "education": "Đại học",
        "occupation": "Chuyên viên HR", "interests": "Thích giao tiếp, tổ chức sự kiện, đi pilates, nghe podcast tâm lý học"
    },
    {
        "id": "C007", "name": "Hoàng Đức Anh", "phone": "0923456789", "gender": "Nam",
        "age": 25, "location": "Hà Nội", "height_cm": 178, "education": "Đại học",
        "occupation": "Data Analyst", "interests": "Thích phân tích dữ liệu, chơi cờ vua, đá bóng cuối tuần, xem phim trinh thám"
    },
    {
        "id": "C008", "name": "Ngô Thùy Trang", "phone": "0945678901", "gender": "Nữ",
        "age": 27, "location": "TP.HCM", "height_cm": 167, "education": "Đại học",
        "occupation": "Chuyên viên Tài chính", "interests": "Đầu tư tài chính, đi du lịch nghỉ dưỡng, yoga mỗi sáng, thưởng thức rượu vang"
    },
    {
        "id": "C009", "name": "Bùi Văn Nam", "phone": "0918273645", "gender": "Nam",
        "age": 28, "location": "Hà Nội", "height_cm": 172, "education": "Đại học",
        "occupation": "Nhiếp ảnh gia", "interests": "Đam mê nhiếp ảnh, thích khám phá góc phố cổ Hà Nội, uống cà phê trứng, du lịch tự túc"
    },
    {
        "id": "C010", "name": "Đặng Phương Thảo", "phone": "0981928374", "gender": "Nữ",
        "age": 23, "location": "Hà Nội", "height_cm": 161, "education": "Cử nhân",
        "occupation": "Giáo viên Tiếng Anh", "interests": "Yêu trẻ em, học ngôn ngữ mới, xem phim hoạt hình Ghibli, làm đồ thủ công handmade"
    },
    {
        "id": "C011", "name": "Dương Quốc Bảo", "phone": "0938475612", "gender": "Nam",
        "age": 30, "location": "TP.HCM", "height_cm": 182, "education": "Thạc sĩ",
        "occupation": "Bác sĩ Đa khoa", "interests": "Chăm sóc sức khỏe, đọc sách y khoa, chơi tennis, yêu thích hòa nhạc cổ điển"
    },
    {
        "id": "C012", "name": "Nguyễn Minh Châu", "phone": "0909182736", "gender": "Nữ",
        "age": 28, "location": "Đà Nẵng", "height_cm": 164, "education": "Đại học",
        "occupation": "Quản lý Khách sạn", "interests": "Yêu biển, thích học pha chế cocktail, khiêu vũ Latin, du lịch châu Âu"
    },
    {
        "id": "C013", "name": "Trịnh Hải Đăng", "phone": "0977665544", "gender": "Nam",
        "age": 26, "location": "Bắc Ninh", "height_cm": 175, "education": "Đại học",
        "occupation": "Kỹ sư Điện tử", "interests": "Mê mẩn đồ công nghệ thông minh, nuôi chó Corgi, thích cắm trại dã ngoại"
    },
    {
        "id": "C014", "name": "Lương Thanh Hà", "phone": "0911223344", "gender": "Nữ",
        "age": 29, "location": "Hải Phòng", "height_cm": 166, "education": "Đại học",
        "occupation": "Luật sư", "interests": "Công lý, đọc sách triết học, thiền định, thích uống trà ô long và đi dạo"
    },
    {
        "id": "C015", "name": "Phan Việt Cường", "phone": "0944556677", "gender": "Nam",
        "age": 32, "location": "Cần Thơ", "height_cm": 177, "education": "Thạc sĩ",
        "occupation": "Chủ doanh nghiệp nông nghiệp", "interests": "Yêu thiên nhiên, trồng cây ăn quả, bảo vệ môi trường, nấu ăn món miền Tây"
    }
]


# 🛡️ PRIVACY MASKING HELPER
def mask_phone_number(phone: str) -> str:
    """Mask SĐT: '0912345678' -> '0912***678'"""
    clean_p = str(phone).strip()
    if len(clean_p) >= 10:
        return f"{clean_p[:4]}***{clean_p[-3:]}"
    elif len(clean_p) >= 7:
        return f"{clean_p[:3]}***{clean_p[-2:]}"
    return "09** *** ***"


def mask_full_name(name: str) -> str:
    """Mask Họ tên: 'Nguyễn Văn Tuấn' -> 'Văn Tuấn' hoặc 'Anh V.T'"""
    parts = name.strip().split()
    if len(parts) >= 3:
        return f"{parts[-2]} {parts[-1]}"
    elif len(parts) == 2:
        return parts[1]
    return name


def search_candidates(
    target_gender: str,
    min_age: int = 18,
    max_age: int = 60,
    location: str = "",
    query_interests: str = "",
    top_k: int = 5
) -> dict:
    """
    Tìm kiếm ứng viên phù hợp dựa trên tiêu chí Hard Filter và Vector Search sở thích.
    """
    try:
        gender_req = target_gender.strip().lower() if target_gender else ""
        loc_req = location.strip().lower() if location else ""
        
        # 1. HARD FILTER
        filtered_candidates = []
        for c in MOCK_CANDIDATE_DB:
            if gender_req and c["gender"].lower() != gender_req:
                continue
            if not (min_age <= c["age"] <= max_age):
                continue
            if loc_req and loc_req not in c["location"].lower() and c["location"].lower() not in loc_req:
                continue
            
            filtered_candidates.append(c)

        is_relaxed = False
        note = None

        # 2. EMPTY RESULTS GUARDRAIL (RELAXED SEARCH)
        if not filtered_candidates:
            is_relaxed = True
            note = f"Không tìm thấy ứng viên thỏa mãn chính xác tiêu chí ({target_gender}, {min_age}-{max_age} tuổi, vị trí: {location}). Đã tự động nới lỏng bán kính vị trí và độ tuổi để gợi ý ứng viên tiềm năng!"
            
            for c in MOCK_CANDIDATE_DB:
                if gender_req and c["gender"].lower() != gender_req:
                    continue
                if not (max(18, min_age - 5) <= c["age"] <= max_age + 5):
                    continue
                filtered_candidates.append(c)

        if not filtered_candidates:
            return SearchResponse(
                candidates=[],
                total_found=0,
                is_relaxed_search=True,
                note="Hệ thống chưa tìm thấy ứng viên phù hợp trong cơ sở dữ liệu."
            ).model_dump()

        # 3. HYBRID SEMANTIC RANKING
        scored_list = []
        for c in filtered_candidates:
            if query_interests:
                sim = calculate_text_similarity(query_interests, c["interests"])
                loc_bonus = 0.2 if (loc_req and loc_req in c["location"].lower()) else 0.0
                match_score = round(min(100.0, (sim * 80.0 + loc_bonus * 20.0 + 10.0)), 1)
            else:
                match_score = 75.0
            
            scored_list.append((match_score, c))

        scored_list.sort(key=lambda x: x[0], reverse=True)
        top_candidates = scored_list[:top_k]
        
        matches = []
        for score, c in top_candidates:
            match_obj = CandidateMatch(
                id=c["id"],
                masked_name=mask_full_name(c["name"]),
                masked_phone=mask_phone_number(c["phone"]),
                gender=c["gender"],
                age=c["age"],
                location=c["location"],
                height_cm=c["height_cm"],
                education=c["education"],
                occupation=c["occupation"],
                interests_highlight=c["interests"],
                match_score=score
            )
            matches.append(match_obj)

        res = SearchResponse(
            candidates=matches,
            total_found=len(matches),
            is_relaxed_search=is_relaxed,
            note=note
        )
        return res.model_dump()

    except Exception as e:
        return {
            "candidates": [],
            "total_found": 0,
            "is_relaxed_search": False,
            "note": f"Lỗi thực thi tìm kiếm: {str(e)}"
        }


if __name__ == "__main__":
    print("Test Search Candidates:")
    res = search_candidates(
        target_gender="Nữ",
        min_age=22,
        max_age=28,
        location="Hà Nội",
        query_interests="Thích nghe nhạc indie, vẽ tranh, uống cà phê"
    )
    print(res)
