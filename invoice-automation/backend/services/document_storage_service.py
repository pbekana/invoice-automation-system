"""
Document Storage Service with Storage Provider Abstraction.
Handles secure file storage, integrity checking (SHA-256), magic-byte validation,
and controlled document retrieval.
"""

import os
import hashlib
import uuid
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
from config import Config
from logger_config import logger


class StorageProvider(ABC):
    """Abstract interface for document storage providers (Local disk, S3, GCS, etc.)."""

    @abstractmethod
    def save(self, file_bytes: bytes, filename: str, mime_type: str) -> Tuple[bool, str, Optional[str]]:
        """Save file bytes and return (success, storage_path_or_key, error_message)."""
        pass

    @abstractmethod
    def retrieve(self, storage_key: str) -> Optional[bytes]:
        """Retrieve file bytes given the storage key."""
        pass

    @abstractmethod
    def delete(self, storage_key: str) -> bool:
        """Delete file from storage."""
        pass

    @abstractmethod
    def exists(self, storage_key: str) -> bool:
        """Check if file exists in storage."""
        pass


class LocalStorageProvider(StorageProvider):
    """Local filesystem storage provider."""

    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = base_dir or os.path.join(Config.UPLOAD_FOLDER, "documents")
        os.makedirs(self.base_dir, exist_ok=True)

    def _resolve_path(self, storage_key: str) -> str:
        # Prevent directory traversal
        safe_key = os.path.basename(storage_key)
        return os.path.join(self.base_dir, safe_key)

    def save(self, file_bytes: bytes, filename: str, mime_type: str) -> Tuple[bool, str, Optional[str]]:
        try:
            ext = os.path.splitext(filename)[1].lower()
            storage_key = f"{uuid.uuid4().hex}{ext}"
            target_path = self._resolve_path(storage_key)
            with open(target_path, "wb") as f:
                f.write(file_bytes)
            return True, storage_key, None
        except Exception as e:
            logger.error(f"Failed to save file to local storage: {e}")
            return False, "", str(e)

    def retrieve(self, storage_key: str) -> Optional[bytes]:
        target_path = self._resolve_path(storage_key)
        if not os.path.exists(target_path):
            return None
        try:
            with open(target_path, "rb") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read file from local storage: {e}")
            return None

    def get_absolute_path(self, storage_key: str) -> Optional[str]:
        target_path = self._resolve_path(storage_key)
        return target_path if os.path.exists(target_path) else None

    def delete(self, storage_key: str) -> bool:
        target_path = self._resolve_path(storage_key)
        if os.path.exists(target_path):
            try:
                os.remove(target_path)
                return True
            except Exception as e:
                logger.error(f"Failed to delete file from local storage: {e}")
                return False
        return False

    def exists(self, storage_key: str) -> bool:
        return os.path.exists(self._resolve_path(storage_key))


class DocumentStorageService:
    """Manages document storage, file signature verification, and retrieval."""

    MAGIC_SIGNATURES = {
        b"%PDF": "application/pdf",
        b"\x89PNG\r\n\x1a\n": "image/png",
        b"\xff\xd8\xff": "image/jpeg",
        b"GIF87a": "image/gif",
        b"GIF89a": "image/gif",
        b"BM": "image/bmp",
        b"II*\x00": "image/tiff",
        b"MM\x00*": "image/tiff",
        b"RIFF": "image/webp",  # Sub-verified below
    }

    def __init__(self, provider: Optional[StorageProvider] = None, db=None):
        self.provider = provider or LocalStorageProvider()
        self.db = db
        self.documents_collection = db["documents"] if db is not None else None

    def validate_file_signature(self, file_bytes: bytes, filename: str) -> Tuple[bool, str, Optional[str]]:
        """Validate both extension and magic bytes header to prevent malicious disguised files."""
        if not file_bytes:
            return False, "", "Empty file content"

        ext = os.path.splitext(filename)[1].lower().lstrip(".")
        if ext not in Config.ALLOWED_EXTENSIONS:
            return False, "", f"File extension '.{ext}' is not permitted"

        # Check magic bytes
        detected_mime = None
        for sig, mime in self.MAGIC_SIGNATURES.items():
            if file_bytes.startswith(sig):
                if sig == b"RIFF" and len(file_bytes) >= 12:
                    if file_bytes[8:12] != b"WEBP":
                        continue
                detected_mime = mime
                break

        if not detected_mime:
            # Fallback for tiff or other formats
            if ext in ["tif", "tiff"]:
                detected_mime = "image/tiff"
            else:
                return False, "", "File content does not match any valid document or image signature"

        return True, detected_mime, None

    def store_document(
        self,
        file_bytes: bytes,
        original_filename: str,
        user_id: str,
        tenant_id: Optional[str] = None
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Validate, hash, and store the original document.
        Returns (success, metadata_dict, error_message).
        """
        valid, mime_type, err = self.validate_file_signature(file_bytes, original_filename)
        if not valid:
            return False, None, err

        file_size = len(file_bytes)
        if file_size > Config.MAX_CONTENT_LENGTH:
            return False, None, f"File exceeds maximum allowed size of {Config.MAX_CONTENT_LENGTH // (1024 * 1024)}MB"

        sha256_hash = hashlib.sha256(file_bytes).hexdigest()

        # Save to storage provider
        success, storage_key, err = self.provider.save(file_bytes, original_filename, mime_type)
        if not success:
            return False, None, f"Storage failed: {err}"

        doc_record = {
            "document_id": uuid.uuid4().hex,
            "original_filename": original_filename,
            "storage_key": storage_key,
            "mime_type": mime_type,
            "file_size": file_size,
            "sha256_hash": sha256_hash,
            "uploaded_by": user_id,
            "tenant_id": tenant_id,
            "created_at": datetime.utcnow()
        }

        if self.documents_collection is not None:
            try:
                self.documents_collection.insert_one(doc_record.copy())
            except Exception as e:
                logger.error(f"Error persisting document record to database: {e}")

        return True, doc_record, None

    def retrieve_document(self, storage_key: str) -> Tuple[Optional[bytes], Optional[str]]:
        """Retrieve raw document bytes."""
        data = self.provider.retrieve(storage_key)
        if not data:
            return None, "Document not found in storage"
        return data, None

    def get_document_path(self, storage_key: str) -> Optional[str]:
        """Get absolute path if supported by provider."""
        if hasattr(self.provider, "get_absolute_path"):
            return self.provider.get_absolute_path(storage_key)
        return None


document_storage_service = DocumentStorageService()
