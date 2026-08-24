"""Comprehensive unit tests for deterministic visualization engine and chart rendering."""

from pathlib import Path
import pytest

from app.engine.analytics import (
    AggregationOpEnum,
    AggregationSpec,
    AnalyticalEngine,
    AnalyticalInstruction,
    OperationEnum,
)
from app.engine.pipeline import ingestion_pipeline
from app.engine.visualization import (
    ChartSelector,
    ChartTypeEnum,
    IncompatibleChartError,
    VisualizationEngine,
    VisualizationRequest,
)


def test_all_chart_types_rendering(vertical_table_file: Path, horizontal_table_file: Path):
    # Process vertical sales table
    ingestion_pipeline.process_workbook(
        dataset_id="test-viz-dataset",
        file_path=vertical_table_file,
        original_filename=vertical_table_file.name,
        file_size_bytes=1024,
    )
    # Process horizontal financials table
    ingestion_pipeline.process_workbook(
        dataset_id="test-viz-horiz",
        file_path=horizontal_table_file,
        original_filename=horizontal_table_file.name,
        file_size_bytes=1024,
    )

    analytics = AnalyticalEngine()
    viz_engine = VisualizationEngine()

    # -------------------------------------------------------------
    # 1. BAR CHART: GROUP_BY(Status) -> SUM(Revenue)
    # -------------------------------------------------------------
    inst_bar = AnalyticalInstruction(
        operation=OperationEnum.GROUP_BY,
        dataset_id="test-viz-dataset",
        sheet_name="Sales",
        group_by_columns=["Status"],
        aggregations=[AggregationSpec(column="Revenue", operation=AggregationOpEnum.SUM, alias="Total_Revenue")],
    )
    res_bar = analytics.execute(inst_bar)
    req_bar = VisualizationRequest(
        dataset_id="test-viz-dataset",
        analytical_result=res_bar,
        chart_type=ChartTypeEnum.BAR,
        include_base64=True,
    )
    resp_bar = viz_engine.render(req_bar)
    assert resp_bar.chart_metadata.chart_type == ChartTypeEnum.BAR
    assert resp_bar.chart_metadata.x_axis_label == "Status"
    assert resp_bar.chart_metadata.y_axis_label == "Total_Revenue"
    assert resp_bar.chart_metadata.x_categories == ["Completed", "Pending"]
    assert resp_bar.chart_metadata.series[0].values == [3460.0, 175.0]
    assert resp_bar.image_base64 is not None
    assert viz_engine.get_chart_file(resp_bar.chart_metadata.chart_id) is not None

    # -------------------------------------------------------------
    # 2. PIE CHART: GROUP_BY(Product) -> SUM(Revenue) (5 items <= 10, all >= 0)
    # -------------------------------------------------------------
    inst_pie = AnalyticalInstruction(
        operation=OperationEnum.GROUP_BY,
        dataset_id="test-viz-dataset",
        sheet_name="Sales",
        group_by_columns=["Product"],
        aggregations=[AggregationSpec(column="Revenue", operation=AggregationOpEnum.SUM, alias="Revenue_Sum")],
    )
    res_pie = analytics.execute(inst_pie)
    req_pie = VisualizationRequest(
        dataset_id="test-viz-dataset",
        analytical_result=res_pie,
        chart_type=ChartTypeEnum.PIE,
    )
    resp_pie = viz_engine.render(req_pie)
    assert resp_pie.chart_metadata.chart_type == ChartTypeEnum.PIE
    assert len(resp_pie.chart_metadata.x_categories) == 5
    assert sum(resp_pie.chart_metadata.series[0].values) == 3635.0

    # -------------------------------------------------------------
    # 3. LINE CHART: Temporal or ordered multi-point
    # -------------------------------------------------------------
    req_line = VisualizationRequest(
        dataset_id="test-viz-dataset",
        analytical_result=res_pie,
        chart_type=ChartTypeEnum.LINE,
    )
    resp_line = viz_engine.render(req_line)
    assert resp_line.chart_metadata.chart_type == ChartTypeEnum.LINE
    assert len(resp_line.chart_metadata.series[0].values) == 5

    # -------------------------------------------------------------
    # 4. AREA CHART: Cumulative / Area series
    # -------------------------------------------------------------
    req_area = VisualizationRequest(
        dataset_id="test-viz-dataset",
        analytical_result=res_pie,
        chart_type=ChartTypeEnum.AREA,
    )
    resp_area = viz_engine.render(req_area)
    assert resp_area.chart_metadata.chart_type == ChartTypeEnum.AREA

    # -------------------------------------------------------------
    # 5. SCATTER PLOT: 2 Numeric Variables (Quantity vs Revenue)
    # -------------------------------------------------------------
    inst_scatter = AnalyticalInstruction(
        operation=OperationEnum.FILTER,
        dataset_id="test-viz-dataset",
        sheet_name="Sales",
    )
    res_scatter = analytics.execute(inst_scatter)
    req_scatter = VisualizationRequest(
        dataset_id="test-viz-dataset",
        analytical_result=res_scatter,
        chart_type=ChartTypeEnum.SCATTER,
        x_column="Quantity",
        y_column="Revenue",
    )
    resp_scatter = viz_engine.render(req_scatter)
    assert resp_scatter.chart_metadata.chart_type == ChartTypeEnum.SCATTER
    assert resp_scatter.chart_metadata.x_axis_label == "Quantity"
    assert resp_scatter.chart_metadata.y_axis_label == "Revenue"

    # -------------------------------------------------------------
    # 6. HISTOGRAM: Distribution of Revenue
    # -------------------------------------------------------------
    req_hist = VisualizationRequest(
        dataset_id="test-viz-dataset",
        analytical_result=res_scatter,
        chart_type=ChartTypeEnum.HISTOGRAM,
        y_column="Revenue",
    )
    resp_hist = viz_engine.render(req_hist)
    assert resp_hist.chart_metadata.chart_type == ChartTypeEnum.HISTOGRAM
    assert resp_hist.chart_metadata.x_axis_label == "Revenue"


