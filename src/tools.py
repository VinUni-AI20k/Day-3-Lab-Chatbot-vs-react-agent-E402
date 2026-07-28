

"""
🛠️ TOOL REGISTRY & SCHEMAS
Chủ đề: CHATBOT ĐỊNH HƯỚNG SỰ NGHIỆP

File: src/tools.py

Mục tiêu:
- Thiết kế tool deterministic cho ReAct Agent.
- Tool có contract rõ ràng: input, output, error semantics, side effect.
- Không để tool crash khi nhập sai dữ liệu.
- Error nghiệp vụ trả về chuỗi "LỖI: ..." để Agent đọc và xử lý tiếp.
"""

import json
import re
from typing import Dict, List, Any


# ============================================================
# 📚 MOCK DATABASE
# ============================================================

CAREER_DB = {
    "ai_engineer": {
        "id": "ai_engineer",
        "name": "AI Engineer",
        "description": "Xây dựng, huấn luyện, triển khai và tối ưu các hệ thống AI/ML, LLM, chatbot và agent.",
        "tasks": [
            "Xây dựng mô hình Machine Learning",
            "Tích hợp LLM vào sản phẩm",
            "Thiết kế pipeline huấn luyện và đánh giá mô hình",
            "Triển khai mô hình lên production",
        ],
        "required_skills": [
            "Python",
            "Machine Learning",
            "Deep Learning",
            "LLM",
            "Prompt Engineering",
            "SQL",
            "MLOps",
        ],
        "salary_range": "Junior: 15-25tr | Middle: 25-45tr | Senior: 45-80tr VNĐ/tháng",
        "growth_outlook": "Rất cao do nhu cầu ứng dụng AI trong doanh nghiệp tăng mạnh.",
        "education": "Nên có nền tảng CNTT, Khoa học dữ liệu, Toán tin hoặc tự học qua dự án thực tế.",
        "riasec": {
            "R": 1,
            "I": 5,
            "A": 2,
            "S": 2,
            "E": 2,
            "C": 3,
        },
    },
    "data_engineer": {
        "id": "data_engineer",
        "name": "Data Engineer",
        "description": "Thiết kế, xây dựng và vận hành hệ thống dữ liệu, ETL/ELT pipeline, Data Warehouse/Lakehouse.",
        "tasks": [
            "Xây dựng pipeline xử lý dữ liệu",
            "Thiết kế Data Warehouse",
            "Tối ưu truy vấn SQL",
            "Đảm bảo chất lượng và độ tin cậy dữ liệu",
        ],
        "required_skills": [
            "SQL",
            "Python",
            "Airflow",
            "Spark",
            "Kafka",
            "ClickHouse",
            "Data Warehouse",
        ],
        "salary_range": "Junior: 12-20tr | Middle: 20-40tr | Senior: 40-70tr VNĐ/tháng",
        "growth_outlook": "Cao do doanh nghiệp ngày càng cần hạ tầng dữ liệu tốt để ra quyết định và ứng dụng AI.",
        "education": "Phù hợp với nền tảng CNTT, Hệ thống thông tin, Khoa học dữ liệu.",
        "riasec": {
            "R": 2,
            "I": 4,
            "A": 1,
            "S": 1,
            "E": 2,
            "C": 5,
        },
    },
    "backend_developer": {
        "id": "backend_developer",
        "name": "Backend Developer",
        "description": "Phát triển API, xử lý logic nghiệp vụ, làm việc với cơ sở dữ liệu và hệ thống phía server.",
        "tasks": [
            "Thiết kế REST API",
            "Xử lý logic nghiệp vụ",
            "Làm việc với database",
            "Tối ưu hiệu năng hệ thống",
        ],
        "required_skills": [
            "Java",
            "C#",
            "Python",
            "Go",
            "REST API",
            "Database",
            "Docker",
            "Microservices",
        ],
        "salary_range": "Junior: 10-18tr | Middle: 18-35tr | Senior: 35-60tr VNĐ/tháng",
        "growth_outlook": "Ổn định và cao vì hầu hết sản phẩm số đều cần backend.",
        "education": "Phù hợp với nền tảng CNTT, Kỹ thuật phần mềm hoặc tự học lập trình.",
        "riasec": {
            "R": 3,
            "I": 3,
            "A": 1,
            "S": 1,
            "E": 2,
            "C": 4,
        },
    },
    "business_analyst": {
        "id": "business_analyst",
        "name": "Business Analyst",
        "description": "Phân tích nghiệp vụ, làm cầu nối giữa khách hàng, người dùng và đội phát triển sản phẩm.",
        "tasks": [
            "Thu thập yêu cầu nghiệp vụ",
            "Viết tài liệu đặc tả",
            "Vẽ BPMN/UML",
            "Trao đổi với stakeholder",
        ],
        "required_skills": [
            "Requirement Analysis",
            "Communication",
            "BPMN",
            "UML",
            "SQL cơ bản",
            "Documentation",
        ],
        "salary_range": "Junior: 10-15tr | Middle: 15-30tr | Senior: 30-50tr VNĐ/tháng",
        "growth_outlook": "Tốt, đặc biệt trong công ty phần mềm, ERP, ngân hàng, bảo hiểm và chuyển đổi số.",
        "education": "Phù hợp với CNTT, Kinh tế, Quản trị kinh doanh hoặc người có tư duy hệ thống.",
        "riasec": {
            "R": 1,
            "I": 3,
            "A": 2,
            "S": 4,
            "E": 4,
            "C": 3,
        },
    },
    "ux_ui_designer": {
        "id": "ux_ui_designer",
        "name": "UX/UI Designer",
        "description": "Thiết kế trải nghiệm người dùng và giao diện cho website, mobile app, SaaS hoặc sản phẩm số.",
        "tasks": [
            "Nghiên cứu người dùng",
            "Thiết kế wireframe",
            "Thiết kế prototype",
            "Xây dựng design system",
        ],
        "required_skills": [
            "Figma",
            "Design Thinking",
            "User Research",
            "Prototyping",
            "Design System",
        ],
        "salary_range": "Junior: 8-15tr | Middle: 15-28tr | Senior: 28-45tr VNĐ/tháng",
        "growth_outlook": "Tốt nếu có portfolio mạnh và hiểu sâu về sản phẩm.",
        "education": "Phù hợp với thiết kế, mỹ thuật, truyền thông hoặc người yêu thích sáng tạo sản phẩm.",
        "riasec": {
            "R": 1,
            "I": 2,
            "A": 5,
            "S": 3,
            "E": 2,
            "C": 2,
        },
    },
}


