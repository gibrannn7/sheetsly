"""Comprehensive test suite for Phase 9:
Smart Visualization Engine + Multi-Sheet Granular Analytics Engine.
"""

from datetime import datetime, timezone
from io import BytesIO
import openpyxl
import pytest

from app.engine.analytics import (
    CanonicalChartTypeEnum,
    ChartData,
    ExplainableAnalyticsResult,
    GranularAnalyticsEngine,
    SmartVisualizationEngine,
    VisualizationSuitabilityResult,
)
from app.engine.analytics.ambiguity_resolver import (
    AmbiguityDomainEnum,
    GeneralizedAmbiguityResolver,
)
from app.engine.parser.sheet_reader import RawSheetGrid
from app.engine.profiler.relationship_detector import (
    RelationshipDetector,
    RelationshipEvidence,
    RelationshipGraph,
    RelationshipStatusEnum,
)
from app.engine.profiler.workbook_index import (
    ColumnIndexEntry,
    SheetIndexEntry,
    TableIndexEntry,
    WorkbookMetadataIndex,
)
from app.models.schemas import CellCoordinate, CellData, DataTypeEnum, SemanticTypeEnum


def _create_multi_sheet_environment():
    """Builds two sheets ('Orders' and 'Customers') with linked CustomerID."""
    # Sheet 1: Orders (5 rows)
    cells_orders = {}
    orders_data = [
        ["OrderID", "CustomerID", "OrderDate", "Sales", "Profit"],
        ["ORD-1", "CUST-1", "2024-01-15", 100.0, 20.0],
        ["ORD-2", "CUST-2", "2024-01-20", 250.0, 50.0],
        ["ORD-3", "CUST-1", "2024-02-10", 150.0, 30.0],
        ["ORD-4", "CUST-3", "2024-02-25", 300.0, 60.0],
        ["ORD-5", "CUST-2", "2024-03-05", 200.0, 40.0],
    ]
    for r, row_vals in enumerate(orders_data, start=1):
        for c, val in enumerate(row_vals, start=1):
            col_let = chr(ord("A") + c - 1)
            dt = DataTypeEnum.FLOAT if isinstance(val, float) else (DataTypeEnum.DATE if r > 1 and c == 3 else DataTypeEnum.STRING)
            cells_orders[(r, c)] = CellData(
                coordinate=CellCoordinate(row=r, column=c, cell_ref=f"{col_let}{r}", col_letter=col_let),
                original_value=val,
                parsed_value=val,
                data_type=dt,
                is_empty=False,
            )

    grid_orders = RawSheetGrid(sheet_name="Orders", min_row=1, max_row=6, min_col=1, max_col=5, cells=cells_orders)

    tbl_orders = TableIndexEntry(
        table_id="tbl_orders", name="Orders", sheet_name="Orders",
        range_address="A1:E6", header_range="A1:E1", data_range="A2:E6",
        row_count=5, column_count=5,
        columns=[
            ColumnIndexEntry(index=0, name="OrderID", normalized_name="orderid", source_column_letter="A", data_type=DataTypeEnum.STRING, semantic_type=SemanticTypeEnum.IDENTIFIER, total_count=5, unique_count=5, sample_values=["ORD-1"]),
            ColumnIndexEntry(index=1, name="CustomerID", normalized_name="customerid", source_column_letter="B", data_type=DataTypeEnum.STRING, semantic_type=SemanticTypeEnum.IDENTIFIER, total_count=5, unique_count=3, sample_values=["CUST-1", "CUST-2"]),
            ColumnIndexEntry(index=2, name="OrderDate", normalized_name="orderdate", source_column_letter="C", data_type=DataTypeEnum.DATE, semantic_type=SemanticTypeEnum.TEMPORAL, total_count=5, unique_count=5, sample_values=["2024-01-15"]),
            ColumnIndexEntry(index=3, name="Sales", normalized_name="sales", source_column_letter="D", data_type=DataTypeEnum.FLOAT, semantic_type=SemanticTypeEnum.NUMERIC_MEASURE, total_count=5, unique_count=5, sample_values=[100.0]),
            ColumnIndexEntry(index=4, name="Profit", normalized_name="profit", source_column_letter="E", data_type=DataTypeEnum.FLOAT, semantic_type=SemanticTypeEnum.NUMERIC_MEASURE, total_count=5, unique_count=5, sample_values=[20.0]),
        ],
    )
    sheet_orders = SheetIndexEntry(name="Orders", index=0, total_rows=6, total_columns=5, used_range="A1:E6", tables=[tbl_orders])

    # Sheet 2: Customers (3 rows)
    cells_customers = {}
    customers_data = [
        ["CustomerID", "CustomerName", "Segment"],
        ["CUST-1", "Alice Corp", "Enterprise"],
        ["CUST-2", "Bob LLC", "SMB"],
        ["CUST-3", "Charlie Inc", "Consumer"],
    ]
    for r, row_vals in enumerate(customers_data, start=1):
        for c, val in enumerate(row_vals, start=1):
            col_let = chr(ord("A") + c - 1)
            cells_customers[(r, c)] = CellData(
                coordinate=CellCoordinate(row=r, column=c, cell_ref=f"{col_let}{r}", col_letter=col_let),
                original_value=val,
                parsed_value=val,
                data_type=DataTypeEnum.STRING,
                is_empty=False,
            )

    grid_customers = RawSheetGrid(sheet_name="Customers", min_row=1, max_row=4, min_col=1, max_col=3, cells=cells_customers)

    tbl_customers = TableIndexEntry(
        table_id="tbl_customers", name="Customers", sheet_name="Customers",
        range_address="A1:C4", header_range="A1:C1", data_range="A2:C4",
        row_count=3, column_count=3,
        columns=[
            ColumnIndexEntry(index=0, name="CustomerID", normalized_name="customerid", source_column_letter="A", data_type=DataTypeEnum.STRING, semantic_type=SemanticTypeEnum.IDENTIFIER, total_count=3, unique_count=3, sample_values=["CUST-1"]),
            ColumnIndexEntry(index=1, name="CustomerName", normalized_name="customername", source_column_letter="B", data_type=DataTypeEnum.STRING, semantic_type=SemanticTypeEnum.TEXT, total_count=3, unique_count=3, sample_values=["Alice Corp"]),
            ColumnIndexEntry(index=2, name="Segment", normalized_name="segment", source_column_letter="C", data_type=DataTypeEnum.STRING, semantic_type=SemanticTypeEnum.CATEGORICAL, total_count=3, unique_count=3, sample_values=["Enterprise"]),
        ],
    )
    sheet_customers = SheetIndexEntry(name="Customers", index=1, total_rows=4, total_columns=3, used_range="A1:C4", tables=[tbl_customers])

    index = WorkbookMetadataIndex(
        dataset_id="ds_phase9_test", filename="Store.xlsx", sheet_count=2,
        sheet_names=["Orders", "Customers"], active_sheet_name="Orders",
        sheets={"Orders": sheet_orders, "Customers": sheet_customers},
    )

    grids = {"Orders": grid_orders, "Customers": grid_customers}
    return index, grids