def test_incompatible_chart_rejections(vertical_table_file: Path):
    ingestion_pipeline.process_workbook(
        dataset_id="test-viz-reject",
        file_path=vertical_table_file,
        original_filename=vertical_table_file.name,
        file_size_bytes=1024,
    )
    analytics = AnalyticalEngine()
    viz_engine = VisualizationEngine()

    # Case A: SCATTER requested on 1 categorical + 1 numeric table (requires 2 continuous numeric variables)
    inst_group = AnalyticalInstruction(
        operation=OperationEnum.GROUP_BY,
        dataset_id="test-viz-reject",
        sheet_name="Sales",
        group_by_columns=["Status"],
        aggregations=[AggregationSpec(column="Revenue", operation=AggregationOpEnum.SUM)],
    )
    res_group = analytics.execute(inst_group)

    req_invalid_scatter = VisualizationRequest(
        dataset_id="test-viz-reject",
        analytical_result=res_group,
        chart_type=ChartTypeEnum.SCATTER,
    )
    with pytest.raises(IncompatibleChartError) as exc_info:
        viz_engine.render(req_invalid_scatter)
    assert "SCATTER chart requires 2 continuous numeric columns" in str(exc_info.value)


def test_deterministic_chart_recommendation(vertical_table_file: Path):
    ingestion_pipeline.process_workbook(
        dataset_id="test-viz-rec",
        file_path=vertical_table_file,
        original_filename=vertical_table_file.name,
        file_size_bytes=1024,
    )
    analytics = AnalyticalEngine()

    # 1. Categorical + Numeric -> Recommend BAR
    inst_group = AnalyticalInstruction(
        operation=OperationEnum.GROUP_BY,
        dataset_id="test-viz-rec",
        sheet_name="Sales",
        group_by_columns=["Product"],
        aggregations=[AggregationSpec(column="Revenue", operation=AggregationOpEnum.SUM)],
    )
    res_group = analytics.execute(inst_group)
    rec = ChartSelector.recommend(res_group)
    assert rec.preferred_type == ChartTypeEnum.BAR
    assert ChartTypeEnum.PIE in rec.compatible_types
    assert ChartTypeEnum.LINE in rec.compatible_types
    assert "Categorical dimension 'Product'" in rec.reason
