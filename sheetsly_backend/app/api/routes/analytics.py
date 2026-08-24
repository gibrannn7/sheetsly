"""API endpoints for deterministic spreadsheet analysis and operation catalog."""

from typing import Any, Dict, List
from fastapi import APIRouter, Path
from app.engine.analytics import (
    AggregationOpEnum,
    AnalyticalEngine,
    AnalyticalInstruction,
    AnalyticalResult,
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
