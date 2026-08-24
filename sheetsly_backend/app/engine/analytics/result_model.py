"""Analytical Result and Calculation Lineage schemas."""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class ResultTypeEnum(str, Enum):
    """Data shape of an analytical result."""

    SCALAR = "SCALAR"
    TABLE = "TABLE"
    SERIES = "SERIES"
    METADATA = "METADATA"


class CalculationLineage(BaseModel):
    """Complete provenance and calculation lineage for full traceability."""

    dataset_id: str = Field(..., description="Source dataset UUID")
    sheet_name: str = Field(..., description="Source sheet name")
    table_id: str = Field(..., description="Source table identifier")
    source_range: str = Field(..., description="Physical bounding range of source data used, e.g. 'E2:E100'")
    source_columns: List[str] = Field(default_factory=list, description="Column names involved in query")
    total_table_rows: int = Field(0, description="Total rows in the source table")
    rows_included: int = Field(0, description="Number of rows included after filtering")
    rows_excluded: int = Field(0, description="Number of rows excluded by filters")
    filters_applied: List[str] = Field(default_factory=list, description="Human-readable filters applied")
    grouping_applied: List[str] = Field(default_factory=list, description="Group-by dimensions applied")
    operations_performed: List[str] = Field(default_factory=list, description="Ordered list of executed operation primitives")
    calculation_steps: List[str] = Field(default_factory=list, description="Detailed trace answering 'How was this calculated?'")
    execution_time_ms: float = Field(0.0, description="Calculation runtime in milliseconds")


class SeriesDataPoint(BaseModel):
    """Single labeled data point for 1D series results."""

    label: str = Field(..., description="Category or temporal label")
    value: Optional[Union[float, int, str]] = Field(None, description="Numeric or scalar value")


class TableResultData(BaseModel):
    """Tabular result structure for GROUP_BY or filtered datasets."""

    columns: List[str] = Field(default_factory=list, description="Ordered result column headers")
    rows: List[Dict[str, Any]] = Field(default_factory=list, description="List of row dictionaries keyed by column name")
    total_rows: int = Field(0, description="Total number of result rows")


class AnalyticalResult(BaseModel):
    """Authoritative result envelope produced exclusively by the Python analytical engine."""

    result_type: ResultTypeEnum = Field(..., description="Shape of result (SCALAR, TABLE, SERIES, METADATA)")
    operation: str = Field(..., description="Operation executed")
    scalar_value: Optional[Union[float, int, str, bool]] = Field(None, description="Scalar result value (for SUM, AVG, COUNT, etc.)")
    scalar_formatted: Optional[str] = Field(None, description="Human-formatted scalar string")
    series_data: Optional[List[SeriesDataPoint]] = Field(None, description="Ordered series points if result is 1D series")
    table_data: Optional[TableResultData] = Field(None, description="Tabular data if result is 2D table")
    lineage: CalculationLineage = Field(..., description="Complete audit and calculation lineage")
