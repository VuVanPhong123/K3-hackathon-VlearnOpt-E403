import { FileText, X } from "lucide-react";

export default function PageAttachment({ attachment, onRemove }) {
  if (!attachment) return null;
  return (
    <div className="attachment-card">
      <FileText size={18} aria-hidden="true" />
      <div>
        <strong>{attachment.filename}</strong>
        <span>Trang {attachment.pageNumber}</span>
      </div>
      <button onClick={onRemove} title="Xóa trang đã gắn" aria-label="Xóa trang đã gắn">
        <X size={16} />
      </button>
    </div>
  );
}
