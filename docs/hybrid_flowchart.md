```mermaid
  flowchart TD
      A[User hỏi] --> B{Câu hỏi đơn giản?}
      B -->|Có| C[Chatbot Baseline]
      C --> D[Trả lời kiến thức chung]
      B -->|Không| E[ReAct Agent]
      E --> F[Thought]
      F --> G[Action gọi Tool]
      G --> H[Observation]
      H --> I{Đủ bằng chứng?}
      I -->|Chưa| F
      I -->|Rồi| J[Final Answer]
      G --> K{Tool lỗi?}
      K -->|Yes| L[Safe Fallback hoặc hỏi lại]
      K -->|No| H  