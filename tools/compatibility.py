"""
🛠️ TOOL 1: CALCULATE COMPATIBILITY (`tools/compatibility.py`)
Đánh giá độ tương thích giữa 2 hồ sơ người dùng dựa trên ma trận trọng số (Thang điểm 100).
"""

import math
import re
from typing import List, Dict, Optional, Union
from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    id: str = Field(..., description="Mã định danh duy nhất")
    name: str = Field(..., description="Tên người dùng")
    phone: str = Field(..., description="Số điện thoại")
    gender: str = Field(..., description="Nam / Nữ / Khác")
    age: int = Field(..., description="Tuổi")
    location: str = Field(..., description="Tỉnh / Thành phố")
    height_cm: int = Field(..., description="Chiều cao tính theo cm")
    education: str = Field(..., description="Trình độ học vấn (VD: Đại học, Thạc sĩ...)")
    occupation: str = Field(..., description="Nghề nghiệp hiện tại")
    interests: str = Field(..., description="Mô tả chi tiết sở thích, lối sống")


class CompatibilityResult(BaseModel):
    total_score: float = Field(..., description="Tổng điểm tương thích từ 0 - 100")
    breakdown: dict = Field(..., description="Chi tiết điểm số từng tiêu chí")
    strengths: List[str] = Field(..., description="Các điểm hợp nhau nhất")
    weaknesses: List[str] = Field(..., description="Các điểm chưa đồng điệu")
    summary: str = Field(..., description="Đánh giá ngắn gọn 2-3 câu từ AI Matchmaker")


# Helper Vector Similarity (Cos Similarity with TF-IDF / Embedding fallback)
def calculate_text_similarity(text1: str, text2: str) -> float:
    """
    Tính Cosine Similarity giữa 2 văn bản sở thích.
    Sử dụng sentence-transformers nếu có, fallback sang Vectorizer chuẩn.
    """
    if not text1 or not text2:
        return 0.0
    
    try:
        from sentence_transformers import SentenceTransformer, util
        # Load small model if available
        model = SentenceTransformer('all-MiniLM-L6-v2')
        emb1 = model.encode(text1, convert_to_tensor=True)
        emb2 = model.encode(text2, convert_to_tensor=True)
        sim = float(util.cos_sim(emb1, emb2)[0][0])
        return max(0.0, min(1.0, sim))
    except Exception:
        # Fallback Vectorizer using Word Frequency (TF/Bag-of-Words Cosine Sim)
        def tokenize(text: str) -> List[str]:
            words = re.findall(r'\w+', text.lower())
            return [w for w in words if len(w) > 1]
        
        words1 = tokenize(text1)
        words2 = tokenize(text2)
        
        vocab = list(set(words1 + words2))
        if not vocab:
            return 0.0
        
        v1 = [words1.count(w) for w in vocab]
        v2 = [words2.count(w) for w in vocab]
        
        dot_product = sum(a * b for a, b in zip(v1, v2))
        mag1 = math.sqrt(sum(a * a for a in v1))
        mag2 = math.sqrt(sum(b * b for b in v2))
        
        if mag1 == 0 or mag2 == 0:
            return 0.0
        
        # Add a small semantic boost for keyword matches
        sim = dot_product / (mag1 * mag2)
        return max(0.1, min(1.0, sim))


NORTH_REGION = ["hà nội", "ha noi", "bắc ninh", "bắc giang", "hải phòng", "quảng ninh", "hải dương", "hưng yên", "vĩnh phúc", "thái nguyên"]
SOUTH_REGION = ["tp.hcm", "tphcm", "hồ chí minh", "bình dương", "đồng nai", "bà rịa", "vũng tàu", "long an", "cần thơ"]
CENTRAL_REGION = ["đà nẵng", "da nang", "huế", "quảng nam", "quảng ngãi", "nha trang", "khánh hòa", "bình định"]

