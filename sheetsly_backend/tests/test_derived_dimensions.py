"""Regression and integration tests for derived analytical dimensions, temporal grouping, and deterministic seasonality."""

from unittest.mock import AsyncMock, patch
import pandas as pd
import pytest

from app.engine.ai.orchestrator import AIOrchestrator
from app.engine.ai.planner import QwenQueryPlanner
from app.engine.analytics.engine import AnalyticalEngine
from app.engine.analytics.expressions import DateDimensionOpEnum, DimensionEvaluator, DimensionParser
from app.engine.analytics.filters import DeterministicFilterEngine
from app.engine.analytics.instruction_model import (
    AggregationOpEnum,
    AggregationSpec,
    AnalyticalInstruction,
    FilterCondition,
    FilterOperatorEnum,
    OperationEnum,
    SortSpec,
)
from app.engine.analytics.temporal_evidence import TemporalEvidenceCalculator
from app.engine.analytics.validator import AnalyticalValidationError, InstructionValidator
from app.engine.parser.sheet_reader import RawSheetGrid
from app.engine.pipeline import ingestion_pipeline
from app.engine.visualization.chart_selector import ChartSelector
from app.models.schemas import (
    CellCoordinate,
    CellData,
    ColumnMetadata,
    DataTypeEnum,
    SemanticTypeEnum,
    SheetMetadata,
    TableRegion,
    WorkbookOverview,
)


def _make_sample_table(col_names_and_types, sheet_name="Sheet1"):
    columns = []
    for idx, (name, dtype, stype) in enumerate(col_names_and_types):
        letter = chr(ord("A") + idx)
        columns.append(
            ColumnMetadata(
                index=idx,
                name=name,
                source_column_letter=letter,
                data_type=dtype,
                semantic_type=stype,
                type_confidence=1.0,
                null_count=0,
                unique_count=10,
                sample_values=["sample"],
            )
        )
    return TableRegion(
        table_id="table_1",
        sheet_name=sheet_name,
        name="Sales_Data",
        range_address=f"A1:{chr(ord('A') + len(col_names_and_types) - 1)}100",
        header_range=f"A1:{chr(ord('A') + len(col_names_and_types) - 1)}1",
        data_range=f"A2:{chr(ord('A') + len(col_names_and_types) - 1)}100",
        row_count=99,
        column_count=len(col_names_and_types),
        columns=columns,
    )


# ----------------------------------------------------------------------
# 1. DimensionParser Tests
# ----------------------------------------------------------------------

def test_dimension_parser_allowlist_success():
    cases = [
        ("YEAR(Order Date)", "Order Date", DateDimensionOpEnum.YEAR),
        ("QUARTER(Order Date)", "Order Date", DateDimensionOpEnum.QUARTER),
        ("MONTH(Order Date)", "Order Date", DateDimensionOpEnum.MONTH),
        ("MONTH_NAME(Order Date)", "Order Date", DateDimensionOpEnum.MONTH_NAME),
        ("YEAR_MONTH(Order Date)", "Order Date", DateDimensionOpEnum.YEAR_MONTH),
        ("YEAR-MONTH(Order Date)", "Order Date", DateDimensionOpEnum.YEAR_MONTH),
        ("WEEK(Order Date)", "Order Date", DateDimensionOpEnum.WEEK),
        ("DAY(Order Date)", "Order Date", DateDimensionOpEnum.DAY),
        ("DAY_OF_WEEK(Order Date)", "Order Date", DateDimensionOpEnum.DAY_OF_WEEK),
        ("year('Transaction Date')", "Transaction Date", DateDimensionOpEnum.YEAR),
        ('month_name("Ship Date")', "Ship Date", DateDimensionOpEnum.MONTH_NAME),
    ]
    for raw_expr, expected_col, expected_op in cases:
        parsed = DimensionParser.parse(raw_expr)
        assert parsed is not None, f"Failed to parse {raw_expr}"
        assert parsed.source_column == expected_col
        assert parsed.operation == expected_op


