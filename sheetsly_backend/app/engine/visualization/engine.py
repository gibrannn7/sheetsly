"""Central Visualization Engine orchestrating recommendation, validation, and rendering."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Tuple
import uuid

from app.storage.file_manager import file_manager
from .chart_model import (
    ChartMetadata,
    ChartRecommendation,
    ChartTypeEnum,
    VisualizationRequest,
    VisualizationResponse,
)
from .chart_selector import ChartSelector, IncompatibleChartError
from .renderer import ChartRenderer


class VisualizationEngine:
    """Authoritative deterministic visualization engine producing chart artifacts from AnalyticalResults."""

    def __init__(self):
        # In-memory session cache for active charts: chart_id -> (ChartMetadata, Path)
        self._chart_cache: Dict[str, Tuple[ChartMetadata, Path]] = {}

    def recommend(self, analytical_result) -> ChartRecommendation:
        """Deterministically recommends suitable chart types."""
        return ChartSelector.recommend(analytical_result)

    def render(self, request: VisualizationRequest) -> VisualizationResponse:
        """
        Renders a chart from a verified AnalyticalResult.
        Validates structural compatibility and produces a static PNG artifact and metadata.
        """
        result = request.analytical_result
        dataset_id = request.dataset_id

        # Determine chart type (explicit or recommended)
        if request.chart_type is not None:
            chart_type = request.chart_type
        else:
            rec = ChartSelector.recommend(result)
            if rec.preferred_type is None:
                raise IncompatibleChartError(
                    f"Unable to automatically recommend a chart: {rec.reason}",
                    details={"recommendation_reason": rec.reason},
                )
            chart_type = rec.preferred_type

        # Validate compatibility and extract data
        x_categories, series_list, x_label, y_label, title, warnings = (
            ChartSelector.validate_and_extract_plot_data(
                result=result,
                requested_type=chart_type,
                x_col_override=request.x_column,
                y_col_override=request.y_column,
                title_override=request.title,
            )
        )

        chart_id = f"chart_{uuid.uuid4().hex[:12]}"
        dataset_dir = file_manager.get_dataset_dir(dataset_id)
        output_file = dataset_dir / "charts" / f"{chart_id}.png"

        # Render to file
        base64_str = ChartRenderer.render_to_file(
            chart_type=chart_type,
            title=title,
            x_categories=x_categories,
            series=series_list,
            x_axis_label=x_label,
            y_axis_label=y_label,
            output_file_path=output_file,
            include_base64=request.include_base64,
        )

        now_iso = datetime.now(timezone.utc).isoformat()
        metadata = ChartMetadata(
            chart_id=chart_id,
            chart_type=chart_type,
            title=title,
            x_axis_label=x_label,
            y_axis_label=y_label,
            x_categories=x_categories,
            series=series_list,
            dataset_id=dataset_id,
            sheet_name=result.lineage.sheet_name,
            table_id=result.lineage.table_id,
            source_range=result.lineage.source_range,
            rows_included=result.lineage.rows_included,
            rows_excluded=result.lineage.rows_excluded,
            generated_at=now_iso,
            warnings=warnings,
        )

        self._chart_cache[chart_id] = (metadata, output_file)

        return VisualizationResponse(
            chart_metadata=metadata,
            image_url=f"/api/v1/datasets/{dataset_id}/charts/{chart_id}/image",
            image_base64=base64_str,
        )

    def get_chart_file(self, chart_id: str, dataset_id: Optional[str] = None) -> Optional[Path]:
        """Retrieves path to generated chart PNG artifact, checking in-memory cache then dataset storage."""
        if chart_id in self._chart_cache:
            _, path = self._chart_cache[chart_id]
            if path.exists():
                return path

        # Fallback to filesystem lookup if dataset_id provided or scanning cache
        if dataset_id:
            try:
                dataset_dir = file_manager.get_dataset_dir(dataset_id)
                candidate = dataset_dir / "charts" / f"{chart_id}.png"
                if candidate.exists():
                    return candidate
            except Exception:
                pass
        return None

    def get_chart_metadata(self, chart_id: str) -> Optional[ChartMetadata]:
        """Retrieves cached metadata for a chart."""
        if chart_id in self._chart_cache:
            meta, _ = self._chart_cache[chart_id]
            return meta
        return None


visualization_engine = VisualizationEngine()
