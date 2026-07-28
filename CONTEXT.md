# CONTEXT.md — Lab 3: Chatbot vs ReAct Agent (Topic 8: Financial Data Helper)

## 1. PROJECT SUMMARY

| Item | Detail |
|------|--------|
| **Repo origin** | `Muscar1a/Day-3-Lab-Chatbot-vs-react-agent-E402` (branch: `muscar1a-main`) |
| **Lab** | VinUni Bài Lab 3: Chatbot vs ReAct Agent |
| **Topic** | #8: Trợ Lý Duyệt Chi Phí Doanh Nghiệp / Financial Data Helper Chatbot |
| **Goal** | Build a ReAct Agent that retrieves Vietnam stock market data, company financials, analyzes expenses, and answers financial queries using tools |
| **Python** | 3.14.6 |
| **venv** | `.venv/` (created, active) |

## 2. 4-LEVEL AI SPECTRUM

| Level | Type | What It Does |
|-------|------|-------------|
| 1 | Rule-Based Bot | if/else keyword matching (no LLM) |
| 2 | LLM Chatbot | Pure LLM, no tool use — answers from static knowledge |
| 3 | **ReAct Agent** | Thought → Action → Observation loop with tools (TARGET) |
| 4 | Autonomous Agent | Self-planning, memory, goal decomposition (Bonus +10%) |

Our ReAct Agent needs financial tools to go beyond what a static LLM knows.

## 3. FINANCIAL DATA SOURCES — WHAT WORKS

### ✅ yfinance (Yahoo Finance) — PRIMARY SOURCE

```python
import yfinance as yf
```

| Data Type | Example | Status |
|-----------|---------|--------|
| VN Stocks (price) | `yf.Ticker("VNM.VN")` | ✅ Live |
| VN Stocks (fundamentals) | `.info` → marketCap, PE, dividendYield, sector | ✅ |
| VN Stocks (financials) | `.financials` → income statement 4 years | ✅ |
| VN Stocks (balance sheet) | `.balance_sheet` | ✅ Expected |
| VN Stocks (cash flow) | `.cash_flow` | ✅ Expected |
| VN Stocks (historical) | `.history(period="1mo")` | ✅ |
| ETF | `E1VFVN30.VN` | ✅ (VN30 ETF) |
| Forex | `USDVND=X`, `EURVND=X` | ✅ |
| US Indices | `^DJI`, `^GSPC` | ✅ |
| VNIndex | `^VNINDEX` | ❌ 404 — not on Yahoo Finance |

**Tested tickers that work:** VNM.VN, VCB.VN, VIC.VN, HPG.VN, FPT.VN, E1VFVN30.VN

**Sample data (VNM.VN as of 2026-07-28):**
- Price: 58,200 VND
- Market Cap: ~121.6 trillion VND
- P/E: 12.98
- Dividend Yield: 3.2%
- Sector: Consumer Defensive

### ❌ vnstock — BLOCKED (Python 3.14 incompatibility)

`vnstock` requires `numpy`, which fails metadata generation on Python 3.14. Cannot install.
**Workaround:** Use yfinance for the same data categories.

### ❌ investpy — BLOCKED (Python 3.14 incompatibility)

`investpy` uses deprecated `pkg_resources` (removed in Python 3.12+). Cannot import.
**Workaround:** yfinance covers most investpy use cases.

### ❌ dnspy (pip) — WRONG PACKAGE

`dnspy` on PyPI is a DNS domain parser (Mozilla TLD list), NOT a Vietnamese financial data library. The user likely meant a different package or it may not exist on PyPI under this name.

## 4. PROJECT STRUCTURE (CURRENT)

```
.
├── .env.example              # API keys config
├── .venv/                    # Python venv (3.14.6)
├── requirements.txt          # google-genai, openai, anthropic, python-dotenv, requests
├── config/
│   └── test_cases.json       # 5 test cases (simple, multi-step, edge)
├── src/
│   ├── app.py                # Main app: Chatbot baseline + ReAct Agent loop
│   ├── providers.py          # Multi-provider LLM adapter (Gemini, OpenAI, Anthropic, OpenRouter, Mock)
│   ├── prompts.py            # System prompts + guardrails (MAX_ITERATIONS=3)
│   └── tools.py              # Tool registry (get_weather, search_flights — STOCK demos)
├── docs/
│   ├── CODELAB.md            # Step-by-step lab instructions
│   ├── PHAN_CONG_CONG_VIEC.md
│   ├── DANH_SACH_DE_TAI.md  # 10 suggested topics
│   └── trace_eval.md         # Trace logs & evaluation
└── CONTEXT.md                # THIS FILE
```