def test_dimension_parser_rejects_unsafe_and_unapproved():
    invalid_cases = [
        "FOO(Order Date)",
        "RANDOM(Order Date)",
        "PYTHON(Order Date)",
        "EVAL(Order Date)",
        "EXECUTE(Order Date)",
        "__import__('os')",
        "Order Date + 10",
        "YEAR()",
        "YEAR(Order Date; DROP TABLE)",
    ]
    for expr in invalid_cases:
        assert DimensionParser.parse(expr) is None, f"Should reject invalid syntax: {expr}"


# ----------------------------------------------------------------------
# 2. InstructionValidator Tests
# ----------------------------------------------------------------------

def test_validator_accepts_valid_derived_date_dimensions():
    table = _make_sample_table([
        ("Order Date", DataTypeEnum.DATE, SemanticTypeEnum.TEMPORAL),
        ("Sales", DataTypeEnum.FLOAT, SemanticTypeEnum.NUMERIC_MEASURE),
        ("Category", DataTypeEnum.STRING, SemanticTypeEnum.CATEGORICAL),
    ])

    inst = AnalyticalInstruction(
        operation=OperationEnum.GROUP_BY,
        dataset_id="ds1",
        sheet_name="Sheet1",
        table_id="table_1",
        group_by_columns=["YEAR(Order Date)", "MONTH(Order Date)"],
        aggregations=[
            AggregationSpec(column="Sales", operation=AggregationOpEnum.SUM, alias="Total_Sales")
        ],
    )
    # Should not raise
    InstructionValidator.validate(inst, table)


def test_validator_accepts_derived_dimensions_in_filter():
    table = _make_sample_table([
        ("Order Date", DataTypeEnum.DATE, SemanticTypeEnum.TEMPORAL),
        ("Sales", DataTypeEnum.FLOAT, SemanticTypeEnum.NUMERIC_MEASURE),
        ("Category", DataTypeEnum.STRING, SemanticTypeEnum.CATEGORICAL),
    ])

    # Test YEAR in BETWEEN filter
    inst1 = AnalyticalInstruction(
        operation=OperationEnum.GROUP_BY,
        dataset_id="ds1",
        sheet_name="Sheet1",
        table_id="table_1",
        filters=[
            FilterCondition(column="YEAR(Order Date)", operator=FilterOperatorEnum.BETWEEN, value=[2017, 2018])
        ],
        group_by_columns=["YEAR_MONTH(Order Date)"],
        aggregations=[
            AggregationSpec(column="Sales", operation=AggregationOpEnum.SUM, alias="Total_Sales")
        ],
    )
    InstructionValidator.validate(inst1, table)

    # Test MONTH in EQUALS filter
    inst2 = AnalyticalInstruction(
        operation=OperationEnum.GROUP_BY,
        dataset_id="ds1",
        sheet_name="Sheet1",
        table_id="table_1",
        filters=[
            FilterCondition(column="MONTH(Order Date)", operator=FilterOperatorEnum.EQUALS, value=11)
        ],
        group_by_columns=["YEAR(Order Date)"],
        aggregations=[
            AggregationSpec(column="Sales", operation=AggregationOpEnum.SUM, alias="November_Sales")
        ],
    )
    InstructionValidator.validate(inst2, table)


def test_validator_rejects_date_dimensions_on_numeric_or_missing_columns():
    table = _make_sample_table([
        ("Sales", DataTypeEnum.FLOAT, SemanticTypeEnum.NUMERIC_MEASURE),
        ("Customer Name", DataTypeEnum.STRING, SemanticTypeEnum.CATEGORICAL),
    ])

    # Non-date column (Sales)
    inst1 = AnalyticalInstruction(
        operation=OperationEnum.GROUP_BY,
        dataset_id="ds1",
        sheet_name="Sheet1",
        table_id="table_1",
        group_by_columns=["YEAR(Sales)"],
        aggregations=[
            AggregationSpec(column="Sales", operation=AggregationOpEnum.SUM)
        ],
    )
    with pytest.raises(AnalyticalValidationError) as exc:
        InstructionValidator.validate(inst1, table)
    assert "Cannot apply date dimension 'YEAR' to non-date column 'Sales'" in str(exc.value)

    # Missing column (Order Date)
    inst2 = AnalyticalInstruction(
        operation=OperationEnum.GROUP_BY,
        dataset_id="ds1",
        sheet_name="Sheet1",
        table_id="table_1",
        group_by_columns=["YEAR(Order Date)"],
        aggregations=[
            AggregationSpec(column="Sales", operation=AggregationOpEnum.SUM)
        ],
    )
    with pytest.raises(AnalyticalValidationError) as exc:
        InstructionValidator.validate(inst2, table)
    assert "Source column 'Order Date' for derived dimension 'YEAR(Order Date)' not found" in str(exc.value)


