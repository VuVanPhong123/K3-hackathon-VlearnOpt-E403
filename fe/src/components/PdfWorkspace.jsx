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
  const [pdfUrl, setPdfUrl] = useState("");
  const [pdfLoading, setPdfLoading] = useState(false);
  const [documentReady, setDocumentReady] = useState(false);
  const [tool, setTool] = useState("pointer");
  const [color, setColor] = useState("#2563eb");
  const [strokeWidth, setStrokeWidth] = useState(4);
  const [zoom, setZoom] = useState(1);
  const [loadError, setLoadError] = useState("");
  const { getStrokes, addStroke, undoPage, clearPage, eraseNearPoint } = usePageAnnotations(currentDocument?.id);

  useEffect(() => {
    setPageCount(0);
    setCurrentPage(1);
    setDocumentReady(false);
    setLoadError("");
  }, [currentDocument?.id]);

  useEffect(() => {
    let cancelled = false;
    let objectUrl = "";

    async function loadPdfBlob() {
      if (!currentDocument?.id) {
        setPdfUrl("");
        return;
      }

      setPdfLoading(true);
      setDocumentReady(false);
      setLoadError("");
      try {
        const response = await fetch(getDocumentFileUrl(currentDocument.id));
        if (!response.ok) {
          throw new Error("Không thể tải PDF. Hãy thử lại.");
        }
        const blob = await response.blob();
        objectUrl = URL.createObjectURL(blob);
        if (!cancelled) {
          setPdfUrl(objectUrl);
        } else {
          URL.revokeObjectURL(objectUrl);
        }
      } catch (error) {
        if (!cancelled) {
          setPdfUrl("");
          setLoadError(error?.message || "Không thể tải PDF. Hãy thử lại.");
        }
      } finally {
        if (!cancelled) {
          setPdfLoading(false);
        }
      }
    }

    loadPdfBlob();

    return () => {
      cancelled = true;
      if (objectUrl) {
        URL.revokeObjectURL(objectUrl);
      }
    };
  }, [currentDocument?.id]);

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
  const jumpToPage = (pageNumber) => {
    if (!scrollRef.current || !pageCount) return;
    const nextPage = Math.min(Math.max(pageNumber, 1), pageCount);
    const target = scrollRef.current.querySelector(`[data-page-number="${nextPage}"]`);
    if (target) {
      target.scrollIntoView({ behavior: "smooth", block: "start" });
      setCurrentPage(nextPage);
    }
  };

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
        onPreviousPage={() => jumpToPage(currentPage - 1)}
        onNextPage={() => jumpToPage(currentPage + 1)}
        onJumpPage={jumpToPage}
      />

      {loadError && <div className="workspace-error">{loadError}</div>}

      <div className="pdf-scroll" ref={scrollRef}>
        {pdfLoading && <div className="pdf-loading">Đang tải PDF...</div>}
        {!pdfLoading && pdfUrl && (
          <Document
          file={pdfUrl}
          loading={<div className="pdf-loading">Đang tải PDF...</div>}
          error={<div className="pdf-loading error">{loadError || "Không thể tải PDF. Hãy thử lại."}</div>}
          onLoadSuccess={({ numPages }) => {
            setPageCount(numPages);
            setDocumentReady(true);
            setLoadError("");
          }}
          onLoadError={(error) => {
            setDocumentReady(false);
            setLoadError(error?.message || "Không thể tải PDF. Hãy thử lại.");
          }}
        >
          {documentReady && Array.from({ length: pageCount }, (_, index) => (
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
        )}
      </div>
    </section>
  );
}
