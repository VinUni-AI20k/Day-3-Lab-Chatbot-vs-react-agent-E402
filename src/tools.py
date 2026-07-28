"""LLM-backed gift-advice tools: LLM drafts; Python validates and ranks."""
from __future__ import annotations
import json, re, sys, time, unicodedata
from collections.abc import Callable
from difflib import SequenceMatcher
from typing import Any

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

StructuredLLMCallable = Callable[[str, dict[str, Any]], dict[str, Any]]
_TOOL_LLM: StructuredLLMCallable | None = None
PROFILE_FIELDS = ("traits","interests","preferences","exclusions","relationship","occasion","age","budget_vnd")
LIST_FIELDS = PROFILE_FIELDS[:4]
ANALYSIS_LIST_FIELDS = ("priority_interests","preferred_gift_styles","avoid_features","generation_guidelines","clarification_questions","analysis_notes")
CANDIDATE_LIST_FIELDS = ("fit_tags","gift_styles","suitable_occasions","suitable_relationships","possible_risks")
URL_RE = re.compile(r"(?:https?://|www\\.|\\b[a-z0-9-]+\\.(?:com|vn|net|org)\\b)", re.I)
SHOP_RE = re.compile(r"\\b(?:shop|store|cửa\\s*hàng|thương\\s*hiệu|brand)\\b", re.I)

class ToolFailure(Exception):
    """Internal safe error carrier."""
    def __init__(self, code: str, message: str, *, field: str | None=None, retryable: bool=False) -> None:
        super().__init__(message)
        self.code,self.message,self.field,self.retryable=code,message,field,retryable

def configure_tool_llm(llm_callable: StructuredLLMCallable) -> None:
    """Configure the structured LLM dependency used by all tools.

    Summary: Install one reusable callable; this module never reads API keys.
    Role in pipeline: One-time setup before Tools 1-4.
    Args: llm_callable: Callable accepting system prompt and payload.
    Returns: None.
    Error semantics: TypeError for integration misuse; tools return JSON errors.
    Use when: Role 4 has a provider adapter, or tests use a fake LLM.
    Do not use when: Passing credentials or constructing a client per call.
    Side effects: Replaces the callable used by later tool calls.
    Safety: Stores only the callable and never logs credentials.
    Example: configure_tool_llm(call_structured_llm)
    """
    if not callable(llm_callable): raise TypeError("llm_callable must be callable")
    global _TOOL_LLM
    _TOOL_LLM=llm_callable

def _json(data: dict[str,Any])->str: return json.dumps(data,ensure_ascii=False)
def _error(code:str,message:str,*,field:str|None=None,retryable:bool=False)->str:
    detail={"code":code,"message":message,"retryable":retryable}
    if field is not None: detail["field"]=field
    return _json({"ok":False,"error":detail})
def _safe(exc:ToolFailure)->str: return _error(exc.code,exc.message,field=exc.field,retryable=exc.retryable)

def _api_failure(exc:Exception)->ToolFailure:
    text=f"{exc.__class__.__name__} {exc}".casefold()
    if any(x in text for x in ("auth","unauthorized","forbidden","401")): return ToolFailure("API_AUTHENTICATION_ERROR","Không thể xác thực dịch vụ LLM. Hãy kiểm tra cấu hình máy chủ.")
    if any(x in text for x in ("rate","429","quota")): return ToolFailure("API_RATE_LIMIT","Dịch vụ LLM đang giới hạn tần suất.",retryable=True)
    if "timeout" in text or "timed out" in text: return ToolFailure("API_TIMEOUT","Dịch vụ LLM phản hồi quá thời gian.",retryable=True)
    return ToolFailure("API_REQUEST_FAILED","Không thể hoàn tất yêu cầu tới dịch vụ LLM.")

def _call_tool_llm(system_prompt:str,payload:dict[str,Any])->dict[str,Any]:
    if _TOOL_LLM is None: raise ToolFailure("TOOL_LLM_NOT_CONFIGURED","Structured LLM cho tools chưa được cấu hình.")
    for attempt in range(2):
        try:
            raw:Any=_TOOL_LLM(system_prompt,payload)
            if isinstance(raw,str):
                try: raw=json.loads(raw)
                except json.JSONDecodeError as exc: raise ToolFailure("INVALID_JSON_RESPONSE","LLM trả về JSON không hợp lệ.") from exc
            if not isinstance(raw,dict): raise ToolFailure("INVALID_LLM_RESPONSE","LLM phải trả về một JSON object.")
            return raw
        except ToolFailure: raise
        except Exception as exc:
            failure=_api_failure(exc)
            if failure.retryable and attempt==0: time.sleep(.05); continue
            raise failure from exc
    raise ToolFailure("API_REQUEST_FAILED","Không thể gọi dịch vụ LLM.")

def _parse_dict(value:Any,field:str,wrapper:str|None=None)->dict[str,Any]:
    if isinstance(value,str):
        try: value=json.loads(value)
        except json.JSONDecodeError as exc: raise ToolFailure("INVALID_JSON_RESPONSE",f"{field} không phải JSON hợp lệ.",field=field) from exc
    if not isinstance(value,dict): raise ToolFailure("INVALID_LLM_RESPONSE",f"{field} phải là JSON object.",field=field)
    return value[wrapper] if wrapper and isinstance(value.get(wrapper),dict) else value

