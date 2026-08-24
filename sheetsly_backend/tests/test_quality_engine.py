"""Tests for deterministic data quality evaluation and hygiene scoring."""

from pathlib import Path
from app.engine.parser.workbook_inspector import WorkbookInspector
from app.engine.profiler.quality_engine import DataQualityEngine
from app.engine.profiler.table_detector import TableDetector
from app.models.schemas import IssueSeverityEnum


def test_clean_table_quality_score(vertical_table_file: Path):
    _, grids = WorkbookInspector.inspect_file(vertical_table_file)
    grid = grids["Sales"]
    tables = TableDetector.detect_tables_in_sheet(grid)
    report = DataQualityEngine.evaluate_sheet_quality(grid, tables)

    assert report.overall_score == 100.0
    assert report.total_issues == 0


def test_mixed_types_detection(mixed_values_file: Path):
    _, grids = WorkbookInspector.inspect_file(mixed_values_file)
    grid = grids["Inventory"]
    tables = TableDetector.detect_tables_in_sheet(grid)
    report = DataQualityEngine.evaluate_sheet_quality(grid, tables)

    assert report.overall_score < 100.0
    issue_types = [i.issue_type for i in report.issues]
    assert "MIXED_DATA_TYPES" in issue_types

    mixed_issue = next(i for i in report.issues if i.issue_type == "MIXED_DATA_TYPES")
    assert mixed_issue.column_name == "Quantity"
    assert mixed_issue.affected_cells_count == 2
    assert "C3" in mixed_issue.sample_locations
    assert "C5" in mixed_issue.sample_locations


def test_missing_values_detection(missing_values_file: Path):
    _, grids = WorkbookInspector.inspect_file(missing_values_file)
    grid = grids["Customers"]
    tables = TableDetector.detect_tables_in_sheet(grid)
    report = DataQualityEngine.evaluate_sheet_quality(grid, tables)

    assert report.overall_score < 100.0
    issue_types = [i.issue_type for i in report.issues]
    assert "MISSING_VALUES" in issue_types


def test_duplicate_detection(duplicate_rows_file: Path):
    _, grids = WorkbookInspector.inspect_file(duplicate_rows_file)
    grid = grids["Orders"]
    tables = TableDetector.detect_tables_in_sheet(grid)
    report = DataQualityEngine.evaluate_sheet_quality(grid, tables)

    assert report.overall_score < 100.0
    issue_types = [i.issue_type for i in report.issues]
    assert "DUPLICATE_ROWS" in issue_types or "DUPLICATE_IDENTIFIERS" in issue_types
