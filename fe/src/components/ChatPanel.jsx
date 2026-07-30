import { useEffect, useRef, useState } from "react";
import { Bot, Send } from "lucide-react";

import { sendChat } from "../services/api";
import ChatMessage from "./ChatMessage";
import PageAttachment from "./PageAttachment";

const PAGE_MIME = "application/x-vlearn-pdf-page";

export default function ChatPanel({ currentDocument }) {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content: "Xin chào! Bạn có thể kéo một trang PDF vào đây rồi đặt câu hỏi về nội dung của trang đó.",
    },
  ]);
  const [input, setInput] = useState("");
  const [attachment, setAttachment] = useState(null);
  const [isOver, setIsOver] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const listRef = useRef(null);

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, loading]);

  function parseDrag(event) {
    const raw = event.dataTransfer.getData(PAGE_MIME) || event.dataTransfer.getData("text/plain");
    if (!raw) return null;
    try {
      const payload = JSON.parse(raw);
      if (!payload.documentId || !payload.pageNumber || !payload.filename) {
        return null;
      }
      return payload;
    } catch {
      return null;
    }
  }

  function handleDrop(event) {
    event.preventDefault();
    setIsOver(false);
    const payload = parseDrag(event);
    if (!payload) {
      setError("Trang PDF không hợp lệ.");
      return;
    }
    if (currentDocument && payload.documentId !== currentDocument.id) {
      setError("Trang này không thuộc tài liệu đang mở.");
      return;
    }
    setAttachment(payload);
    setError("");
  }

  async function handleSend() {
    const text = input.trim();
    if (!text || loading) return;
    const userMessage = { role: "user", content: text, attachment };
    setMessages((current) => [...current, userMessage]);
    setInput("");
    setLoading(true);
    setError("");
    try {
      const history = messages
        .filter((message) => message.role === "user" || message.role === "assistant")
        .slice(-8)
        .map((message) => ({ role: message.role, content: message.content }));
      const response = await sendChat({
        message: text,
        history,
        document_id: attachment?.documentId || null,
        page_number: attachment?.pageNumber || null,
      });
      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content: response.answer,
          provider: response.fallback_used ? "Gemini fallback" : "OpenAI",
        },
      ]);
    } catch (err) {
      setError(err.message || "Không thể gửi câu hỏi. Hãy thử lại.");
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  }

  return (
    <aside
      className={isOver ? "chat-panel drag-over" : "chat-panel"}
      onDragOver={(event) => {
        event.preventDefault();
        setIsOver(true);
      }}
      onDragLeave={() => setIsOver(false)}
      onDrop={handleDrop}
    >
      <header className="chat-header">
        <div className="bot-icon" aria-hidden="true">
          <Bot size={20} />
        </div>
        <div>
          <h2>VLearn Tutor</h2>
          <p>Trợ lý học theo ngữ cảnh</p>
        </div>
      </header>

      <div className="messages" ref={listRef}>
        {messages.map((message, index) => (
          <ChatMessage key={`${message.role}-${index}`} message={message} />
        ))}
        {loading && (
          <div className="chat-message assistant">
            <div className="message-bubble loading">Đang suy nghĩ...</div>
          </div>
        )}
      </div>

      {isOver && <div className="drop-hint">Thả trang PDF vào đây</div>}
      {error && <div className="inline-error">{error}</div>}

      <div className="composer">
        <PageAttachment attachment={attachment} onRemove={() => setAttachment(null)} />
        {attachment && <p className="replace-note">Kéo trang khác vào đây để thay trang hiện tại.</p>}
        <label htmlFor="chat-input" className="sr-only">Câu hỏi cho Tutor</label>
        <textarea
          id="chat-input"
          value={input}
          onChange={(event) => setInput(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Hỏi về trang đã gắn..."
          rows={3}
        />
        <button
          className="send-button"
          onClick={handleSend}
          disabled={!input.trim() || loading}
          aria-label="Gửi câu hỏi"
          title="Gửi câu hỏi"
        >
          <Send size={18} />
          Gửi
        </button>
      </div>
    </aside>
  );
}
