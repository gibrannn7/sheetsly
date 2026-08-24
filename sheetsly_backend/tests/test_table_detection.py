"""Tests for table detection, region classification, and column profiling across structural scenarios."""

from pathlib import Path
from app.engine.parser.workbook_inspector import WorkbookInspector
from app.engine.profiler.table_detector import TableDetector
from app.models.schemas import DataTypeEnum, OrientationEnum


def test_detect_single_vertical_table(vertical_table_file: Path):
    _, grids = WorkbookInspector.inspect_file(vertical_table_file)
    tables = TableDetector.detect_tables_in_sheet(grids["Sales"])

    assert len(tables) == 1
    tbl = tables[0]
    assert tbl.orientation == OrientationEnum.VERTICAL
    assert tbl.column_count == 6
    assert tbl.row_count == 5
    assert tbl.header_row_indices == [1]
    assert [c.name for c in tbl.columns] == ["Transaction_ID", "Product", "Date", "Quantity", "Revenue", "Status"]


def test_detect_title_metadata_table(title_metadata_table_file: Path):
    _, grids = WorkbookInspector.inspect_file(title_metadata_table_file)
    tables = TableDetector.detect_tables_in_sheet(grids["ExecutiveReport"])

    assert len(tables) == 1
    tbl = tables[0]
    # Header was detected at row 4 (skipping title rows 1-2 and blank row 3)
    assert 4 in tbl.header_row_indices
    # Data rows are 5, 6, 7, 8 (excluding footer row 9 and note row 10)
    assert tbl.row_count == 4
    col_names = [c.name for c in tbl.columns]
    assert "Region" in col_names
    assert "Manager" in col_names
    assert "Target_Sales" in col_names


def test_detect_multiple_tables_in_single_sheet(multi_table_file: Path):
    _, grids = WorkbookInspector.inspect_file(multi_table_file)
    tables = TableDetector.detect_tables_in_sheet(grids["Dashboard"])

    # Must detect 2 distinct tables
    assert len(tables) == 2
    tbl1, tbl2 = tables[0], tables[1]

    assert [c.name for c in tbl1.columns] == ["Product", "Category", "Inventory_Count"]
    assert tbl1.row_count == 2

    assert [c.name for c in tbl2.columns] == ["Vendor_Name", "Rating", "Active_Orders"]
    assert tbl2.row_count == 2


def test_detect_multi_row_header(multi_row_header_file: Path):
    _, grids = WorkbookInspector.inspect_file(multi_row_header_file)
    tables = TableDetector.detect_tables_in_sheet(grids["MultiHeader"])

    assert len(tables) == 1
    tbl = tables[0]
    assert len(tbl.header_row_indices) == 2
    assert tbl.row_count == 3
    # Verify merged header disambiguation / combination
    col_names = [c.name for c in tbl.columns]
    assert any("2025 Performance" in name for name in col_names)
    assert any("2026 Performance" in name for name in col_names)


def test_detect_table_with_empty_gaps(empty_gaps_file: Path):
    _, grids = WorkbookInspector.inspect_file(empty_gaps_file)
    tables = TableDetector.detect_tables_in_sheet(grids["Gaps"])

    assert len(tables) >= 1
    tbl = tables[0]
    assert "Score" in [c.name for c in tbl.columns]
