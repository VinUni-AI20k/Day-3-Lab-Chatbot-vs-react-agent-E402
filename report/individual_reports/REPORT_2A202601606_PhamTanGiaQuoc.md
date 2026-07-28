# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Pham Tan Gia Quoc
- **Student ID**: 2A202601606
- **Role**: Role 3 - Prompt & Safeguard Engineer
- **Date**: 2026-07-28

---

## I. Technical Contribution (15 Points)

Toi phu trach **Role 3 - Prompt & Safeguard Engineer**. Phan viec cua toi la viet va dieu chinh system prompt cho hai che do, quy dinh Tool Contract cho ReAct, va dat cac rang buoc de Agent khong tu tao du lieu khi chua co Observation.

- **Modules implemented**: `src/prompts.py`
- **Modules collaborated/tested**: `src/app.py`, `config/test_cases.json`, `docs/trace_eval.md`

### Code highlights

1. **Tach prompt cua Baseline va ReAct**

   `CHATBOT_BASELINE_PROMPT` quy dinh Chatbot chi tra loi bang kien thuc co san, khong goi tool va khong tu nhan da tra cuu du lieu. Nho do, Baseline la doi chung dung nghia khi so sanh voi Agent.

   ```python
   Ban la mot Chatbot tu van tinh yeu & tinh cam thong thuong.
   Hay tra loi cau hoi cua nguoi dung mot cach than thien dua tren kien thuc chung co san.
   Neu nguoi dung yeu cau tra cuu danh sach nguoi that hoac tinh diem tuong thich du lieu thuc te thoi gian thuc, hay lich su thong bao rang ban khong co truy cap du lieu he thong.
   ```

2. **Dinh nghia ReAct Tool Contract**

   Trong `REACT_SYSTEM_PROMPT`, moi luot LLM chi duoc tra ve mot trong hai khuon dang sau:

   ```text
   Thought: Suy luan chi tiet ve y dinh cua nguoi dung va cac thong tin da thu thap duoc.
   Action: ten_cong_cu[cac_tham_so_chuan_json_hoac_dang_chuoi]
   ```

   hoac:

   ```text
   Thought: Danh gia ket qua thu duoc hoac nhan dien thong tin con thieu.
   Final Answer: Loi phan hoi am ap, chu dao cua Ba Moi AI gui toi nguoi dung.
   ```

   Contract nay giup `agent.py` co the trich xuat Action bang regex (`re.search(r'Action:\s*`?([a-zA-Z0-9_]+)`?\s*\[(.*?)\]', llm_out)`) va quyet dinh giua nhanh goi tool va nhanh ket thuc.

3. **Intent routing va rang buoc tool path**

   Prompt cua ReAct phan biet ro:

   - Y dinh `SEARCH`: Nguoi dung muon tim goi y ghep doi. Can goi `search_candidates` voi cac tham so: `target_gender`, `min_age`, `max_age`, `location`, `query_interests`.
   - Y dinh `COMPATIBILITY`: Nguoi dung muon danh gia do hop nhau. Can goi `calculate_compatibility` voi hai doi tuong cu the.

4. **Grounding va guardrails**

   Toi bo sung cac rang buoc trong prompt va config: Agent khong duoc tu tao Observation; chi duoc ket luan khi co ket qua tu tool; khong duoc tu doan hay fallback tham so mac dinh.

   Prompt dong thoi chi dan xu ly loi bang cau tra loi lich su, khong co gang lap lai tool loi. Gioi han vong lap duoc dat la:

   ```python
   MAX_ITERATIONS = 5
   MAX_INFO_GATHERING_TURNS = 5
   MAX_TOOL_CALLS_PER_TURN = 3
   ```

### Ket qua dong gop duoc xac nhan

- Case 1 (ly thuyet): Agent tra loi bang `Final Answer` ngay, khong goi tool.
- Case 2 (search): Agent goi `search_candidates` voi tham so day du, tra ve danh sach ung vien co PII masking.
- Case 3 (compatibility): Agent goi `calculate_compatibility` cho 2 ho so C001 va C002, nhan total_score 87.5/100.
- Case 4 (thieu thong tin): Agent phat hien thieu location, age range, interests; khong goi tool, dat cau hoi bo sung.
- Case 5 (edge case): Tool `search_candidates` khong tim thay ket qua khop cung, kich hoat Relaxed Search.
- Tool contract da duoc kiem tra doc lap: `calculate_compatibility` yeu cau du thong tin ca 2 nguoi va thong bao loi ro rang khi thieu.

