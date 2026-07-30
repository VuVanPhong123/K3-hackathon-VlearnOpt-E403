import {
  Eraser,
  Highlighter,
  MousePointer2,
  PenLine,
  Plus,
  RotateCcw,
  Trash2,
  Upload,
  ZoomIn,
  ZoomOut,
} from "lucide-react";

const colors = [
  { label: "Đỏ", value: "#d92d20" },
  { label: "Xanh dương", value: "#2563eb" },
  { label: "Xanh lá", value: "#159947" },
  { label: "Vàng", value: "#f5c542" },
  { label: "Cam", value: "#f97316" },
  { label: "Đen", value: "#111827" },
];

export default function PdfToolbar({
  tool,
  setTool,
  color,
  setColor,
  width,
  setWidth,
  zoom,
  setZoom,
  currentPage,
  pageCount,
  onImport,
  onUndo,
  onClear,
}) {
  const chooseTool = (value) => tool === value ? "tool-button active" : "tool-button";
  return (
    <div className="pdf-toolbar" aria-label="Thanh công cụ PDF">
      <button className="toolbar-action" onClick={onImport} title="Nhập PDF mới" aria-label="Nhập PDF mới">
        <Upload size={18} />
      </button>
      <div className="toolbar-group">
        <button className={chooseTool("pointer")} onClick={() => setTool("pointer")} title="Chọn và cuộn" aria-label="Chọn và cuộn">
          <MousePointer2 size={18} />
        </button>
        <button className={chooseTool("pen")} onClick={() => setTool("pen")} title="Bút" aria-label="Bút">
          <PenLine size={18} />
        </button>
        <button className={chooseTool("highlighter")} onClick={() => setTool("highlighter")} title="Highlight" aria-label="Highlight">
          <Highlighter size={18} />
        </button>
        <button className={chooseTool("eraser")} onClick={() => setTool("eraser")} title="Tẩy" aria-label="Tẩy">
          <Eraser size={18} />
        </button>
      </div>
      <div className="toolbar-group swatches" aria-label="Màu nét vẽ">
        {colors.map((item) => (
          <button
            key={item.value}
            className={color === item.value ? "swatch active" : "swatch"}
            style={{ background: item.value }}
            title={item.label}
            aria-label={item.label}
            onClick={() => setColor(item.value)}
          />
        ))}
      </div>
      <label className="width-control">
        <span>Độ dày</span>
        <input
          type="range"
          min="2"
          max="18"
          value={width}
          onChange={(event) => setWidth(Number(event.target.value))}
          aria-label="Độ dày nét vẽ"
        />
      </label>
      <div className="toolbar-group">
        <button className="tool-button" onClick={onUndo} title="Hoàn tác trang hiện tại" aria-label="Hoàn tác trang hiện tại">
          <RotateCcw size={18} />
        </button>
        <button className="tool-button" onClick={onClear} title="Xóa ghi chú trang hiện tại" aria-label="Xóa ghi chú trang hiện tại">
          <Trash2 size={18} />
        </button>
      </div>
      <div className="toolbar-group zoom-control">
        <button className="tool-button" onClick={() => setZoom((value) => Math.max(0.7, value - 0.1))} title="Thu nhỏ" aria-label="Thu nhỏ">
          <ZoomOut size={18} />
        </button>
        <span>{Math.round(zoom * 100)}%</span>
        <button className="tool-button" onClick={() => setZoom((value) => Math.min(1.8, value + 0.1))} title="Phóng to" aria-label="Phóng to">
          <ZoomIn size={18} />
        </button>
      </div>
      <div className="page-indicator">
        Trang {currentPage || 0} / {pageCount || 0}
      </div>
      <button className="toolbar-action import-compact" onClick={onImport} title="Thêm tài liệu" aria-label="Thêm tài liệu">
        <Plus size={18} />
      </button>
    </div>
  );
}
