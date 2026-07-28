```python
"""
🛠️ TOOL REGISTRY & SCHEMAS
(Dành cho Role 2: Tool & Spec Engineer)

Nơi khai báo tất cả các "món đồ nghề" mà ReAct Agent có thể gọi.

Gift Recommendation Pipeline:

Câu mô tả người dùng
        ↓
1. extract_recipient_profile
        ↓
2. analyze_recipient_profile
        ↓
3. generate_gift_candidates
        ↓
4. explain_recommendations
"""

from typing import Any, Dict, List


def extract_recipient_profile(
    user_description: str
) -> Dict[str, Any]:
    ...


def analyze_recipient_profile(
    recipient_profile: Dict[str, Any]
) -> Dict[str, Any]:
    ...


def generate_gift_candidates(
    recipient_profile: Dict[str, Any],
    profile_analysis: Dict[str, Any],
    max_candidates: int = 10
) -> List[Dict[str, Any]]:
    ...


def explain_recommendations(
    recipient_profile: Dict[str, Any],
    profile_analysis: Dict[str, Any],
    gift_candidates: List[Dict[str, Any]],
    top_k: int = 5
) -> Dict[str, Any]:
    ...


# Danh sách các tool được đăng ký để ReAct Agent sử dụng
AVAILABLE_TOOLS = {
    "extract_recipient_profile": extract_recipient_profile,
    "analyze_recipient_profile": analyze_recipient_profile,
    "generate_gift_candidates": generate_gift_candidates,
    "explain_recommendations": explain_recommendations,
}
```
