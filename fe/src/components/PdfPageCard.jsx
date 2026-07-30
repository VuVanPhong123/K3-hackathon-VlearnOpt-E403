import { useEffect, useRef, useState } from "react";
import { GripVertical, Link2, Sparkles, X } from "lucide-react";
import { Page } from "react-pdf";

import { PDF_PAGE_MIME } from "../constants/dragTypes";

function toPoint(event, element) {
  const rect = element.getBoundingClientRect();
  return {
    x: Math.min(1, Math.max(0, (event.clientX - rect.left) / rect.width)),
    y: Math.min(1, Math.max(0, (event.clientY - rect.top) / rect.height)),
  };
}

function pointDistance(first, second) {
  return Math.hypot(first.x - second.x, first.y - second.y);
}

function pointsToPath(points) {
  if (!points.length) return "";
  const [first, ...rest] = points;
  return `M ${first.x * 100} ${first.y * 100} ${rest
    .map((point) => `L ${point.x * 100} ${point.y * 100}`)
    .join(" ")}`;
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
  onAttachPage,
  setTool,
  contextAttachment,
  highlighted = false,
}) {
  const shellRef = useRef(null);
  const overlayRef = useRef(null);
  const draftRef = useRef(null);
  const activePointerRef = useRef(null);
  const erasingRef = useRef(false);
  const [draft, setDraft] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [rendered, setRendered] = useState(false);
  const [selectionPopup, setSelectionPopup] = useState(null);
  const [regionDraft, setRegionDraft] = useState(null);
  const [regionPopup, setRegionPopup] = useState(null);
  const regionStartRef = useRef(null);
  const strokes = getStrokes(pageNumber);
  const isDrawingTool =
    tool === "pen" || tool === "highlighter" || tool === "eraser";

  useEffect(() => {
    setSelectionPopup(null);
    setRegionDraft(null);
    setRegionPopup(null);
  }, [document.id]);

  useEffect(() => {
    setSelectionPopup(null);
    setRegionPopup(null);
  }, [tool]);

  useEffect(() => {
    if (!selectionPopup && !regionPopup) return undefined;
    function closePopup(event) {
      if (event.key === "Escape") {
        setSelectionPopup(null);
        setRegionPopup(null);
      }
    }
    function closeOnOutsideClick(event) {
      if (!event.target.closest?.(".context-popup")) {
        setSelectionPopup(null);
        setRegionPopup(null);
      }
    }
    window.addEventListener("keydown", closePopup);
    window.addEventListener("mousedown", closeOnOutsideClick);
    return () => {
      window.removeEventListener("keydown", closePopup);
      window.removeEventListener("mousedown", closeOnOutsideClick);
    };
  }, [selectionPopup, regionPopup]);

  function pagePayload() {
    return {
      type: "page",
      documentId: document.id,
      pageNumber,
      filename: document.original_filename,
    };
  }

  function handleDragStart(event) {
    event.stopPropagation();
    const value = JSON.stringify(pagePayload());
    event.dataTransfer.setData(PDF_PAGE_MIME, value);
    event.dataTransfer.setData("text/plain", value);
    event.dataTransfer.effectAllowed = "copy";
    setDragging(true);
  }

  function eraseAt(event) {
    const overlay = overlayRef.current;
    if (!overlay) return;
    const rect = overlay.getBoundingClientRect();
    const radius = Math.max(0.012, (10 + strokeWidth * 0.35) / rect.width);
    eraseNearPoint(pageNumber, toPoint(event, overlay), radius);
  }

  function beginDraw(event) {
    if (!isDrawingTool || !overlayRef.current) return;
    if (
      event.isPrimary === false ||
      (Number.isFinite(event.button) && event.button !== 0)
    ) {
      return;
    }
    event.preventDefault();
    activePointerRef.current = event.pointerId ?? 1;
    event.currentTarget.setPointerCapture(event.pointerId ?? 1);

    if (tool === "eraser") {
      erasingRef.current = true;
      eraseAt(event);
      return;
    }

    const stroke = {
      pageNumber,
      tool,
      color,
      width:
        tool === "highlighter"
          ? Math.max(strokeWidth + 8, 12)
          : strokeWidth,
      opacity: tool === "highlighter" ? 0.28 : 0.92,
      points: [toPoint(event, overlayRef.current)],
    };
    draftRef.current = stroke;
    setDraft(stroke);
  }

  function moveDraw(event) {
    if (
      !isDrawingTool ||
      !overlayRef.current ||
      activePointerRef.current === null ||
      (event.pointerId != null && activePointerRef.current !== event.pointerId)
    ) {
      return;
    }
    if (tool === "eraser" && erasingRef.current) {
      eraseAt(event);
      return;
    }
    const current = draftRef.current;
    if (!current) return;
    const point = toPoint(event, overlayRef.current);
    const lastPoint = current.points[current.points.length - 1];
    if (pointDistance(lastPoint, point) < 0.0015) return;
    const next = { ...current, points: [...current.points, point] };
    draftRef.current = next;
    setDraft(next);
  }

  function finishDraw(event, save = true) {
    if (
      activePointerRef.current === null ||
      (event.pointerId != null && activePointerRef.current !== event.pointerId)
    ) {
      return;
    }
    const current = draftRef.current;
    if (!current && !erasingRef.current) return;
    draftRef.current = null;
    activePointerRef.current = null;
    erasingRef.current = false;
    setDraft(null);

    if (
      event.currentTarget.hasPointerCapture?.(event.pointerId)
    ) {
      event.currentTarget.releasePointerCapture(event.pointerId);
    }
    if (save && current?.points?.length >= 2) {
      addStroke(pageNumber, current);
    }
  }

  function handleTextSelection() {
    if (tool !== "pointer" || !shellRef.current) return;
    const selection = window.getSelection?.();
    const anchorElement =
      selection?.anchorNode?.nodeType === Node.ELEMENT_NODE
        ? selection.anchorNode
        : selection?.anchorNode?.parentElement;
    const focusElement =
      selection?.focusNode?.nodeType === Node.ELEMENT_NODE
        ? selection.focusNode
        : selection?.focusNode?.parentElement;
    if (
      !selection ||
      selection.isCollapsed ||
      !selection.anchorNode ||
      !selection.focusNode ||
      !shellRef.current.contains(selection.anchorNode) ||
      !shellRef.current.contains(selection.focusNode) ||
      !anchorElement?.closest(".textLayer") ||
      !focusElement?.closest(".textLayer")
    ) {
      return;
    }
    const selectedText = selection.toString().trim().slice(0, 6000);
    if (!selectedText) return;
    const range = selection.getRangeAt(0);
    const shellRect = shellRef.current.getBoundingClientRect();
    const rects = Array.from(range.getClientRects())
      .filter((rect) => rect.width > 0 && rect.height > 0)
      .map((rect) => ({
        x: Math.max(0, (rect.left - shellRect.left) / shellRect.width),
        y: Math.max(0, (rect.top - shellRect.top) / shellRect.height),
        width: Math.min(1, rect.width / shellRect.width),
        height: Math.min(1, rect.height / shellRect.height),
      }));
    if (!rects.length) return;
    const lastRect = range.getBoundingClientRect();
    setSelectionPopup({
      left: Math.min(
        Math.max(8, lastRect.left - shellRect.left),
        Math.max(8, shellRect.width - 190),
      ),
      top: Math.min(
        Math.max(8, lastRect.bottom - shellRect.top + 8),
        Math.max(8, shellRect.height - 48),
      ),
      payload: {
        type: "text_selection",
        documentId: document.id,
        pageNumber,
        filename: document.original_filename,
        selectedText,
        boundingBoxes: rects,
      },
    });
  }

  function beginRegion(event) {
    if (tool !== "ask_region" || !shellRef.current || event.button !== 0) return;
    event.preventDefault();
    const start = toPoint(event, shellRef.current);
    regionStartRef.current = start;
    setRegionPopup(null);
    setRegionDraft({ x: start.x, y: start.y, width: 0, height: 0 });
    event.currentTarget.setPointerCapture?.(event.pointerId);
  }

  function moveRegion(event) {
    if (tool !== "ask_region" || !regionStartRef.current || !shellRef.current) return;
    const current = toPoint(event, shellRef.current);
    const start = regionStartRef.current;
    setRegionDraft({
      x: Math.min(start.x, current.x),
      y: Math.min(start.y, current.y),
      width: Math.abs(current.x - start.x),
      height: Math.abs(current.y - start.y),
    });
  }

  function finishRegion(event) {
    if (tool !== "ask_region" || !regionStartRef.current || !shellRef.current) return;
    moveRegion(event);
    const current = toPoint(event, shellRef.current);
    const start = regionStartRef.current;
    const bbox = {
      x: Math.min(start.x, current.x),
      y: Math.min(start.y, current.y),
      width: Math.abs(current.x - start.x),
      height: Math.abs(current.y - start.y),
    };
    regionStartRef.current = null;
    event.currentTarget.releasePointerCapture?.(event.pointerId);
    if (bbox.width < 0.02 || bbox.height < 0.02) {
      setRegionDraft(null);
      return;
    }
    setRegionDraft(bbox);
    setRegionPopup({
      left: `${Math.min(92, (bbox.x + bbox.width) * 100)}%`,
      top: `${Math.min(94, (bbox.y + bbox.height) * 100)}%`,
      bbox,
    });
  }

  function attachSelection() {
    if (!selectionPopup) return;
    onAttachPage?.(selectionPopup.payload);
    setSelectionPopup(null);
    window.getSelection?.()?.removeAllRanges();
  }

  function attachRegion() {
    if (!regionPopup) return;
    onAttachPage?.({
      type: "visual_region",
      documentId: document.id,
      pageNumber,
      filename: document.original_filename,
      bbox: regionPopup.bbox,
    });
    setRegionDraft(null);
    setRegionPopup(null);
    setTool?.("pointer");
  }

  const attachedRegion =
    contextAttachment?.type === "visual_region" &&
    contextAttachment.documentId === document.id &&
    contextAttachment.pageNumber === pageNumber
      ? contextAttachment.bbox
      : null;
  const visibleRegion = regionDraft || attachedRegion;

  return (
    <article
      className={[
        "page-card",
        dragging ? "dragging" : "",
        highlighted ? "citation-highlight" : "",
      ].filter(Boolean).join(" ")}
      data-page-number={pageNumber}
    >
      <div className="page-card-header">
        <span>Trang {pageNumber}</span>
        <div className="page-card-actions">
          <button
            type="button"
            className="attach-page-button"
            onClick={() => onAttachPage?.(pagePayload())}
            title="Gắn trang vào chat"
            aria-label={`Gắn trang ${pageNumber} vào chat`}
          >
            <Link2 size={15} />
            Gắn trang vào chat
          </button>
          <button
            type="button"
            className="drag-handle"
            draggable
            onDragStart={handleDragStart}
            onDragEnd={() => setDragging(false)}
            onPointerDown={(event) => event.stopPropagation()}
            aria-label={`Kéo trang ${pageNumber} vào Tutor`}
          >
            <GripVertical size={16} />
            Kéo trang này vào Tutor
          </button>
        </div>
      </div>
      <div
        ref={shellRef}
        className={rendered ? "page-shell rendered" : "page-shell"}
        style={{ width }}
        onMouseUp={handleTextSelection}
      >
        <Page
          pageNumber={pageNumber}
          width={width}
          renderTextLayer
          onRenderSuccess={() => setRendered(true)}
          loading={
            <div className="page-placeholder">
              Đang tải trang {pageNumber}...
            </div>
          }
          error={
            <div className="page-placeholder error">
              Không thể hiển thị trang này.
            </div>
          }
        />
        <svg
          ref={overlayRef}
          className={`annotation-layer ${isDrawingTool ? `drawing ${tool}` : "pointer"}`}
          viewBox="0 0 100 100"
          preserveAspectRatio="none"
          aria-label={`Lớp ghi chú trang ${pageNumber}`}
          onPointerDown={beginDraw}
          onPointerMove={moveDraw}
          onPointerUp={(event) => finishDraw(event, true)}
          onPointerCancel={(event) => finishDraw(event, false)}
          onLostPointerCapture={(event) => finishDraw(event, true)}
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
            />
          ))}
        </svg>
        {tool === "ask_region" && (
          <div
            className="region-select-layer"
            aria-label={`Khoanh vùng trên trang ${pageNumber}`}
            onPointerDown={beginRegion}
            onPointerMove={moveRegion}
            onPointerUp={finishRegion}
            onPointerCancel={() => {
              regionStartRef.current = null;
              setRegionDraft(null);
            }}
          />
        )}
        {visibleRegion && (
          <div
            className={attachedRegion && !regionDraft ? "region-preview attached" : "region-preview"}
            style={{
              left: `${visibleRegion.x * 100}%`,
              top: `${visibleRegion.y * 100}%`,
              width: `${visibleRegion.width * 100}%`,
              height: `${visibleRegion.height * 100}%`,
            }}
          />
        )}
        {selectionPopup && (
          <div
            className="context-popup"
            style={{ left: selectionPopup.left, top: selectionPopup.top }}
            onMouseDown={(event) => event.preventDefault()}
          >
            <button type="button" onClick={attachSelection}>
              <Sparkles size={15} /> Hỏi AI
            </button>
            <button
              type="button"
              className="icon-only"
              onClick={() => setSelectionPopup(null)}
              title="Đóng"
              aria-label="Đóng"
            >
              <X size={15} />
            </button>
          </div>
        )}
        {regionPopup && (
          <div
            className="context-popup region-popup"
            style={{ left: regionPopup.left, top: regionPopup.top }}
          >
            <button type="button" onClick={attachRegion}>
              <Sparkles size={15} /> Hỏi AI
            </button>
            <button
              type="button"
              onClick={() => {
                setRegionDraft(null);
                setRegionPopup(null);
              }}
            >
              Khoanh lại
            </button>
            <button
              type="button"
              className="icon-only"
              onClick={() => {
                setRegionDraft(null);
                setRegionPopup(null);
                setTool?.("pointer");
              }}
              title="Hủy"
              aria-label="Hủy"
            >
              <X size={15} />
            </button>
          </div>
        )}
      </div>
    </article>
  );
}
