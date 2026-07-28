import { useState, useRef, useEffect } from 'react';
import './ChatPanel.css';

const STEP_ICONS = {
  thought: '🧠',
  action: '🛠️',
  observation: '👁️',
  final_answer: '🏁'
};

const STEP_LABELS = {
  thought: 'Thought',
  action: 'Action',
  observation: 'Observation',
  final_answer: 'Final Answer'
};

const QUICK_ACTIONS = [
  { label: '🎬 Phim đang chiếu', message: 'Có phim gì đang chiếu ở CGV?' },
  { label: '🕵️ Suất chiếu Conan', message: 'Phim Conan chiếu lúc mấy giờ ở CGV Vincom Bà Triệu?' },
  { label: '💺 Xem ghế trống', message: 'Còn ghế trống nào suất 19h Conan ở CGV Vincom Bà Triệu ngày 2026-07-28?' },
  { label: '🎟️ Đặt vé Conan', message: 'Đặt giúp tôi 2 ghế A5, A6 suất 19h phim Conan ở CGV Vincom Bà Triệu ngày 2026-07-28, tên Khanh' }
];

/**
 * Format message content - handle simple markdown-like bold markers
 */
function formatContent(text) {
  if (!text) return '';
  // Split by **bold** patterns
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={i}>{part.slice(2, -2)}</strong>;
    }
    return part;
  });
}

/**
 * ChatPanel - Left side agent chat interface with ReAct step visualization
 */
export default function ChatPanel({ messages, isTyping, agentSteps, onSendMessage, onClear }) {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, agentSteps, isTyping]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    onSendMessage(input);
    setInput('');
  };

  const handleQuickAction = (message) => {
    onSendMessage(message);
    inputRef.current?.focus();
  };

  return (
    <div className="chat-panel">
      {/* Header */}
      <div className="chat-header">
        <div className="chat-header-left">
          <div className="agent-avatar">🤖</div>
          <div className="agent-info">
            <h2>Trợ Lý Đặt Vé CGV</h2>
            <div className="agent-status">
              <span className="status-dot" />
              <span>ReAct Agent • Online</span>
            </div>
          </div>
        </div>
        <button className="btn-clear" onClick={onClear}>
          🗑️ Xóa chat
        </button>
      </div>

      {/* Messages */}
      <div className="chat-messages">
        {messages.map(msg => (
          <div key={msg.id} className={`message message--${msg.role}`}>
            <div className="message-avatar">
              {msg.role === 'user' ? '👤' : '🤖'}
            </div>
            <div>
              <div className="message-bubble">
                {formatContent(msg.content)}
              </div>
              <div className="message-time">
                {msg.timestamp.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })}
              </div>
            </div>
          </div>
        ))}

        {/* Agent Steps (ReAct Trace) */}
        {agentSteps.length > 0 && (
          <div className="agent-steps">
            {agentSteps.map(step => (
              <div key={step.id} className={`agent-step agent-step--${step.type}`}>
                <span className="step-icon">{STEP_ICONS[step.type]}</span>
                <div className="step-content">
                  <div className="step-label">{STEP_LABELS[step.type]}</div>
                  <div className="step-text">{step.content}</div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Typing Indicator */}
        {isTyping && (
          <div className="typing-indicator">
            <div className="typing-dots">
              <span className="typing-dot" />
              <span className="typing-dot" />
              <span className="typing-dot" />
            </div>
            <span className="typing-label">Agent đang suy luận...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="chat-input-area">
        <form onSubmit={handleSubmit} className="chat-input-wrapper">
          <input
            ref={inputRef}
            type="text"
            className="chat-input"
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder="Nhập tin nhắn... (VD: Phim gì đang chiếu?)"
            disabled={isTyping}
          />
          <button type="submit" className="btn-send" disabled={isTyping || !input.trim()}>
            ▶
          </button>
        </form>

        {/* Quick Actions */}
        <div className="quick-actions">
          {QUICK_ACTIONS.map(action => (
            <button
              key={action.label}
              className="quick-action-btn"
              onClick={() => handleQuickAction(action.message)}
              disabled={isTyping}
            >
              {action.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
