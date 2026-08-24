"""Tests for multi-signal table orientation detection."""

from pathlib import Path
from app.engine.parser.workbook_inspector import WorkbookInspector
from app.engine.profiler.orientation_detector import OrientationDetector
from app.models.schemas import OrientationEnum


def test_vertical_orientation_detection(vertical_table_file: Path):
    _, grids = WorkbookInspector.inspect_file(vertical_table_file)
    grid = grids["Sales"]
    assessment = OrientationDetector.detect_orientation(grid, grid.min_row, grid.min_col, grid.max_row, grid.max_col)
    assert assessment.orientation == OrientationEnum.VERTICAL
    assert assessment.confidence >= 0.65
    assert len(assessment.reasons) > 0


def test_horizontal_orientation_detection(horizontal_table_file: Path):
    _, grids = WorkbookInspector.inspect_file(horizontal_table_file)
    grid = grids["MonthlyFinancials"]
    assessment = OrientationDetector.detect_orientation(grid, grid.min_row, grid.min_col, grid.max_row, grid.max_col)
    assert assessment.orientation == OrientationEnum.HORIZONTAL
    assert assessment.confidence >= 0.65
    assert len(assessment.reasons) > 0


def test_ambiguous_orientation_detection(ambiguous_layout_file: Path):
    _, grids = WorkbookInspector.inspect_file(ambiguous_layout_file)
    grid = grids["Matrix"]
    assessment = OrientationDetector.detect_orientation(grid, grid.min_row, grid.min_col, grid.max_row, grid.max_col)
    assert assessment.orientation == OrientationEnum.AMBIGUOUS
