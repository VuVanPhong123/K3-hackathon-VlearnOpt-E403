import { useEffect, useRef, useState } from "react";
import { Document } from "react-pdf";

import { getDocumentFileUrl } from "../services/api";
import { usePageAnnotations } from "../hooks/usePageAnnotations";
import PdfPageCard from "./PdfPageCard";
import PdfToolbar from "./PdfToolbar";
import PdfUploadEmptyState from "./PdfUploadEmptyState";

export default function PdfWorkspace({
  currentDocument,
  onSelectFile,
  uploading,
  uploadInputRef,
}) {
  const scrollRef = useRef(null);
  const [pageCount, setPageCount] = useState(currentDocument?.page_count || 0);
  const [currentPage, setCurrentPage] = useState(1);
  const [tool, setTool] = useState("pointer");
  const [color, setColor] = useState("#2563eb");
  const [strokeWidth, setStrokeWidth] = useState(4);
  const [zoom, setZoom] = useState(1);
  const [loadError, setLoadError] = useState("");
  const { getStrokes, addStroke, undoPage, clearPage, eraseNearPoint } = usePageAnnotations(currentDocument?.id);

  useEffect(() => {
    setPageCount(currentDocument?.page_count || 0);
    setCurrentPage(1);
    setLoadError("");
  }, [currentDocument?.id, currentDocument?.page_count]);

  useEffect(() => {
    const root = scrollRef.current;
    if (!root || !currentDocument) return undefined;
    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((entry) => entry.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
        if (visible) {
          setCurrentPage(Number(visible.target.dataset.pageNumber));
        }
      },
      {
        root,
        threshold: [0.2, 0.4, 0.6, 0.8],
      },
    );
    const cards = root.querySelectorAll(".page-card");
    cards.forEach((card) => observer.observe(card));
    return () => observer.disconnect();
  }, [currentDocument, pageCount, zoom]);

  if (!currentDocument) {
    return (
      <section className="pdf-workspace">
        <PdfUploadEmptyState onSelectFile={onSelectFile} uploading={uploading} />
      </section>
    );
  }

  const pageWidth = Math.round(720 * zoom);

  return (
    <section className="pdf-workspace">
      <PdfToolbar
        tool={tool}
        setTool={setTool}
        color={color}
        setColor={setColor}
        width={strokeWidth}
        setWidth={setStrokeWidth}
        zoom={zoom}
        setZoom={setZoom}
        currentPage={currentPage}
        pageCount={pageCount}
        onImport={() => uploadInputRef.current?.click()}
        onUndo={() => undoPage(currentPage)}
        onClear={() => clearPage(currentPage)}
      />

      {loadError && <div className="workspace-error">{loadError}</div>}

      <div className="pdf-scroll" ref={scrollRef}>
        <Document
          file={getDocumentFileUrl(currentDocument.id)}
          loading={<div className="pdf-loading">Đang tải PDF...</div>}
          error={<div className="pdf-loading error">Không thể tải PDF. Hãy thử lại.</div>}
          onLoadSuccess={({ numPages }) => {
            setPageCount(numPages);
            setLoadError("");
          }}
          onLoadError={() => setLoadError("Không thể tải PDF. Hãy thử lại.")}
        >
          {Array.from({ length: pageCount }, (_, index) => (
            <PdfPageCard
              key={`${currentDocument.id}-${index + 1}`}
              document={currentDocument}
              pageNumber={index + 1}
              width={pageWidth}
              tool={tool}
              color={color}
              strokeWidth={strokeWidth}
              getStrokes={getStrokes}
              addStroke={addStroke}
              eraseNearPoint={eraseNearPoint}
            />
          ))}
        </Document>
      </div>
    </section>
  );
}