JOB_MARKET_DB = {
    "ai_engineer": {
        "hà nội": "Hà Nội: Nhu cầu AI Engineer cao trong các công ty công nghệ, ngân hàng, ERP, chatbot, automation.",
        "tp.hcm": "TP.HCM: Nhiều cơ hội AI Engineer tại startup, product company và công ty có yếu tố nước ngoài.",
        "đà nẵng": "Đà Nẵng: Cơ hội AI Engineer ít hơn Hà Nội/TP.HCM nhưng phù hợp nếu làm remote hoặc outsourcing.",
    },
    "data_engineer": {
        "hà nội": "Hà Nội: Nhu cầu Data Engineer cao tại ngân hàng, viễn thông, ERP, thương mại điện tử.",
        "tp.hcm": "TP.HCM: Cơ hội Data Engineer nhiều trong fintech, retail, logistics, startup.",
        "đà nẵng": "Đà Nẵng: Có nhu cầu Data Engineer ở các công ty outsourcing và một số doanh nghiệp chuyển đổi số.",
    },
    "backend_developer": {
        "hà nội": "Hà Nội: Backend Developer có nhu cầu ổn định trong hầu hết công ty phần mềm.",
        "tp.hcm": "TP.HCM: Nhu cầu Backend Developer rất cao, nhiều lựa chọn startup và công ty quốc tế.",
        "đà nẵng": "Đà Nẵng: Backend Developer phù hợp với outsourcing, product nhỏ và remote job.",
    },
}


MENTOR_PROGRAM_DB = {
    "ai_engineer": {
        "hà nội": [
            "Cộng đồng Machine Learning Cơ Bản",
            "AI Vietnam",
            "Các chương trình AI/ML tại trường đại học và trung tâm công nghệ",
        ],
        "tp.hcm": [
            "AI Vietnam",
            "VietAI community",
            "Các workshop AI tại startup hub",
        ],
    },
    "data_engineer": {
        "hà nội": [
            "Cộng đồng Data Engineering Việt Nam",
            "Các khóa học Data Warehouse, Airflow, Spark",
        ],
        "tp.hcm": [
            "Data community tại TP.HCM",
            "Workshop về Analytics Engineering và Cloud Data",
        ],
    },
}


USER_PROFILE_STORE = {}


