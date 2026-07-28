"use client";

import { FormEvent, KeyboardEvent, useEffect, useMemo, useRef, useState } from "react";

type ProfileKey = "relationship" | "occasion" | "interests" | "budget";
type SearchResult = { title: string; url: string; content: string };
type GiftSuggestion = { title: string; reason: string; recommended: boolean };
type ToolTrace = { tool: string; status: "success" | "skipped" | "error"; thought: string; action: string; observation: string };
type Message = { id: number; role: "agent" | "user"; text: string; sources?: SearchResult[]; suggestions?: GiftSuggestion[]; closing?: string; state?: string; trace?: ToolTrace[] };
type AgentResponse = { profile: Record<ProfileKey, string>; reply: string; sources: SearchResult[]; suggestions?: GiftSuggestion[]; closing?: string; state: string; trace: ToolTrace[] };
type ChatMode = "baseline" | "agent";

type SpeechRecognitionResultEvent = { results: { 0: { 0: { transcript: string } } } };
type BrowserSpeechRecognition = {
  lang: string;
  interimResults: boolean;
  onresult: ((event: SpeechRecognitionResultEvent) => void) | null;
  onerror: (() => void) | null;
  onend: (() => void) | null;
  start: () => void;
};
type SpeechRecognitionConstructor = new () => BrowserSpeechRecognition;

declare global {
  interface Window {
    SpeechRecognition?: SpeechRecognitionConstructor;
    webkitSpeechRecognition?: SpeechRecognitionConstructor;
  }
}

const emptyProfile: Record<ProfileKey, string> = {
  relationship: "",
  occasion: "",
  interests: "",
  budget: "",
};

const profileLabels: Record<ProfileKey, string> = {
  relationship: "Mối quan hệ",
  occasion: "Dịp tặng",
  interests: "Điều người ấy thích",
  budget: "Khoảng chi",
};

const quickStarts = [
  "Quà sinh nhật cho bạn thân nữ thích xem phim, ngân sách 500k",
  "Quà cảm ơn đồng nghiệp thích cà phê, khoảng 300k",
  "Quà kỷ niệm cho người yêu thích chơi game, ngân sách 1 triệu",
];

const toolLabels: Record<string, string> = {
  normalize_profile: "Chuẩn hóa hồ sơ",
  select_product: "Chọn sản phẩm đích",
  search_web: "Tìm kiếm sàn TMĐT",
  generate_recommendation: "Tạo khuyến nghị",
  baseline_llm: "Baseline chatbot",
};

const traceStatus: Record<ToolTrace["status"], string> = { success: "Thành công", skipped: "Bỏ qua", error: "Lỗi" };

function sourceDomain(url: string) {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return "Nguồn tham khảo";
  }
}

