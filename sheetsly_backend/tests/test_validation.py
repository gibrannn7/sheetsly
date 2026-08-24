"""Tests for pre-execution instruction validation rules and safe rejection of invalid operations."""

from pathlib import Path
import pytest
from app.engine.analytics import (
    AggregationOpEnum,
    AggregationSpec,
    AnalyticalEngine,
    AnalyticalInstruction,
    FilterCondition,
    FilterOperatorEnum,
    OperationEnum,
)
from app.engine.analytics.validator import AnalyticalValidationError
from app.engine.pipeline import ingestion_pipeline


def test_reject_sum_on_text_column(vertical_table_file: Path):
    ingestion_pipeline.process_workbook(
        dataset_id="test-val-dataset",
        file_path=vertical_table_file,
        original_filename=vertical_table_file.name,
        file_size_bytes=1024,
    )
    engine = AnalyticalEngine()

    # SUM on 'Product' (string column) must fail with validation error
    inst = AnalyticalInstruction(
        operation=OperationEnum.SUM,
        dataset_id="test-val-dataset",
        sheet_name="Sales",
        target_column="Product",
    )
    with pytest.raises(AnalyticalValidationError) as exc_info:
        engine.execute(inst)
    assert "Cannot perform numeric operation 'SUM' on non-numeric column 'Product'" in str(exc_info.value)


def test_reject_unknown_target_column(vertical_table_file: Path):
    engine = AnalyticalEngine()
    inst = AnalyticalInstruction(
        operation=OperationEnum.SUM,
        dataset_id="test-val-dataset",
        sheet_name="Sales",
        target_column="NonExistentColumn",
    )
    with pytest.raises(AnalyticalValidationError) as exc_info:
        engine.execute(inst)
    assert "Target column 'NonExistentColumn' not found" in str(exc_info.value)


def test_reject_missing_target_column_for_scalar(vertical_table_file: Path):
    engine = AnalyticalEngine()
    inst = AnalyticalInstruction(
        operation=OperationEnum.AVERAGE,
        dataset_id="test-val-dataset",
        sheet_name="Sales",
        target_column=None,
    )
    with pytest.raises(AnalyticalValidationError) as exc_info:
        engine.execute(inst)
    assert "requires a 'target_column' to be specified" in str(exc_info.value)


def test_reject_unknown_group_by_column(vertical_table_file: Path):
    engine = AnalyticalEngine()
    inst = AnalyticalInstruction(
        operation=OperationEnum.GROUP_BY,
        dataset_id="test-val-dataset",
        sheet_name="Sales",
        group_by_columns=["UnknownGroupCol"],
        aggregations=[AggregationSpec(column="Revenue", operation=AggregationOpEnum.SUM)],
    )
    with pytest.raises(AnalyticalValidationError) as exc_info:
        engine.execute(inst)
    assert "Group-by column 'UnknownGroupCol' not found" in str(exc_info.value)


def test_reject_invalid_between_operand(vertical_table_file: Path):
    engine = AnalyticalEngine()
    inst = AnalyticalInstruction(
        operation=OperationEnum.FILTER,
        dataset_id="test-val-dataset",
        sheet_name="Sales",
        filters=[FilterCondition(column="Quantity", operator=FilterOperatorEnum.BETWEEN, value=50)],  # not a list
    )
    with pytest.raises(AnalyticalValidationError) as exc_info:
        engine.execute(inst)
    assert "requires a 2-element list [min, max]" in str(exc_info.value)
