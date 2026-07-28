# 👥 DANH SÁCH THÀNH VIÊN VÀ PHÂN CÔNG NHÓM (LAB 3 - RE-ACT AGENT)

## 📋 THÔNG TIN NHÓM

| STT | MSSV | Họ và tên | Vai trò | Branch Git | File đảm nhận chính | Nhiệm vụ chính |
| :---: | :---: | :--- | :--- | :--- | :--- | :--- |
| **1** | **2A202601115** | **Nguyễn Phúc Hưng** | **Tech Lead & Core Integrator** | `develop` | `src/app.py` | • Quản lý Git Repository (`develop`, `main`), duyệt Pull Request.<br>• Tích hợp các module (`tools.py`, `prompts.py`, `test_cases.json`) vào `app.py`.<br>• Chạy thử nghiệm ReAct Agent Loop & làm đầu mối Demo / Cross-Audit. |
| **2** | **2A202601087** | **Nguyễn Văn Phong** | **Product Architect & Evaluator** | `feature/phong-eval` | `config/test_cases.json`<br>`docs/trace_eval.md` | • Định hướng bài toán thực tế cho Agent.<br>• Xây dựng 5 Test Cases (Đơn giản, Multi-step, Edge case).<br>• Đánh giá Scoring Matrix & trích xuất Trace Log (`Thought -> Action -> Observation`). |
| **3** | **2A202601781** | **Nguyễn Hữu Khánh Tùng** | **Tool Engineer** | `feature/tung-tools` | `src/tools.py` | • Định nghĩa và phát triển các hàm Tool cho Agent.<br>• Viết docstring/description chuẩn xác để LLM dễ nhận diện Tool.<br>• Xử lý ngoại lệ (tránh crash ứng dụng khi Tool bị lỗi). |
| **4** | **2A202601845** | **Nguyễn Tuấn Vũ** | **Prompt & Safeguard Engineer** | `feature/vu-prompts` | `src/prompts.py`<br>`docs/hybrid_flowchart.mermaid` | • Soạn `CHATBOT_BASELINE_PROMPT` và `REACT_SYSTEM_PROMPT` (ép AI suy luận Thought ➔ Action).<br>• Thiết lập Guardrails (`MAX_ITERATIONS`, phanh an toàn chống lặp vô hạn).<br>• Vẽ sơ đồ phân luồng **Hybrid Flowchart** (Chatbot Path vs ReAct Agent Path). |

---

## ⏱️ QUY TRÌNH THỰC HÀNH THEO BRANCH RIÊNG

1. **Chuyển sang branch của bạn**:
   - Nguyễn Văn Phong: `git checkout feature/phong-eval`
   - Nguyễn Hữu Khánh Tùng: `git checkout feature/tung-tools`
   - Nguyễn Tuấn Vũ: `git checkout feature/vu-prompts`
   - Nguyễn Phúc Hưng (Lead): `git checkout develop`

2. **Cập nhật code từ develop trước khi sửa**:
   ```bash
   git pull origin develop
   ```

3. **Đẩy code lên branch riêng**:
   ```bash
   git add .
   git commit -m "Moc X: [Ten thanh vien] cap nhat"
   git push origin <ten-branch-cua-ban>
   ```

4. **Tạo Pull Request trên GitHub**: Đẩy code về nhánh `develop` để Tech Lead review & merge.
