import { useEffect, useRef, useState } from "react";

import ChatPanel from "./components/ChatPanel";
import PdfWorkspace from "./components/PdfWorkspace";
import {
  getDocumentStatus,
  healthCheck,
  listDocuments,
  uploadDocument,
} from "./services/api";

const CHAT_WIDTH_KEY = "vlearn-chat-panel-width";
const MIN_CHAT_WIDTH = 320;
const MIN_PDF_WIDTH = 480;
const DIVIDER_WIDTH = 7;

export function clampChatWidth(value, viewportWidth = window.innerWidth) {
  const maximum = Math.max(
    MIN_CHAT_WIDTH,
    Math.min(viewportWidth * 0.6, viewportWidth - MIN_PDF_WIDTH - DIVIDER_WIDTH),
  );
  return Math.round(Math.min(maximum, Math.max(MIN_CHAT_WIDTH, value)));
}

function initialChatWidth() {
  const stored = Number(localStorage.getItem(CHAT_WIDTH_KEY));
  const preferred = Number.isFinite(stored) && stored > 0
    ? stored
    : Math.max(400, window.innerWidth * 0.32);
  return clampChatWidth(preferred);
}

function documentStatusText(documentStatus) {
  if (!documentStatus) return "";
  if (documentStatus.status === "READY") return "Tài liệu đã sẵn sàng";
  if (documentStatus.status === "FAILED") return "Xử lý tài liệu thất bại";
  return "Đang xử lý tài liệu...";
}