def _parse_candidates(value:Any)->list[dict[str,Any]]:
    if isinstance(value,str):
        try: value=json.loads(value)
        except json.JSONDecodeError as exc: raise ToolFailure("INVALID_JSON_RESPONSE","gift_candidates không phải JSON hợp lệ.",field="gift_candidates") from exc
    if isinstance(value,dict): value=value.get("ranked_candidates")
    if not isinstance(value,list) or not value or not all(isinstance(x,dict) for x in value):
        raise ToolFailure("INVALID_CANDIDATE_SCHEMA","gift_candidates phải là danh sách object không rỗng.",field="gift_candidates")
    return value

def _norm(value:str)->str: return " ".join(value.casefold().split())
def _fold(value:str)->str:
    value=unicodedata.normalize("NFD",_norm(value))
    return "".join(c for c in value if unicodedata.category(c)!="Mn")

def _strings(value:Any,field:str)->list[str]:
    if not isinstance(value,list): raise ToolFailure("INVALID_LLM_RESPONSE",f"{field} phải là list string.",field=field)
    result:list[str]=[]; seen:set[str]=set()
    for item in value:
        if not isinstance(item,str): raise ToolFailure("INVALID_LLM_RESPONSE",f"{field} chỉ được chứa string.",field=field)
        clean=" ".join(item.split())
        if clean and _norm(clean) not in seen: result.append(clean); seen.add(_norm(clean))
    return result

def _nullable(value:Any,field:str)->str|None:
    if value is None: return None
    if not isinstance(value,str): raise ToolFailure("INVALID_LLM_RESPONSE",f"{field} phải là string hoặc null.",field=field)
    return " ".join(value.split()) or None

def _positive(value:Any,field:str,maximum:int|None=None)->int|None:
    if value is None: return None
    if isinstance(value,bool) or not isinstance(value,int) or value<=0:
        raise ToolFailure("INVALID_BUDGET" if field=="budget_vnd" else "INVALID_LLM_RESPONSE",f"{field} phải là integer dương hoặc null.",field=field)
    if maximum is not None and value>maximum: raise ToolFailure("INVALID_LLM_RESPONSE",f"{field} vượt giới hạn.",field=field)
    return value

def _validate_profile(raw:dict[str,Any])->dict[str,Any]:
    out={f:_strings(raw.get(f),f) for f in LIST_FIELDS}
    out["relationship"]=_nullable(raw.get("relationship"),"relationship")
    out["occasion"]=_nullable(raw.get("occasion"),"occasion")
    out["age"]=_positive(raw.get("age"),"age",120)
    out["budget_vnd"]=_positive(raw.get("budget_vnd"),"budget_vnd")
    excluded={_norm(x) for x in out["exclusions"]}
    out["interests"]=[x for x in out["interests"] if _norm(x) not in excluded]
    return out

def _validate_analysis(raw:dict[str,Any],profile:dict[str,Any])->dict[str,Any]:
    out={f:_strings(raw.get(f),f) for f in ANALYSIS_LIST_FIELDS}
    out["gift_goal"]=_nullable(raw.get("gift_goal"),"gift_goal") or ""
    if not isinstance(raw.get("needs_clarification"),bool): raise ToolFailure("INVALID_LLM_RESPONSE","needs_clarification phải là boolean.",field="needs_clarification")
    out["needs_clarification"]=raw["needs_clarification"]
    strategy=raw.get("budget_strategy")
    if not isinstance(strategy,dict): raise ToolFailure("INVALID_LLM_RESPONSE","budget_strategy phải là object.",field="budget_strategy")
    low,high=strategy.get("minimum_vnd"),strategy.get("maximum_vnd")
    for key,value in (("minimum_vnd",low),("maximum_vnd",high)):
        if value is not None and (isinstance(value,bool) or not isinstance(value,int) or value<0):
            raise ToolFailure("INVALID_LLM_RESPONSE",f"budget_strategy.{key} không hợp lệ.",field=f"budget_strategy.{key}")
    if low is not None and high is not None and low>high: raise ToolFailure("INVALID_LLM_RESPONSE","Khoảng budget strategy không hợp lệ.",field="budget_strategy")
    budget=profile.get("budget_vnd")
    if budget is not None and high is not None: high=min(high,budget); low=min(low,high) if low is not None else None
    out["budget_strategy"]={"minimum_vnd":low,"maximum_vnd":high}
    known={_norm(x) for x in out["avoid_features"]}
    for x in profile["exclusions"]:
        if _norm(x) not in known: out["avoid_features"].append(x); known.add(_norm(x))
    if budget is None:
        out["needs_clarification"]=True
        if not any("ngân sách" in _norm(q) for q in out["clarification_questions"]): out["clarification_questions"].append("Ngân sách tối đa là bao nhiêu VND?")
    if not profile["interests"]:
        out["needs_clarification"]=True
        if not any("sở thích" in _norm(q) for q in out["clarification_questions"]): out["clarification_questions"].append("Người nhận có sở thích cụ thể nào?")
    return out