# ----------------------------------------------------------------------
# 3. Deterministic DimensionEvaluator & Filter Tests
# ----------------------------------------------------------------------

def test_dimension_evaluator_vectors():
    dates = pd.Series(["2017-01-15", "2018-06-20", "2019-11-05", "2020-12-31", None])

    # YEAR
    disp, sk = DimensionEvaluator.evaluate(dates, DateDimensionOpEnum.YEAR)
    assert [x if pd.notna(x) else None for x in disp] == [2017, 2018, 2019, 2020, None]

    # QUARTER
    disp, sk = DimensionEvaluator.evaluate(dates, DateDimensionOpEnum.QUARTER)
    assert [x if pd.notna(x) else None for x in disp] == ["Q1", "Q2", "Q4", "Q4", None]
    assert [int(x) if pd.notna(x) else None for x in sk] == [1, 2, 4, 4, None]

    # MONTH_NAME
    disp, sk = DimensionEvaluator.evaluate(dates, DateDimensionOpEnum.MONTH_NAME)
    assert [x if pd.notna(x) else None for x in disp] == ["January", "June", "November", "December", None]

    # YEAR_MONTH
    disp, sk = DimensionEvaluator.evaluate(dates, DateDimensionOpEnum.YEAR_MONTH)
    assert [x if pd.notna(x) else None for x in disp] == ["2017-01", "2018-06", "2019-11", "2020-12", None]
    assert [int(x) if pd.notna(x) else None for x in sk] == [201701, 201806, 201911, 202012, None]


def test_filter_engine_derived_dimensions():
    df = pd.DataFrame({
        "Order Date": ["2015-02-10", "2017-05-12", "2017-11-20", "2018-11-15", "2019-03-01"],
        "Sales": [100.0, 200.0, 300.0, 400.0, 500.0],
    })

    # Filter: YEAR(Order Date) BETWEEN [2017, 2018]
    filters_year = [
        FilterCondition(column="YEAR(Order Date)", operator=FilterOperatorEnum.BETWEEN, value=[2017, 2018])
    ]
    f_df, ret, exc, desc = DeterministicFilterEngine.apply_filters(df, filters_year)
    assert len(f_df) == 3
    assert list(f_df["Sales"]) == [200.0, 300.0, 400.0]

    # Filter: MONTH(Order Date) == 'November' / 11
    filters_month = [
        FilterCondition(column="MONTH(Order Date)", operator=FilterOperatorEnum.EQUALS, value="November")
    ]
    f_df, ret, exc, desc = DeterministicFilterEngine.apply_filters(df, filters_month)
    assert len(f_df) == 2
    assert list(f_df["Sales"]) == [300.0, 400.0]

    # Filter: QUARTER(Order Date) == 4 / 'Q4'
    filters_quarter = [
        FilterCondition(column="QUARTER(Order Date)", operator=FilterOperatorEnum.EQUALS, value="Q4")
    ]
    f_df, ret, exc, desc = DeterministicFilterEngine.apply_filters(df, filters_quarter)
    assert len(f_df) == 2
    assert list(f_df["Sales"]) == [300.0, 400.0]


def test_filter_engine_physical_date_comparisons_no_float_error():
    df = pd.DataFrame({
        "Order Date": ["2015-01-01", "2016-06-15", "2017-12-31", "2019-01-01"],
        "Sales": [50.0, 150.0, 250.0, 350.0],
    })

    # GREATER_OR_EQUAL on date string
    filters = [
        FilterCondition(column="Order Date", operator=FilterOperatorEnum.GREATER_OR_EQUAL, value="2016-01-01")
    ]
    f_df, ret, exc, desc = DeterministicFilterEngine.apply_filters(df, filters)
    assert len(f_df) == 3
    assert list(f_df["Sales"]) == [150.0, 250.0, 350.0]

    # BETWEEN on date strings
    filters_btw = [
        FilterCondition(column="Order Date", operator=FilterOperatorEnum.BETWEEN, value=["2016-01-01", "2017-12-31"])
    ]
    f_df, ret, exc, desc = DeterministicFilterEngine.apply_filters(df, filters_btw)
    assert len(f_df) == 2
    assert list(f_df["Sales"]) == [150.0, 250.0]


