import { FileText, Upload } from "lucide-react";

export default function PdfUploadEmptyState({ onSelectFile, uploading }) {
  return (
    <div className="empty-state">
      <div className="empty-icon" aria-hidden="true">
        <FileText size={40} />
      </div>
      <h1>Chưa có tài liệu</h1>
      <p>Tải lên một file PDF để bắt đầu học cùng VLearn Tutor.</p>
      <label className="primary-button">
        <Upload size={18} />
        {uploading ? "Đang tải lên..." : "Nhập tài liệu PDF"}
        <input
          type="file"
          accept=".pdf,application/pdf"
          onChange={onSelectFile}
          disabled={uploading}
          hidden
        />
      </label>
    </div>
  );
}
