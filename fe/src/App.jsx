import { useEffect, useRef, useState } from "react";

import ChatPanel from "./components/ChatPanel";
import PdfWorkspace from "./components/PdfWorkspace";
import { healthCheck, listDocuments, uploadDocument } from "./services/api";

export default function App() {
  const [documents, setDocuments] = useState([]);
  const [currentDocument, setCurrentDocument] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const uploadInputRef = useRef(null);

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
    healthCheck().catch(() => {
      setError("Backend chưa sẵn sàng. Hãy chạy API ở cổng 8000.");
    });
    loadDocuments();
  }, []);

  async function handleSelectFile(event) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    if (file.type && file.type !== "application/pdf") {
      setError("Chỉ hỗ trợ file PDF.");
      return;
    }
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setError("Chỉ hỗ trợ file PDF.");
      return;
    }
    setUploading(true);
    setError("");
    setStatus("Đang tải tài liệu lên...");
    try {
      const metadata = await uploadDocument(file);
      setCurrentDocument(metadata);
      const items = await listDocuments();
      setDocuments(items);
      setStatus("Đã tải tài liệu. Bạn có thể kéo một trang vào Tutor.");
    } catch (err) {
      setError(err.message || "Không thể tải PDF. Hãy thử lại.");
      setStatus("");
    } finally {
      setUploading(false);
    }
  }

  return (
    <main className="app-shell">
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
            <p>Kéo đúng một trang PDF vào khung chat để hỏi theo ngữ cảnh.</p>
          </div>
          {documents.length > 0 && (
            <label className="document-picker">
              <span>Tài liệu</span>
              <select
                value={currentDocument?.id || ""}
                onChange={(event) => {
                  const next = documents.find((item) => item.id === event.target.value);
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
        />
      </section>
      <ChatPanel currentDocument={currentDocument} />
    </main>
  );
}