# ----------------------------------------------------------------------
# 4. End-to-End Execution & Evidence Grounding
# ----------------------------------------------------------------------

def test_e2e_quarterly_trend_execution_and_chart_recommendation(monkeypatch):
    dataset_id = "test_ds_quarter"
    sheet_name = "Sheet1"

    rows_data = [
        {"Order Date": "2015-01-15", "Sales": 100.0},
        {"Order Date": "2015-05-15", "Sales": 200.0},
        {"Order Date": "2015-08-15", "Sales": 300.0},
        {"Order Date": "2015-11-15", "Sales": 400.0},
        {"Order Date": "2016-02-15", "Sales": 150.0},
        {"Order Date": "2016-06-15", "Sales": 250.0},
        {"Order Date": "2016-09-15", "Sales": 350.0},
        {"Order Date": "2016-12-15", "Sales": 450.0},
    ]

    grid = RawSheetGrid(sheet_name=sheet_name, max_row=len(rows_data) + 1, max_col=2, cells={})
    grid.cells[(1, 1)] = CellData(coordinate=CellCoordinate(row=1, column=1, cell_ref="A1"), original_value="Order Date")
    grid.cells[(1, 2)] = CellData(coordinate=CellCoordinate(row=1, column=2, cell_ref="B1"), original_value="Sales")

    for r_idx, r_data in enumerate(rows_data, start=2):
        grid.cells[(r_idx, 1)] = CellData(coordinate=CellCoordinate(row=r_idx, column=1, cell_ref=f"A{r_idx}"), original_value=r_data["Order Date"])
        grid.cells[(r_idx, 2)] = CellData(coordinate=CellCoordinate(row=r_idx, column=2, cell_ref=f"B{r_idx}"), original_value=r_data["Sales"])

    table = _make_sample_table([
        ("Order Date", DataTypeEnum.DATE, SemanticTypeEnum.TEMPORAL),
        ("Sales", DataTypeEnum.FLOAT, SemanticTypeEnum.NUMERIC_MEASURE),
    ], sheet_name=sheet_name)
    table.data_range = f"A2:B{len(rows_data) + 1}"
    table.range_address = f"A1:B{len(rows_data) + 1}"

    overview = WorkbookOverview(
        dataset_id=dataset_id,
        filename="Quarterly_Test.xlsx",
        file_size_bytes=50000,
        sheet_count=1,
        sheets=[
            SheetMetadata(
                name=sheet_name,
                index=0,
                total_rows=len(rows_data) + 1,
                total_columns=2,
                used_range=f"A1:B{len(rows_data) + 1}",
                tables=[table],
            )
        ],
        overall_quality_score=99.0,
        created_at="2026-08-25T00:00:00Z",
    )

    monkeypatch.setattr(ingestion_pipeline, "get_sheet_grid", lambda d_id, s_name: grid)
    monkeypatch.setattr(ingestion_pipeline, "get_overview", lambda d_id: overview)

    instruction = AnalyticalInstruction(
        operation=OperationEnum.GROUP_BY,
        dataset_id=dataset_id,
        sheet_name=sheet_name,
        table_id=table.table_id,
        group_by_columns=["YEAR(Order Date)", "QUARTER(Order Date)"],
        aggregations=[
            AggregationSpec(column="Sales", operation=AggregationOpEnum.SUM, alias="Total_Sales")
        ],
    )

    engine = AnalyticalEngine()
    result = engine.execute(instruction)

    assert result.result_type.value == "TABLE"
    assert result.table_data.total_rows == 8
    assert result.series_data is not None
    assert len(result.series_data) == 8
    assert result.series_data[0].label == "2015 Q1"
    assert result.series_data[-1].label == "2016 Q4"

    # Verify Chart Recommendation handles multi-dimension temporal group without error
    rec = ChartSelector.recommend(result)
    assert rec.preferred_type is not None
    assert rec.preferred_type.value in {"LINE", "BAR"}


