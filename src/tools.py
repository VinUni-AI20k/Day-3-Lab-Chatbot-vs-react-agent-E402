"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool & Spec Engineer)
Khai báo và xuất các công cụ (Tools) cho AI Matchmaking Agent.
"""

import sys
import os
import importlib.util

# Đường dẫn thư mục gốc dự án
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Load compatibility module dynamically
comp_path = os.path.join(root_dir, "tools", "compatibility.py")
spec_comp = importlib.util.spec_from_file_location("tools_compatibility_module", comp_path)
comp_mod = importlib.util.module_from_spec(spec_comp)
spec_comp.loader.exec_module(comp_mod)

calculate_compatibility = comp_mod.calculate_compatibility
UserProfile = comp_mod.UserProfile
CompatibilityResult = comp_mod.CompatibilityResult

# Load search module dynamically
search_path = os.path.join(root_dir, "tools", "search.py")
spec_search = importlib.util.spec_from_file_location("tools_search_module", search_path)
srch_mod = importlib.util.module_from_spec(spec_search)
spec_search.loader.exec_module(srch_mod)

search_candidates = srch_mod.search_candidates
CandidateMatch = srch_mod.CandidateMatch
SearchResponse = srch_mod.SearchResponse
MOCK_CANDIDATE_DB = srch_mod.MOCK_CANDIDATE_DB


def get_weather(location: str) -> str:
    """
    Tra cứu thời tiết hiện tại của một thành phố.
    
    Args:
        location (str): Tên thành phố (Ví dụ: 'Hà Nội', 'TP.HCM', 'Đà Nẵng')
        
    Returns:
        str: Thông tin thời tiết chi tiết
    """
    loc_lower = location.lower()
    if "hà nội" in loc_lower or "ha noi" in loc_lower:
        return "Thời tiết Hà Nội: 28°C, Nắng nhẹ, Độ ẩm 65%."
    elif "hồ chí minh" in loc_lower or "tp.hcm" in loc_lower or "hcm" in loc_lower:
        return "Thời tiết TP.HCM: 33°C, Nắng nóng, Có mây."
    elif "đà nẵng" in loc_lower or "da nang" in loc_lower:
        return "Thời tiết Đà Nẵng: 30°C, Gió nhẹ, Mát mẻ."
    else:
        return f"LỖI: Không tìm thấy dữ liệu thời tiết cho địa điểm '{location}'."


# Danh sách công cụ sẵn sàng phục vụ ReAct Agent
AVAILABLE_TOOLS = {
    "calculate_compatibility": calculate_compatibility,
    "search_candidates": search_candidates,
    "get_weather": get_weather
}

__all__ = [
    "calculate_compatibility",
    "search_candidates",
    "get_weather",
    "AVAILABLE_TOOLS",
    "UserProfile",
    "CompatibilityResult",
    "CandidateMatch",
    "SearchResponse",
    "MOCK_CANDIDATE_DB"
]
