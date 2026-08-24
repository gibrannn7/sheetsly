"""Tests for source traceability, calculation lineage, and step audit trails."""

from pathlib import Path
from app.engine.analytics import (
    AnalyticalEngine,
    AnalyticalInstruction,
    FilterCondition,
    FilterOperatorEnum,
    OperationEnum,
)
from app.engine.pipeline import ingestion_pipeline


def test_calculation_lineage_traceability(vertical_table_file: Path):
    ingestion_pipeline.process_workbook(
        dataset_id="test-lin-dataset",
        file_path=vertical_table_file,
        original_filename=vertical_table_file.name,
        file_size_bytes=1024,
    )
    engine = AnalyticalEngine()

    inst = AnalyticalInstruction(
        operation=OperationEnum.SUM,
        dataset_id="test-lin-dataset",
        sheet_name="Sales",
        target_column="Revenue",
        filters=[FilterCondition(column="Status", operator=FilterOperatorEnum.EQUALS, value="Completed")],
    )

    result = engine.execute(inst)
    lineage = result.lineage

    assert lineage.dataset_id == "test-lin-dataset"
    assert lineage.sheet_name == "Sales"
    assert "E" in lineage.source_range  # Column letter for Revenue is E
    assert lineage.total_table_rows == 5
    assert lineage.rows_included == 4
    assert lineage.rows_excluded == 1
    assert len(lineage.filters_applied) == 1
    assert "Status == Completed" in lineage.filters_applied[0]
    assert len(lineage.calculation_steps) >= 3
    assert lineage.execution_time_ms >= 0.0

    # Verify calculation steps contain human-readable reasoning
    steps_joined = " ".join(lineage.calculation_steps)
    assert "Loaded table" in steps_joined
    assert "Applied filter" in steps_joined
    assert "retained 4 of 5 rows" in steps_joined