def _candidate(raw:Any,budget:int,exclusions:list[str],names:list[str])->tuple[dict[str,Any]|None,str|None]:
    if not isinstance(raw,dict): return None,"INVALID_CANDIDATE_SCHEMA"
    expected={"name","concept","components","estimated_price_range_vnd","fit_tags","gift_styles","suitable_occasions","suitable_relationships","possible_risks"}
    if set(raw)!=expected: return None,"INVALID_CANDIDATE_SCHEMA"
    name,concept=raw.get("name"),raw.get("concept")
    if not isinstance(name,str) or not name.strip() or not isinstance(concept,str) or not concept.strip(): return None,"INVALID_CANDIDATE_SCHEMA"
    name,concept=" ".join(name.split())," ".join(concept.split())
    forbidden={"brand","brand_name","shop","store","url","link","product_id"}
    serialized=json.dumps(raw,ensure_ascii=False)
    if forbidden.intersection(raw) or URL_RE.search(serialized) or SHOP_RE.search(serialized): return None,"INVALID_CANDIDATE_SCHEMA"
    folded=_fold(name)
    if any(SequenceMatcher(None,folded,old).ratio()>=.86 for old in names): return None,"DUPLICATE_CANDIDATE"
    components=raw.get("components")
    if not isinstance(components,list) or not components: return None,"INVALID_CANDIDATE_SCHEMA"
    clean_components=[]
    for c in components:
        if not isinstance(c,dict) or set(c)!={"name","estimated_price_vnd"}: return None,"INVALID_CANDIDATE_SCHEMA"
        cn,price=c.get("name"),c.get("estimated_price_vnd")
        if not isinstance(cn,str) or not cn.strip() or isinstance(price,bool) or not isinstance(price,int) or price<0: return None,"INVALID_CANDIDATE_SCHEMA"
        clean_components.append({"name":" ".join(cn.split()),"estimated_price_vnd":price})
    pr=raw.get("estimated_price_range_vnd")
    if not isinstance(pr,dict) or set(pr)!={"minimum","maximum"}: return None,"INVALID_CANDIDATE_SCHEMA"
    low,high=pr.get("minimum"),pr.get("maximum")
    if any(isinstance(x,bool) or not isinstance(x,int) or x<0 for x in (low,high)) or low>high: return None,"INVALID_CANDIDATE_SCHEMA"
    if high>budget: return None,"CANDIDATE_OVER_BUDGET"
    try: lists={f:_strings(raw.get(f),f) for f in CANDIDATE_LIST_FIELDS}
    except ToolFailure: return None,"INVALID_CANDIDATE_SCHEMA"
    clean={"name":name,"concept":concept,"components":clean_components,"estimated_price_range_vnd":{"minimum":low,"maximum":high},**lists}
    searchable=_fold(json.dumps(clean,ensure_ascii=False))
    if any(_fold(x) and _fold(x) in searchable for x in exclusions): return None,"CANDIDATE_VIOLATES_EXCLUSION"
    return clean,None

def _matches(values:list[str],targets:list[str])->list[str]:
    mapping={_norm(x):x for x in targets}
    return list(dict.fromkeys(mapping[_norm(x)] for x in values if _norm(x) in mapping))

def _score(c:dict[str,Any],p:dict[str,Any],a:dict[str,Any])->tuple[int,dict[str,int],list[str]]:
    interests=_matches(c["fit_tags"],p["interests"])
    styles=_matches(c["gift_styles"],a["preferred_gift_styles"])
    preferences=_matches(c["fit_tags"]+c["gift_styles"],p["preferences"])
    personal=3 if "ca nhan hoa" in _fold(" ".join([c["name"],c["concept"]]+c["fit_tags"]+c["gift_styles"])) else 0
    occasion=2 if p["occasion"] and _matches(c["suitable_occasions"],[p["occasion"]]) else 0
    relationship=2 if p["relationship"] and _matches(c["suitable_relationships"],[p["relationship"]]) else 0
    strategy=a["budget_strategy"]; low,high=strategy["minimum_vnd"],strategy["maximum_vnd"]; pr=c["estimated_price_range_vnd"]
    strategy_points=2 if low is not None and high is not None and pr["minimum"]>=low and pr["maximum"]<=high else 0
    breakdown={"interest_match":len(interests)*5,"preferred_gift_style_match":len(styles)*3,"preference_match":len(preferences)*3,"personalization_bonus":personal,"occasion_match":occasion,"relationship_match":relationship,"within_budget":2,"within_budget_strategy":strategy_points,"risk_penalty":-len(c["possible_risks"])}
    signals=list(dict.fromkeys(interests+styles+preferences))
    if personal: signals.append("cá nhân hóa")
    if occasion: signals.append(p["occasion"])
    if relationship: signals.append(p["relationship"])
    return sum(breakdown.values()),breakdown,signals

