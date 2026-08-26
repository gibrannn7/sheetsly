"""API endpoints for deterministic spreadsheet analysis and operation catalog."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Path
from pydantic import BaseModel
from app.engine.analytics import (
    AggregationOpEnum,
    AnalyticalEngine,
    AnalyticalInstruction,
    AnalyticalResult,
    ExplainableAnalyticsResult,
    FilterOperatorEnum,
    OperationEnum,
    analytical_engine,
)

router = APIRouter(tags=["Analytical Engine"])


@router.post("/datasets/{dataset_id}/analyze", response_model=AnalyticalResult)
async def analyze_dataset(
    dataset_id: str = Path(..., description="Target dataset UUID"),
    instruction: AnalyticalInstruction = ...,
) -> AnalyticalResult:
    """
    Executes a deterministic analytical instruction (SUM, AVERAGE, GROUP_BY, FILTER, etc.)
    against a verified spreadsheet table.
    Returns structured results (SCALAR, TABLE, SERIES) along with complete provenance and calculation lineage.
    """
    # Enforce dataset_id alignment
    instruction.dataset_id = dataset_id
    return analytical_engine.execute(instruction)


@router.get("/operations/catalog")
async def get_operation_catalog() -> Dict[str, Any]:
    """
    Returns the supported deterministic operation catalog, aggregations, and filter operators.
    Used by both the frontend Operation Builder UI and the query planner.
    """
    return {
        "operations": [op.value for op in OperationEnum],
        "aggregations": [agg.value for agg in AggregationOpEnum],
        "filter_operators": [f.value for f in FilterOperatorEnum],
        "count_semantics": {
            "COUNT_ROWS": "Counts total number of rows/records in table or selection",
            "COUNT_VALUES": "Counts non-null, non-empty cells in specified column",
            "DISTINCT_COUNT": "Counts unique non-null values in specified column",
        },
        "supported_primitives": ["CALCULATE", "FILTER", "GROUP_BY", "SORT", "CONDITIONAL"],
    }


class GranularAnalyticsQueryRequest(BaseModel):
    """Payload for requesting deterministic granular analytical visualization."""

    query: str
    active_sheet_name: Optional[str] = None


@router.post("/datasets/{dataset_id}/granular-analytics", response_model=ExplainableAnalyticsResult)
async def execute_granular_analytics(
    dataset_id: str = Path(..., description="Target dataset UUID"),
    payload: GranularAnalyticsQueryRequest = ...,
) -> ExplainableAnalyticsResult:
    """
    Executes a deterministic smart analytical visualization query with full provenance and verification.
    """
    from app.engine.pipeline import ingestion_pipeline
    from app.engine.analytics import GranularAnalyticsEngine

    grids = ingestion_pipeline.get_all_grids(dataset_id)
    index = ingestion_pipeline.get_workbook_index(dataset_id)

    return GranularAnalyticsEngine.execute_analytics_query(
        user_query=payload.query,
        workbook_index=index,
        grids=grids,
        active_sheet_name=payload.active_sheet_name,
    )

