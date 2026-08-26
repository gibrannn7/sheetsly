"""Deterministic Smart Visualization Engine enforcing evidence-based suitability and provenance."""

from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from app.engine.profiler.workbook_index import (
    ColumnIndexEntry,
    SheetIndexEntry,
    TableIndexEntry,
    WorkbookMetadataIndex,
)
from app.models.schemas import DataTypeEnum, SemanticTypeEnum


class CanonicalChartTypeEnum(str, Enum):
    """Canonical chart types supported by the Smart Visualization Engine."""

    LINE = "LINE"
    BAR = "BAR"
    COLUMN = "COLUMN"
    AREA = "AREA"
    SCATTER = "SCATTER"
    PIE = "PIE"
    DONUT = "DONUT"
    TABLE = "TABLE"
    KPI = "KPI"


class VisualizationSuitabilityResult(BaseModel):
    """Suitability assessment outcome for visualization."""

    is_suitable: bool
    recommended_chart_type: CanonicalChartTypeEnum
    confidence: float = Field(..., ge=0.0, le=1.0)
    reason: str
    rejection_reasons: List[str] = Field(default_factory=list)


class ChartProvenance(BaseModel):
    """Factual metadata detailing the exact source origin of rendered chart data."""

    dataset_id: str
    source_sheets: List[str]
    source_columns: List[str]
    source_ranges: List[str] = Field(default_factory=list, description="e.g. ['Orders!D2:D9801', 'Customers!C2:C500']")
    filters_applied: List[str] = Field(default_factory=list)
    aggregation: str
    dimension: Optional[str] = None
    measure: str
    verification_status: str = "VERIFIED_NUMERIC_TRUTH"


class ChartDataset(BaseModel):
    """Dataset series for chart rendering."""

    name: str
    values: List[Any]
    color: Optional[str] = None


class ChartData(BaseModel):
    """Canonical Chart Data contract for frontend presentation."""

    chart_type: CanonicalChartTypeEnum
    title: str
    labels: List[str]
    datasets: List[ChartDataset]
    provenance: ChartProvenance
    summary_metric: Optional[str] = None
    summary_value: Optional[Any] = None


class VisualizationPlan(BaseModel):
    """Structured plan for generating evidence-backed chart visualizations."""

    chart_type: CanonicalChartTypeEnum
    dataset_id: str
    sheet_name: str
    table_id: Optional[str] = None
    dimension_columns: List[str] = Field(default_factory=list)
    measure_columns: List[str] = Field(default_factory=list)
    aggregation: str = "SUM"
    temporal_granularity: Optional[str] = None
    filters: List[Dict[str, Any]] = Field(default_factory=list)
    sort_order: Optional[str] = None
    limit: Optional[int] = None
    confidence: float = 1.0
    reason: str
    source_ranges: List[str] = Field(default_factory=list)


class SmartVisualizationEngine:
    """Evaluates suitability and synthesizes deterministic, evidence-grounded visualizations."""

    @classmethod
    def evaluate_suitability(
        cls,
        dimension_col: Optional[ColumnIndexEntry],
        measure_cols: List[ColumnIndexEntry],
        query: str,
        dimension_cardinality: int = 0,
        is_temporal: bool = False,
    ) -> VisualizationSuitabilityResult:
        """
        Determines the optimal canonical chart type based on strict metadata evidence.
        """
        q_norm = query.strip().lower()

        # 1. Scalar KPI suitability
        if not dimension_col and len(measure_cols) == 1:
            return VisualizationSuitabilityResult(
                is_suitable=True,
                recommended_chart_type=CanonicalChartTypeEnum.KPI,
                confidence=1.0,
                reason=f"Single numeric measure '{measure_cols[0].name}' without grouping is best represented as a KPI metric card.",
            )

        # 2. Scatter plot suitability
        if len(measure_cols) >= 2 and not dimension_col:
            # Check neither measure is an identifier
            if all(m.semantic_type != SemanticTypeEnum.IDENTIFIER for m in measure_cols[:2]):
                return VisualizationSuitabilityResult(
                    is_suitable=True,
                    recommended_chart_type=CanonicalChartTypeEnum.SCATTER,
                    confidence=0.95,
                    reason=f"Two numeric measures ('{measure_cols[0].name}', '{measure_cols[1].name}') are best visualized as a SCATTER plot.",
                )

        # 3. Temporal Line / Area chart suitability
        if is_temporal or (dimension_col and dimension_col.semantic_type == SemanticTypeEnum.TEMPORAL):
            chart_t = CanonicalChartTypeEnum.AREA if "area" in q_norm else CanonicalChartTypeEnum.LINE
            return VisualizationSuitabilityResult(
                is_suitable=True,
                recommended_chart_type=chart_t,
                confidence=1.0,
                reason=f"Temporal dimension '{dimension_col.name if dimension_col else 'Time'}' with measure '{measure_cols[0].name if measure_cols else 'Value'}' is best visualized as a {chart_t.value} chart.",
            )

        # 4. Categorical Pie / Donut chart suitability
        if dimension_col and dimension_col.semantic_type in {SemanticTypeEnum.CATEGORICAL, SemanticTypeEnum.TEXT} and len(measure_cols) == 1:
            if "pie" in q_norm or "donut" in q_norm or "proporsi" in q_norm or "komposisi" in q_norm:
                if 2 <= dimension_cardinality <= 10:
                    chart_t = CanonicalChartTypeEnum.DONUT if "donut" in q_norm else CanonicalChartTypeEnum.PIE
                    return VisualizationSuitabilityResult(
                        is_suitable=True,
                        recommended_chart_type=chart_t,
                        confidence=0.95,
                        reason=f"Categorical dimension '{dimension_col.name}' has suitable low cardinality ({dimension_cardinality}) for a {chart_t.value} chart.",
                    )
                else:
                    # High cardinality rejection for Pie/Donut -> Downgrade to BAR
                    return VisualizationSuitabilityResult(
                        is_suitable=True,
                        recommended_chart_type=CanonicalChartTypeEnum.BAR,
                        confidence=0.9,
                        reason=f"Category '{dimension_col.name}' has high cardinality ({dimension_cardinality} > 10). A BAR chart is recommended over PIE to avoid clutter.",
                        rejection_reasons=[f"Pie chart unsuitable for high cardinality ({dimension_cardinality} items)."],
                    )

            # Standard Categorical Bar/Column
            chart_t = CanonicalChartTypeEnum.COLUMN if ("column" in q_norm or dimension_cardinality <= 6) else CanonicalChartTypeEnum.BAR
            return VisualizationSuitabilityResult(
                is_suitable=True,
                recommended_chart_type=chart_t,
                confidence=0.95,
                reason=f"Categorical dimension '{dimension_col.name}' with numeric measure '{measure_cols[0].name}' is best visualized as a {chart_t.value} chart.",
            )

        # Fallback to TABLE
        return VisualizationSuitabilityResult(
            is_suitable=True,
            recommended_chart_type=CanonicalChartTypeEnum.TABLE,
            confidence=0.8,
            reason="Tabular presentation is the most accurate format for this dataset structure.",
        )