# ============================================================
# 🧩 HELPER FUNCTIONS
# ============================================================

def _safe_json(data: Any) -> str:
    """
    Chuyển dữ liệu Python sang JSON string an toàn, hỗ trợ tiếng Việt.
    """
    return json.dumps(data, ensure_ascii=False, indent=2)


def _normalize_text(text: str) -> str:
    """
    Chuẩn hóa text về lowercase và strip.
    """
    return str(text).strip().lower()


def _find_career_id(value: str) -> str:
    """
    Tìm career_id từ id hoặc tên nghề.
    """
    key = _normalize_text(value)

    for career_id, career in CAREER_DB.items():
        name = _normalize_text(career["name"])

        if key == career_id:
            return career_id

        if key == name:
            return career_id

        if key in name or name in key:
            return career_id

    return ""


# ============================================================
# 🔧 TOOLS
# ============================================================

def run_personality_assessment(answers: Dict[str, int]) -> str:
    """
    Chấm điểm trắc nghiệm định hướng nghề nghiệp theo rubric RIASEC self-built.

    Name:
        run_personality_assessment

    Purpose:
        Dùng khi người dùng trả lời bộ câu hỏi tính cách/sở thích.
        Không dùng để tra cứu thông tin nghề cụ thể.

    Input schema:
        answers (dict): Dictionary gồm các key thuộc R, I, A, S, E, C.
                        Giá trị là điểm từ 1 đến 5.
                        Ví dụ: {"R": 2, "I": 5, "A": 3, "S": 2, "E": 1, "C": 4}

    Output schema:
        str: JSON string chứa vector RIASEC, top_traits và holland_code.

    Error semantics:
        Nếu thiếu input, sai kiểu dữ liệu hoặc điểm ngoài 1-5 -> trả về "LỖI: ...".

    Side effect:
        Read-only, không thay đổi trạng thái.

    Example:
        >>> run_personality_assessment({"R": 2, "I": 5, "A": 3, "S": 2, "E": 1, "C": 4})
    """
    try:
        if not isinstance(answers, dict):
            return "LỖI: answers phải là dict. Ví dụ: {'R': 2, 'I': 5, 'A': 3, 'S': 2, 'E': 1, 'C': 4}."

        traits = ["R", "I", "A", "S", "E", "C"]
        vector = {}

        for trait in traits:
            score = answers.get(trait, 0)

            if not isinstance(score, int):
                return f"LỖI: Điểm của '{trait}' phải là số nguyên từ 1 đến 5."

            if score < 0 or score > 5:
                return f"LỖI: Điểm của '{trait}' phải nằm trong khoảng 0 đến 5."

            vector[trait] = score

        ranked = sorted(vector.items(), key=lambda x: x[1], reverse=True)
        holland_code = "".join([item[0] for item in ranked[:3]])

        result = {
            "profile_vector": vector,
            "top_traits": ranked[:3],
            "holland_code": holland_code,
            "note": "Vector này có thể dùng làm input cho match_profile_to_careers.",
        }

        return _safe_json(result)

    except Exception as e:
        return f"LỖI: Xảy ra lỗi khi chấm trắc nghiệm tính cách ({e})."


def extract_skills_from_cv(cv_text: str) -> str:
    """
    Trích xuất kỹ năng từ nội dung CV/portfolio.

    Name:
        extract_skills_from_cv

    Purpose:
        Dùng khi người dùng gửi nội dung CV dạng text.
        Không dùng khi người dùng chỉ hỏi thông tin nghề chung.

    Input schema:
        cv_text (str): Nội dung CV/portfolio dạng plain text.

    Output schema:
        str: JSON string gồm technical_skills, soft_skills, tools, languages.

    Error semantics:
        Nếu cv_text rỗng hoặc không phải string -> trả về "LỖI: ...".

    Side effect:
        Read-only.

    Example:
        >>> extract_skills_from_cv("Python, SQL, Airflow, teamwork")
    """
    try:
        if not isinstance(cv_text, str):
            return "LỖI: cv_text phải là chuỗi văn bản."

        text = cv_text.strip()
        if not text:
            return "LỖI: cv_text đang rỗng. Vui lòng cung cấp nội dung CV."

        lower = text.lower()

        skill_keywords = {
            "technical_skills": [
                "python",
                "sql",
                "machine learning",
                "deep learning",
                "java",
                "c#",
                "go",
                "spark",
                "airflow",
                "kafka",
                "clickhouse",
                "docker",
                "rest api",
            ],
            "soft_skills": [
                "communication",
                "teamwork",
                "problem solving",
                "leadership",
                "giao tiếp",
                "làm việc nhóm",
                "giải quyết vấn đề",
            ],
            "tools": [
                "figma",
                "jira",
                "git",
                "github",
                "gitlab",
                "power bi",
                "tableau",
                "excel",
            ],
            "languages": [
                "english",
                "tiếng anh",
                "japanese",
                "tiếng nhật",
                "korean",
                "tiếng hàn",
            ],
        }

        extracted = {}

        for group, keywords in skill_keywords.items():
            found = []
            for kw in keywords:
                if kw in lower:
                    found.append(kw)
            extracted[group] = sorted(list(set(found)))

        extracted["raw_skill_count"] = sum(len(v) for v in extracted.values())

        return _safe_json(extracted)

    except Exception as e:
        return f"LỖI: Xảy ra lỗi khi trích xuất kỹ năng từ CV ({e})."


