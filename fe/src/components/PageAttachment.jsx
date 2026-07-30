import { FileText, ScanSearch, TextSelect, X } from "lucide-react";

export default function PageAttachment({ attachment, onRemove }) {
  if (!attachment) return null;

  const details = {
    page: {
      icon: <FileText size={18} aria-hidden="true" />,
      label: `Trang ${attachment.pageNumber}`,
    },
    text_selection: {
      icon: <TextSelect size={18} aria-hidden="true" />,
      label: `Đoạn đã chọn · Trang ${attachment.pageNumber}`,
    },
    visual_region: {
      icon: <ScanSearch size={18} aria-hidden="true" />,
      label: `Vùng được chọn · Trang ${attachment.pageNumber}`,
    },
  }[attachment.type];

  if (!details) return null;

  return (
    <div className="attachment-card">
      {details.icon}
      <div>
        <strong>{attachment.filename}</strong>
        <span>{details.label}</span>
        {attachment.type === "text_selection" && attachment.selectedText && (
          <span className="attachment-preview">
            {attachment.selectedText.slice(0, 120)}
            {attachment.selectedText.length > 120 ? "…" : ""}
          </span>
        )}
      </div>
      <button onClick={onRemove} title="Gỡ ngữ cảnh đã gắn" aria-label="Gỡ ngữ cảnh đã gắn">
        <X size={16} />
      </button>
    </div>
  );
}