def test_e2e_monthly_trend_over_4_years_with_seasonality(monkeypatch):
    dataset_id = "test_ds_superstore"
    sheet_name = "Sheet1"

    rows_data = []
    for y in [2017, 2018, 2019, 2020]:
        for m in range(1, 13):
            for d in [5, 12, 18, 25]:
                sales_val = (150.0 + (d * 5) + (m * 10)) * (1.0 + (y - 2017) * 0.15)
                if m in [11, 12]:
                    sales_val *= 2.5  # Q4 holiday season
                rows_data.append({
                    "Order Date": f"{y}-{m:02d}-{d:02d}",
                    "Sales": sales_val,
                    "Category": "Technology" if d % 2 == 0 else "Furniture",
                    "Region": "West" if d > 15 else "East",
                })

    grid = RawSheetGrid(sheet_name=sheet_name, max_row=len(rows_data) + 1, max_col=4, cells={})
    headers = ["Order Date", "Sales", "Category", "Region"]
    for c_idx, h in enumerate(headers, start=1):
        grid.cells[(1, c_idx)] = CellData(coordinate=CellCoordinate(row=1, column=c_idx, cell_ref=f"{chr(64 + c_idx)}1"), original_value=h)

    for r_idx, r_data in enumerate(rows_data, start=2):
        for c_idx, h in enumerate(headers, start=1):
            val = r_data[h]
            grid.cells[(r_idx, c_idx)] = CellData(coordinate=CellCoordinate(row=r_idx, column=c_idx, cell_ref=f"{chr(64 + c_idx)}{r_idx}"), original_value=val)

    table = _make_sample_table([
        ("Order Date", DataTypeEnum.DATE, SemanticTypeEnum.TEMPORAL),
        ("Sales", DataTypeEnum.FLOAT, SemanticTypeEnum.NUMERIC_MEASURE),
        ("Category", DataTypeEnum.STRING, SemanticTypeEnum.CATEGORICAL),
        ("Region", DataTypeEnum.STRING, SemanticTypeEnum.CATEGORICAL),
    ], sheet_name=sheet_name)
    table.data_range = f"A2:D{len(rows_data) + 1}"
    table.range_address = f"A1:D{len(rows_data) + 1}"

    overview = WorkbookOverview(
        dataset_id=dataset_id,
        filename="Superstore_Sales.xlsx",
        file_size_bytes=1024000,
        sheet_count=1,
        sheets=[
            SheetMetadata(
                name=sheet_name,
                index=0,
                total_rows=len(rows_data) + 1,
                total_columns=4,
                used_range=f"A1:D{len(rows_data) + 1}",
                tables=[table],
            )
        ],
        overall_quality_score=98.5,
        created_at="2026-08-25T00:00:00Z",
    )

    monkeypatch.setattr(ingestion_pipeline, "get_sheet_grid", lambda d_id, s_name: grid)
    monkeypatch.setattr(ingestion_pipeline, "get_overview", lambda d_id: overview)

    instruction = AnalyticalInstruction(
        operation=OperationEnum.GROUP_BY,
        dataset_id=dataset_id,
        sheet_name=sheet_name,
        table_id=table.table_id,
        group_by_columns=["YEAR_MONTH(Order Date)"],
        aggregations=[
            AggregationSpec(column="Sales", operation=AggregationOpEnum.SUM, alias="Total_Sales")
        ],
        sort=None,
    )

    engine = AnalyticalEngine()
    result = engine.execute(instruction)

    assert result.result_type.value == "TABLE"
    assert result.table_data is not None
    assert result.table_data.total_rows == 48

    first_period = result.table_data.rows[0]["YEAR_MONTH(Order Date)"]
    last_period = result.table_data.rows[-1]["YEAR_MONTH(Order Date)"]
    assert first_period == "2017-01"
    assert last_period == "2020-12"

    steps_joined = " ".join(result.lineage.calculation_steps)
    assert "Highest period" in steps_joined
    assert "Lowest period" in steps_joined
    assert "Seasonality evidence" in steps_joined

    assert "Order Date" in result.lineage.source_columns
    assert "Sales" in result.lineage.source_columns