EXTRACT_PROMPT="Chỉ trích xuất dữ kiện đã nêu. Không suy diễn, chẩn đoán hay gợi ý quà. Trả JSON đúng schema profile; tuổi integer, ngân sách integer VND, thiếu dùng null/list rỗng; exclusion thắng interest."
ANALYZE_PROMPT="Tạo brief từ profile, không catalog/candidate/chẩn đoán/thêm sở thích. Trả JSON đúng schema analysis. Exclusions nằm trong avoid_features; thiếu ngân sách hoặc sở thích thì needs_clarification=true."
GENERATE_PROMPT="Sinh requested_count concept quà mới khác nhau từ profile và analysis, không catalog, brand, shop, URL, tồn kho, yếu tố nhạy cảm hay giá chính xác. Khoảng giá ước tính không vượt budget, không exclusion. Không score/rank/ID. Trả JSON {candidates:[{name,concept,components,estimated_price_range_vnd,fit_tags,gift_styles,suitable_occasions,suitable_relationships,possible_risks}]}."
EXPLAIN_PROMPT="Chỉ giải thích candidate khóa; không sinh mới hay đổi ID, rank, name, components, giá, score; không link. Trả JSON {explanations:[{candidate_id,reason,why_it_fits,personalization_tip,verify_before_buying,budget_note}]}."

def extract_recipient_profile(user_description:str)->str:
    """Extract an evidence-only recipient profile with a structured LLM.

    Summary: Convert natural language to the fixed profile schema.
    Role in pipeline: Tool 1/4; recipient_profile feeds Tool 2.
    Args: user_description: Non-empty user description.
    Returns: JSON string with ok, profile, missing_fields and source.
    Error semantics: Input, provider and LLM errors become ok:false JSON.
    Use when: Starting the gift pipeline from raw text.
    Do not use when: Inferring facts, diagnosing personality or suggesting gifts.
    Side effects: Calls the injected LLM/API; does not read API keys.
    Safety: LLM output may be imperfect; Python validates fields and exclusions.
    Example: json.loads(extract_recipient_profile("Bạn thân thích sách"))
    """
    if not isinstance(user_description,str) or not user_description.strip():
        return _error("INVALID_INPUT","user_description phải là chuỗi không rỗng.",field="user_description",retryable=True)
    try:
        raw=_call_tool_llm(EXTRACT_PROMPT,{"_operation":"extract_recipient_profile","user_description":user_description.strip()})
        profile=_validate_profile(raw.get("recipient_profile",raw))
        missing=[f for f in PROFILE_FIELDS if profile[f] is None or profile[f]==[]]
        return _json({"ok":True,"recipient_profile":profile,"missing_fields":missing,"source":"llm_structured_extraction"})
    except ToolFailure as exc: return _safe(exc)

AVAILABLE_TOOLS: dict[str, Callable[..., str]] = {}
TOOL_CONTRACTS={
 "extract_recipient_profile":{"input":{"user_description":"str"},"output":"JSON string: {ok,recipient_profile,missing_fields,source}"},
 "analyze_recipient_profile":{"input":{"recipient_profile":"dict | JSON string"},"output":"JSON string: {ok,profile_analysis,source}"},
 "generate_gift_candidates":{"input":{"recipient_profile":"dict | JSON string","profile_analysis":"dict | JSON string","max_candidates":"int 1..50"},"output":"JSON string: {ok,ranked_candidates,generation_summary}"},
 "explain_recommendations":{"input":{"recipient_profile":"dict | JSON string","profile_analysis":"dict | JSON string","gift_candidates":"list | JSON string","top_k":"int 1..50"},"output":"JSON string: {ok,recommendations,explanation_note}"}}

def _arr()->dict[str,Any]: return {"type":"array","items":{"type":"string"}}
PROFILE_SCHEMA={"type":"object","properties":{
 "traits":_arr(),"interests":_arr(),"preferences":_arr(),"exclusions":_arr(),
 "relationship":{"type":["string","null"]},"occasion":{"type":["string","null"]},
 "age":{"type":["integer","null"],"minimum":1,"maximum":120},
 "budget_vnd":{"type":["integer","null"],"minimum":1}},
 "required":list(PROFILE_FIELDS),"additionalProperties":False}
ANALYSIS_SCHEMA={"type":"object","properties":{
 "priority_interests":_arr(),"preferred_gift_styles":_arr(),"avoid_features":_arr(),
 "gift_goal":{"type":"string"},"budget_strategy":{"type":"object","properties":{
  "minimum_vnd":{"type":["integer","null"],"minimum":0},
  "maximum_vnd":{"type":["integer","null"],"minimum":0}},
  "required":["minimum_vnd","maximum_vnd"],"additionalProperties":False},
 "generation_guidelines":_arr(),"needs_clarification":{"type":"boolean"},
 "clarification_questions":_arr(),"analysis_notes":_arr()},
 "required":["priority_interests","preferred_gift_styles","avoid_features","gift_goal","budget_strategy","generation_guidelines","needs_clarification","clarification_questions","analysis_notes"],"additionalProperties":False}
