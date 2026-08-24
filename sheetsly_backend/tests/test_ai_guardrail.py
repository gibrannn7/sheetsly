"""Tests for Phase 8 AI Guardrail and Validator Enforcement."""

import pytest
from app.engine.ai.guardrail import ai_guardrail
from app.engine.analytics.instruction_model import (
    AggregationSpec,
    AnalyticalInstruction,
    FilterCondition,
    OperationEnum,
)
from app.models.schemas import ColumnMetadata, DataTypeEnum, SemanticTypeEnum, TableRegion


@pytest.fixture
def sales_table_region() -> TableRegion:
    return TableRegion(
        table_id="T1",
        sheet_name="Sales",
        name="T1",
        range_address="A1:E6",
        data_range="A2:E6",
        header_row_indices=[1],
        row_count=5,
        column_count=4,
        columns=[
            ColumnMetadata(index=0, name="Region", source_column_letter="A", data_type=DataTypeEnum.STRING, semantic_type=SemanticTypeEnum.CATEGORICAL),
            ColumnMetadata(index=1, name="Product", source_column_letter="B", data_type=DataTypeEnum.STRING, semantic_role=SemanticTypeEnum.CATEGORICAL),
            ColumnMetadata(index=2, name="Units", source_column_letter="C", data_type=DataTypeEnum.INTEGER, semantic_type=SemanticTypeEnum.NUMERIC_MEASURE),
            ColumnMetadata(index=3, name="Revenue", source_column_letter="E", data_type=DataTypeEnum.FLOAT, semantic_type=SemanticTypeEnum.NUMERIC_MEASURE),
        ],
    )


def test_guardrail_rejects_sum_on_string_column(sales_table_region):
    """Verifies that the guardrail blocks an LLM-planned SUM on a text/string column."""
    instruction = AnalyticalInstruction(
        operation=OperationEnum.SUM,
        dataset_id="ds_123",
        sheet_name="Sales",
        table_id="T1",
        target_column="Region",  # Text column!
    )

    is_valid, error = ai_guardrail.validate_instruction(instruction, sales_table_region)
    assert is_valid is False
    assert error is not None
    assert "non-numeric column 'Region'" in error


def test_guardrail_rejects_nonexistent_column(sales_table_region):
    """Verifies that the guardrail blocks references to hallucinated/nonexistent columns."""
    instruction = AnalyticalInstruction(
        operation=OperationEnum.SUM,
        dataset_id="ds_123",
        sheet_name="Sales",
        table_id="T1",
        target_column="HallucinatedProfit",
    )

    is_valid, error = ai_guardrail.validate_instruction(instruction, sales_table_region)
    assert is_valid is False
    assert "not found in table" in error


def test_guardrail_rejects_invalid_filter_operator(sales_table_region):
    """Verifies that the guardrail blocks invalid filter operators on string columns."""
    instruction = AnalyticalInstruction(
        operation=OperationEnum.SUM,
        dataset_id="ds_123",
        sheet_name="Sales",
        table_id="T1",
        target_column="Revenue",
        filters=[
            FilterCondition(column="Region", operator="greater_than", value=100)  # Non-orderable string
        ],
    )

    is_valid, error = ai_guardrail.validate_instruction(instruction, sales_table_region)
    assert is_valid is False
    assert "cannot be applied to non-orderable column 'Region'" in error


def test_guardrail_approves_valid_instruction(sales_table_region):
    """Verifies that the guardrail approves well-formed instructions."""
    instruction = AnalyticalInstruction(
        operation=OperationEnum.SUM,
        dataset_id="ds_123",
        sheet_name="Sales",
        table_id="T1",
        target_column="Revenue",
        filters=[
            FilterCondition(column="Region", operator="equals", value="West")
        ],
    )

    is_valid, error = ai_guardrail.validate_instruction(instruction, sales_table_region)
    assert is_valid is True
    assert error is None