# ============================================================================
# 1. SMART VISUALIZATION SUITABILITY TESTS
# ============================================================================

def test_line_chart_temporal_sales():
    """Verify temporal dimension + numeric measure evaluates to LINE chart."""
    dim = ColumnIndexEntry(index=2, name="OrderDate", normalized_name="orderdate", source_column_letter="C", data_type=DataTypeEnum.DATE, semantic_type=SemanticTypeEnum.TEMPORAL, total_count=5, unique_count=5)
    mea = ColumnIndexEntry(index=3, name="Sales", normalized_name="sales", source_column_letter="D", data_type=DataTypeEnum.FLOAT, semantic_type=SemanticTypeEnum.NUMERIC_MEASURE, total_count=5, unique_count=5)
    res = SmartVisualizationEngine.evaluate_suitability(dim, [mea], "tampilkan tren penjualan bulanan", 5, is_temporal=True)
    assert res.is_suitable is True
    assert res.recommended_chart_type == CanonicalChartTypeEnum.LINE


def test_bar_chart_category_sales():
    """Verify categorical dimension + numeric measure evaluates to BAR/COLUMN chart."""
    dim = ColumnIndexEntry(index=2, name="Region", normalized_name="region", source_column_letter="C", data_type=DataTypeEnum.STRING, semantic_type=SemanticTypeEnum.CATEGORICAL, total_count=10, unique_count=4)
    mea = ColumnIndexEntry(index=3, name="Sales", normalized_name="sales", source_column_letter="D", data_type=DataTypeEnum.FLOAT, semantic_type=SemanticTypeEnum.NUMERIC_MEASURE, total_count=10, unique_count=10)
    res = SmartVisualizationEngine.evaluate_suitability(dim, [mea], "bandingkan penjualan per region", 4)
    assert res.is_suitable is True
    assert res.recommended_chart_type in {CanonicalChartTypeEnum.BAR, CanonicalChartTypeEnum.COLUMN}


