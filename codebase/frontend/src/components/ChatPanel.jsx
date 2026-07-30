import { useCallback, useEffect, useRef, useState } from "react";
import { Bot, RotateCcw, Send } from "lucide-react";

import { PDF_PAGE_MIME } from "../constants/dragTypes";
import { deleteConversation, streamChatV2 } from "../services/api";
import { buildChatContext } from "../utils/chatContext";
import ChatMessage from "./ChatMessage";
import PageAttachment from "./PageAttachment";

const enableDebugPanel = import.meta.env.VITE_ENABLE_DEBUG_PANEL === "true";
const CHAT_HISTORY_FALLBACK_LIMIT = 12;
const WELCOME_MESSAGE = {
  role: "assistant",
  content:
    "Xin chào! Bạn có thể nhập câu hỏi, kéo một trang PDF, bôi đen văn bản hoặc khoanh vùng hình ảnh để hỏi Tutor.",
  localOnly: true,
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
  const [notice, setNotice] = useState("");
  const listRef = useRef(null);
  const inputRef = useRef(null);
  const dragEnterCount = useRef(0);
  const abortControllerRef = useRef(null);
  const conversationIdRef = useRef(null);
  const previousDocumentIdRef = useRef(currentDocument?.id || null);

  const setCurrentConversationId = useCallback((value) => {
    conversationIdRef.current = value;
    setConversationId(value);
  }, []);

  const abortActiveStream = useCallback(() => {
    abortControllerRef.current?.abort();
    abortControllerRef.current = null;
  }, []);

  const resetConversation = useCallback(
    async ({ deleteRemote = true, preserveInput = false } = {}) => {
      abortActiveStream();
      const remoteId = conversationIdRef.current;
      if (remoteId && deleteRemote) {
        try {
          await deleteConversation(remoteId);
        } catch {
          setNotice("Không xoá được hội thoại cũ trên máy chủ, nhưng khung chat đã được làm mới.");
        }
      }
      setCurrentConversationId(null);
      setMessages([WELCOME_MESSAGE]);
      setAttachment(null);
      setContextAttachment?.(null);
      setLoading(false);
      setError("");
      if (!preserveInput) setInput("");
      window.requestAnimationFrame(() => inputRef.current?.focus());
    },
    [abortActiveStream, setContextAttachment, setCurrentConversationId],
  );

  useEffect(() => {
    if (typeof listRef.current?.scrollTo !== "function") return;
    listRef.current.scrollTo({
      top: listRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, loading]);

  useEffect(() => {
    const previous = previousDocumentIdRef.current;
    const next = currentDocument?.id || null;
    if (previous !== next) {
      previousDocumentIdRef.current = next;
      resetConversation({ deleteRemote: Boolean(previous), preserveInput: false });
    }
  }, [currentDocument?.id, resetConversation]);

  useEffect(() => {
    return () => abortActiveStream();
  }, [abortActiveStream]);

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
    setNotice("");
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

  function buildHistoryFallback(sourceMessages) {
    return sourceMessages
      .filter((message) => !message.localOnly)
      .filter((message) => message.role === "user" || message.role === "assistant")
      .filter((message) => !message.streaming && message.content?.trim())
      .slice(-CHAT_HISTORY_FALLBACK_LIMIT)
      .map((message) => ({ role: message.role, content: message.content }));
  }

  async function handleSend() {
    const text = input.trim();
    if (!text || loading) return;

    abortActiveStream();
    const controller = new AbortController();
    abortControllerRef.current = controller;
    const selectedAttachment = attachment;
    const userMessage = { role: "user", content: text, attachment: selectedAttachment };
    const assistantMessage = {
      role: "assistant",
      content: "",
      streaming: true,
      statusText:
        selectedAttachment?.type === "visual_region" || selectedAttachment?.type === "page"
          ? "Đang đọc hình ảnh và nội dung trang..."
          : "Đang phân tích tài liệu...",
    };
    const history = buildHistoryFallback(messages);

    setMessages((current) => [...current, userMessage, assistantMessage]);
    setInput("");
    setLoading(true);
    setError("");
    setNotice("");

    try {
      await streamChatV2(
        {
          message: text,
          conversation_id: conversationIdRef.current,
          history,
          document_id: currentDocument?.id || null,
          context: buildChatContext({
            attachment: selectedAttachment,
            activePage,
          }),
          answer_mode: currentDocument ? "document_only" : "allow_general_knowledge",
        },
        {
          onMeta: (meta) => {
            if (meta.conversation_id) setCurrentConversationId(meta.conversation_id);
          },
          onDelta: ({ text: delta }) => {
            setMessages((current) => {
              const next = [...current];
              const index = next.findLastIndex((message) => message.streaming);
              if (index >= 0) {
                next[index] = {
                  ...next[index],
                  content: `${next[index].content || ""}${delta || ""}`,
                  statusText: "",
                };
              }
              return next;
            });
          },
          onDone: (done) => {
            setCurrentConversationId(done.conversation_id);
            setMessages((current) => {
              const next = [...current];
              const index = next.findLastIndex((message) => message.streaming);
              if (index >= 0) {
                next[index] = {
                  ...next[index],
                  content: done.answer,
                  streaming: false,
                  statusText: "",
                  provider: done.provider || done.trace?.provider,
                  model: done.model || done.trace?.model,
                  fallbackUsed: done.fallback_used ?? done.trace?.fallback ?? false,
                  citations: done.citations || [],
                  trace: done.trace,
                  debug: done.debug,
                };
              }
              return next;
            });
          },
          onError: (streamError) => {
            setMessages((current) => {
              const next = [...current];
              const index = next.findLastIndex((message) => message.streaming);
              if (index >= 0) {
                next[index] = {
                  ...next[index],
                  streaming: false,
                  statusText: "",
                  incomplete: true,
                  retryText: text,
                  errorDetail: streamError.detail,
                };
              }
              return next;
            });
          },
        },
        controller.signal,
      );
    } catch (requestError) {
      if (requestError.name === "AbortError") return;
      setError(
        requestError.message ||
          "Không thể gửi câu hỏi. Hãy thử lại.",
      );
      setMessages((current) =>
        current.map((message) =>
          message.streaming
            ? {
                ...message,
                streaming: false,
                incomplete: true,
                retryText: text,
                errorDetail: "Phản hồi bị gián đoạn.",
              }
            : message,
        ),
      );
    } finally {
      if (abortControllerRef.current === controller) {
        abortControllerRef.current = null;
      }
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

  function handleRetry(text) {
    setInput(text);
    inputRef.current?.focus();
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
        <div className="chat-title-row">
          <div className="bot-icon" aria-hidden="true">
            <Bot size={20} />
          </div>
          <div>
            <h2>VLearn Tutor</h2>
            <p>Trợ lý học tập theo ngữ cảnh</p>
          </div>
        </div>
        <button
          type="button"
          className="reset-chat-button"
          onClick={() => resetConversation({ deleteRemote: true })}
          aria-label="Tạo cuộc trò chuyện mới"
          title="Tạo cuộc trò chuyện mới"
        >
          <RotateCcw size={16} />
          <span>Cuộc trò chuyện mới</span>
        </button>
      </header>

      <div className="messages" ref={listRef}>
        {messages.map((message, index) => (
          <ChatMessage
            key={`${message.role}-${index}`}
            message={message}
            onCitationClick={onCitationClick}
            onRetry={handleRetry}
            showDebug={enableDebugPanel}
          />
        ))}
      </div>

      {isOver && <div className="drop-hint">Thả trang PDF vào đây</div>}
      {notice && <div className="inline-warning">{notice}</div>}
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
