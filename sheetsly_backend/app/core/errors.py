"""Domain exceptions and FastAPI error handling handlers."""

from typing import Any, Dict, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse


class SheetslyError(Exception):
    """Base domain exception for Sheetsly."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


class FileValidationError(SheetslyError):
    """Raised when uploaded file fails format or size validation."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="FILE_VALIDATION_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


class DatasetNotFoundError(SheetslyError):
    """Raised when requested dataset ID is not found in temporary storage."""

    def __init__(self, dataset_id: str):
        super().__init__(
            message=f"Dataset with ID '{dataset_id}' not found or expired.",
            code="DATASET_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"dataset_id": dataset_id},
        )


class SheetNotFoundError(SheetslyError):
    """Raised when requested sheet is not found in workbook."""

    def __init__(self, sheet_name: str):
        super().__init__(
            message=f"Sheet '{sheet_name}' not found in workbook.",
            code="SHEET_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"sheet_name": sheet_name},
        )


class WorkbookParseError(SheetslyError):
    """Raised when parsing or reading workbook fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="WORKBOOK_PARSE_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )


class TableAmbiguityError(SheetslyError):
    """Raised when sheet structure or table orientation cannot be determined safely."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="STRUCTURAL_AMBIGUITY",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )


async def sheetsly_exception_handler(request: Request, exc: SheetslyError) -> JSONResponse:
    """FastAPI exception handler for domain exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """FastAPI exception handler for unhandled exceptions."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred during processing.",
                "details": {"error_type": type(exc).__name__},
            }
        },
    )
