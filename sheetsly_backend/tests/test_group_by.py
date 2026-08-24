"""Deterministic tests for GROUP_BY queries, multi-aggregations, sorting, and slicing."""

from pathlib import Path
from app.engine.analytics import (
    AggregationOpEnum,
    AggregationSpec,
    AnalyticalEngine,
    AnalyticalInstruction,
    OperationEnum,
    ResultTypeEnum,
    SortSpec,
)
from app.engine.pipeline import ingestion_pipeline


def test_group_by_with_multi_aggregation(vertical_table_file: Path):
    ingestion_pipeline.process_workbook(
        dataset_id="test-groupby-dataset",
        file_path=vertical_table_file,
        original_filename=vertical_table_file.name,
        file_size_bytes=1024,
    )
    engine = AnalyticalEngine()

    # GROUP_BY(Status) -> SUM(Revenue), AVERAGE(Quantity), COUNT_ROWS
    inst_group = AnalyticalInstruction(
        operation=OperationEnum.GROUP_BY,
        dataset_id="test-groupby-dataset",
        sheet_name="Sales",
        group_by_columns=["Status"],
        aggregations=[
            AggregationSpec(column="Revenue", operation=AggregationOpEnum.SUM, alias="Total_Revenue"),
            AggregationSpec(column="Quantity", operation=AggregationOpEnum.AVERAGE, alias="Avg_Quantity"),
            AggregationSpec(column="Quantity", operation=AggregationOpEnum.COUNT_ROWS, alias="Record_Count"),
        ],
        sort=SortSpec(column="Total_Revenue", ascending=False),
    )

    result = engine.execute(inst_group)
    assert result.result_type == ResultTypeEnum.TABLE
    assert result.table_data is not None
    assert result.table_data.total_rows == 2

    # Verify rows
    rows = result.table_data.rows
    # Row 1 must be 'Completed' with Total_Revenue = 3460.0 (2400 + 250 + 450 + 360)
    assert rows[0]["Status"] == "Completed"
    assert rows[0]["Total_Revenue"] == 3460.0
    assert rows[0]["Record_Count"] == 4
    # Avg_Quantity = (2 + 10 + 1 + 3) / 4 = 16 / 4 = 4.0
    assert rows[0]["Avg_Quantity"] == 4.0

    # Row 2 must be 'Pending' with Total_Revenue = 175.0
    assert rows[1]["Status"] == "Pending"
    assert rows[1]["Total_Revenue"] == 175.0
    assert rows[1]["Record_Count"] == 1

    # Verify 1D series data points populated for 1-dimension grouping
    assert result.series_data is not None
    assert len(result.series_data) == 2
    assert result.series_data[0].label == "Completed"
    assert result.series_data[0].value == 3460.0


def test_group_by_with_filter_and_limit(vertical_table_file: Path):
    ingestion_pipeline.process_workbook(
        dataset_id="test-groupby-dataset",
        file_path=vertical_table_file,
        original_filename=vertical_table_file.name,
        file_size_bytes=1024,
    )
    engine = AnalyticalEngine()

    # GROUP_BY(Product) -> SUM(Revenue), limited to top 2 by Revenue DESC
    inst = AnalyticalInstruction(
        operation=OperationEnum.GROUP_BY,
        dataset_id="test-groupby-dataset",
        sheet_name="Sales",
        group_by_columns=["Product"],
        aggregations=[
            AggregationSpec(column="Revenue", operation=AggregationOpEnum.SUM, alias="Revenue_Sum"),
        ],
        sort=SortSpec(column="Revenue_Sum", ascending=False),
        limit=2,
    )

    result = engine.execute(inst)
    assert result.table_data.total_rows == 2
    # Top 1 is Laptop Pro ($2,400.00), Top 2 is 4K Monitor ($450.00)
    assert result.table_data.rows[0]["Product"] == "Laptop Pro"
    assert result.table_data.rows[0]["Revenue_Sum"] == 2400.0
    assert result.table_data.rows[1]["Product"] == "4K Monitor"
    assert result.table_data.rows[1]["Revenue_Sum"] == 450.0
