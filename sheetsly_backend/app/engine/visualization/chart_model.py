"""Domain models and schemas for deterministic visualization."""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

from app.engine.analytics.instruction_model import AnalyticalInstruction
from app.engine.analytics.result_model import AnalyticalResult


class ChartTypeEnum(str, Enum):
    """Supported deterministic chart types in Sheetsly."""

    BAR = "BAR"
    COLUMN = "COLUMN"
    LINE = "LINE"
    PIE = "PIE"
    AREA = "AREA"
    SCATTER = "SCATTER"
    HISTOGRAM = "HISTOGRAM"


class ChartSeriesSpec(BaseModel):
    """Data series specification for chart rendering."""

    name: str = Field(..., description="Series identifier / metric label")
    values: List[Optional[Union[float, int]]] = Field(default_factory=list, description="Ordered numeric values")
    color: Optional[str] = Field(None, description="Optional hex or theme color code")


class ChartMetadata(BaseModel):
    """Metadata describing a generated chart artifact and preserving provenance."""

    chart_id: str = Field(..., description="Unique chart identifier")
    chart_type: ChartTypeEnum = Field(..., description="Rendered chart type")
    title: str = Field(..., description="Chart title")
    x_axis_label: Optional[str] = Field(None, description="Label for horizontal axis")
    y_axis_label: Optional[str] = Field(None, description="Label for vertical axis")
    x_categories: List[str] = Field(default_factory=list, description="Categorical or temporal X-axis labels")
    series: List[ChartSeriesSpec] = Field(default_factory=list, description="Data series plotted")
    dataset_id: str = Field(..., description="Source dataset UUID")
    sheet_name: str = Field(..., description="Source worksheet name")
    table_id: str = Field(..., description="Source table ID")
    source_range: str = Field(..., description="Source cell range lineage")
    rows_included: int = Field(0, description="Rows included in analytical result")
    rows_excluded: int = Field(0, description="Rows excluded by filters")
    generated_at: str = Field(..., description="ISO timestamp of chart generation")
    warnings: List[str] = Field(default_factory=list, description="Any rendering notices or presentation constraints")


class ChartRecommendation(BaseModel):
    """Deterministic recommendation of compatible chart types based on result shape and types."""

    preferred_type: Optional[ChartTypeEnum] = Field(None, description="Highest-affinity recommended chart type")
    compatible_types: List[ChartTypeEnum] = Field(default_factory=list, description="All structurally valid chart types")
    reason: str = Field(..., description="Deterministic structural justification for recommendation")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="Confidence in recommendation")


class VisualizationRequest(BaseModel):
    """Request envelope for generating a chart from an existing AnalyticalResult."""

    dataset_id: str = Field(..., description="Target dataset UUID")
    analytical_result: AnalyticalResult = Field(..., description="Verified AnalyticalResult payload")
    chart_type: Optional[ChartTypeEnum] = Field(None, description="Explicit chart type requested (defaults to recommended)")
    title: Optional[str] = Field(None, description="User-supplied title override")
    x_column: Optional[str] = Field(None, description="Explicit X-axis column override")
    y_column: Optional[str] = Field(None, description="Explicit Y-axis metric column override")
    include_base64: bool = Field(False, description="Optionally include base64-encoded image string")


class InstructionVisualizationRequest(BaseModel):
    """Convenience request envelope to analyze and visualize in a single step."""

    instruction: AnalyticalInstruction = Field(..., description="Analytical instruction to execute")
    chart_type: Optional[ChartTypeEnum] = Field(None, description="Explicit chart type requested")
    title: Optional[str] = Field(None, description="User-supplied title override")
    include_base64: bool = Field(False, description="Optionally include base64-encoded image string")


class VisualizationResponse(BaseModel):
    """Complete visualization payload returned to API consumers."""

    chart_metadata: ChartMetadata = Field(..., description="Structured chart metadata and lineage")
    image_url: str = Field(..., description="Relative API URL to retrieve the rendered PNG artifact")
    image_base64: Optional[str] = Field(None, description="Optional Base64-encoded PNG image payload")


class SmartChartItem(BaseModel):
    """A single deterministic smart-generated chart with lineage and explainability."""

    chart_id: str = Field(..., description="Unique chart identifier")
    title: str = Field(..., description="Descriptive chart title")
    chart_type: ChartTypeEnum = Field(..., description="Rendered chart type")
    dimension_column: Optional[str] = Field(None, description="Primary grouping or X-axis dimension")
    metric_column: Optional[str] = Field(None, description="Primary quantitative measure")
    analytical_intent: str = Field(..., description="Analytical purpose of the visualization")
    why_this_chart: str = Field(..., description="Deterministic explanation of why this chart was selected")
    rank_score: float = Field(..., description="Deterministic ranking score")
    instruction: AnalyticalInstruction = Field(..., description="Compiled instruction used to produce this chart")
    visualization: VisualizationResponse = Field(..., description="Rendered chart response and image URL")


class SmartGenerateRequest(BaseModel):
    """Request payload for smart chart generation."""

    sheet_name: Optional[str] = Field(None, description="Target worksheet name (defaults to active/first sheet)")
    table_id: Optional[str] = Field(None, description="Target table ID (defaults to active/first table)")
    max_charts: int = Field(5, ge=1, le=5, description="Maximum number of meaningful charts to return")


class SmartGenerateResponse(BaseModel):
    """Response containing the ranked set of smart-generated charts."""

    dataset_id: str = Field(..., description="Target dataset UUID")
    sheet_name: str = Field(..., description="Target worksheet name")
    table_id: str = Field(..., description="Target table ID")
    total_candidates_evaluated: int = Field(0, description="Total candidate charts analyzed before filtering")
    selected_charts_count: int = Field(0, description="Number of charts generated and returned")
    charts: List[SmartChartItem] = Field(default_factory=list, description="Ranked meaningful visualizations")
    empty_reason: Optional[str] = Field(None, description="Truthful explanation if no charts could be generated")
