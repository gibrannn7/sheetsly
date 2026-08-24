"""Tests for workbook inspection and raw sheet coordinate reading."""

from pathlib import Path
from app.engine.parser.workbook_inspector import WorkbookInspector


def test_inspect_vertical_workbook(vertical_table_file: Path):
    sheet_names, grids = WorkbookInspector.inspect_file(vertical_table_file)
    assert sheet_names == ["Sales"]
    grid = grids["Sales"]

    assert grid.min_row == 1
    assert grid.max_row == 6
    assert grid.min_col == 1
    assert grid.max_col == 6
    assert grid.total_rows == 6
    assert grid.total_cols == 6
    assert grid.used_range == "A1:F6"

    # Verify cell coordinate preservation
    cell_a1 = grid.get_cell(1, 1)
    assert cell_a1.coordinate.cell_ref == "A1"
    assert cell_a1.original_value == "Transaction_ID"

    cell_e2 = grid.get_cell(2, 5)
    assert cell_e2.coordinate.cell_ref == "E2"
    assert cell_e2.original_value == "$2,400.00"


def test_inspect_title_metadata_workbook(title_metadata_table_file: Path):
    sheet_names, grids = WorkbookInspector.inspect_file(title_metadata_table_file)
    assert sheet_names == ["ExecutiveReport"]
    grid = grids["ExecutiveReport"]

    assert len(grid.merged_ranges) > 0
    assert "A1:E1" in grid.merged_ranges

    # Verify formula detection in footer
    cell_c9 = grid.get_cell(9, 3)
    assert cell_c9.formula is not None
    assert "SUM" in cell_c9.formula