def get_user_profile(user_id: str) -> str:
    """
    Đọc hồ sơ người dùng từ bộ nhớ giả lập.

    Name:
        get_user_profile

    Purpose:
        Dùng khi Agent cần biết thông tin đã lưu của người dùng.
        Không dùng nếu chưa có user_id.

    Input schema:
        user_id (str): ID người dùng.

    Output schema:
        str: JSON string chứa profile người dùng.

    Error semantics:
        Nếu user_id rỗng -> "LỖI: ...".
        Nếu chưa có profile -> trả profile mặc định.

    Side effect:
        Read-only.

    Example:
        >>> get_user_profile("user_001")
    """
    try:
        if not isinstance(user_id, str) or not user_id.strip():
            return "LỖI: user_id phải là chuỗi không rỗng."

        profile = USER_PROFILE_STORE.get(user_id, {
            "user_id": user_id,
            "interests": [],
            "expected_salary": None,
            "preferred_location": None,
            "avoid_industries": [],
            "skills": [],
            "profile_vector": None,
        })

        return _safe_json(profile)

    except Exception as e:
        return f"LỖI: Xảy ra lỗi khi đọc hồ sơ người dùng ({e})."


def update_user_profile(user_id: str, updates: Dict[str, Any]) -> str:
    """
    Cập nhật hồ sơ người dùng vào bộ nhớ giả lập.

    Name:
        update_user_profile

    Purpose:
        Dùng khi cần lưu sở thích, kỹ năng, mức lương mong muốn, địa điểm, ngành muốn tránh.
        Không dùng để tra cứu nghề nghiệp.

    Input schema:
        user_id (str): ID người dùng.
        updates (dict): Các trường cần cập nhật.
                        Hỗ trợ: interests, expected_salary, preferred_location,
                        avoid_industries, skills, profile_vector.

    Output schema:
        str: JSON string chứa profile sau khi cập nhật.

    Error semantics:
        Nếu user_id rỗng hoặc updates không phải dict -> "LỖI: ...".

    Side effect:
        Có thay đổi trạng thái trong USER_PROFILE_STORE.

    Example:
        >>> update_user_profile("user_001", {"interests": ["AI", "Data"], "preferred_location": "Hà Nội"})
    """
    try:
        if not isinstance(user_id, str) or not user_id.strip():
            return "LỖI: user_id phải là chuỗi không rỗng."

        if not isinstance(updates, dict):
            return "LỖI: updates phải là dict."

        allowed_fields = {
            "interests",
            "expected_salary",
            "preferred_location",
            "avoid_industries",
            "skills",
            "profile_vector",
        }

        invalid_fields = [key for key in updates.keys() if key not in allowed_fields]
        if invalid_fields:
            return f"LỖI: Trường không hợp lệ: {invalid_fields}. Trường hỗ trợ: {sorted(allowed_fields)}."

        current = USER_PROFILE_STORE.get(user_id, {
            "user_id": user_id,
            "interests": [],
            "expected_salary": None,
            "preferred_location": None,
            "avoid_industries": [],
            "skills": [],
            "profile_vector": None,
        })

        current.update(updates)
        USER_PROFILE_STORE[user_id] = current

        return _safe_json({
            "message": "Cập nhật profile thành công.",
            "profile": current,
        })

    except Exception as e:
        return f"LỖI: Xảy ra lỗi khi cập nhật hồ sơ người dùng ({e})."