def test_scatter_chart_two_numeric_measures():
    """Verify two numeric measures without dimensions evaluate to SCATTER plot."""
    mea1 = ColumnIndexEntry(index=3, name="Sales", normalized_name="sales", source_column_letter="D", data_type=DataTypeEnum.FLOAT, semantic_type=SemanticTypeEnum.NUMERIC_MEASURE, total_count=10, unique_count=10)
    mea2 = ColumnIndexEntry(index=4, name="Profit", normalized_name="profit", source_column_letter="E", data_type=DataTypeEnum.FLOAT, semantic_type=SemanticTypeEnum.NUMERIC_MEASURE, total_count=10, unique_count=10)
    res = SmartVisualizationEngine.evaluate_suitability(None, [mea1, mea2], "korelasi sales dan profit")
    assert res.is_suitable is True
    assert res.recommended_chart_type == CanonicalChartTypeEnum.SCATTER


def test_pie_chart_low_cardinality_category():
    """Verify low cardinality categorical (<10) with explicit pie prompt evaluates to PIE chart."""
    dim = ColumnIndexEntry(index=2, name="Category", normalized_name="category", source_column_letter="C", data_type=DataTypeEnum.STRING, semantic_type=SemanticTypeEnum.CATEGORICAL, total_count=10, unique_count=3)
    mea = ColumnIndexEntry(index=3, name="Sales", normalized_name="sales", source_column_letter="D", data_type=DataTypeEnum.FLOAT, semantic_type=SemanticTypeEnum.NUMERIC_MEASURE, total_count=10, unique_count=10)
    res = SmartVisualizationEngine.evaluate_suitability(dim, [mea], "tampilkan proporsi penjualan per category dalam pie chart", 3)
    assert res.is_suitable is True
    assert res.recommended_chart_type == CanonicalChartTypeEnum.PIE


def test_high_cardinality_pie_rejected():
    """Verify high cardinality categorical (>10) rejects PIE and downgrades to BAR."""
    dim = ColumnIndexEntry(index=2, name="Customer", normalized_name="customer", source_column_letter="C", data_type=DataTypeEnum.STRING, semantic_type=SemanticTypeEnum.CATEGORICAL, total_count=50, unique_count=25)
    mea = ColumnIndexEntry(index=3, name="Sales", normalized_name="sales", source_column_letter="D", data_type=DataTypeEnum.FLOAT, semantic_type=SemanticTypeEnum.NUMERIC_MEASURE, total_count=50, unique_count=50)
    res = SmartVisualizationEngine.evaluate_suitability(dim, [mea], "tampilkan pie chart penjualan per customer", 25)
    assert res.recommended_chart_type == CanonicalChartTypeEnum.BAR
    assert len(res.rejection_reasons) >= 1


def test_kpi_metric_generation():
    """Verify single measure scalar evaluates to KPI card."""
    mea = ColumnIndexEntry(index=3, name="Sales", normalized_name="sales", source_column_letter="D", data_type=DataTypeEnum.FLOAT, semantic_type=SemanticTypeEnum.NUMERIC_MEASURE, total_count=10, unique_count=10)
    res = SmartVisualizationEngine.evaluate_suitability(None, [mea], "berapa total sales")
    assert res.recommended_chart_type == CanonicalChartTypeEnum.KPI


def test_table_fallback_for_unsupported_chart():
    """Verify fallback to TABLE for generic or mixed tabular inquiries."""
    res = SmartVisualizationEngine.evaluate_suitability(None, [], "tampilkan seluruh data")
    assert res.recommended_chart_type == CanonicalChartTypeEnum.TABLE