export default function Home() {
  const [profile, setProfile] = useState(emptyProfile);
  const [messages, setMessages] = useState<Message[]>([
    { id: 1, role: "agent", text: "Chào bạn! Bạn có thể kể một lần luôn: tặng ai, dịp gì, sở thích và ngân sách. Mình sẽ tìm một sản phẩm cụ thể cho bạn." },
  ]);
  const [input, setInput] = useState("");
  const [mode, setMode] = useState<ChatMode>("agent");
  const [isThinking, setIsThinking] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [listeningTranscript, setListeningTranscript] = useState("");
  const messageId = useRef(2);
  const ambientAudio = useRef<HTMLAudioElement | null>(null);
  const recognizedText = useRef("");

  const complete = useMemo(() => Object.values(profile).every(Boolean), [profile]);
  const filledCount = Object.values(profile).filter(Boolean).length;

  async function runGiftAgent(message: string) {
    try {
      const response = await fetch("/api/gift-agent", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, profile, mode }),
      });
      const data = (await response.json()) as AgentResponse & { error?: string };
      if (!response.ok) throw new Error(data.error ?? "Không thể xử lý yêu cầu chọn quà.");
      setProfile(data.profile);
      setMessages((items) => [...items, {
        id: messageId.current++, role: "agent",
        text: data.reply,
        sources: data.sources,
        suggestions: data.suggestions,
        closing: data.closing,
        state: data.state,
        trace: data.trace,
      }]);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Không thể tìm kiếm web lúc này.";
      setMessages((items) => [...items, { id: messageId.current++, role: "agent", text: message }]);
    } finally {
      setIsThinking(false);
    }
  }

  function startListening() {
    const Recognition = window.SpeechRecognition ?? window.webkitSpeechRecognition;
    if (!Recognition) {
      window.alert("Trình duyệt này chưa hỗ trợ nhận giọng nói. Hãy dùng Chrome hoặc Edge.");
      return;
    }

    const recognition = new Recognition();
    recognition.lang = "vi-VN";
    recognition.interimResults = false;
    recognizedText.current = "";
    setListeningTranscript("");
    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript.trim();
      recognizedText.current = transcript;
      setListeningTranscript(transcript);
      setInput(transcript);
    };
    recognition.onerror = () => {
      recognizedText.current = "";
      setListeningTranscript("");
      setIsListening(false);
    };
    recognition.onend = () => {
      const transcript = recognizedText.current.trim();
      recognizedText.current = "";
      setListeningTranscript("");
      setIsListening(false);
      if (transcript) sendMessage(transcript);
    };
    setIsListening(true);
    recognition.start();
  }

  useEffect(() => {
    const audio = ambientAudio.current;
    if (!audio) return;
    audio.volume = 0.16;
    void audio.play().catch(() => undefined);
  }, []);

  function startAmbientAudio() {
    void ambientAudio.current?.play().catch(() => undefined);
  }

  function sendMessage(rawText: string) {
    const text = rawText.trim();
    if (!text || isThinking) return;
    setMessages((items) => [...items, { id: messageId.current++, role: "user", text }]);
    setInput("");
    setIsThinking(true);
    void runGiftAgent(text);
  }

  function changeMode(nextMode: ChatMode) {
    if (nextMode === mode) return;
    setMode(nextMode);
    setProfile(emptyProfile);
    setInput("");
    setMessages([{ id: messageId.current++, role: "agent", text: nextMode === "agent" ? "Chế độ Agent đã bật. Hãy kể tặng ai, dịp gì, sở thích và ngân sách để mình tìm sản phẩm thực tế." : "Chế độ Baseline đã bật. Mình sẽ tư vấn trực tiếp từ kiến thức có sẵn, không gọi web hay tool." }]);
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    sendMessage(input);
  }

  function onKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage(input);
    }
  }

  return (
    <main className="gift-page" onPointerDown={startAmbientAudio}>
      <audio ref={ambientAudio} src="/audio/tour-ambient-loop.mp3" autoPlay loop preload="auto" aria-hidden="true" />
      <div className="ambient ambient-one" aria-hidden="true" />
      <div className="ambient ambient-two" aria-hidden="true" />
      <section className="app-shell" aria-label="Mèo Hồng, trợ lý chọn quà">
        <header className="app-nav">
          <div className="brand-lockup">
            <div className="kitty-mark" aria-hidden="true"><img src="/f874ea293fdb543ed108da1e155c9fd5.gif" alt="" /></div>
            <div><p className="team-name">Team Heli Kitto</p><p className="brand-name">Mèo Hồng</p><p className="brand-subtitle">Trợ lý chọn quà</p></div>
          </div>
          <div className="mode-switch" aria-label="Chọn chế độ chatbot">
            <button type="button" className={mode === "baseline" ? "active" : ""} onClick={() => changeMode("baseline")}>Baseline</button>
            <button type="button" className={mode === "agent" ? "active" : ""} onClick={() => changeMode("agent")}>Agent</button>
          </div>
        </header>

        <div className="main-layout">
          <section className="conversation-card">
            <header className="conversation-top">
              <div className="welcome-copy">
                <p className="tiny-label">Chọn quà có chủ đích</p>
                <h1>Quà xinh sẽ dễ tìm hơn<br />khi mình hiểu người nhận.</h1>
                <p>Chỉ cần kể tự nhiên. Mình hỏi từng ý nhỏ, không biến bạn thành người điền form.</p>
              </div>
              <div className="gift-illustration" aria-hidden="true"><span className="ribbon-loop loop-left" /><span className="ribbon-loop loop-right" /><span className="ribbon-knot" /><span className="gift-sparkle sparkle-one">✦</span><span className="gift-sparkle sparkle-two">♡</span></div>
            </header>

            <div className="chat-stream" aria-live="polite">
              {messages.map((message) => (
                <article key={message.id} className={`chat-message ${message.role}`}>
                  {message.role === "agent" && <div className="message-avatar" aria-hidden="true"><img src="/f874ea293fdb543ed108da1e155c9fd5.gif" alt="" /></div>}
                  <div className="message-content">
                    <p>{message.text}</p>
                    {message.suggestions && <ol className="gift-suggestions" aria-label="Gợi ý quà phù hợp">
                      {message.suggestions.map((suggestion, index) => <li key={`${suggestion.title}-${index}`} className={suggestion.recommended ? "recommended" : ""}>
                        <span className="suggestion-rank">{String(index + 1).padStart(2, "0")}</span>
                        <span><strong>{suggestion.title}</strong><small>{suggestion.reason}</small></span>
                        {suggestion.recommended && <em>Nên chọn</em>}
                      </li>)}
                    </ol>}
                    {message.closing && <p className="recommendation-closing">{message.closing}</p>}
                    {message.sources && message.sources.length > 0 && <ul className="search-sources" aria-label="Nguồn tham khảo">
                      {message.sources.slice(0, 3).map((source, index) => <li key={source.url}>
                        <a href={source.url} target="_blank" rel="noreferrer">
                          <span className="source-number">{String(index + 1).padStart(2, "0")}</span>
                          <span className="source-copy"><strong>{source.title}</strong><small>{sourceDomain(source.url)}</small></span>
                          <span className="source-action">Xem ↗</span>
                        </a>
                      </li>)}
                    </ul>}
                    {message.trace && <details className="tool-trace">
                      <summary>Trace agent · {message.state ?? "đã xử lý"}</summary>
                      <ol>
                        {message.trace.map((item, index) => <li key={`${item.tool}-${index}`} className={item.status}>
                          <div><strong>{index + 1}. {toolLabels[item.tool] ?? item.tool}</strong><p><b>Thought:</b> {item.thought}</p><p><b>Action:</b> <code>{item.action}</code></p><p><b>Observation:</b> {item.observation}</p></div><em>{traceStatus[item.status]}</em>
                        </li>)}
                      </ol>
                    </details>}
                  </div>
                </article>
              ))}
              {isThinking && <div className="thinking"><img src="/loading.gif" alt="" /> Mèo Hồng đang tìm quà phù hợp</div>}
            </div>

            {mode === "agent" && !complete && messages.length < 3 && (
              <div className="quick-starts" aria-label="Gợi ý mở đầu">
                {quickStarts.map((text) => <button type="button" key={text} onClick={() => sendMessage(text)}>{text}</button>)}
              </div>
            )}

            {isListening && <div className="listening-status" role="status"><span className="listening-pulse" />Đang lắng nghe{listeningTranscript ? `: “${listeningTranscript}”` : "..."}</div>}
            <form className="chat-composer" onSubmit={handleSubmit}>
              <label htmlFor="gift-message" className="sr-only">Nhập tin nhắn</label>
              <textarea id="gift-message" value={input} onChange={(event) => setInput(event.target.value)} onKeyDown={onKeyDown} placeholder="Ví dụ: Quà sinh nhật cho bạn thân thích xem phim, ngân sách 500k" rows={1} />
              <button type="button" className={`mic-button ${isListening ? "listening" : ""}`} onClick={startListening} aria-label="Nói bằng giọng nói" disabled={isThinking || isListening}>{isListening ? "●" : "◉"}</button>
              <button type="submit" aria-label="Gửi tin nhắn" disabled={!input.trim() || isThinking}>↑</button>
            </form>
          </section>

          <aside className="profile-card">
            <div className="profile-heading"><p className="tiny-label">Mình đang ghi nhớ</p><span>{filledCount}/4 ý chính</span></div>
            <p className="profile-intro">Từ những gì bạn đã kể, không lưu thông tin cá nhân nhạy cảm.</p>
            <div className="profile-list">
              {(Object.keys(profile) as ProfileKey[]).map((key) => (
                <div key={key} className={`profile-row ${profile[key] ? "ready" : ""}`}>
                  <span className="profile-icon">{profile[key] ? "✓" : "·"}</span>
                  <div><p>{profileLabels[key]}</p><strong>{profile[key] || "Chưa có"}</strong></div>
                </div>
              ))}
            </div>
            {complete && <div className="profile-status complete"><span>♡</span><p>Đủ thông tin để bắt đầu chọn quà rồi.</p></div>}
            {complete && <div className="gift-preview"><span>Đang chọn</span><strong>Gợi ý quà phù hợp</strong><p>Ưu tiên món quà có lý do rõ ràng, không phải danh sách chung chung.</p></div>}
          </aside>
        </div>
      </section>
    </main>
  );
}
