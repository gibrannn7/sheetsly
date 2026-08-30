"""Canonical Spreadsheet Action Registry, Action DSL, and Formatting models."""

import re
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field, field_validator


class ActionTypeEnum(str, Enum):
    """Authoritative registry of supported spreadsheet mutation actions."""

    WRITE_VALUE = "WRITE_VALUE"
    WRITE_FORMULA = "WRITE_FORMULA"
    INSERT_ROW = "INSERT_ROW"
    INSERT_COLUMN = "INSERT_COLUMN"
    FORMAT_CELL = "FORMAT_CELL"
    FORMAT_RANGE = "FORMAT_RANGE"
    SET_NUMBER_FORMAT = "SET_NUMBER_FORMAT"
    CLEAR_CONTENT = "CLEAR_CONTENT"
    CREATE_CHART = "CREATE_CHART"
    UPDATE_CHART = "UPDATE_CHART"
    MOVE_CHART = "MOVE_CHART"
    RESIZE_CHART = "RESIZE_CHART"
    DELETE_CHART = "DELETE_CHART"
    CREATE_KPI = "CREATE_KPI"
    CREATE_WORKSHEET = "CREATE_WORKSHEET"


SUPPORTED_ACTION_REGISTRY: Set[ActionTypeEnum] = frozenset({
    ActionTypeEnum.WRITE_VALUE,
    ActionTypeEnum.WRITE_FORMULA,
    ActionTypeEnum.INSERT_ROW,
    ActionTypeEnum.INSERT_COLUMN,
    ActionTypeEnum.FORMAT_CELL,
    ActionTypeEnum.FORMAT_RANGE,
    ActionTypeEnum.SET_NUMBER_FORMAT,
    ActionTypeEnum.CLEAR_CONTENT,
    ActionTypeEnum.CREATE_CHART,
    ActionTypeEnum.UPDATE_CHART,
    ActionTypeEnum.MOVE_CHART,
    ActionTypeEnum.RESIZE_CHART,
    ActionTypeEnum.DELETE_CHART,
    ActionTypeEnum.CREATE_KPI,
    ActionTypeEnum.CREATE_WORKSHEET,
})


