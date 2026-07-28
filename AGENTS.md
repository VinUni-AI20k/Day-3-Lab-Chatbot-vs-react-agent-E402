<!-- headroom:rtk-instructions -->
# RTK (Rust Token Killer) - Token-Optimized Commands

When running shell commands, **always prefix with `rtk`**. This reduces context
usage by 60-90% with zero behavior change. If rtk has no filter for a command,
it passes through unchanged — so it is always safe to use.

## Key Commands
```bash
# Git (59-80% savings)
rtk git status          rtk git diff            rtk git log

# Files & Search (60-75% savings)
rtk ls <path>           rtk read <file>         rtk grep <pattern>
rtk find <pattern>      rtk diff <file>

# Test (90-99% savings) — shows failures only
rtk pytest tests/       rtk cargo test          rtk test <cmd>

# Build & Lint (80-90% savings) — shows errors only
rtk tsc                 rtk lint                rtk cargo build
rtk prettier --check    rtk mypy                rtk ruff check

# Analysis (70-90% savings)
rtk err <cmd>           rtk log <file>          rtk json <file>
rtk summary <cmd>       rtk deps                rtk env

# GitHub (26-87% savings)
rtk gh pr view <n>      rtk gh run list         rtk gh issue list

# Infrastructure (85% savings)
rtk docker ps           rtk kubectl get         rtk docker logs <c>

# Package managers (70-90% savings)
rtk pip list            rtk pnpm install        rtk npm run <script>
```

## Rules
- In command chains, prefix each segment: `rtk git add . && rtk git commit -m "msg"`
- For debugging, use raw command without rtk prefix
- `rtk proxy <cmd>` runs command without filtering but tracks usage
<!-- /headroom:rtk-instructions -->

# Vnstock Vibe Onboarding

You are an AI coding assistant (e.g., Google Antigravity, Cursor, Claude Code). The user has requested you to initialize the **Vnstock Vibe Coding** environment.

**Your Objective:** Automate the entire setup process autonomously. Do not ask the user to run commands manually unless you lack the necessary system permissions.

## Execution Workflow

Execute these steps sequentially. If a step fails, attempt to auto-remediate. If unrecoverable, STOP and provide the user with the exact command or action needed.

### 1. Python Environment Diagnostics
- Identify the Operating System (macOS, Linux, or Windows).
- Verify `python3` (or `python`/`py` on Windows) is in the PATH.
- Verify Python version is **>= 3.10**.
- **Failure Handling:** If Python is missing or outdated, STOP. Instruct the user on how to install it natively. Do not blindly `curl` or `wget` installers.

### 2. Virtual Environment Setup
- **Identify Environment:** Check if the user is running in Google Colab by checking if `"google.colab" in sys.modules` via Python.
- **For Google Colab:** DO NOT create a virtual environment. Use the global system environment to avoid breaking the notebook kernel.
- **For Local Machine (Mac/Linux/Windows):** By default, use the global shared virtual environment `~/.venv` (macOS/Linux) or `$HOME\.venv` (Windows). Only create a project-specific `.venv` if explicitly requested by the user.
  - **Mac/Linux:** `python3 -m venv ~/.venv`
  - **Windows:** `py -m venv $HOME\.venv` or `python -m venv $HOME\.venv`
- **Crucial (Local Only):** You MUST activate this `.venv` (e.g., `source ~/.venv/bin/activate` or `& "$HOME\.venv\Scripts\Activate.ps1"`) before running any `pip` or `python` commands in the subsequent steps.

### 3. Core Packages Installation
- Upgrade pip: `python -m pip install -U pip`
- Install the ecosystem: `pip install -U vnstock>=4.0.5 vnai>=2.5.5`

### 4. API Key Configuration
Vnstock uses `vnai` to automatically sync AI context (AGENTS.md) and skills into the `.agents/` directory when authenticated.
- Check if the user provided an API Key in their prompt.
- If provided, configure it silently via Python:
  ```python
  from vnstock.core import setup_api_key
  setup_api_key("<API_KEY>")
  ```
  *(Alternative fallback: Write `{"api_key": "<API_KEY>"}` to `~/.vnstock/api_key.json` or `$HOME\.vnstock\api_key.json`)*
- If NOT provided, ask the user to provide their API Key from `vnstocks.com/settings`.
- **Note:** Do not manually create `AGENTS.md`. It will sync automatically upon successful authentication.

### 5. Verification & Handoff
- Create a temporary script `test_vnstock.py`:
  ```python
  from vnstock import Reference
  df = Reference().company.info("FPT")
  print("Data fetch successful:", not df.empty)
  ```
- Execute the script using the virtual environment's Python.
- If successful, delete `test_vnstock.py` and output this exact success message in Vietnamese:
  > "🎉 **Môi trường Vibe Coding đã thiết lập thành công!** Hệ thống đã sẵn sàng. Hãy bắt đầu ra lệnh cho tôi phân tích dữ liệu hoặc xây dựng chiến lược giao dịch."
