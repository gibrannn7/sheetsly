"""Deterministic tests for composed conditional operations (SUMIF, SUMIFS, COUNTIF, COUNTIFS)."""

from pathlib import Path
from app.engine.analytics import (
    AnalyticalEngine,
    AnalyticalInstruction,
    FilterCondition,
    FilterOperatorEnum,
    OperationEnum,
)
from app.engine.pipeline import ingestion_pipeline


def test_conditional_sumif_and_sumifs(vertical_table_file: Path):
    ingestion_pipeline.process_workbook(
        dataset_id="test-cond-dataset",
        file_path=vertical_table_file,
        original_filename=vertical_table_file.name,
        file_size_bytes=1024,
    )
    engine = AnalyticalEngine()

    # SUMIF: Total Revenue where Status == 'Completed' (2400 + 250 + 450 + 360 = 3460.0)
    inst_sumif = AnalyticalInstruction(
        operation=OperationEnum.SUMIF,
        dataset_id="test-cond-dataset",
        sheet_name="Sales",
        target_column="Revenue",
        filters=[FilterCondition(column="Status", operator=FilterOperatorEnum.EQUALS, value="Completed")],
    )
    res_sumif = engine.execute(inst_sumif)
    assert res_sumif.scalar_value == 3460.0

    # SUMIFS: Total Revenue where Status == 'Completed' AND Quantity >= 2
    # Rows: Laptop (2400, qty 2), Mouse (250, qty 10), Keyboard (360, qty 3) -> Total = 3010.0
    inst_sumifs = AnalyticalInstruction(
        operation=OperationEnum.SUMIFS,
        dataset_id="test-cond-dataset",
        sheet_name="Sales",
        target_column="Revenue",
        filters=[
            FilterCondition(column="Status", operator=FilterOperatorEnum.EQUALS, value="Completed"),
            FilterCondition(column="Quantity", operator=FilterOperatorEnum.GREATER_OR_EQUAL, value=2),
        ],
    )
    res_sumifs = engine.execute(inst_sumifs)
    assert res_sumifs.scalar_value == 3010.0


def test_conditional_countif_and_countifs(vertical_table_file: Path):
    ingestion_pipeline.process_workbook(
        dataset_id="test-cond-dataset",
        file_path=vertical_table_file,
        original_filename=vertical_table_file.name,
        file_size_bytes=1024,
    )
    engine = AnalyticalEngine()

    # COUNTIF: Count records where Quantity > 2 -> 3 rows (Mouse=10, Hub=5, Keyboard=3)
    inst_countif = AnalyticalInstruction(
        operation=OperationEnum.COUNTIF,
        dataset_id="test-cond-dataset",
        sheet_name="Sales",
        target_column="Product",
        filters=[FilterCondition(column="Quantity", operator=FilterOperatorEnum.GREATER_THAN, value=2)],
    )
    res_countif = engine.execute(inst_countif)
    assert res_countif.scalar_value == 3

    # COUNTIFS: Count records where Status == 'Completed' AND Quantity >= 3 -> 2 rows (Mouse=10, Keyboard=3)
    inst_countifs = AnalyticalInstruction(
        operation=OperationEnum.COUNTIFS,
        dataset_id="test-cond-dataset",
        sheet_name="Sales",
        target_column="Product",
        filters=[
            FilterCondition(column="Status", operator=FilterOperatorEnum.EQUALS, value="Completed"),
            FilterCondition(column="Quantity", operator=FilterOperatorEnum.GREATER_OR_EQUAL, value=3),
        ],
    )
    res_countifs = engine.execute(inst_countifs)
    assert res_countifs.scalar_value == 2
