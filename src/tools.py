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


# Danh sách công cụ sẵn sàng phục vụ ReAct Agent
AVAILABLE_TOOLS = {
    "calculate_compatibility": calculate_compatibility,
    "search_candidates": search_candidates
}

__all__ = [
    "calculate_compatibility",
    "search_candidates",
    "AVAILABLE_TOOLS",
    "UserProfile",
    "CompatibilityResult",
    "CandidateMatch",
    "SearchResponse",
    "MOCK_CANDIDATE_DB"
]