COMPONENT_SCHEMA={"type":"object","properties":{"name":{"type":"string"},"estimated_price_vnd":{"type":"integer","minimum":0}},"required":["name","estimated_price_vnd"],"additionalProperties":False}
CANDIDATE_SCHEMA={"type":"object","properties":{
 "rank":{"type":"integer","minimum":1},"candidate_id":{"type":"string"},"name":{"type":"string"},"concept":{"type":"string"},
 "components":{"type":"array","items":COMPONENT_SCHEMA,"minItems":1},
 "estimated_price_range_vnd":{"type":"object","properties":{"minimum":{"type":"integer","minimum":0},"maximum":{"type":"integer","minimum":0}},"required":["minimum","maximum"],"additionalProperties":False},
 "fit_tags":_arr(),"gift_styles":_arr(),"suitable_occasions":_arr(),"suitable_relationships":_arr(),
 "score":{"type":"integer"},"score_breakdown":{"type":"object","properties":{
  "interest_match":{"type":"integer"},"preferred_gift_style_match":{"type":"integer"},
  "preference_match":{"type":"integer"},"personalization_bonus":{"type":"integer"},
  "occasion_match":{"type":"integer"},"relationship_match":{"type":"integer"},
  "within_budget":{"type":"integer"},"within_budget_strategy":{"type":"integer"},
  "risk_penalty":{"type":"integer"}},
  "required":["interest_match","preferred_gift_style_match","preference_match","personalization_bonus","occasion_match","relationship_match","within_budget","within_budget_strategy","risk_penalty"],"additionalProperties":False},
 "matched_signals":_arr(),"possible_risks":_arr(),
 "data_source":{"type":"string"},"requires_market_verification":{"type":"boolean"}},
 "required":["rank","candidate_id","name","concept","components","estimated_price_range_vnd","fit_tags","gift_styles","suitable_occasions","suitable_relationships","score","score_breakdown","matched_signals","possible_risks","data_source","requires_market_verification"],"additionalProperties":False}

TOOL_SPECS=[
 {"name":"extract_recipient_profile","description":"Tool 1/4: structured LLM chỉ trích xuất dữ kiện đã nêu; không suy diễn, chẩn đoán hoặc gợi ý quà.","parameters":{"type":"object","properties":{"user_description":{"type":"string","minLength":1}},"required":["user_description"],"additionalProperties":False}},
 {"name":"analyze_recipient_profile","description":"Tool 2/4: structured LLM tạo brief từ profile; không catalog, candidate hoặc thêm sở thích.","parameters":{"type":"object","properties":{"recipient_profile":PROFILE_SCHEMA},"required":["recipient_profile"],"additionalProperties":False}},
 {"name":"generate_gift_candidates","description":"Tool 3/4 dùng LLM để sinh các concept quà mới dựa trên hồ sơ và profile analysis; Python kiểm tra ngân sách, exclusions, schema, sau đó chấm điểm và gán rank. Candidate là ý tưởng được sinh, không phải sản phẩm hoặc giá thị trường đã xác minh.","parameters":{"type":"object","properties":{"recipient_profile":PROFILE_SCHEMA,"profile_analysis":ANALYSIS_SCHEMA,"max_candidates":{"type":"integer","minimum":1,"maximum":50,"default":10}},"required":["recipient_profile","profile_analysis"],"additionalProperties":False}},
 {"name":"explain_recommendations","description":"Tool 4/4 chỉ giải thích các candidate từ Tool 3. Không được thay đổi rank, candidate_id, components hoặc khoảng giá.","parameters":{"type":"object","properties":{"recipient_profile":PROFILE_SCHEMA,"profile_analysis":ANALYSIS_SCHEMA,"gift_candidates":{"type":"array","items":CANDIDATE_SCHEMA,"minItems":1},"top_k":{"type":"integer","minimum":1,"maximum":50,"default":5}},"required":["recipient_profile","profile_analysis","gift_candidates"],"additionalProperties":False}}]

def _fake_candidate(name:str,tag:str,maximum:int,risks:list[str]|None=None)->dict[str,Any]:
    return {"name":name,"concept":f"Concept {tag} cá nhân hóa.","components":[{"name":f"Thành phần {tag}","estimated_price_vnd":maximum-100_000}],"estimated_price_range_vnd":{"minimum":maximum-150_000,"maximum":maximum},"fit_tags":[tag,"cá nhân hóa"],"gift_styles":["ý nghĩa","cá nhân hóa"],"suitable_occasions":["sinh nhật"],"suitable_relationships":["bạn thân"],"possible_risks":risks or []}

def _fake_llm(_:str,payload:dict[str,Any])->dict[str,Any]:
    op=payload["_operation"]
    if op=="extract_recipient_profile":
        text=_norm(payload["user_description"])
        return {"traits":["sáng tạo"],"interests":["đọc sách","trà","đọc sách"],"preferences":["ý nghĩa"],"exclusions":["trà"],"relationship":"bạn thân","occasion":"sinh nhật","age":21,"budget_vnd":None if "không ngân sách" in text else 800_000}
    if op=="analyze_recipient_profile":
        p=payload["recipient_profile"]; budget=p["budget_vnd"]
        return {"priority_interests":p["interests"],"preferred_gift_styles":["ý nghĩa","cá nhân hóa"],"avoid_features":[],"gift_goal":"Quà dựa trên sở thích.","budget_strategy":{"minimum_vnd":int(budget*.5) if budget else None,"maximum_vnd":budget},"generation_guidelines":["Concept khác nhau"],"needs_clarification":budget is None or not p["interests"],"clarification_questions":[],"analysis_notes":[]}
    if op=="generate_gift_candidates":
        return {"candidates":[_fake_candidate("Không gian đọc sách cá nhân","đọc sách",700_000),_fake_candidate("Bộ sáng tạo ký ức","sáng tạo",600_000,["Xác nhận màu."]),_fake_candidate("Concept vượt ngân sách","đọc sách",900_000),_fake_candidate("Hộp trà thư giãn","trà",500_000)]}
    if op=="explain_recommendations":
        return {"explanations":[{"candidate_id":c["candidate_id"],"reason":"Phù hợp tín hiệu đã xác nhận.","why_it_fits":c["matched_signals"],"personalization_tip":"Thêm lời nhắn.","verify_before_buying":["Xác minh giá thực tế."],"budget_note":"Giá chỉ ước tính.","rank":999,"components":[],"estimated_price_range_vnd":{"minimum":1,"maximum":1}} for c in payload["gift_candidates"]]}
    raise AssertionError("unknown operation")

