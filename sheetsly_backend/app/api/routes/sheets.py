"""Sheet-level inspection, table discovery, and data grid viewer endpoints."""

from typing import List
from fastapi import APIRouter, Query
from app.engine.pipeline import ingestion_pipeline
from app.models.schemas import (
    SheetDataGridResponse,
    SheetMetadata,
    TableRegion,
)

router = APIRouter(prefix="/datasets/{dataset_id}/sheets", tags=["Sheets & Data Explorer"])


@router.get("", response_model=List[SheetMetadata])
async def list_sheets(dataset_id: str) -> List[SheetMetadata]:
    """Lists all sheets and their structural profiles in a dataset."""
    overview = ingestion_pipeline.get_overview(dataset_id)
    return overview.sheets


@router.get("/{sheet_name}", response_model=SheetMetadata)
async def get_sheet_metadata(dataset_id: str, sheet_name: str) -> SheetMetadata:
    """Retrieves detailed structural and profiling metadata for a specific sheet."""
    overview = ingestion_pipeline.get_overview(dataset_id)
    for s in overview.sheets:
        if s.name == sheet_name:
            return s
    from app.core.errors import SheetNotFoundError
    raise SheetNotFoundError(sheet_name)


@router.get("/{sheet_name}/tables", response_model=List[TableRegion])
async def get_sheet_tables(dataset_id: str, sheet_name: str) -> List[TableRegion]:
    """Retrieves all candidate tables detected inside a sheet."""
    sheet_meta = await get_sheet_metadata(dataset_id, sheet_name)
    return sheet_meta.tables


@router.get("/{sheet_name}/data", response_model=SheetDataGridResponse)
async def get_sheet_data_grid(
    dataset_id: str,
    sheet_name: str,
    page: int = Query(1, ge=1, description="1-indexed page number"),
    page_size: int = Query(50, ge=1, le=500, description="Number of rows per page"),
) -> SheetDataGridResponse:
    """
    Retrieves a paginated 2D cell slice of actual spreadsheet data for the frontend viewer.
    Preserves row numbers, column headers, cell coordinates, data types, and raw/parsed values.
    """
    return ingestion_pipeline.get_sheet_data_page(
        dataset_id=dataset_id,
        sheet_name=sheet_name,
        page=page,
        page_size=page_size,
    )
