from __future__ import annotations

import json
import shutil
import uuid
from datetime import UTC, datetime
from pathlib import Path

import fitz
from fastapi import HTTPException, UploadFile

from app.config import settings
from app.schemas import DocumentMetadata


class DocumentService:
    def __init__(self) -> None:
        self.storage_dir = settings.storage_dir
        self.metadata_dir = settings.metadata_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)

    def _metadata_path(self, document_id: str) -> Path:
        self._validate_document_id(document_id)
        return self.metadata_dir / f"{document_id}.json"

    def _file_path(self, document_id: str) -> Path:
        self._validate_document_id(document_id)
        return self.storage_dir / f"{document_id}.pdf"

    @staticmethod
    def _validate_document_id(document_id: str) -> None:
        try:
            uuid.UUID(document_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu.") from exc

    @staticmethod
    def _validate_filename(filename: str | None) -> str:
        if not filename:
            raise HTTPException(status_code=400, detail="File PDF không hợp lệ.")
        original = Path(filename).name
        if Path(original).suffix.lower() != ".pdf":
            raise HTTPException(status_code=400, detail="Chỉ hỗ trợ file PDF.")
        return original

    def _write_metadata(self, metadata: DocumentMetadata) -> None:
        path = self._metadata_path(metadata.id)
        path.write_text(
            metadata.model_dump_json(indent=2),
            encoding="utf-8",
        )

    def get_metadata(self, document_id: str) -> DocumentMetadata:
        path = self._metadata_path(document_id)
        if not path.exists():
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu.")
        return DocumentMetadata(**json.loads(path.read_text(encoding="utf-8")))

    def list_documents(self) -> list[DocumentMetadata]:
        documents: list[DocumentMetadata] = []
        for path in self.metadata_dir.glob("*.json"):
            try:
                documents.append(DocumentMetadata(**json.loads(path.read_text(encoding="utf-8"))))
            except (json.JSONDecodeError, TypeError, ValueError):
                continue
        return sorted(documents, key=lambda item: item.uploaded_at, reverse=True)

    def get_file_path(self, document_id: str) -> Path:
        metadata = self.get_metadata(document_id)
        path = self.storage_dir / metadata.stored_filename
        if not path.exists() or path.resolve().parent != self.storage_dir.resolve():
            raise HTTPException(status_code=404, detail="Không tìm thấy file PDF.")
        return path

    async def save_upload(self, file: UploadFile) -> DocumentMetadata:
        original_filename = self._validate_filename(file.filename)
        if file.content_type and file.content_type not in {
            "application/pdf",
            "application/x-pdf",
            "application/octet-stream",
        }:
            raise HTTPException(status_code=400, detail="Chỉ hỗ trợ file PDF.")

        document_id = str(uuid.uuid4())
        stored_filename = f"{document_id}.pdf"
        target_path = self.storage_dir / stored_filename
        max_bytes = settings.max_upload_mb * 1024 * 1024
        size_bytes = 0

        try:
            with target_path.open("wb") as output:
                while chunk := await file.read(1024 * 1024):
                    size_bytes += len(chunk)
                    if size_bytes > max_bytes:
                        raise HTTPException(
                            status_code=413,
                            detail="File vượt quá dung lượng cho phép.",
                        )
                    output.write(chunk)

            try:
                with fitz.open(target_path) as pdf:
                    page_count = pdf.page_count
            except Exception as exc:
                raise HTTPException(status_code=400, detail="Không thể đọc PDF. Hãy thử file khác.") from exc

            if page_count < 1:
                raise HTTPException(status_code=400, detail="PDF không có trang hợp lệ.")

            metadata = DocumentMetadata(
                id=document_id,
                original_filename=original_filename,
                stored_filename=stored_filename,
                page_count=page_count,
                size_bytes=size_bytes,
                uploaded_at=datetime.now(UTC).isoformat(),
            )
            self._write_metadata(metadata)
            return metadata
        except Exception:
            if target_path.exists():
                target_path.unlink(missing_ok=True)
            raise
        finally:
            await file.close()

    def delete_document(self, document_id: str) -> bool:
        metadata = self.get_metadata(document_id)
        file_path = self.storage_dir / metadata.stored_filename
        metadata_path = self._metadata_path(document_id)
        if file_path.exists() and file_path.resolve().parent == self.storage_dir.resolve():
            file_path.unlink()
        if metadata_path.exists():
            metadata_path.unlink()
        return True

    def clear_runtime_storage(self) -> None:
        for folder in [self.storage_dir, self.metadata_dir]:
            for path in folder.iterdir():
                if path.name != ".gitkeep":
                    if path.is_dir():
                        shutil.rmtree(path)
                    else:
                        path.unlink()
