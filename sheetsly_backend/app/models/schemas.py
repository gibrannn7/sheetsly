"""Pydantic schema definitions for workbook inspection, profiling, and quality reports."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DataTypeEnum(str, Enum):
    """Physical data types detectable in spreadsheet cells and columns."""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    CURRENCY = "currency"
    PERCENTAGE = "percentage"
    DATE = "date"
    DATETIME = "datetime"
    BOOLEAN = "boolean"
    FORMULA = "formula"
    NULL = "null"
    UNKNOWN = "unknown"


class OrientationEnum(str, Enum):
    """Table structure orientations."""

    VERTICAL = "VERTICAL"
    HORIZONTAL = "HORIZONTAL"
    AMBIGUOUS = "AMBIGUOUS"
    IRREGULAR = "IRREGULAR"


class SemanticTypeEnum(str, Enum):
    """Inferred semantic role of a column."""

    CATEGORICAL = "categorical"
    NUMERIC_MEASURE = "numeric_measure"
    TEMPORAL = "temporal"
    IDENTIFIER = "identifier"
    TEXT = "text"
    BOOLEAN = "boolean"
    UNKNOWN = "unknown"


class IssueSeverityEnum(str, Enum):
    """Severity levels for data quality issues."""

    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class CellCoordinate(BaseModel):
    """Accurate physical location of a cell in a sheet."""

    row: int = Field(..., description="1-indexed row number")
    column: int = Field(..., description="1-indexed column number")
    cell_ref: str = Field(..., description="A1-style cell reference, e.g., 'B4'")


class CellData(BaseModel):
    """Cell-level representation preserving original and parsed data for full traceability."""

    coordinate: CellCoordinate
    original_value: Optional[Any] = Field(None, description="Raw unparsed value or string from workbook")
    parsed_value: Optional[Any] = Field(None, description="Parsed deterministic value (int, float, date, etc.)")
    data_type: DataTypeEnum = Field(DataTypeEnum.UNKNOWN, description="Detected physical data type")
    formula: Optional[str] = Field(None, description="Raw formula string if cell contains a formula")
    is_empty: bool = Field(False, description="True if cell has no value")


class ColumnMetadata(BaseModel):
    """Metadata profile for a detected table column."""

    index: int = Field(..., description="0-indexed position within the detected table")
    name: str = Field(..., description="Header or column identifier name")
    original_header_cell: Optional[str] = Field(None, description="Coordinate of source header cell e.g. 'A1'")
    source_column_letter: str = Field(..., description="Excel column letter e.g. 'A', 'B', 'AA'")
    data_type: DataTypeEnum = Field(..., description="Dominant physical data type")
    semantic_type: SemanticTypeEnum = Field(SemanticTypeEnum.UNKNOWN, description="Inferred semantic role")
    type_confidence: float = Field(1.0, ge=0.0, le=1.0, description="Confidence in assigned data type")
    total_count: int = Field(0, description="Total rows inspected in this column")
    null_count: int = Field(0, description="Count of empty or null cells")
    unique_count: int = Field(0, description="Count of distinct non-null values")
    sample_values: List[Any] = Field(default_factory=list, description="First few non-null sample values")


class TableRegion(BaseModel):
    """Detected candidate table/data region within a sheet."""

    table_id: str = Field(..., description="Unique table identifier within the dataset")
    name: str = Field(..., description="Human-readable table name")
    sheet_name: str = Field(..., description="Name of parent sheet")
    range_address: str = Field(..., description="Bounding box range, e.g., 'A4:F50'")
    header_range: Optional[str] = Field(None, description="Header cells range, e.g., 'A4:F4'")
    data_range: Optional[str] = Field(None, description="Data rows range, e.g., 'A5:F50'")
    header_row_indices: List[int] = Field(default_factory=list, description="1-indexed row numbers containing headers")
    orientation: OrientationEnum = Field(OrientationEnum.VERTICAL, description="Detected orientation")
    orientation_confidence: float = Field(1.0, ge=0.0, le=1.0, description="Confidence score for orientation")
    orientation_reasons: List[str] = Field(default_factory=list, description="Structural evidence explaining orientation")
    row_count: int = Field(0, description="Total data rows in table")
    column_count: int = Field(0, description="Total columns in table")
    columns: List[ColumnMetadata] = Field(default_factory=list, description="Detected column metadata")
    confidence_score: float = Field(1.0, ge=0.0, le=1.0, description="Overall table detection confidence")


class DataQualityIssue(BaseModel):
    """Specific data quality anomaly or violation detected in sheet or table."""

    issue_type: str = Field(..., description="Issue category identifier")
    severity: IssueSeverityEnum = Field(IssueSeverityEnum.WARNING, description="Severity of issue")
    message: str = Field(..., description="Actionable explanation of data quality issue")
    sheet_name: str = Field(..., description="Affected sheet")
    table_id: Optional[str] = Field(None, description="Affected table ID if scoped to a table")
    column_name: Optional[str] = Field(None, description="Affected column if scoped to a column")
    affected_cells_count: int = Field(0, description="Number of cells or rows impacted")
    sample_locations: List[str] = Field(default_factory=list, description="Sample cell references e.g. ['B5', 'B12']")


class DataQualityReport(BaseModel):
    """Aggregate data quality score and diagnostics for a sheet or workbook."""

    overall_score: float = Field(100.0, ge=0.0, le=100.0, description="Score from 0 to 100")
    total_issues: int = Field(0, description="Count of detected quality issues")
    issues: List[DataQualityIssue] = Field(default_factory=list, description="List of quality issues")
    summary: str = Field("Data quality checks completed.", description="High-level quality summary")


class SheetMetadata(BaseModel):
    """Comprehensive sheet-level metadata."""

    name: str = Field(..., description="Sheet name")
    index: int = Field(..., description="0-indexed sheet position in workbook")
    is_hidden: bool = Field(False, description="True if sheet is marked hidden in Excel")
    dimensions: str = Field("A1:A1", description="Reported or computed sheet dimensions, e.g. 'A1:H150'")
    total_rows: int = Field(0, description="Total row span")
    total_columns: int = Field(0, description="Total column span")
    used_range: str = Field("A1:A1", description="Non-empty cell bounding box range")
    empty_rows_count: int = Field(0, description="Number of fully empty rows in used range")
    empty_cols_count: int = Field(0, description="Number of fully empty columns in used range")
    merged_cells_regions: List[str] = Field(default_factory=list, description="List of merged cell ranges e.g. ['A1:D1']")
    formula_cells_count: int = Field(0, description="Number of formula-bearing cells")
    tables: List[TableRegion] = Field(default_factory=list, description="Detected candidate tables in this sheet")
    quality_report: DataQualityReport = Field(default_factory=DataQualityReport, description="Data quality report for sheet")


class WorkbookOverview(BaseModel):
    """Top-level dataset metadata returned after spreadsheet upload and inspection."""

    dataset_id: str = Field(..., description="UUID identifier for the active dataset")
    filename: str = Field(..., description="Original user file name")
    file_size_bytes: int = Field(..., description="File size in bytes")
    sheet_count: int = Field(..., description="Number of sheets in workbook")
    sheets: List[SheetMetadata] = Field(default_factory=list, description="Metadata for each sheet")
    overall_quality_score: float = Field(100.0, description="Aggregated quality score across workbook")
    created_at: str = Field(..., description="ISO timestamp of ingestion")


class SheetDataGridResponse(BaseModel):
    """Paginated raw & parsed cell grid for the actual spreadsheet viewer."""

    dataset_id: str
    sheet_name: str
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=500)
    total_rows: int
    total_columns: int
    column_headers: List[str] = Field(default_factory=list, description="Column letters or detected names")
    rows: List[List[CellData]] = Field(default_factory=list, description="2D grid of cells")
    merged_cells: List[str] = Field(default_factory=list, description="Merged regions intersecting this sheet")


class HealthResponse(BaseModel):
    """Healthcheck endpoint response."""

    status: str = "ok"
    app_name: str
    version: str
    environment: str
    engine: Dict[str, Any]
