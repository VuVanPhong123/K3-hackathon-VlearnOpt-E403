from __future__ import annotations

import hashlib
import json
import shutil
import uuid
from datetime import UTC, datetime
from pathlib import Path

import fitz
from fastapi import HTTPException, UploadFile

from app.config import settings
from app.repositories.document_repository import DocumentRepository
from app.schemas import DocumentMetadata


class DocumentService:
    def __init__(self) -> None:
        self.storage_dir = settings.storage_dir
        self.metadata_dir = settings.metadata_dir
        self.page_cache_dir = settings.page_cache_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        self.page_cache_dir.mkdir(parents=True, exist_ok=True)
        self.repository = DocumentRepository()

    def _metadata_path(self, document_id: str) -> Path:
        self._validate_document_id(document_id)
        return self.metadata_dir / f"{document_id}.json"

    @staticmethod
    def _validate_document_id(document_id: str) -> None:
        try:
            uuid.UUID(document_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail="Document not found.") from exc

    @staticmethod
    def _validate_filename(filename: str | None) -> str:
        if not filename:
            raise HTTPException(status_code=400, detail="Invalid PDF file.")
        original = Path(filename).name
        if Path(original).suffix.lower() != ".pdf":
            raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        return original

    def _write_metadata(self, metadata: DocumentMetadata) -> None:
        path = self._metadata_path(metadata.id)
        path.write_text(metadata.model_dump_json(indent=2), encoding="utf-8")
        self.repository.upsert_document(metadata)

    def get_metadata(self, document_id: str) -> DocumentMetadata:
        metadata = self.repository.get_document(document_id)
        if metadata:
            return metadata
        path = self._metadata_path(document_id)
        if not path.exists():
            raise HTTPException(status_code=404, detail="Document not found.")
        metadata = DocumentMetadata(**json.loads(path.read_text(encoding="utf-8")))
        if metadata.status == "UPLOADED" and metadata.chunk_count == 0:
            metadata.status = "NEEDS_INDEX"
        self.repository.upsert_document(metadata)
        return metadata

    def list_documents(self) -> list[DocumentMetadata]:
        documents = {item.id: item for item in self.repository.list_documents()}
        for path in self.metadata_dir.glob("*.json"):
            try:
                metadata = DocumentMetadata(**json.loads(path.read_text(encoding="utf-8")))
                documents.setdefault(metadata.id, metadata)
                self.repository.upsert_document(documents[metadata.id])
            except (json.JSONDecodeError, TypeError, ValueError):
                continue
        return sorted(documents.values(), key=lambda item: item.uploaded_at, reverse=True)

    def get_file_path(self, document_id: str) -> Path:
        metadata = self.get_metadata(document_id)
        path = self.storage_dir / Path(metadata.stored_filename).name
        if not path.exists() or path.resolve().parent != self.storage_dir.resolve():
            raise HTTPException(status_code=404, detail="PDF file not found.")
        return path

    async def save_upload(self, file: UploadFile) -> DocumentMetadata:
        original_filename = self._validate_filename(file.filename)
        if file.content_type and file.content_type not in {
            "application/pdf",
            "application/x-pdf",
            "application/octet-stream",
        }:
            raise HTTPException(status_code=400, detail="Only PDF files are supported.")

        document_id = str(uuid.uuid4())
        stored_filename = f"{document_id}.pdf"
        target_path = self.storage_dir / stored_filename
        max_bytes = settings.max_upload_mb * 1024 * 1024
        size_bytes = 0
        hasher = hashlib.sha256()

        try:
            with target_path.open("wb") as output:
                while chunk := await file.read(1024 * 1024):
                    size_bytes += len(chunk)
                    if size_bytes > max_bytes:
                        raise HTTPException(status_code=413, detail="File is larger than the configured limit.")
                    hasher.update(chunk)
                    output.write(chunk)

            checksum_sha256 = hasher.hexdigest()
            existing = self.repository.find_by_checksum(checksum_sha256)
            if existing:
                target_path.unlink(missing_ok=True)
                return existing

            try:
                with fitz.open(target_path) as pdf:
                    page_count = pdf.page_count
            except Exception as exc:
                raise HTTPException(status_code=400, detail="Could not read PDF. Try another file.") from exc

            if page_count < 1:
                raise HTTPException(status_code=400, detail="PDF has no valid pages.")

            metadata = DocumentMetadata(
                id=document_id,
                original_filename=original_filename,
                stored_filename=stored_filename,
                checksum_sha256=checksum_sha256,
                version=1,
                page_count=page_count,
                size_bytes=size_bytes,
                uploaded_at=datetime.now(UTC).isoformat(),
                status="UPLOADED",
            )
            self._write_metadata(metadata)
            self.repository.set_job(document_id, "UPLOADED", "queued", 0)
            return metadata
        except Exception:
            if target_path.exists():
                target_path.unlink(missing_ok=True)
            raise
        finally:
            await file.close()

    def delete_document(self, document_id: str) -> bool:
        metadata = self.get_metadata(document_id)
        self.repository.update_status(document_id, "DELETING")
        file_path = self.storage_dir / Path(metadata.stored_filename).name
        metadata_path = self._metadata_path(document_id)
        if file_path.exists() and file_path.resolve().parent == self.storage_dir.resolve():
            file_path.unlink()
        if metadata_path.exists():
            metadata_path.unlink()
        for path in self.page_cache_dir.iterdir():
            if path.name != ".gitkeep" and path.is_file():
                path.unlink(missing_ok=True)
        self.repository.delete_document_data(document_id)
        return True

    def clear_runtime_storage(self) -> None:
        for folder in [self.storage_dir, self.metadata_dir, self.page_cache_dir]:
            for path in folder.iterdir():
                if path.name != ".gitkeep":
                    if path.is_dir():
                        shutil.rmtree(path)
                    else:
                        path.unlink()