def search_career_paths(query: str, filters: Dict[str, Any] = None) -> str:
    """
    Tìm kiếm nghề nghiệp trong corpus nghề nghiệp giả lập.

    Name:
        search_career_paths

    Purpose:
        Dùng khi người dùng hỏi mơ hồ về nghề, nhiệm vụ, kỹ năng, ngành.
        Đây là bản mock của RAG/vector search.

    Input schema:
        query (str): Từ khóa tìm kiếm.
        filters (dict, optional): Bộ lọc, ví dụ {"min_trait": "I"}.

    Output schema:
        str: JSON string chứa danh sách nghề phù hợp.

    Error semantics:
        Nếu query rỗng -> "LỖI: ...".

    Side effect:
        Read-only.

    Example:
        >>> search_career_paths("python dữ liệu", {})
    """
    try:
        if not isinstance(query, str) or not query.strip():
            return "LỖI: query phải là chuỗi không rỗng."

        if filters is None:
            filters = {}

        if not isinstance(filters, dict):
            return "LỖI: filters phải là dict hoặc None."

        q = _normalize_text(query)
        results = []

        for career_id, career in CAREER_DB.items():
            searchable_text = " ".join([
                career["name"],
                career["description"],
                " ".join(career["tasks"]),
                " ".join(career["required_skills"]),
            ]).lower()

            score = 0
            for token in re.split(r"\s+", q):
                if token and token in searchable_text:
                    score += 1

            min_trait = filters.get("min_trait")
            if min_trait:
                trait_score = career["riasec"].get(str(min_trait).upper(), 0)
                if trait_score < 3:
                    continue

            if score > 0:
                results.append({
                    "career_id": career_id,
                    "name": career["name"],
                    "match_score": score,
                    "description": career["description"],
                })

        results = sorted(results, key=lambda item: item["match_score"], reverse=True)

        if not results:
            return f"LỖI: Không tìm thấy nghề phù hợp với truy vấn '{query}'."

        return _safe_json({
            "query": query,
            "filters": filters,
            "results": results,
        })

    except Exception as e:
        return f"LỖI: Xảy ra lỗi khi tìm kiếm nghề nghiệp ({e})."


def get_career_detail(career_id: str) -> str:
    """
    Lấy chi tiết một nghề theo career_id.

    Name:
        get_career_detail

    Purpose:
        Dùng khi người dùng muốn xem chi tiết nghề: mô tả, nhiệm vụ, kỹ năng, lương, triển vọng.

    Input schema:
        career_id (str): ID hoặc tên nghề.
                         Ví dụ: "ai_engineer", "AI Engineer".

    Output schema:
        str: JSON string chứa thông tin chi tiết nghề.

    Error semantics:
        Nếu không tìm thấy career_id -> "LỖI: ...".

    Side effect:
        Read-only.

    Example:
        >>> get_career_detail("ai_engineer")
    """
    try:
        found_id = _find_career_id(career_id)

        if not found_id:
            return f"LỖI: Không tìm thấy nghề '{career_id}'. Nghề hỗ trợ: {list(CAREER_DB.keys())}."

        return _safe_json(CAREER_DB[found_id])

    except Exception as e:
        return f"LỖI: Xảy ra lỗi khi lấy chi tiết nghề nghiệp ({e})."


def search_job_market_data(role: str, region: str) -> str:
    """
    Tra cứu dữ liệu thị trường việc làm theo vai trò và khu vực.

    Name:
        search_job_market_data

    Purpose:
        Dùng khi người dùng hỏi về nhu cầu tuyển dụng, mức độ phổ biến của nghề theo địa điểm.

    Input schema:
        role (str): Tên nghề hoặc career_id.
        region (str): Khu vực, ví dụ: "Hà Nội", "TP.HCM", "Đà Nẵng".

    Output schema:
        str: Chuỗi mô tả dữ liệu thị trường việc làm.

    Error semantics:
        Nếu không có dữ liệu role/region -> "LỖI: ...".

    Side effect:
        Read-only.

    Example:
        >>> search_job_market_data("AI Engineer", "Hà Nội")
    """
    try:
        career_id = _find_career_id(role)

        if not career_id:
            return f"LỖI: Không tìm thấy role '{role}'."

        region_key = _normalize_text(region)

        aliases = {
            "hồ chí minh": "tp.hcm",
            "ho chi minh": "tp.hcm",
            "hcm": "tp.hcm",
            "tphcm": "tp.hcm",
            "tp hcm": "tp.hcm",
            "ha noi": "hà nội",
            "da nang": "đà nẵng",
        }

        region_key = aliases.get(region_key, region_key)

        market_by_role = JOB_MARKET_DB.get(career_id, {})

        if region_key not in market_by_role:
            return f"LỖI: Không có dữ liệu thị trường cho role '{role}' tại khu vực '{region}'."

        return market_by_role[region_key]

    except Exception as e:
        return f"LỖI: Xảy ra lỗi khi tra cứu thị trường việc làm ({e})."


