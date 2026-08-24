"""Deterministic tests for all filter operators and Boolean AND/OR logic."""

from pathlib import Path
from app.engine.analytics import (
    AnalyticalEngine,
    AnalyticalInstruction,
    FilterCombinationEnum,
    FilterCondition,
    FilterOperatorEnum,
    OperationEnum,
)
from app.engine.pipeline import ingestion_pipeline


def test_filtering_operations(vertical_table_file: Path):
    ingestion_pipeline.process_workbook(
        dataset_id="test-filter-dataset",
        file_path=vertical_table_file,
        original_filename=vertical_table_file.name,
        file_size_bytes=1024,
    )
    engine = AnalyticalEngine()

    # 1. Filter: Status == 'Completed' (4 out of 5 rows)
    inst_eq = AnalyticalInstruction(
        operation=OperationEnum.FILTER,
        dataset_id="test-filter-dataset",
        sheet_name="Sales",
        filters=[FilterCondition(column="Status", operator=FilterOperatorEnum.EQUALS, value="Completed")],
    )
    res_eq = engine.execute(inst_eq)
    assert res_eq.table_data.total_rows == 4
    assert res_eq.lineage.rows_included == 4
    assert res_eq.lineage.rows_excluded == 1

    # 2. Filter: Quantity > 2 (Mouse=10, Hub=5, Keyboard=3 -> 3 rows)
    inst_gt = AnalyticalInstruction(
        operation=OperationEnum.FILTER,
        dataset_id="test-filter-dataset",
        sheet_name="Sales",
        filters=[FilterCondition(column="Quantity", operator=FilterOperatorEnum.GREATER_THAN, value=2)],
    )
    res_gt = engine.execute(inst_gt)
    assert res_gt.table_data.total_rows == 3

    # 3. Filter: Quantity BETWEEN [2, 5] (Laptop=2, Hub=5, Keyboard=3 -> 3 rows)
    inst_between = AnalyticalInstruction(
        operation=OperationEnum.FILTER,
        dataset_id="test-filter-dataset",
        sheet_name="Sales",
        filters=[FilterCondition(column="Quantity", operator=FilterOperatorEnum.BETWEEN, value=[2, 5])],
    )
    res_between = engine.execute(inst_between)
    assert res_between.table_data.total_rows == 3

    # 4. Filter: Product CONTAINS 'Mouse' (1 row)
    inst_contains = AnalyticalInstruction(
        operation=OperationEnum.FILTER,
        dataset_id="test-filter-dataset",
        sheet_name="Sales",
        filters=[FilterCondition(column="Product", operator=FilterOperatorEnum.CONTAINS, value="Mouse")],
    )
    res_contains = engine.execute(inst_contains)
    assert res_contains.table_data.total_rows == 1
    assert res_contains.table_data.rows[0]["Product"] == "Wireless Mouse"

    # 5. Compound AND: Quantity >= 3 AND Status == 'Completed' (Mouse=10, Keyboard=3 -> 2 rows)
    inst_and = AnalyticalInstruction(
        operation=OperationEnum.FILTER,
        dataset_id="test-filter-dataset",
        sheet_name="Sales",
        filter_combination=FilterCombinationEnum.AND,
        filters=[
            FilterCondition(column="Quantity", operator=FilterOperatorEnum.GREATER_OR_EQUAL, value=3),
            FilterCondition(column="Status", operator=FilterOperatorEnum.EQUALS, value="Completed"),
        ],
    )
    res_and = engine.execute(inst_and)
    assert res_and.table_data.total_rows == 2

    # 6. Compound OR: Product CONTAINS 'Laptop' OR Product CONTAINS 'Monitor' -> 2 rows
    inst_or = AnalyticalInstruction(
        operation=OperationEnum.FILTER,
        dataset_id="test-filter-dataset",
        sheet_name="Sales",
        filter_combination=FilterCombinationEnum.OR,
        filters=[
            FilterCondition(column="Product", operator=FilterOperatorEnum.CONTAINS, value="Laptop"),
            FilterCondition(column="Product", operator=FilterOperatorEnum.CONTAINS, value="Monitor"),
        ],
    )
    res_or = engine.execute(inst_or)
    assert res_or.table_data.total_rows == 2