class FormattingStyle(BaseModel):
    """Controlled, safe formatting attributes for cells and ranges."""

    bold: Optional[bool] = Field(None, description="Whether text should be bold")
    italic: Optional[bool] = Field(None, description="Whether text should be italicized")
    font_size: Optional[int] = Field(None, ge=6, le=72, description="Font size in points (6-72)")
    font_color: Optional[str] = Field(None, description="Hex font color code e.g. '#1E293B'")
    fill_color: Optional[str] = Field(None, description="Hex background fill color e.g. '#F1F5F9'")
    alignment: Optional[str] = Field(None, description="Horizontal alignment: 'left', 'center', 'right'")
    border_top: Optional[str] = Field(None, description="Border style: 'thin', 'medium', 'double', 'none'")
    border_bottom: Optional[str] = Field(None, description="Border style: 'thin', 'medium', 'double', 'none'")
    border_left: Optional[str] = Field(None, description="Border style: 'thin', 'medium', 'double', 'none'")
    border_right: Optional[str] = Field(None, description="Border style: 'thin', 'medium', 'double', 'none'")

    @field_validator("font_color", "fill_color")
    @classmethod
    def validate_hex_color(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        clean = v.strip()
        if not re.match(r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$", clean):
            if clean.lower() in {"black", "white", "yellow", "red", "green", "blue", "gray", "grey"}:
                return clean.lower()
            raise ValueError(f"Invalid color format: '{v}'. Must be a valid hex color e.g. '#F1F5F9'.")
        return clean.upper()

    @field_validator("alignment")
    @classmethod
    def validate_alignment(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        clean = v.strip().lower()
        if clean not in {"left", "center", "right", "justify"}:
            raise ValueError(f"Invalid alignment: '{v}'. Must be 'left', 'center', or 'right'.")
        return clean


class NumberFormatSpec(BaseModel):
    """Standard number formatting definition."""

    format_code: str = Field(..., description="Excel number format string e.g. '$#,##0.00', '0.0%'")
    category: Optional[str] = Field(None, description="Format category: 'currency', 'percentage', 'number', 'date', 'text'")
    decimal_places: Optional[int] = Field(None, ge=0, le=10, description="Decimal places precision")


class ChartActionSpec(BaseModel):
    """Specification for spreadsheet chart visualization action."""

    chart_id: str = Field(..., description="Unique chart identifier")
    sheet_name: Optional[str] = Field(None, description="Worksheet where chart is anchored")
    chart_type: str = Field("BAR", description="Chart type e.g. PIE, BAR, COLUMN, LINE, AREA, SCATTER, HISTOGRAM")
    title: str = Field(..., description="Descriptive chart title")
    dimension_column: Optional[str] = Field(None, description="Category or X-axis grouping column")
    category_column: Optional[str] = Field(None, description="Alias for category/dimension column")
    measure_column: Optional[str] = Field(None, description="Quantitative Y-axis metric column")
    aggregation: str = Field("SUM", description="Aggregation method: SUM, AVERAGE, COUNT, MIN, MAX")
    source_range: Optional[str] = Field(None, description="Source table or range lineage")
    destination_cell: str = Field("", description="Top-left anchor cell coordinate on sheet e.g. 'B12', 'N2'")
    anchor_cell: Optional[str] = Field(None, description="Explicit alias for destination anchor cell")
    width_cols: int = Field(8, ge=2, le=30, description="Visual width in spreadsheet columns")
    height_rows: int = Field(15, ge=2, le=50, description="Visual height in spreadsheet rows")
    image_url: Optional[str] = Field(None, description="Relative URL to retrieve the rendered PNG artifact")
    image_base64: Optional[str] = Field(None, description="Optional base64-encoded PNG image")
    summary_data: Optional[List[Dict[str, Any]]] = Field(None, description="Deterministic summarized plot data points")
    summary_range: Optional[str] = Field(None, description="Range of materialized summary table if written")
    calculation_reference: Optional[str] = Field(None, description="Reference to calculation helper location")
    provenance_note: Optional[str] = Field(None, description="Explainable lineage trace note")


class KPIActionSpec(BaseModel):
    """Specification for single-metric KPI card visualization."""

    kpi_id: str = Field(..., description="Unique KPI identifier")
    title: str = Field(..., description="KPI card label e.g. 'Total Sales'")
    measure_column: str = Field(..., description="Target quantitative measure column")
    aggregation: str = Field("SUM", description="Aggregation method: SUM, AVERAGE, COUNT, MIN, MAX")
    calculated_value: Any = Field(..., description="Authoritative deterministic scalar value")
    formatted_value: str = Field(..., description="Formatted value string e.g. '$2,297,200.86'")
    destination_cell: str = Field("G2", description="Top-left anchor cell coordinate on sheet e.g. 'G2'")
    source_range: Optional[str] = Field(None, description="Source cell range lineage")


class SpreadsheetAction(BaseModel):
    """Canonical bounded spreadsheet mutation action."""

    action_id: str = Field(..., description="Unique identifier for this action in a transaction")
    action_type: ActionTypeEnum = Field(..., description="Type of action from SUPPORTED_ACTION_REGISTRY")
    sheet_name: str = Field(..., description="Target worksheet name")
    target_cell: Optional[str] = Field(None, description="Single cell coordinate e.g. 'D102'")
    target_range: Optional[str] = Field(None, description="Range coordinate e.g. 'C102:D102'")
    value: Optional[Any] = Field(None, description="Literal value to write (for WRITE_VALUE)")
    formula: Optional[str] = Field(None, description="Excel formula string starting with '=' (for WRITE_FORMULA)")
    style: Optional[FormattingStyle] = Field(None, description="Formatting styling to apply")
    number_format: Optional[str] = Field(None, description="Number format code to apply")
    row_index: Optional[int] = Field(None, ge=1, description="1-indexed row number (for INSERT_ROW)")
    column_index: Optional[int] = Field(None, ge=1, description="1-indexed column number (for INSERT_COLUMN)")
    chart_spec: Optional[ChartActionSpec] = Field(None, description="Chart visualization spec for CREATE/UPDATE_CHART")
    kpi_spec: Optional[KPIActionSpec] = Field(None, description="KPI visualization spec for CREATE_KPI")
    expected_result: Optional[Any] = Field(None, description="Deterministic calculated expected result for verification")
    description: Optional[str] = Field(None, description="Human-readable explanation of this action")

    @field_validator("action_type")
    @classmethod
    def validate_action_type(cls, v: ActionTypeEnum) -> ActionTypeEnum:
        if v not in SUPPORTED_ACTION_REGISTRY:
            raise ValueError(f"Unsupported action type: '{v}'. Must be one of {sorted(list(SUPPORTED_ACTION_REGISTRY))}.")
        return v

    @field_validator("target_cell")
    @classmethod
    def validate_target_cell(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        clean = v.strip().upper()
        if not re.match(r"^[A-Z]{1,3}\d+$", clean):
            raise ValueError(f"Invalid cell reference: '{v}'. Must be valid A1-notation e.g. 'B4', 'AA10'.")
        return clean

    @field_validator("target_range")
    @classmethod
    def validate_target_range(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        clean = v.strip().upper()
        if not re.match(r"^[A-Z]{1,3}\d+:[A-Z]{1,3}\d+$", clean):
            if re.match(r"^[A-Z]{1,3}\d+$", clean):
                return f"{clean}:{clean}"
            raise ValueError(f"Invalid range reference: '{v}'. Must be valid A1:B2 notation.")
        return clean

    @field_validator("formula")
    @classmethod
    def validate_formula_format(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        clean = v.strip()
        if not clean.startswith("="):
            clean = f"={clean}"
        return clean