export default function App() {
  const [documents, setDocuments] = useState([]);
  const [currentDocument, setCurrentDocument] = useState(null);
  const [documentStatus, setDocumentStatus] = useState(null);
  const [activePage, setActivePage] = useState(1);
  const [contextAttachment, setContextAttachment] = useState(null);
  const [jumpToPageRequest, setJumpToPageRequest] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [chatWidth, setChatWidth] = useState(initialChatWidth);
  const uploadInputRef = useRef(null);
  const resizeHandlersRef = useRef(null);

  async function loadDocuments() {
    try {
      const items = await listDocuments();
      setDocuments(items);
      setCurrentDocument((current) => current || items[0] || null);
    } catch {
      setError("Backend chưa sẵn sàng. Hãy chạy API ở cổng 8000.");
    }
  }

  useEffect(() => {
    healthCheck().catch(() =>
      setError("Backend chưa sẵn sàng. Hãy chạy API ở cổng 8000."),
    );
    loadDocuments();
  }, []);

  useEffect(() => {
    setContextAttachment(null);
    setActivePage(1);
  }, [currentDocument?.id]);

  useEffect(() => {
    localStorage.setItem(CHAT_WIDTH_KEY, String(chatWidth));
  }, [chatWidth]);

  useEffect(() => {
    function handleViewportResize() {
      setChatWidth((current) => clampChatWidth(current));
    }
    window.addEventListener("resize", handleViewportResize);
    return () => window.removeEventListener("resize", handleViewportResize);
  }, []);

  useEffect(() => {
    return () => {
      const handlers = resizeHandlersRef.current;
      if (!handlers) return;
      window.removeEventListener("pointermove", handlers.move);
      window.removeEventListener("pointerup", handlers.end);
      window.removeEventListener("pointercancel", handlers.end);
      document.body.classList.remove("resizing-panels");
    };
  }, []);

  useEffect(() => {
    if (!currentDocument?.id) {
      setDocumentStatus(null);
      return undefined;
    }
    let cancelled = false;
    async function poll() {
      try {
        const next = await getDocumentStatus(currentDocument.id);
        if (!cancelled) setDocumentStatus(next);
      } catch {
        if (!cancelled) setDocumentStatus(null);
      }
    }
    poll();
    const timer = window.setInterval(poll, 2500);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [currentDocument?.id]);

  async function handleSelectFile(event) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    if (
      (file.type && file.type !== "application/pdf") ||
      !file.name.toLowerCase().endsWith(".pdf")
    ) {
      setError("Chỉ hỗ trợ tệp PDF.");
      return;
    }
    setUploading(true);
    setError("");
    setStatus("Đang tải tài liệu...");
    try {
      const metadata = await uploadDocument(file);
      setCurrentDocument(metadata);
      setDocuments(await listDocuments());
      setStatus("Đã tải tài liệu. Hệ thống đang xử lý nội dung.");
    } catch (uploadError) {
      setError(uploadError.message || "Không thể tải PDF. Hãy thử lại.");
      setStatus("");
    } finally {
      setUploading(false);
    }
  }

  function startResize(event) {
    if (event.button !== 0) return;
    event.preventDefault();
    const startX = event.clientX;
    const startWidth = chatWidth;
    document.body.classList.add("resizing-panels");

    function move(pointerEvent) {
      setChatWidth(
        clampChatWidth(startWidth + startX - pointerEvent.clientX),
      );
    }

    function end() {
      window.removeEventListener("pointermove", move);
      window.removeEventListener("pointerup", end);
      window.removeEventListener("pointercancel", end);
      resizeHandlersRef.current = null;
      document.body.classList.remove("resizing-panels");
    }

    resizeHandlersRef.current = { move, end };
    window.addEventListener("pointermove", move);
    window.addEventListener("pointerup", end);
    window.addEventListener("pointercancel", end);
  }

  function resizeWithKeyboard(event) {
    if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
    event.preventDefault();
    const step = event.shiftKey ? 48 : 16;
    const direction = event.key === "ArrowLeft" ? 1 : -1;
    setChatWidth((current) => clampChatWidth(current + direction * step));
  }

  const maximumChatWidth = clampChatWidth(window.innerWidth);

  return (
    <main
      className="app-shell"
      style={{ "--chat-panel-width": `${chatWidth}px` }}
    >
      <input
        ref={uploadInputRef}
        type="file"
        accept=".pdf,application/pdf"
        onChange={handleSelectFile}
        hidden
      />
      <section className="main-area">
        <div className="workspace-header">
          <div>
            <h1>VLearn Tutor</h1>
            <p>Đọc PDF, ghi chú và hỏi Tutor theo đúng trang bạn gắn.</p>
            {documentStatus && (
              <p className="doc-status">
                {documentStatusText(documentStatus)}
              </p>
            )}
          </div>
          {documents.length > 0 && (
            <label className="document-picker">
              <span>Tài liệu</span>
              <select
                value={currentDocument?.id || ""}
                onChange={(event) => {
                  const next = documents.find(
                    (item) => item.id === event.target.value,
                  );
                  setCurrentDocument(next || null);
                }}
              >
                {documents.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.original_filename}
                  </option>
                ))}
              </select>
            </label>
          )}
        </div>
        {status && <div className="status-banner">{status}</div>}
        {error && <div className="error-banner">{error}</div>}
        <PdfWorkspace
          currentDocument={currentDocument}
          onSelectFile={handleSelectFile}
          uploading={uploading}
          uploadInputRef={uploadInputRef}
          onActivePageChange={setActivePage}
          onAttachPage={setContextAttachment}
          contextAttachment={contextAttachment}
          jumpToPageRequest={jumpToPageRequest}
        />
      </section>
      <div
        className="panel-divider"
        role="separator"
        aria-label="Thay đổi độ rộng khung chat"
        aria-orientation="vertical"
        aria-valuemin={MIN_CHAT_WIDTH}
        aria-valuemax={maximumChatWidth}
        aria-valuenow={chatWidth}
        tabIndex={0}
        onPointerDown={startResize}
        onKeyDown={resizeWithKeyboard}
      />
      <ChatPanel
        currentDocument={currentDocument}
        activePage={activePage}
        contextAttachment={contextAttachment}
        setContextAttachment={setContextAttachment}
        onCitationClick={(pageNumber) =>
          setJumpToPageRequest({ pageNumber, nonce: Date.now() })
        }
      />
    </main>
  );
}
