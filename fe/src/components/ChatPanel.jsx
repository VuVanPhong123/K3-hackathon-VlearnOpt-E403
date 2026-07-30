import { useEffect, useRef, useState } from "react";
import { Bot, Send } from "lucide-react";

import { sendChatV2 } from "../services/api";
import { buildChatContext } from "../utils/chatContext";
import ChatMessage from "./ChatMessage";
import PageAttachment from "./PageAttachment";

const PAGE_MIME = "application/x-vlearn-pdf-page";
const enableDebugPanel = import.meta.env.VITE_ENABLE_DEBUG_PANEL === "true";

export default function ChatPanel({
  currentDocument,
  activePage,
  contextAttachment,
  setContextAttachment,
  documentStatus,
  onCitationClick,
}) {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content: "Drop a PDF page here, select real text, or draw a region and ask a question.",
    },
  ]);
  const [input, setInput] = useState("");
  const [attachment, setAttachment] = useState(null);
  const [answerMode, setAnswerMode] = useState("document_only");
  const [conversationId, setConversationId] = useState(null);
  const [isOver, setIsOver] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const listRef = useRef(null);

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    setAttachment(null);
    setContextAttachment?.(null);
    setConversationId(null);
  }, [currentDocument?.id, setContextAttachment]);

  useEffect(() => {
    if (contextAttachment) setAttachment(contextAttachment);
  }, [contextAttachment]);

  function parseDrag(event) {
    const raw = event.dataTransfer.getData(PAGE_MIME) || event.dataTransfer.getData("text/plain");
    if (!raw) return null;
    try {
      const payload = JSON.parse(raw);
      if (!payload.documentId || !payload.pageNumber || !payload.filename) return null;
      return { ...payload, type: "page" };
    } catch {
      return null;
    }
  }

  function handleDrop(event) {
    event.preventDefault();
    setIsOver(false);
    const payload = parseDrag(event);
    if (!payload) {
      setError("Invalid PDF page.");
      return;
    }
    if (currentDocument && payload.documentId !== currentDocument.id) {
      setError("This page does not belong to the open document.");
      return;
    }
    setAttachment(payload);
    setContextAttachment?.(payload);
    setError("");
  }

  async function handleSend(nextText) {
    const text = (nextText || input).trim();
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
      const response = await sendChatV2({
        message: text,
        conversation_id: conversationId,
        history,
        document_id: attachment?.documentId || currentDocument?.id || null,
        context: buildChatContext({ attachment, activePage }),
        answer_mode: answerMode,
        requested_output: null,
      });
      setConversationId(response.conversation_id);
      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content: response.answer,
          provider: response.trace?.provider || "Tutor",
          citations: response.citations || [],
          confidence: response.confidence,
          trace: response.trace,
          debug: response.debug,
        },
      ]);
    } catch (err) {
      setError(err.message || "Could not send the question. Try again.");
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
          <p>Grounded study assistant</p>
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
            <div className="message-bubble loading">Thinking...</div>
          </div>
        )}
      </div>

      {isOver && <div className="drop-hint">Drop the PDF page here</div>}
      {error && <div className="inline-error">{error}</div>}

      <div className="composer">
        <PageAttachment
          attachment={attachment}
          onRemove={() => {
            setAttachment(null);
            setContextAttachment?.(null);
          }}
        />
        {attachment && <p className="replace-note">Drop another page, select text, or draw again to replace context.</p>}
        {documentStatus && documentStatus.status !== "READY" && (
          <p className="replace-note">
            Document status: {documentStatus.status} {documentStatus.stage ? `- ${documentStatus.stage}` : ""}
          </p>
        )}
        <div className="quick-actions">
          <button onClick={() => handleSend("Tom tat tai lieu nay")} disabled={!currentDocument || loading}>
            Summary
          </button>
          <button onClick={() => handleSend("Tao quiz ngan tu noi dung nay")} disabled={!currentDocument || loading}>
            Quiz
          </button>
          <button onClick={() => handleSend("Giai thich doan da chon")} disabled={!attachment || loading}>
            Selection
          </button>
        </div>
        <label className="mode-toggle">
          <input
            type="checkbox"
            checked={answerMode === "allow_general_knowledge"}
            onChange={(event) => setAnswerMode(event.target.checked ? "allow_general_knowledge" : "document_only")}
          />
          <span>{answerMode === "document_only" ? "Document only" : "General knowledge allowed"}</span>
        </label>
        <label htmlFor="chat-input" className="sr-only">
          Tutor question
        </label>
        <textarea
          id="chat-input"
          value={input}
          onChange={(event) => setInput(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about the selected context..."
          rows={3}
        />
        <button className="send-button" onClick={() => handleSend()} disabled={!input.trim() || loading} aria-label="Send question" title="Send question">
          <Send size={18} />
          Send
        </button>
      </div>
    </aside>
  );
}
