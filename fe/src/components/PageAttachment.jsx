import { FileText, X } from "lucide-react";

export default function PageAttachment({ attachment, onRemove }) {
  if (!attachment) return null;
  const label =
    attachment.type === "text_selection"
      ? "Selected text"
      : attachment.type === "visual_region"
        ? "Visual region"
        : "Page";
  return (
    <div className="attachment-card">
      <FileText size={18} aria-hidden="true" />
      <div>
        <strong>{attachment.filename}</strong>
        <span>
          {label} {attachment.pageNumber}
        </span>
      </div>
      <button onClick={onRemove} title="Remove attached context" aria-label="Remove attached context">
        <X size={16} />
      </button>
    </div>
  );
}