def match_profile_to_careers(profile_vector: Dict[str, int], top_k: int = 3) -> str:
    """
    Match hồ sơ người dùng với danh sách nghề bằng similarity score.

    Name:
        match_profile_to_careers

    Purpose:
        Dùng khi đã có vector đặc điểm người dùng và cần xếp hạng nghề phù hợp.
        Đây là logic tính toán deterministic, không để LLM tự đoán điểm match.

    Input schema:
        profile_vector (dict): Vector RIASEC, ví dụ {"R": 2, "I": 5, "A": 3, "S": 2, "E": 1, "C": 4}
        top_k (int): Số nghề muốn trả về.

    Output schema:
        str: JSON string chứa ranked list nghề phù hợp.

    Error semantics:
        Nếu vector sai định dạng hoặc top_k không hợp lệ -> "LỖI: ...".

    Side effect:
        Read-only.

    Example:
        >>> match_profile_to_careers({"R": 2, "I": 5, "A": 3, "S": 2, "E": 1, "C": 4}, 3)
    """
    try:
        if not isinstance(profile_vector, dict):
            return "LỖI: profile_vector phải là dict."

        if not isinstance(top_k, int) or top_k <= 0:
            return "LỖI: top_k phải là số nguyên dương."

        traits = ["R", "I", "A", "S", "E", "C"]

        for trait in traits:
            if trait not in profile_vector:
                return f"LỖI: profile_vector thiếu trait '{trait}'."

            if not isinstance(profile_vector[trait], int):
                return f"LỖI: Giá trị của trait '{trait}' phải là số nguyên."

        matches = []

        for career_id, career in CAREER_DB.items():
            career_vector = career["riasec"]

            distance = 0
            for trait in traits:
                distance += abs(profile_vector[trait] - career_vector[trait])

            max_distance = 5 * len(traits)
            similarity = round((1 - distance / max_distance) * 100, 2)

            matches.append({
                "career_id": career_id,
                "name": career["name"],
                "similarity_percent": similarity,
                "reason": f"Phù hợp với nhóm đặc điểm nổi bật của nghề {career['name']}.",
            })

        matches = sorted(matches, key=lambda item: item["similarity_percent"], reverse=True)

        return _safe_json({
            "top_k": top_k,
            "matches": matches[:top_k],
        })

    except Exception as e:
        return f"LỖI: Xảy ra lỗi khi match hồ sơ với nghề nghiệp ({e})."


def compare_careers(career_ids: List[str]) -> str:
    """
    So sánh nhiều nghề side-by-side.

    Name:
        compare_careers

    Purpose:
        Dùng khi người dùng phân vân giữa nhiều lựa chọn nghề nghiệp.

    Input schema:
        career_ids (list[str]): Danh sách career_id hoặc tên nghề.
                                Ví dụ: ["ai_engineer", "data_engineer"]

    Output schema:
        str: JSON string chứa bảng so sánh nghề.

    Error semantics:
        Nếu career_ids không phải list, rỗng, hoặc có nghề không tồn tại -> "LỖI: ...".

    Side effect:
        Read-only.

    Example:
        >>> compare_careers(["ai_engineer", "data_engineer"])
    """
    try:
        if not isinstance(career_ids, list):
            return "LỖI: career_ids phải là list. Ví dụ: ['ai_engineer', 'data_engineer']."

        if len(career_ids) < 2:
            return "LỖI: Cần ít nhất 2 nghề để so sánh."

        comparison = []

        for item in career_ids:
            found_id = _find_career_id(item)

            if not found_id:
                return f"LỖI: Không tìm thấy nghề '{item}'."

            career = CAREER_DB[found_id]
            comparison.append({
                "career_id": found_id,
                "name": career["name"],
                "description": career["description"],
                "required_skills": career["required_skills"],
                "salary_range": career["salary_range"],
                "growth_outlook": career["growth_outlook"],
            })

        return _safe_json({
            "comparison": comparison,
        })

    except Exception as e:
        return f"LỖI: Xảy ra lỗi khi so sánh nghề nghiệp ({e})."


