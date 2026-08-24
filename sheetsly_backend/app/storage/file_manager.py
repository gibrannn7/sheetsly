"""Safe file storage and temporary dataset management."""

import os
import re
import shutil
import uuid
from pathlib import Path
from typing import Dict, Optional, Tuple
from fastapi import UploadFile

from app.core.config import settings
from app.core.errors import FileValidationError, DatasetNotFoundError
from app.core.logging import logger

ALLOWED_EXTENSIONS = {".xlsx", ".xls", ".csv", ".xlsm", ".xltx"}


def sanitize_filename(filename: str) -> str:
    """Sanitizes user-provided filename to prevent path traversal or special character exploits."""
    clean_name = re.sub(r"[^\w\s\.-]", "_", filename).strip()
    return clean_name or "uploaded_dataset.xlsx"


class FileManager:
    """Manages secure temporary storage of uploaded spreadsheet datasets."""

    def __init__(self, base_storage_dir: Optional[Path] = None):
        self.base_dir = base_storage_dir or settings.temp_storage_path
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._dataset_registry: Dict[str, Dict[str, str]] = {}

    def validate_file_metadata(self, filename: str, content_length: Optional[int] = None) -> str:
        """Validates file extension and reported content length."""
        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            allowed_list = ", ".join(ALLOWED_EXTENSIONS)
            raise FileValidationError(
                f"Unsupported file format '{ext}'. Allowed formats: {allowed_list}",
                details={"provided_extension": ext, "allowed_extensions": list(ALLOWED_EXTENSIONS)},
            )

        if content_length and content_length > settings.max_upload_size_bytes:
            raise FileValidationError(
                f"File size exceeds maximum allowed limit of {settings.MAX_UPLOAD_SIZE_MB}MB.",
                details={"file_size_bytes": content_length, "max_allowed_bytes": settings.max_upload_size_bytes},
            )
        return ext

    async def save_uploaded_file(self, upload_file: UploadFile) -> Tuple[str, Path, str, int]:
        """
        Saves an uploaded file to a unique dataset directory in temporary storage.
        Returns: (dataset_id, file_path, original_filename, file_size_bytes)
        """
        original_filename = upload_file.filename or "spreadsheet.xlsx"
        ext = self.validate_file_metadata(original_filename, upload_file.size)

        dataset_id = str(uuid.uuid4())
        dataset_dir = self.base_dir / dataset_id
        dataset_dir.mkdir(parents=True, exist_ok=True)

        safe_name = sanitize_filename(original_filename)
        destination_path = dataset_dir / safe_name

        total_bytes = 0
        try:
            with open(destination_path, "wb") as buffer:
                while chunk := await upload_file.read(1024 * 1024):  # 1MB chunks
                    total_bytes += len(chunk)
                    if total_bytes > settings.max_upload_size_bytes:
                        # Exceeded limit during upload stream
                        raise FileValidationError(
                            f"File size exceeds maximum allowed limit of {settings.MAX_UPLOAD_SIZE_MB}MB.",
                            details={"total_bytes_read": total_bytes, "max_allowed_bytes": settings.max_upload_size_bytes},
                        )
                    buffer.write(chunk)
        except Exception as e:
            # Clean up on failure
            if dataset_dir.exists():
                shutil.rmtree(dataset_dir, ignore_errors=True)
            if isinstance(e, FileValidationError):
                raise
            raise FileValidationError(f"Failed to save uploaded file: {str(e)}")

        self._dataset_registry[dataset_id] = {
            "file_path": str(destination_path),
            "original_filename": original_filename,
            "file_size": str(total_bytes),
        }

        logger.info(f"Dataset {dataset_id} stored successfully ({total_bytes} bytes): {safe_name}")
        return dataset_id, destination_path, original_filename, total_bytes

    def get_dataset_path(self, dataset_id: str) -> Path:
        """Resolves the file path for an active dataset ID."""
        if dataset_id in self._dataset_registry:
            file_path = Path(self._dataset_registry[dataset_id]["file_path"])
            if file_path.exists():
                return file_path

        # Check directory directly if server restarted
        dataset_dir = self.base_dir / dataset_id
        if dataset_dir.exists() and dataset_dir.is_dir():
            files = [f for f in dataset_dir.iterdir() if f.is_file()]
            if files:
                return files[0]

        raise DatasetNotFoundError(dataset_id)

    def get_dataset_dir(self, dataset_id: str) -> Path:
        """Resolves or creates the directory for an active dataset ID."""
        dataset_dir = self.base_dir / dataset_id
        dataset_dir.mkdir(parents=True, exist_ok=True)
        return dataset_dir

    def cleanup_dataset(self, dataset_id: str) -> bool:
        """Removes the dataset directory and files from temporary storage."""
        dataset_dir = self.base_dir / dataset_id
        if dataset_dir.exists():
            shutil.rmtree(dataset_dir, ignore_errors=True)
            self._dataset_registry.pop(dataset_id, None)
            logger.info(f"Cleaned up temporary storage for dataset {dataset_id}")
            return True
        return False

    def cleanup_all(self) -> None:
        """Removes all temporary datasets (called on application startup/shutdown)."""
        if self.base_dir.exists():
            for item in self.base_dir.iterdir():
                if item.is_dir():
                    shutil.rmtree(item, ignore_errors=True)
        self._dataset_registry.clear()
        logger.info("Cleared all temporary dataset storage.")


file_manager = FileManager()