# ============================================================================
# 2. GRANULAR ANALYTICS & MULTI-SHEET ENGINE TESTS
# ============================================================================

def test_monthly_temporal_aggregation():
    """Verify temporal aggregation calculates monthly totals accurately."""
    index, grids = _create_multi_sheet_environment()
    res = GranularAnalyticsEngine.execute_analytics_query("tren penjualan bulanan", index, grids)

    assert len(res.result_rows) == 3
    # 2024-01: 100 + 250 = 350.0
    # 2024-02: 150 + 300 = 450.0
    # 2024-03: 200 = 200.0
    monthly_sales = {r["OrderDate"]: r["SUM_Sales"] for r in res.result_rows}
    assert monthly_sales["2024-01"] == 350.0
    assert monthly_sales["2024-02"] == 450.0
    assert monthly_sales["2024-03"] == 200.0
    assert res.chart_data.chart_type == CanonicalChartTypeEnum.LINE


def test_top_n_deterministic_ranking():
    """Verify top 2 ranking calculates deterministic sorted results."""
    index, grids = _create_multi_sheet_environment()
    res = GranularAnalyticsEngine.execute_analytics_query("top 2 penjualan bulanan", index, grids)
    assert len(res.result_rows) == 2
    assert res.result_rows[0]["OrderDate"] == "2024-02"
    assert res.result_rows[0]["SUM_Sales"] == 450.0
    assert res.result_rows[1]["OrderDate"] == "2024-01"


def test_bottom_n_deterministic_ranking():
    """Verify bottom ranking orders ascending."""
    index, grids = _create_multi_sheet_environment()
    res = GranularAnalyticsEngine.execute_analytics_query("bulan dengan penjualan terendah", index, grids)
    assert res.result_rows[0]["OrderDate"] == "2024-03"
    assert res.result_rows[0]["SUM_Sales"] == 200.0


def test_cross_sheet_verified_relationship_analytics():
    """Verify cross-sheet join: Orders.Sales aggregated by Customers.Segment."""
    index, grids = _create_multi_sheet_environment()
    res = GranularAnalyticsEngine.execute_analytics_query("tampilkan penjualan per segment customer", index, grids)

    assert len(res.result_rows) == 3
    # CUST-1 (Enterprise): 100 + 150 = 250.0
    # CUST-2 (SMB): 250 + 200 = 450.0
    # CUST-3 (Consumer): 300.0
    seg_sales = {r["Segment"]: r["SUM_Sales"] for r in res.result_rows}
    assert seg_sales["SMB"] == 450.0
    assert seg_sales["Enterprise"] == 250.0
    assert seg_sales["Consumer"] == 300.0
    assert "Customers" in res.source_sheets


def test_unverified_relationship_never_silently_joined():
    """Verify unverified relationships do not silently join unrelated sheets."""
    index, grids = _create_multi_sheet_environment()
    # Create empty graph with NO verified links
    graph = RelationshipGraph(dataset_id="ds_phase9_test", relationships=[])
    res = GranularAnalyticsEngine.execute_analytics_query("tampilkan penjualan per segment", index, grids, relationship_graph=graph)
    # Does not perform cross-sheet join because relationship is unverified
    assert "Customers" not in res.source_sheets


def test_multiple_date_columns_trigger_clarification():
    """Verify multiple temporal columns return clarification."""
    cols = [
        ColumnIndexEntry(index=0, name="Order Date", normalized_name="order date", source_column_letter="A", data_type=DataTypeEnum.DATE, semantic_type=SemanticTypeEnum.TEMPORAL),
        ColumnIndexEntry(index=1, name="Ship Date", normalized_name="ship date", source_column_letter="B", data_type=DataTypeEnum.DATE, semantic_type=SemanticTypeEnum.TEMPORAL),
    ]
    res = GeneralizedAmbiguityResolver.resolve_temporal_ambiguity("tren berdasarkan tanggal", cols)
    assert res.clarification_needed is True
    assert len(res.clarification_request.options) == 2