def get_learning_roadmap(career_id: str, current_level: str = "beginner") -> str:
    """
    Gợi ý lộ trình học tập theo nghề và trình độ hiện tại.

    Name:
        get_learning_roadmap

    Purpose:
        Dùng khi người dùng hỏi cần học gì để theo một nghề.

    Input schema:
        career_id (str): ID hoặc tên nghề.
        current_level (str): beginner, intermediate, advanced.

    Output schema:
        str: JSON string chứa roadmap theo từng bước.

    Error semantics:
        Nếu nghề hoặc level không hợp lệ -> "LỖI: ...".

    Side effect:
        Read-only.

    Example:
        >>> get_learning_roadmap("ai_engineer", "beginner")
    """
    try:
        found_id = _find_career_id(career_id)

        if not found_id:
            return f"LỖI: Không tìm thấy nghề '{career_id}'."

        level = _normalize_text(current_level)
        allowed_levels = ["beginner", "intermediate", "advanced"]

        if level not in allowed_levels:
            return f"LỖI: current_level phải thuộc {allowed_levels}."

        roadmap_db = {
            "ai_engineer": {
                "beginner": [
                    "Học Python cơ bản",
                    "Học Toán cho AI: đại số tuyến tính, xác suất, đạo hàm",
                    "Học Machine Learning cơ bản",
                    "Làm 2-3 project nhỏ: phân loại dữ liệu, dự đoán giá, chatbot đơn giản",
                ],
                "intermediate": [
                    "Học Deep Learning với PyTorch hoặc TensorFlow",
                    "Học NLP và LLM",
                    "Tìm hiểu Prompt Engineering, RAG, Agent",
                    "Triển khai model/API bằng FastAPI hoặc Flask",
                ],
                "advanced": [
                    "Học MLOps",
                    "Tối ưu inference",
                    "Xây dựng hệ thống AI production",
                    "Nghiên cứu evaluation, monitoring, guardrails",
                ],
            },
            "data_engineer": {
                "beginner": [
                    "Học SQL thật chắc",
                    "Học Python xử lý dữ liệu",
                    "Hiểu database, indexing, transaction",
                    "Làm project ETL nhỏ từ CSV/API vào database",
                ],
                "intermediate": [
                    "Học Airflow",
                    "Học Data Warehouse",
                    "Học Spark cơ bản",
                    "Thiết kế pipeline batch processing",
                ],
                "advanced": [
                    "Học Kafka/streaming",
                    "Học Lakehouse",
                    "Tối ưu performance cho dữ liệu lớn",
                    "Thiết kế data platform production",
                ],
            },
            "backend_developer": {
                "beginner": [
                    "Chọn một ngôn ngữ backend: Java, C#, Python hoặc Go",
                    "Học REST API",
                    "Học database cơ bản",
                    "Làm project CRUD API",
                ],
                "intermediate": [
                    "Học authentication/authorization",
                    "Học Docker",
                    "Học caching, message queue",
                    "Xây dựng API có logging, validation, error handling",
                ],
                "advanced": [
                    "Học microservices",
                    "Học system design",
                    "Tối ưu performance",
                    "Triển khai CI/CD và observability",
                ],
            },
        }

        if found_id not in roadmap_db:
            return f"LỖI: Chưa có roadmap cho nghề '{career_id}'."

        return _safe_json({
            "career_id": found_id,
            "career_name": CAREER_DB[found_id]["name"],
            "current_level": level,
            "roadmap": roadmap_db[found_id][level],
        })

    except Exception as e:
        return f"LỖI: Xảy ra lỗi khi lấy lộ trình học tập ({e})."


