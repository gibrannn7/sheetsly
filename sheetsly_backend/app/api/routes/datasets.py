"""Dataset management and spreadsheet ingestion endpoints."""

from fastapi import APIRouter, File, UploadFile, status
from app.core.errors import FileValidationError
from app.core.logging import logger
from app.engine.pipeline import ingestion_pipeline
from app.models.schemas import WorkbookOverview
from app.storage.file_manager import file_manager

router = APIRouter(prefix="/datasets", tags=["Datasets"])


@router.post("/upload", response_model=WorkbookOverview, status_code=status.HTTP_201_CREATED)
async def upload_spreadsheet(
    file: UploadFile = File(..., description="Spreadsheet file (.xlsx, .xls, .csv, .xlsm)"),
) -> WorkbookOverview:
    """
    Ingests and deterministically inspects an uploaded spreadsheet workbook.
    Returns complete structural metadata, sheet inventory, detected tables, column types, and data quality metrics.
    """
    if not file.filename:
        raise FileValidationError("Filename cannot be empty.")

    # 1. Save uploaded file to secure temporary storage
    dataset_id, file_path, original_filename, file_size_bytes = await file_manager.save_uploaded_file(file)

    # 2. Run deterministic inspection pipeline
    try:
        overview = ingestion_pipeline.process_workbook(
            dataset_id=dataset_id,
            file_path=file_path,
            original_filename=original_filename,
            file_size_bytes=file_size_bytes,
        )
        return overview
    except Exception as e:
        # Clean up stored file if processing failed
        file_manager.cleanup_dataset(dataset_id)
        raise


@router.get("/{dataset_id}", response_model=WorkbookOverview)
async def get_dataset_overview(dataset_id: str) -> WorkbookOverview:
    """Retrieves workbook structural overview and inspection report for an active dataset ID."""
    return ingestion_pipeline.get_overview(dataset_id)


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dataset(dataset_id: str) -> None:
    """Cleans up temporary files and session data for a dataset ID."""
    file_manager.cleanup_dataset(dataset_id)
