"""Deterministic unit tests for all scalar calculations and explicit COUNT semantics."""

from pathlib import Path
from app.engine.analytics import AnalyticalEngine, AnalyticalInstruction, OperationEnum
from app.engine.pipeline import ingestion_pipeline


def test_scalar_aggregations_on_sales_table(vertical_table_file: Path):
    # Ingest file first
    overview = ingestion_pipeline.process_workbook(
        dataset_id="test-agg-dataset",
        file_path=vertical_table_file,
        original_filename=vertical_table_file.name,
        file_size_bytes=1024,
    )

    engine = AnalyticalEngine()

    # 1. SUM Revenue: 2400 + 250 + 175 + 450 + 360 = 3635.0
    inst_sum = AnalyticalInstruction(
        operation=OperationEnum.SUM,
        dataset_id="test-agg-dataset",
        sheet_name="Sales",
        target_column="Revenue",
    )
    res_sum = engine.execute(inst_sum)
    assert res_sum.scalar_value == 3635.0
    assert res_sum.scalar_formatted == "3,635.00"

    # 2. COUNT_ROWS: 5 data rows
    inst_count_rows = AnalyticalInstruction(
        operation=OperationEnum.COUNT_ROWS,
        dataset_id="test-agg-dataset",
        sheet_name="Sales",
    )
    res_count_rows = engine.execute(inst_count_rows)
    assert res_count_rows.scalar_value == 5

    # 3. COUNT_VALUES: 5 non-null statuses
    inst_count_vals = AnalyticalInstruction(
        operation=OperationEnum.COUNT_VALUES,
        dataset_id="test-agg-dataset",
        sheet_name="Sales",
        target_column="Status",
    )
    res_count_vals = engine.execute(inst_count_vals)
    assert res_count_vals.scalar_value == 5

    # 4. DISTINCT_COUNT: 2 distinct statuses ('Completed', 'Pending')
    inst_distinct = AnalyticalInstruction(
        operation=OperationEnum.DISTINCT_COUNT,
        dataset_id="test-agg-dataset",
        sheet_name="Sales",
        target_column="Status",
    )
    res_distinct = engine.execute(inst_distinct)
    assert res_distinct.scalar_value == 2

    # 5. AVERAGE Quantity: (2 + 10 + 5 + 1 + 3) / 5 = 21 / 5 = 4.2
    inst_avg = AnalyticalInstruction(
        operation=OperationEnum.AVERAGE,
        dataset_id="test-agg-dataset",
        sheet_name="Sales",
        target_column="Quantity",
    )
    res_avg = engine.execute(inst_avg)
    assert res_avg.scalar_value == 4.2

    # 6. MIN Quantity: 1
    inst_min = AnalyticalInstruction(
        operation=OperationEnum.MIN,
        dataset_id="test-agg-dataset",
        sheet_name="Sales",
        target_column="Quantity",
    )
    res_min = engine.execute(inst_min)
    assert res_min.scalar_value == 1

    # 7. MAX Quantity: 10
    inst_max = AnalyticalInstruction(
        operation=OperationEnum.MAX,
        dataset_id="test-agg-dataset",
        sheet_name="Sales",
        target_column="Quantity",
    )
    res_max = engine.execute(inst_max)
    assert res_max.scalar_value == 10

    # 8. MEDIAN Quantity: sorted [1, 2, 3, 5, 10] -> median is 3
    inst_med = AnalyticalInstruction(
        operation=OperationEnum.MEDIAN,
        dataset_id="test-agg-dataset",
        sheet_name="Sales",
        target_column="Quantity",
    )
    res_med = engine.execute(inst_med)
    assert res_med.scalar_value == 3


def test_aggregations_with_missing_values(missing_values_file: Path):
    ingestion_pipeline.process_workbook(
        dataset_id="test-null-dataset",
        file_path=missing_values_file,
        original_filename=missing_values_file.name,
        file_size_bytes=1024,
    )
    engine = AnalyticalEngine()

    # Total rows = 4
    # Email column has 2 nulls -> COUNT_VALUES should be 2
    inst_null_count = AnalyticalInstruction(
        operation=OperationEnum.COUNT_VALUES,
        dataset_id="test-null-dataset",
        sheet_name="Customers",
        target_column="Email",
    )
    res = engine.execute(inst_null_count)
    assert res.scalar_value == 2
    assert "excluded 2 null/empty cells" in res.lineage.calculation_steps[-1]

    # Age column has values [34, 29, null, 41] -> AVERAGE = (34 + 29 + 41) / 3 = 104 / 3 = 34.6667
    inst_age_avg = AnalyticalInstruction(
        operation=OperationEnum.AVERAGE,
        dataset_id="test-null-dataset",
        sheet_name="Customers",
        target_column="Age",
    )
    res_age = engine.execute(inst_age_avg)
    assert res_age.scalar_value == 34.6667