def _run_smoke_tests()->None:
    """Run deterministic offline assertions and exit non-zero on failure."""
    global _TOOL_LLM
    passed=attempted=0
    def check(condition:bool,label:str)->None:
        nonlocal passed,attempted
        attempted+=1
        if condition: passed+=1; print(f"[PASS] {label}")
        else: print(f"[FAIL] {label}")
    _TOOL_LLM=None
    check(json.loads(extract_recipient_profile("x"))["error"]["code"]=="TOOL_LLM_NOT_CONFIGURED","LLM chưa cấu hình")
    configure_tool_llm(_fake_llm)
    check(not json.loads(extract_recipient_profile(""))["ok"],"description rỗng")
    check(not json.loads(extract_recipient_profile(7))["ok"],"description sai kiểu")  # type: ignore[arg-type]
    extracted=json.loads(extract_recipient_profile("Bạn thân thích sách, 800k"))
    check(extracted["ok"] and set(extracted["recipient_profile"])==set(PROFILE_FIELDS),"structured extraction")
    exclusion=json.loads(extract_recipient_profile("Từng thích trà nhưng hiện không uống trà"))
    check("trà" not in exclusion["recipient_profile"]["interests"],"exclusion thắng interest")
    missing=json.loads(extract_recipient_profile("không ngân sách"))
    missing_analysis=json.loads(analyze_recipient_profile(missing["recipient_profile"]))
    check(missing_analysis["profile_analysis"]["needs_clarification"],"thiếu ngân sách")
    invalid={**extracted["recipient_profile"],"budget_vnd":-1}
    check(json.loads(generate_gift_candidates(invalid,missing_analysis["profile_analysis"]))["error"]["code"]=="INVALID_BUDGET","ngân sách âm")
    original=_TOOL_LLM
    configure_tool_llm(lambda _s,_p:"not-json")  # type: ignore[arg-type,return-value]
    check(json.loads(extract_recipient_profile("x"))["error"]["code"]=="INVALID_JSON_RESPONSE","invalid LLM JSON")
    configure_tool_llm(lambda s,p:{"candidates":[]} if p["_operation"]=="generate_gift_candidates" else _fake_llm(s,p))
    check(json.loads(generate_gift_candidates(extracted["recipient_profile"],missing_analysis["profile_analysis"]))["error"]["code"]=="EMPTY_GENERATION","empty generation")
    configure_tool_llm(original)  # type: ignore[arg-type]
    analysis=json.loads(analyze_recipient_profile(extracted["recipient_profile"]))
    generated=json.loads(generate_gift_candidates(extracted["recipient_profile"],analysis["profile_analysis"]))
    candidates=generated["ranked_candidates"]; rejected={x["code"] for x in generated["generation_summary"]["rejected_candidates"]}
    check("CANDIDATE_OVER_BUDGET" in rejected,"over budget rejected")
    check("CANDIDATE_VIOLATES_EXCLUSION" in rejected,"exclusion rejected")
    check({x["candidate_id"] for x in candidates}=={"C001","C002"},"C001/C002 assigned")
    check(all(isinstance(x["score"],int) for x in candidates),"score exists")
    check(all(x["score_breakdown"] for x in candidates),"breakdown exists")
    check([x["rank"] for x in candidates]==list(range(1,len(candidates)+1)),"continuous ranks")
    check([x["score"] for x in candidates]==sorted((x["score"] for x in candidates),reverse=True),"score descending")
    explained=json.loads(explain_recommendations(extracted["recipient_profile"],analysis["profile_analysis"],candidates,2)); recs=explained["recommendations"]
    check([x["candidate_id"] for x in recs]==[x["candidate_id"] for x in candidates],"Tool 4 locks IDs")
    check([x["rank"] for x in recs]==[x["rank"] for x in candidates],"Tool 4 locks ranks")
    check(recs[0]["components"]==candidates[0]["components"],"Tool 4 locks components")
    check(recs[0]["estimated_price_range_vnd"]==candidates[0]["estimated_price_range_vnd"],"Tool 4 locks prices")
    check(json.loads(explain_recommendations(extracted["recipient_profile"],analysis["profile_analysis"],candidates,0))["error"]["code"]=="INVALID_TOP_K","invalid top_k")
    check(all(isinstance(x,dict) for x in (extracted,analysis,generated,explained)),"outputs parse in app")
    secret="sk-test-secret"
    configure_tool_llm(lambda _s,_p:(_ for _ in ()).throw(RuntimeError(f"authentication failed {secret}")))
    safe=extract_recipient_profile("x")
    check(json.loads(safe)["error"]["code"]=="API_AUTHENTICATION_ERROR","API error mapped")
    check(secret not in safe,"secret not exposed")
    check(not any(k.startswith("GIFT_") for k in globals()),"no fixed catalog")
    check(set(AVAILABLE_TOOLS)=={"extract_recipient_profile","analyze_recipient_profile","generate_gift_candidates","explain_recommendations"},"exactly four tools")
    configure_tool_llm(_fake_llm)
    print(f"Smoke tests: {passed}/{attempted} passed")
    if passed!=attempted: raise SystemExit(1)