## 5. ARCHITECTURE NOTES

- **LLM Providers:** Factory pattern via `get_llm_provider()` — reads `LLM_PROVIDER` env var
- **Tools:** Plain Python dict `AVAILABLE_TOOLS` in `tools.py` — simple function registration
- **ReAct Loop:** Currently hardcoded (app.py line 60-78) — needs to be made dynamic with real LLM parsing
- **Guardrails:** `MAX_ITERATIONS=3`, `TIMEOUT_SECONDS=10`
- **Test Cases:** 5 cases in JSON — from simple LLM to multi-step tool use to edge case traps

## 6. PLAN: FINANCIAL DATA HELPER REACT AGENT

### Tools to Build (in `tools.py`)

| Tool | Function | Data Source |
|------|----------|-------------|
| `get_stock_price(symbol)` | Current price, change % | yfinance |
| `get_company_info(symbol)` | Market cap, P/E, sector, dividend | yfinance |
| `get_stock_history(symbol, period)` | OHLCV historical data | yfinance |
| `get_financial_ratios(symbol)` | P/E, EPS, ROE, debt/equity | yfinance (computed) |
| `get_forex_rate(pair)` | USD/VND, EUR/VND exchange rate | yfinance |
| `get_market_overview()` | Top movers, VN30 ETF snapshot | yfinance |
| `search_stock(query)` | Find ticker by company name | yfinance search or static mapping |

### Test Cases to Write (in `test_cases.json`)

1. **Simple:** "Giá cổ phiếu VNM hôm nay là bao nhiêu?"
2. **Analysis:** "So sánh P/E của VNM và HPG, cổ phiếu nào đang rẻ hơn?"
3. **Multi-tool:** "Cho tôi giá VCB, tỷ giá USD/VND hôm nay, và tính giá VCB theo USD"
4. **Historical:** "VNM đã tăng bao nhiêu % trong 1 tháng qua?"
5. **Edge case:** "Tra cứu mã cổ phiếu ATLANTIS" → tool báo lỗi, guardrail kích hoạt

### Evaluation Criteria (from rubric)

| Criteria | Weight | How We Meet It |
|----------|--------|----------------|
| Agentic Fit | 20% | Financial queries need real-time data → strong fit |
| ReAct + Tools | 30% | 5+ financial tools with real API calls |
| Guardrails | 20% | MAX_ITERATIONS, timeout, error handling per tool |
| Attack/Defense | 20% | Cross-audit: bad symbols, invalid dates, multi-tool abuse |
| Flowchart | 10% | Hybrid decision: when Chatbot (simple) vs Agent (data) |

## 7. KNOWN ISSUES

1. **Python 3.14 too new:** vnstock, investpy blocked. yfinance is sufficient.
2. **No VNIndex:** Yahoo Finance dropped `^VNINDEX`. Use VN30 ETF (`E1VFVN30.VN`) as proxy.
3. **Hardcoded ReAct loop:** `app.py` demo loop is hardcoded — needs real LLM-driven ReAct parsing.
4. **dnspy confusion:** The PyPI `dnspy` package is a DNS tool. Vietnam financial `dnspy` may be a different package or needs specific install instructions not found on PyPI.

## 8. NEXT STEPS

1. Rewrite `tools.py` with financial tools backed by yfinance
2. Rewrite `test_cases.json` for financial domain
3. Make `app.py` ReAct loop dynamic (parse LLM `Action:` output, execute tools, feed `Observation:` back)
4. Update `prompts.py` with financial domain system prompt
5. Add yfinance to `requirements.txt`
6. Test all 5 test cases with mock provider, then with real API key
7. Write `trace_eval.md` with scoring matrix
8. Draw `hybrid_flowchart.mermaid`
