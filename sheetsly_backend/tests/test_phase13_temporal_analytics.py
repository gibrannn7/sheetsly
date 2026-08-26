"""Unit tests for Phase 13: Temporal Analytics, Robust Date Parsing, and Chronological Grouping."""

import pytest
from app.engine.analytics.granular_analytics import GranularAnalyticsEngine
from app.engine.parser.sheet_reader import RawSheetGrid
from app.engine.profiler.workbook_index import (
    ColumnIndexEntry,
    SheetIndexEntry,
    TableIndexEntry,
    WorkbookMetadataIndex,
)
from app.models.schemas import CellCoordinate, CellData, DataTypeEnum, SemanticTypeEnum


@pytest.fixture
def temporal_workbook():
    """Creates a sample workbook index and grid with diverse date formats across 2015-2018."""
    cells = {
        (1, 1): CellData(coordinate=CellCoordinate(row=1, column=1, cell_ref="A1"), original_value="Order Date", parsed_value="Order Date", data_type=DataTypeEnum.STRING, is_empty=False),
        (1, 2): CellData(coordinate=CellCoordinate(row=1, column=2, cell_ref="B1"), original_value="Sales", parsed_value="Sales", data_type=DataTypeEnum.STRING, is_empty=False),
        
        # Row 2: 18/03/2017 -> 100.0
        (2, 1): CellData(coordinate=CellCoordinate(row=2, column=1, cell_ref="A2"), original_value="18/03/2017", parsed_value="18/03/2017", data_type=DataTypeEnum.DATE, is_empty=False),
        (2, 2): CellData(coordinate=CellCoordinate(row=2, column=2, cell_ref="B2"), original_value=100.0, parsed_value=100.0, data_type=DataTypeEnum.FLOAT, is_empty=False),
        
        # Row 3: 2015-11-05 -> 200.0
        (3, 1): CellData(coordinate=CellCoordinate(row=3, column=1, cell_ref="A3"), original_value="2015-11-05", parsed_value="2015-11-05", data_type=DataTypeEnum.DATE, is_empty=False),
        (3, 2): CellData(coordinate=CellCoordinate(row=3, column=2, cell_ref="B3"), original_value=200.0, parsed_value=200.0, data_type=DataTypeEnum.FLOAT, is_empty=False),
        
        # Row 4: 2018-01-10 -> 300.0
        (4, 1): CellData(coordinate=CellCoordinate(row=4, column=1, cell_ref="A4"), original_value="2018-01-10", parsed_value="2018-01-10", data_type=DataTypeEnum.DATE, is_empty=False),
        (4, 2): CellData(coordinate=CellCoordinate(row=4, column=2, cell_ref="B4"), original_value=300.0, parsed_value=300.0, data_type=DataTypeEnum.FLOAT, is_empty=False),
        
        # Row 5: 15/03/2017 -> 150.0 (same month as row 2)
        (5, 1): CellData(coordinate=CellCoordinate(row=5, column=1, cell_ref="A5"), original_value="15/03/2017", parsed_value="15/03/2017", data_type=DataTypeEnum.DATE, is_empty=False),
        (5, 2): CellData(coordinate=CellCoordinate(row=5, column=2, cell_ref="B5"), original_value=150.0, parsed_value=150.0, data_type=DataTypeEnum.FLOAT, is_empty=False),
        
        # Row 6: 2016-07-20 -> 50.0
        (6, 1): CellData(coordinate=CellCoordinate(row=6, column=1, cell_ref="A6"), original_value="2016-07-20", parsed_value="2016-07-20", data_type=DataTypeEnum.DATE, is_empty=False),
        (6, 2): CellData(coordinate=CellCoordinate(row=6, column=2, cell_ref="B6"), original_value=50.0, parsed_value=50.0, data_type=DataTypeEnum.FLOAT, is_empty=False),
    }
    grid = RawSheetGrid(sheet_name="Orders", min_row=1, max_row=6, min_col=1, max_col=2, cells=cells)
    
    col_date = ColumnIndexEntry(
        index=0, name="Order Date", normalized_name="order date", source_column_letter="A",
        data_type=DataTypeEnum.DATE, semantic_type=SemanticTypeEnum.TEMPORAL,
        temporal_bounds={"min_year": 2015, "max_year": 2018, "latest_year": 2018}
    )
    col_sales = ColumnIndexEntry(
        index=1, name="Sales", normalized_name="sales", source_column_letter="B",
        data_type=DataTypeEnum.FLOAT, semantic_type=SemanticTypeEnum.NUMERIC_MEASURE,
    )
    table = TableIndexEntry(
        table_id="tbl_orders_1", name="Orders Data", sheet_name="Orders",
        range_address="A1:B6", header_range="A1:B1", data_range="A2:B6",
        row_count=5, column_count=2, columns=[col_date, col_sales]
    )
    sheet = SheetIndexEntry(name="Orders", index=0, total_rows=6, total_columns=2, used_range="A1:B6", tables=[table])
    idx = WorkbookMetadataIndex(
        dataset_id="ds_temp", filename="temp_test.xlsx", sheet_count=1, sheet_names=["Orders"],
        active_sheet_name="Orders", sheets={"Orders": sheet}
    )
    return idx, grid


def test_annual_temporal_aggregation(temporal_workbook):
    idx, grid = temporal_workbook
    res = GranularAnalyticsEngine.execute_analytics_query("tampilkan tren penjualan tahunan", idx, grid)
    
    assert res.verification_status == "VERIFIED_NUMERIC_TRUTH"
    assert "grouped by Order Date (YEAR)" in res.resolved_intent
    
    # Expected years: 2015, 2016, 2017, 2018 in chronological order
    years = [r["Order Date"] for r in res.result_rows]
    assert years == ["2015", "2016", "2017", "2018"]
    
    # Check sums: 2015=200.0, 2016=50.0, 2017=250.0 (100+150), 2018=300.0
    val_map = {r["Order Date"]: r["SUM_Sales"] for r in res.result_rows}
    assert val_map["2015"] == 200.0
    assert val_map["2016"] == 50.0
    assert val_map["2017"] == 250.0
    assert val_map["2018"] == 300.0
    assert res.chart_data.chart_type in ["LINE", "COLUMN"]


def test_monthly_temporal_aggregation_no_malformed_dates(temporal_workbook):
    idx, grid = temporal_workbook
    res = GranularAnalyticsEngine.execute_analytics_query("tampilkan tren penjualan bulanan", idx, grid)
    
    assert res.verification_status == "VERIFIED_NUMERIC_TRUTH"
    assert "grouped by Order Date (MONTH)" in res.resolved_intent
    
    # Expected months: 2015-11, 2016-07, 2017-03, 2018-01 in chronological order
    months = [r["Order Date"] for r in res.result_rows]
    assert months == ["2015-11", "2016-07", "2017-03", "2018-01"]
    
    # 2017-03 should have combined both 100.0 and 150.0 = 250.0
    val_map = {r["Order Date"]: r["SUM_Sales"] for r in res.result_rows}
    assert val_map["2017-03"] == 250.0
    assert res.chart_data.chart_type == "LINE"


def test_quarterly_temporal_aggregation(temporal_workbook):
    idx, grid = temporal_workbook
    res = GranularAnalyticsEngine.execute_analytics_query("tampilkan tren penjualan kuartalan", idx, grid)
    
    assert res.verification_status == "VERIFIED_NUMERIC_TRUTH"
    quarters = [r["Order Date"] for r in res.result_rows]
    assert quarters == ["2015 Q4", "2016 Q3", "2017 Q1", "2018 Q1"]
    assert res.chart_data.chart_type == "LINE"