# Registry initialization and smoke-test entry point are deferred until all
# four public functions have been defined.

def analyze_recipient_profile(recipient_profile:dict[str,Any]|str)->str:
    """Build a validated gift-generation brief from a recipient profile.

    Summary: Use structured LLM analysis bounded by known facts.
    Role in pipeline: Tool 2/4; consumes Tool 1 and feeds Tool 3.
    Args: recipient_profile: Profile dict, wrapped response, or JSON string.
    Returns: JSON string with ok, profile_analysis and source.
    Error semantics: Invalid inputs/LLM/API failures return structured errors.
    Use when: A profile exists and generation guidance is needed.
    Do not use when: Accessing catalogs, generating products, or adding traits.
    Side effects: Calls the injected LLM/API; does not mutate input.
    Safety: This is gift guidance, not diagnosis; Python enforces exclusions.
    Example: analyze_recipient_profile(profile_result)
    """
    try:
        profile=_validate_profile(_parse_dict(recipient_profile,"recipient_profile","recipient_profile"))
        raw=_call_tool_llm(ANALYZE_PROMPT,{"_operation":"analyze_recipient_profile","recipient_profile":profile})
        analysis=_validate_analysis(raw.get("profile_analysis",raw),profile)
        return _json({"ok":True,"profile_analysis":analysis,"source":"llm_structured_analysis"})
    except ToolFailure as exc: return _safe(exc)

def generate_gift_candidates(recipient_profile:dict[str,Any]|str,profile_analysis:dict[str,Any]|str,max_candidates:int=10)->str:
    """Generate novel concepts, then validate, score and rank in Python.

    Summary: Ask the LLM for new concepts; no fixed product catalog exists.
    Role in pipeline: Tool 3/4; consumes Tools 1-2 and feeds locked data to Tool 4.
    Args:
        recipient_profile: Tool 1 profile/response.
        profile_analysis: Tool 2 analysis/response.
        max_candidates: Requested/returned limit, 1-50.
    Returns: JSON string with ranked_candidates and generation_summary.
    Error semantics: Budget/schema/generation/API failures are structured JSON.
    Use when: Profile, analysis and a positive budget are available.
    Do not use when: Seeking verified products, stock, sellers, links or exact prices.
    Side effects: Calls injected LLM; local validation/scoring are read-only.
    Safety: Concepts/prices can be imperfect; Python rejects exclusions, excess
        budget, URLs, shops and duplicates. Market verification remains required.
    Example: generate_gift_candidates(profile, analysis, 5)
    """
    if isinstance(max_candidates,bool) or not isinstance(max_candidates,int) or not 1<=max_candidates<=50:
        return _error("INVALID_CANDIDATE_SCHEMA","max_candidates phải là integer 1-50.",field="max_candidates",retryable=True)
    try:
        profile=_validate_profile(_parse_dict(recipient_profile,"recipient_profile","recipient_profile"))
        analysis=_validate_analysis(_parse_dict(profile_analysis,"profile_analysis","profile_analysis"),profile)
        budget=profile["budget_vnd"]
        if budget is None: raise ToolFailure("MISSING_BUDGET","Cần ngân sách trước khi sinh concept.",field="budget_vnd",retryable=True)
        if isinstance(budget,bool) or not isinstance(budget,int) or budget<=0: raise ToolFailure("INVALID_BUDGET","budget_vnd phải là integer dương.",field="budget_vnd",retryable=True)
        raw=_call_tool_llm(GENERATE_PROMPT,{"_operation":"generate_gift_candidates","recipient_profile":profile,"profile_analysis":analysis,"requested_count":max_candidates})
        generated=raw.get("candidates")
        if not isinstance(generated,list) or not generated: raise ToolFailure("EMPTY_GENERATION","LLM không sinh candidate nào.",retryable=True)
        accepted=[]; names=[]; rejected=[]
        for index,item in enumerate(generated,1):
            clean,reason=_candidate(item,budget,profile["exclusions"],names)
            if reason:
                rejected.append({"generated_index":index,"name":item.get("name") if isinstance(item,dict) else None,"code":reason}); continue
            assert clean is not None
            names.append(_fold(clean["name"]))
            candidate_id=f"C{len(accepted)+1:03d}"
            score,breakdown,signals=_score(clean,profile,analysis)
            accepted.append({"candidate_id":candidate_id,**clean,"score":score,"score_breakdown":breakdown,"matched_signals":signals,"data_source":"llm_generated_concept","requires_market_verification":True})
        if not accepted: raise ToolFailure("NO_VALID_CANDIDATES","Không có candidate hợp lệ sau validation.",retryable=True)
        accepted.sort(key=lambda x:(-x["score"],x["estimated_price_range_vnd"]["maximum"],x["candidate_id"]))
        returned=accepted[:max_candidates]
        for rank,item in enumerate(returned,1): item["rank"]=rank
        return _json({"ok":True,"ranked_candidates":returned,"generation_summary":{"requested_count":max_candidates,"generated_count":len(generated),"valid_count":len(accepted),"returned_count":len(returned),"rejected_candidates":rejected}})
    except ToolFailure as exc: return _safe(exc)