def find_mentors_or_programs(career_id: str, region: str) -> str:
    """
    Tìm mentor, cộng đồng hoặc chương trình học phù hợp theo nghề và khu vực.

    Name:
        find_mentors_or_programs

    Purpose:
        Dùng khi người dùng muốn tìm nơi học, mentor, cộng đồng hoặc chương trình phát triển nghề.

    Input schema:
        career_id (str): ID hoặc tên nghề.
        region (str): Khu vực, ví dụ: "Hà Nội", "TP.HCM".

    Output schema:
        str: JSON string chứa danh sách mentor/program/community gợi ý.

    Error semantics:
        Nếu không có dữ liệu cho nghề hoặc khu vực -> "LỖI: ...".

    Side effect:
        Read-only.

    Example:
        >>> find_mentors_or_programs("ai_engineer", "Hà Nội")
    """
    try:
        found_id = _find_career_id(career_id)

        if not found_id:
            return f"LỖI: Không tìm thấy nghề '{career_id}'."

        region_key = _normalize_text(region)

        aliases = {
            "hồ chí minh": "tp.hcm",
            "ho chi minh": "tp.hcm",
            "hcm": "tp.hcm",
            "tphcm": "tp.hcm",
            "tp hcm": "tp.hcm",
            "ha noi": "hà nội",
        }

        region_key = aliases.get(region_key, region_key)

        career_programs = MENTOR_PROGRAM_DB.get(found_id)

        if not career_programs:
            return f"LỖI: Chưa có dữ liệu mentor/program cho nghề '{career_id}'."

        programs = career_programs.get(region_key)

        if not programs:
            return f"LỖI: Chưa có dữ liệu mentor/program cho nghề '{career_id}' tại '{region}'."

        return _safe_json({
            "career_id": found_id,
            "career_name": CAREER_DB[found_id]["name"],
            "region": region,
            "programs": programs,
        })

    except Exception as e:
        return f"LỖI: Xảy ra lỗi khi tìm mentor/program ({e})."


# ============================================================
# 📋 TOOL REGISTRY
# ============================================================

AVAILABLE_TOOLS = {
    "run_personality_assessment": run_personality_assessment,
    "extract_skills_from_cv": extract_skills_from_cv,
    "get_user_profile": get_user_profile,
    "update_user_profile": update_user_profile,
    "search_career_paths": search_career_paths,
    "get_career_detail": get_career_detail,
    "search_job_market_data": search_job_market_data,
    "match_profile_to_careers": match_profile_to_careers,
    "compare_careers": compare_careers,
    "get_learning_roadmap": get_learning_roadmap,
    "find_mentors_or_programs": find_mentors_or_programs,
}


# ============================================================
# ✅ SELF-TEST
# Chạy: python src/tools.py
# ============================================================

if __name__ == "__main__":
    test_cases = [
        (
            "run_personality_assessment",
            ({"R": 2, "I": 5, "A": 3, "S": 2, "E": 1, "C": 4},),
            "Chấm RIASEC hợp lệ",
        ),
        (
            "run_personality_assessment",
            ("sai input",),
            "Input sai kiểu dữ liệu",
        ),
        (
            "extract_skills_from_cv",
            ("Tôi có kinh nghiệm Python, SQL, Airflow, Docker, teamwork và Git.",),
            "Parse CV hợp lệ",
        ),
        (
            "extract_skills_from_cv",
            ("",),
            "CV rỗng",
        ),
        (
            "get_user_profile",
            ("user_001",),
            "Đọc profile mặc định",
        ),
        (
            "update_user_profile",
            ("user_001", {"interests": ["AI", "Data"], "preferred_location": "Hà Nội"}),
            "Cập nhật profile",
        ),
        (
            "search_career_paths",
            ("python dữ liệu", {}),
            "Tìm nghề theo query",
        ),
        (
            "get_career_detail",
            ("ai_engineer",),
            "Lấy chi tiết nghề",
        ),
        (
            "search_job_market_data",
            ("AI Engineer", "Hà Nội"),
            "Tra cứu thị trường việc làm",
        ),
        (
            "match_profile_to_careers",
            ({"R": 2, "I": 5, "A": 3, "S": 2, "E": 1, "C": 4}, 3),
            "Match profile với nghề",
        ),
        (
            "compare_careers",
            (["ai_engineer", "data_engineer"],),
            "So sánh nghề",
        ),
        (
            "get_learning_roadmap",
            ("data_engineer", "beginner"),
            "Lộ trình học",
        ),
        (
            "find_mentors_or_programs",
            ("ai_engineer", "Hà Nội"),
            "Tìm mentor/program",
        ),
        (
            "get_career_detail",
            ("phi_hanh_gia",),
            "Nghề không tồn tại",
        ),
    ]

    passed = 0

    for tool_name, args, description in test_cases:
        try:
            result = AVAILABLE_TOOLS[tool_name](*args)

            assert isinstance(result, str)
            assert len(result) > 0

            print(f"✅ PASS | {tool_name}{args} | {description}")
            print(f"   -> {result[:160]}...\n")

            passed += 1

        except Exception as e:
            print(f"❌ FAIL | {tool_name}{args} | {description}")
            print(f"   Crash: {e}\n")

    print(f"KẾT QUẢ: {passed}/{len(test_cases)} test PASS")