---

## II. Debugging Case Study (10 Points)

### Problem description

Khi LLM tra Action voi tham so JSON trong dau ngoac vuong, parser gap kho khan trong viec phan tach tham so:

```text
Action: search_candidates[{"city":"Hà Nội","age":22,"interest":"âm nhạc"}]
```

Ham `parse_and_execute_tool` trong `agent.py` xu ly theo 3 buoc: thu giai ma JSON dict, thu phan tich Kwargs, va cuoi cung phan tach bang `split(",")` (dòng 67). Trong truong hop JSON hop le, buoc 1 (JSON decode) duoc uu tien truoc. Tuy nhien, neu LLM tra ve Action khong dung format JSON ma la dang CSV, parser co the tach sai tham so.

### Log source

`logs/trace_eval_2026-07-28.txt`, Test #4:

```text
[Action]: search_candidates(['{"city":"Hà Nội', 'age":22', 'interest":"âm nhạc"}'])
[Observation]: ... Minh Anh ... Diem phu hop: 45 ...
```

### Diagnosis

Nguyen nhan nam o dong `raw_tokens = [t.strip().strip('"\'') for t in clean_str.split(",") if t.strip()]` trong `agent.py`. Dau phay trong JSON dict bi xem nham la delimiter giua cac positional arguments. Buoc 1 (JSON decode) chi hoat dong neu JSON la toan bo args_str, nhung LLM co the output JSON mix voi format khac.

Voi vai tro Role 3, toi xac dinh day la gioi han cua **text Tool Contract**: prompt da huong dan dung JSON format, nhung Action tu do co the khong nhat quan, dan den parser gap edge case.

### Solution / recommendation

Prompt hien tai da khuyen khich dung JSON hoac Kwargs format. Buoc can lam tiep la chuyen sang structured output / function calling cua LLM provider (Groq/Gemini):

```json
{"tool":"search_candidates","arguments":{"city":"Ha Noi","age":22,"interest":"am nhac"}}
```

Cai tien parser hien tai: thu giai ma JSON truoc khi split dau phay, va neu that bai moi fallback sang CSV split. Sau khi sua, can chay lai Test Case 4 va yeu cau Final Answer phai ghi ro score va nguon du lieu.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

1. **Reasoning**: `Thought` va `Action` lam ro Agent dang lam gi. O case 3, trace cho thay ly do goi `calculate_compatibility`, Observation tra ve `total_score: 87.5` voi breakdown chi tiet. Baseline chi tao tu van chung, khong the tinh diem.

2. **Reliability**: Agent co the kem hon Baseline khi provider bi rate limit hoac Mock fallback. O cac case do, agent.py co co che `process_message_llm_react` tra ve `None` neu phat hien Mock, roi tuong chat qua `process_message` rule-based path. Baseline van tra loi duoc khi khong can tool.

3. **Observation**: Observation la ranh gioi giua thong tin co bang chung va suy doan. Case 3 cho thay Agent chi bao cao score va breakdown co trong tool output. Can rang buoc Final Answer phai trich dan day du ket qua de dam bao tinh grounded.

---

## IV. Future Improvements (5 Points)

- **Structured tool calling**: Dung JSON Schema / function calling thay cho regex text parser de xu ly tham so phuc tap va loai bo edge case tach dau phay.
- **Grounding validator**: Truoc khi chap nhan Final Answer, kiem tra neu Observation co score thi cau tra loi phai co score day du va breakdown.
- **Provider resilience**: Dung provider co fallback chain (Groq -> Gemini -> Mock) thay vi `None` return de tranh mat thong tin.
- **Safety**: Tiep tuc dung `MAX_ITERATIONS`, `MAX_INFO_GATHERING_TURNS`, `MAX_TOOL_CALLS_PER_TURN` de tranh lap vo han va abuse tool.

> Bao cao nay dua tren code thuc te tren nhanh dev (commit ac7e480). Cac tool co ten `calculate_compatibility`, `search_candidates`, `get_weather`. Ket qua chi danh gia he thong demo va khong su dung API key trong noi dung bao cao.