def explain_recommendations(recipient_profile:dict[str,Any]|str,profile_analysis:dict[str,Any]|str,gift_candidates:list[dict[str,Any]]|str,top_k:int=5)->str:
    """Explain locked ranked candidates without changing core data.

    Summary: Generate grounded prose and merge it onto Tool 3 records.
    Role in pipeline: Tool 4/4, after deterministic ranking.
    Args:
        recipient_profile: Tool 1 profile/response.
        profile_analysis: Tool 2 analysis/response.
        gift_candidates: Tool 3 list/response.
        top_k: Number of leading candidates, 1-50.
    Returns: JSON string whose core fields come only from Tool 3.
    Error semantics: Invalid input/explanations/API failures return JSON errors.
    Use when: Ranked Tool 3 observations need user-facing reasons.
    Do not use when: Generating, re-ranking, or changing price/components/IDs.
    Side effects: Calls injected LLM; never buys, links or verifies products.
    Safety: Explanations may be imperfect; Python locks core data. Estimated
        prices and concepts require market verification before purchase.
    Example: explain_recommendations(profile, analysis, ranked, 3)
    """
    if isinstance(top_k,bool) or not isinstance(top_k,int) or not 1<=top_k<=50:
        return _error("INVALID_TOP_K","top_k phải là integer 1-50.",field="top_k",retryable=True)
    try:
        profile=_validate_profile(_parse_dict(recipient_profile,"recipient_profile","recipient_profile"))
        analysis=_validate_analysis(_parse_dict(profile_analysis,"profile_analysis","profile_analysis"),profile)
        candidates=_parse_candidates(gift_candidates)[:top_k]; seen=set()
        core=("rank","candidate_id","name","components","estimated_price_range_vnd","score")
        for c in candidates:
            cid=c.get("candidate_id")
            if not isinstance(cid,str) or not cid: raise ToolFailure("INVALID_CANDIDATE_SCHEMA","Candidate thiếu candidate_id.",field="candidate_id")
            if cid in seen: raise ToolFailure("DUPLICATE_CANDIDATE","candidate_id bị trùng.",field="candidate_id")
            seen.add(cid)
            if any(f not in c for f in core): raise ToolFailure("INVALID_CANDIDATE_SCHEMA","Candidate thiếu dữ liệu cốt lõi.")
        raw=_call_tool_llm(EXPLAIN_PROMPT,{"_operation":"explain_recommendations","recipient_profile":profile,"profile_analysis":analysis,"gift_candidates":candidates})
        explanations=raw.get("explanations")
        if not isinstance(explanations,list): raise ToolFailure("INVALID_LLM_RESPONSE","LLM phải trả danh sách explanations.")
        by_id={}
        for e in explanations:
            if not isinstance(e,dict): raise ToolFailure("INVALID_LLM_RESPONSE","Explanation phải là object.")
            cid=e.get("candidate_id")
            if not isinstance(cid,str) or cid not in seen or cid in by_id: raise ToolFailure("INVALID_LLM_RESPONSE","candidate_id explanation thiếu, lạ hoặc trùng.",field="candidate_id")
            reason=_nullable(e.get("reason"),"reason"); tip=_nullable(e.get("personalization_tip"),"personalization_tip"); note=_nullable(e.get("budget_note"),"budget_note")
            if not reason or not tip or not note: raise ToolFailure("INVALID_LLM_RESPONSE","Explanation thiếu nội dung.")
            by_id[cid]={"reason":reason,"why_it_fits":_strings(e.get("why_it_fits"),"why_it_fits"),"personalization_tip":tip,"verify_before_buying":_strings(e.get("verify_before_buying"),"verify_before_buying"),"budget_note":note}
        if set(by_id)!=seen: raise ToolFailure("INVALID_LLM_RESPONSE","LLM chưa giải thích đủ candidate.")
        recommendations=[{"rank":c["rank"],"candidate_id":c["candidate_id"],"name":c["name"],"components":c["components"],"estimated_price_range_vnd":c["estimated_price_range_vnd"],"score":c["score"],**by_id[c["candidate_id"]],"requires_market_verification":True} for c in candidates]
        return _json({"ok":True,"recommendations":recommendations,"explanation_note":"Thứ tự và dữ liệu cốt lõi được giữ nguyên từ generate_gift_candidates."})
    except ToolFailure as exc: return _safe(exc)

AVAILABLE_TOOLS = {
    "extract_recipient_profile": extract_recipient_profile,
    "analyze_recipient_profile": analyze_recipient_profile,
    "generate_gift_candidates": generate_gift_candidates,
    "explain_recommendations": explain_recommendations,
}

if __name__ == "__main__":
    _run_smoke_tests()