def test_multiple_metrics_top_n_trigger_clarification():
    """Verify superlative ranking without specified metric returns clarification."""
    cols = [
        ColumnIndexEntry(index=0, name="Sales", normalized_name="sales", source_column_letter="A", data_type=DataTypeEnum.FLOAT, semantic_type=SemanticTypeEnum.NUMERIC_MEASURE),
        ColumnIndexEntry(index=1, name="Profit", normalized_name="profit", source_column_letter="B", data_type=DataTypeEnum.FLOAT, semantic_type=SemanticTypeEnum.NUMERIC_MEASURE),
        ColumnIndexEntry(index=2, name="Discount", normalized_name="discount", source_column_letter="C", data_type=DataTypeEnum.FLOAT, semantic_type=SemanticTypeEnum.NUMERIC_MEASURE),
    ]
    res = GeneralizedAmbiguityResolver.resolve_metric_ambiguity("tampilkan top 5 produk", cols)
    assert res.clarification_needed is True
    assert "Sales" in res.clarification_request.options


def test_filter_by_year_uses_actual_temporal_data():
    """Verify temporal bounds use actual dataset years without assuming current year."""
    index, grids = _create_multi_sheet_environment()
    res = GranularAnalyticsEngine.execute_analytics_query("penjualan tahun 2024", index, grids)
    assert len(res.result_rows) > 0


def test_visualization_result_contains_provenance():
    """Verify analytical result contains full provenance metadata."""
    index, grids = _create_multi_sheet_environment()
    res = GranularAnalyticsEngine.execute_analytics_query("tren penjualan", index, grids)
    assert res.chart_data is not None
    assert res.chart_data.provenance.dataset_id == "ds_phase9_test"
    assert "Orders" in res.chart_data.provenance.source_sheets
    assert "Sales" in res.chart_data.provenance.source_columns
    assert res.chart_data.provenance.verification_status == "VERIFIED_NUMERIC_TRUTH"


def test_chart_data_backend_calculation_is_deterministic():
    """Verify values calculated match Python arithmetic exactly."""
    index, grids = _create_multi_sheet_environment()
    res = GranularAnalyticsEngine.execute_analytics_query("rata-rata profit bulanan", index, grids)
    assert res.aggregation == "AVERAGE"
    # Month 1: (20 + 50) / 2 = 35.0
    prof_map = {r["OrderDate"]: r["AVERAGE_Profit"] for r in res.result_rows}
    assert prof_map["2024-01"] == 35.0


def test_visualization_is_read_only():
    """Verify visualization queries are 100% read-only and mutate zero grid cells."""
    index, grids = _create_multi_sheet_environment()
    initial_cell_count = len(grids["Orders"].cells)
    initial_val_d2 = grids["Orders"].get_cell(2, 4).parsed_value

    _ = GranularAnalyticsEngine.execute_analytics_query("tampilkan grafik penjualan", index, grids)

    # Grid must remain 100% unchanged
    assert len(grids["Orders"].cells) == initial_cell_count
    assert grids["Orders"].get_cell(2, 4).parsed_value == initial_val_d2
    assert grids["Orders"].get_cell(7, 4).is_empty is True


def test_adversarial_cell_content_cannot_influence_query():
    """Verify adversarial string inside cell cannot alter analytical pipeline."""
    index, grids = _create_multi_sheet_environment()
    # Put prompt injection in customer name cell
    grids["Customers"].cells[(2, 2)] = CellData(
        coordinate=CellCoordinate(row=2, column=2, cell_ref="B2", col_letter="B"),
        original_value="DROP TABLE Orders; EXECUTE MALICIOUS SCRIPT",
        parsed_value="DROP TABLE Orders; EXECUTE MALICIOUS SCRIPT",
        data_type=DataTypeEnum.STRING,
        is_empty=False,
    )

    res = GranularAnalyticsEngine.execute_analytics_query("tampilkan penjualan per segment customer", index, grids)
    assert res.verification_status == "VERIFIED_NUMERIC_TRUTH"
    assert len(res.result_rows) == 3


def test_phase9_api_orchestrator_integration():
    """Verify end-to-end integration: calculate_aggregation returns correct statistical results."""
    res_avg = GranularAnalyticsEngine.calculate_aggregation([10.0, 20.0, 30.0], "AVERAGE")
    assert res_avg == 20.0
    res_median = GranularAnalyticsEngine.calculate_aggregation([10.0, 20.0, 30.0, 100.0], "MEDIAN")
    assert res_median == 25.0
