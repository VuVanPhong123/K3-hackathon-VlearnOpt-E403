import { useEffect, useRef, useState } from "react";
import { Bot, Send } from "lucide-react";

import { PDF_PAGE_MIME } from "../constants/dragTypes";
import { sendChatV2 } from "../services/api";
import { buildChatContext } from "../utils/chatContext";
import ChatMessage from "./ChatMessage";
import PageAttachment from "./PageAttachment";

const enableDebugPanel = import.meta.env.VITE_ENABLE_DEBUG_PANEL === "true";
const WELCOME_MESSAGE = {
  role: "assistant",
  content:
    "Xin chào! Bạn có thể nhập câu hỏi, kéo một trang PDF, bôi đen văn bản hoặc khoanh vùng hình ảnh để hỏi Tutor.",
};

function readPagePayload(dataTransfer) {
  const raw =
    dataTransfer.getData(PDF_PAGE_MIME) ||
    dataTransfer.getData("text/plain");
  if (!raw) return null;
  try {
    const payload = JSON.parse(raw);
    if (
      payload.type !== "page" ||
      typeof payload.documentId !== "string" ||
      !payload.documentId.trim() ||
      !Number.isInteger(payload.pageNumber) ||
      payload.pageNumber < 1 ||
      typeof payload.filename !== "string" ||
      !payload.filename.trim()
    ) {
      return null;
    }
    return payload;
  } catch {
    return null;
  }
}

export default function ChatPanel({
  currentDocument,
  activePage,
  contextAttachment,
  setContextAttachment,
  onCitationClick,
}) {
  const [messages, setMessages] = useState([WELCOME_MESSAGE]);
  const [input, setInput] = useState("");
  const [attachment, setAttachment] = useState(null);
  const [conversationId, setConversationId] = useState(null);
  const [isOver, setIsOver] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const listRef = useRef(null);
  const inputRef = useRef(null);
  const dragEnterCount = useRef(0);

  useEffect(() => {
    if (typeof listRef.current?.scrollTo !== "function") return;
    listRef.current.scrollTo({
      top: listRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, loading]);

  useEffect(() => {
    setAttachment(null);
    setContextAttachment?.(null);
    setConversationId(null);
    setMessages([WELCOME_MESSAGE]);
    setInput("");
    setError("");
  }, [currentDocument?.id, setContextAttachment]);

  useEffect(() => {
    setAttachment(contextAttachment || null);
    if (contextAttachment?.type === "text_selection") {
      setInput((current) => current || "Giải thích đoạn được chọn này.");
    } else if (contextAttachment?.type === "visual_region") {
      setInput((current) => current || "Giải thích nội dung trong vùng được chọn.");
    }
    if (contextAttachment) inputRef.current?.focus();
  }, [contextAttachment]);

  function attachPage(payload) {
    setAttachment(payload);
    setContextAttachment?.(payload);
    setError("");
  }

  function handleDragEnter(event) {
    event.preventDefault();
    dragEnterCount.current += 1;
    setIsOver(true);
  }

  function handleDragOver(event) {
    event.preventDefault();
    event.dataTransfer.dropEffect = "copy";
  }

  function handleDragLeave() {
    dragEnterCount.current = Math.max(0, dragEnterCount.current - 1);
    if (dragEnterCount.current === 0) setIsOver(false);
  }

  function handleDrop(event) {
    event.preventDefault();
    dragEnterCount.current = 0;
    setIsOver(false);
    const payload = readPagePayload(event.dataTransfer);
    if (!payload) {
      setError("Dữ liệu trang PDF không hợp lệ.");
      return;
    }
    if (!currentDocument || payload.documentId !== currentDocument.id) {
      setError("Trang này không thuộc tài liệu đang mở.");
      return;
    }
    attachPage(payload);
  }

  async function handleSend() {
    const text = input.trim();
    if (!text || loading) return;

    const selectedAttachment = attachment;
    setMessages((current) => [
      ...current,
      { role: "user", content: text, attachment: selectedAttachment },
    ]);
    setInput("");
    setLoading(true);
    setError("");

    try {
      const history = messages
        .filter((message) => message.role === "user" || message.role === "assistant")
        .slice(-8)
        .map((message) => ({ role: message.role, content: message.content }));
      const response = await sendChatV2({
        message: text,
        conversation_id: conversationId,
        history,
        document_id: currentDocument?.id || null,
        context: buildChatContext({
          attachment: selectedAttachment,
          activePage,
        }),
        answer_mode: currentDocument ? "document_only" : "allow_general_knowledge",
      });
      setConversationId(response.conversation_id);
      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content: response.answer,
          provider: response.provider || response.trace?.provider,
          model: response.model || response.trace?.model,
          fallbackUsed: response.fallback_used ?? response.trace?.fallback ?? false,
          citations: response.citations || [],
          trace: response.trace,
          debug: response.debug,
        },
      ]);
    } catch (requestError) {
      setError(
        requestError.message ||
          "Không thể gửi câu hỏi. Hãy thử lại.",
      );
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

  function removeAttachment() {
    setAttachment(null);
    setContextAttachment?.(null);
  }

  return (
    <aside
      className={isOver ? "chat-panel drag-over" : "chat-panel"}
      onDragEnter={handleDragEnter}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <header className="chat-header">
        <div className="bot-icon" aria-hidden="true">
          <Bot size={20} />
        </div>
        <div>
          <h2>VLearn Tutor</h2>
          <p>Trợ lý học tập theo ngữ cảnh</p>
        </div>
      </header>

      <div className="messages" ref={listRef}>
        {messages.map((message, index) => (
          <ChatMessage
            key={`${message.role}-${index}`}
            message={message}
            onCitationClick={onCitationClick}
            showDebug={enableDebugPanel}
          />
        ))}
        {loading && (
          <div className="chat-message assistant">
            <div className="message-bubble loading">
              {attachment?.type === "visual_region" || attachment?.type === "page"
                ? "Đang đọc hình ảnh và nội dung trang..."
                : "Đang phân tích tài liệu..."}
            </div>
          </div>
        )}
      </div>

      {isOver && <div className="drop-hint">Thả trang PDF vào đây</div>}
      {error && <div className="inline-error">{error}</div>}

      <div className="composer">
        <PageAttachment attachment={attachment} onRemove={removeAttachment} />
        <label htmlFor="chat-input" className="sr-only">
          Câu hỏi cho Tutor
        </label>
        <textarea
          ref={inputRef}
          id="chat-input"
          value={input}
          onChange={(event) => setInput(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={
            attachment?.type === "text_selection"
              ? "Hỏi về đoạn được chọn..."
              : attachment?.type === "visual_region"
                ? "Hỏi về vùng hình ảnh được chọn..."
                : attachment
                  ? "Hỏi về trang đã gắn..."
                  : "Nhập câu hỏi cho Tutor..."
          }
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
