import { useEffect, useRef, useState } from "react";

import ChatPanel from "./components/ChatPanel";
import PdfWorkspace from "./components/PdfWorkspace";
import { getDocumentStatus, healthCheck, listDocuments, uploadDocument } from "./services/api";

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
  const uploadInputRef = useRef(null);

  async function loadDocuments() {
    try {
      const items = await listDocuments();
      setDocuments(items);
      setCurrentDocument((current) => current || items[0] || null);
    } catch {
      setError("Backend is not ready. Start the API on port 8000.");
    }
  }

  useEffect(() => {
    healthCheck().catch(() => setError("Backend is not ready. Start the API on port 8000."));
    loadDocuments();
  }, []);

  useEffect(() => {
    setContextAttachment(null);
    setActivePage(1);
  }, [currentDocument?.id]);

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
    if (file.type && file.type !== "application/pdf") {
      setError("Only PDF files are supported.");
      return;
    }
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setError("Only PDF files are supported.");
      return;
    }
    setUploading(true);
    setError("");
    setStatus("Uploading document...");
    try {
      const metadata = await uploadDocument(file);
      setCurrentDocument(metadata);
      const items = await listDocuments();
      setDocuments(items);
      setStatus("Uploaded. Indexing runs in the background; wait for READY for document-wide search.");
    } catch (err) {
      setError(err.message || "Could not upload PDF. Try again.");
      setStatus("");
    } finally {
      setUploading(false);
    }
  }

  return (
    <main className="app-shell">
      <input ref={uploadInputRef} type="file" accept=".pdf,application/pdf" onChange={handleSelectFile} hidden />
      <section className="main-area">
        <div className="workspace-header">
          <div>
            <h1>VLearn Tutor</h1>
            <p>Ask from a page, selected text, visual region, or the whole indexed PDF.</p>
            {documentStatus && (
              <p className="doc-status">
                {documentStatus.status} {documentStatus.stage ? `- ${documentStatus.stage}` : ""} {documentStatus.progress ?? 0}%
              </p>
            )}
          </div>
          {documents.length > 0 && (
            <label className="document-picker">
              <span>Document</span>
              <select
                value={currentDocument?.id || ""}
                onChange={(event) => {
                  const next = documents.find((item) => item.id === event.target.value);
                  setCurrentDocument(next || null);
                  setContextAttachment(null);
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
          onContextAttachment={setContextAttachment}
          jumpToPageRequest={jumpToPageRequest}
        />
      </section>
      <ChatPanel
        currentDocument={currentDocument}
        activePage={activePage}
        contextAttachment={contextAttachment}
        setContextAttachment={setContextAttachment}
        documentStatus={documentStatus}
        onCitationClick={(pageNumber) => setJumpToPageRequest({ pageNumber, nonce: Date.now() })}
      />
    </main>
  );
}