def get_region(loc: str) -> str:
    loc_l = loc.lower()
    for r in NORTH_REGION:
        if r in loc_l:
            return "NORTH"
    for r in SOUTH_REGION:
        if r in loc_l:
            return "SOUTH"
    for r in CENTRAL_REGION:
        if r in loc_l:
            return "CENTRAL"
    return "OTHER"


def calculate_compatibility(person_a: Union[dict, UserProfile], person_b: Union[dict, UserProfile]) -> dict:
    """
    Tính toán điểm tương thích toàn diện giữa Person A và Person B (Thang điểm 100).
    
    Args:
        person_a (dict hoặc UserProfile): Hồ sơ người thứ nhất
        person_b (dict hoặc UserProfile): Hồ sơ người thứ hai
        
    Returns:
        dict: CompatibilityResult dạng dictionary
    """
    try:
        if isinstance(person_a, dict):
            pa = UserProfile(**person_a)
        else:
            pa = person_a
            
        if isinstance(person_b, dict):
            pb = UserProfile(**person_b)
        else:
            pb = person_b

        breakdown = {}
        strengths = []
        weaknesses = []

        # 1. HARD FILTER (Giới tính & Định hướng)
        # Giả định ghép đôi Nam - Nữ tiêu chuẩn trừ khi trùng giới tính
        g1, g2 = pa.gender.strip().lower(), pb.gender.strip().lower()
        if g1 == g2 and g1 in ["nam", "nữ"]:
            res = CompatibilityResult(
                total_score=0.0,
                breakdown={"hard_filter": 0, "location": 0, "age_height": 0, "interests": 0, "edu_occ": 0},
                strengths=[],
                weaknesses=["Giới tính / Định hướng ghép đôi không trùng khớp trong thiết lập mặc định"],
                summary=f"Hồ sơ của {pa.name} và {pb.name} không thỏa mãn điều kiện ghép đôi giới tính cơ bản."
            )
            return res.model_dump()

        # 2. VỊ TRÍ ĐỊA LÝ (Tối đa 20 điểm)
        loc_a, loc_b = pa.location.strip().lower(), pb.location.strip().lower()
        if loc_a == loc_b or loc_a in loc_b or loc_b in loc_a:
            loc_score = 20.0
            strengths.append(f"Cùng sống tại {pa.location}, thuận tiện hẹn hò")
        elif get_region(loc_a) == get_region(loc_b) and get_region(loc_a) != "OTHER":
            loc_score = 10.0
            strengths.append(f"Cùng vùng miền ({pa.location} - {pb.location})")
        else:
            loc_score = 0.0
            weaknesses.append(f"Khoảng cách địa lý ({pa.location} vs {pb.location}) có thể gây khó khăn")
        breakdown["location_score"] = loc_score

        # 3. ĐỘ TUỔI & CHIỀU CAO (Tối đa 20 điểm)
        age_diff = abs(pa.age - pb.age)
        if age_diff <= 3:
            age_score = 10.0
            strengths.append(f"Độ tuổi rất hợp nhau (chênh lệch {age_diff} tuổi)")
        elif age_diff <= 6:
            age_score = 6.0
        else:
            age_score = 2.0
            weaknesses.append(f"Độ tuổi chênh lệch hơi nhiều ({age_diff} tuổi)")

        # Chiều cao
        if g1 == "nam" and g2 == "nữ":
            h_diff = pa.height_cm - pb.height_cm
        elif g1 == "nữ" and g2 == "nam":
            h_diff = pb.height_cm - pa.height_cm
        else:
            h_diff = abs(pa.height_cm - pb.height_cm)

        if 5 <= h_diff <= 20:
            h_score = 10.0
            strengths.append("Tỷ lệ chiều cao chuẩn lý tưởng")
        else:
            h_score = 3.0
            if h_diff < 0:
                weaknesses.append("Chiều cao bạn Nữ cao hơn Nam")

        age_height_score = age_score + h_score
        breakdown["age_height_score"] = age_height_score

        # 4. SỞ THÍCH (Tối đa 40 điểm - Vector Embedding)
        similarity = calculate_text_similarity(pa.interests, pb.interests)
        interests_score = round(similarity * 40.0, 1)
        breakdown["interests_score"] = interests_score
        
        if interests_score >= 25.0:
            strengths.append("Sở thích và lối sống có nhiều điểm chung đồng điệu")
        else:
            weaknesses.append("Sở thích và gu sống có sự khác biệt")

        # 5. HỌC VẤN & NGHỀ NGHIỆP (Tối đa 20 điểm)
        edu_a, edu_b = pa.education.lower(), pb.education.lower()
        occ_a, occ_b = pa.occupation.lower(), pb.occupation.lower()

        edu_score = 10.0 if edu_a == edu_b or ("đại học" in edu_a and "đại học" in edu_b) else 5.0
        
        # Check complementary jobs
        tech_words = ["lập trình", "dev", "it", "kỹ sư", "data", "công nghệ"]
        creative_words = ["thiết kế", "design", "marketing", "content", "nghệ thuật"]
        
        is_occ_matching = False
        if any(w in occ_a for w in tech_words) and any(w in occ_b for w in creative_words):
            is_occ_matching = True
        elif any(w in occ_b for w in tech_words) and any(w in occ_a for w in creative_words):
            is_occ_matching = True
        elif occ_a == occ_b:
            is_occ_matching = True

        occ_score = 10.0 if is_occ_matching else 5.0
        edu_occ_score = edu_score + occ_score
        breakdown["edu_occ_score"] = edu_occ_score

        if is_occ_matching:
            strengths.append(f"Ngành nghề bổ trợ/tương đồng ({pa.occupation} & {pb.occupation})")

        # TỔNG ĐIỂM
        total_score = round(loc_score + age_height_score + interests_score + edu_occ_score, 1)

        # SUMMARY
        if total_score >= 85:
            summary = f"Cặp đôi vàng! {pa.name} và {pb.name} có độ tương thích cực cao ({total_score}/100). Hai bạn vô cùng hòa hợp về vị trí, lối sống và quan điểm!"
        elif total_score >= 65:
            summary = f"Mối duyên tiềm năng! {pa.name} và {pb.name} đạt {total_score}/100 điểm tương thích. Dù có một vài điểm khác biệt nhỏ nhưng hoàn toàn có thể tìm hiểu lâu dài."
        else:
            summary = f"Cần nhiều nỗ lực thấu hiểu. {pa.name} và {pb.name} đạt {total_score}/100 điểm tương thích. Hai bạn có phong cách sống và tiêu chí khá khác biệt."

        result = CompatibilityResult(
            total_score=total_score,
            breakdown=breakdown,
            strengths=strengths,
            weaknesses=weaknesses,
            summary=summary
        )
        return result.model_dump()

    except Exception as e:
        return {
            "total_score": 0.0,
            "error": f"Lỗi tính toán tương thích: {str(e)}",
            "breakdown": {},
            "strengths": [],
            "weaknesses": [str(e)],
            "summary": "Không thể tính toán do dữ liệu không hợp lệ."
        }


if __name__ == "__main__":
    p1 = {
        "id": "U001", "name": "Nguyễn Văn Hoàng", "phone": "0912345678", "gender": "Nam",
        "age": 26, "location": "Hà Nội", "height_cm": 175, "education": "Đại học",
        "occupation": "Lập trình viên Software", "interests": "Thích đi phượt, đọc sách công nghệ, chơi guitar, cà phê cuối tuần"
    }
    p2 = {
        "id": "U002", "name": "Trần Thu Hà", "phone": "0987654321", "gender": "Nữ",
        "age": 24, "location": "Hà Nội", "height_cm": 162, "education": "Đại học",
        "occupation": "UI/UX Designer", "interests": "Thích vẽ tranh, nghe nhạc indie, đi du lịch trải nghiệm, uống cà phê"
    }
    res = calculate_compatibility(p1, p2)
    print("Compatibility Test Result:")
    print(res)
