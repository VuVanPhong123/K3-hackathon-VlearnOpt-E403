import { useRef, useState } from "react";
import { GripVertical } from "lucide-react";
import { Page } from "react-pdf";

const PAGE_MIME = "application/x-vlearn-pdf-page";

function toPoint(event, element) {
  const rect = element.getBoundingClientRect();
  return {
    x: Math.min(1, Math.max(0, (event.clientX - rect.left) / rect.width)),
    y: Math.min(1, Math.max(0, (event.clientY - rect.top) / rect.height)),
  };
}

function pointsToPath(points) {
  if (!points.length) return "";
  const [first, ...rest] = points;
  return `M ${first.x * 100} ${first.y * 100} ${rest.map((point) => `L ${point.x * 100} ${point.y * 100}`).join(" ")}`;
}

export default function PdfPageCard({
  document,
  pageNumber,
  width,
  tool,
  color,
  strokeWidth,
  getStrokes,
  addStroke,
  eraseNearPoint,
}) {
  const overlayRef = useRef(null);
  const [draft, setDraft] = useState(null);
  const strokes = getStrokes(pageNumber);
  const isDrawingTool = tool === "pen" || tool === "highlighter" || tool === "eraser";

  function handleDragStart(event) {
    if (tool !== "pointer") {
      event.preventDefault();
      return;
    }
    const payload = {
      documentId: document.id,
      pageNumber,
      filename: document.original_filename,
    };
    const value = JSON.stringify(payload);
    event.dataTransfer.setData(PAGE_MIME, value);
    event.dataTransfer.setData("text/plain", value);
    event.dataTransfer.effectAllowed = "copy";
  }

  function beginDraw(event) {
    if (!isDrawingTool || !overlayRef.current) return;
    event.currentTarget.setPointerCapture(event.pointerId);
    const point = toPoint(event, overlayRef.current);
    if (tool === "eraser") {
      eraseNearPoint(pageNumber, point);
      return;
    }
    setDraft({
      pageNumber,
      tool,
      color,
      width: tool === "highlighter" ? Math.max(strokeWidth + 8, 12) : strokeWidth,
      opacity: tool === "highlighter" ? 0.28 : 0.9,
      points: [point],
    });
  }

  function moveDraw(event) {
    if (!isDrawingTool || !overlayRef.current) return;
    const point = toPoint(event, overlayRef.current);
    if (tool === "eraser" && event.buttons === 1) {
      eraseNearPoint(pageNumber, point);
      return;
    }
    if (!draft) return;
    setDraft((current) => ({
      ...current,
      points: [...current.points, point],
    }));
  }

  function endDraw() {
    if (draft?.points?.length > 1) {
      addStroke(pageNumber, draft);
    }
    setDraft(null);
  }

  return (
    <article
      className="page-card"
      data-page-number={pageNumber}
    >
      <div className="page-card-header">
        <span>Trang {pageNumber}</span>
        <span className="drag-handle" draggable={true} onDragStart={handleDragStart}>
          <GripVertical size={16} /> Kéo trang này vào Tutor
        </span>
      </div>
      <div className="page-shell" style={{ width }}>
        <Page
          pageNumber={pageNumber}
          width={width}
          loading={<div className="page-placeholder">Đang tải trang {pageNumber}...</div>}
          error={<div className="page-placeholder error">Không thể hiển thị trang này.</div>}
        />
        <svg
          ref={overlayRef}
          className={isDrawingTool ? "annotation-layer drawing" : "annotation-layer"}
          viewBox="0 0 100 100"
          preserveAspectRatio="none"
          onPointerDown={beginDraw}
          onPointerMove={moveDraw}
          onPointerUp={endDraw}
          onPointerCancel={endDraw}
        >
          {[...strokes, ...(draft ? [draft] : [])].map((stroke, index) => (
            <path
              key={`${stroke.pageNumber}-${index}`}
              d={pointsToPath(stroke.points)}
              fill="none"
              stroke={stroke.color}
              strokeWidth={stroke.width / 10}
              strokeLinecap="round"
              strokeLinejoin="round"
              opacity={stroke.opacity}
              vectorEffect="non-scaling-stroke"
            />
          ))}
        </svg>
      </div>
    </article>
  );
}
