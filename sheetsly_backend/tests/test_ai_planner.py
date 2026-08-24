"""Tests for Phase 8 Qwen Natural Language Query Planner and Ambiguity Handling."""

from unittest.mock import AsyncMock, patch
import pytest

from app.engine.ai.client import AIProviderError
from app.engine.ai.models import AIQueryStatus
from app.engine.ai.planner import QwenQueryPlanner
from app.models.schemas import ColumnMetadata, DataTypeEnum, SemanticTypeEnum, TableRegion


@pytest.fixture
def sales_table_region() -> TableRegion:
    """Fixture providing a verified multi-column sales table schema."""
    return TableRegion(
        table_id="T1",
        sheet_name="Sales",
        name="T1",
        range_address="A1:E6",
        data_range="A2:E6",
        header_row_indices=[1],
        row_count=5,
        column_count=5,
        columns=[
            ColumnMetadata(index=0, name="Region", source_column_letter="A", data_type=DataTypeEnum.STRING, semantic_type=SemanticTypeEnum.CATEGORICAL, sample_values=["West", "East", "North"]),
            ColumnMetadata(index=1, name="Product", source_column_letter="B", data_type=DataTypeEnum.STRING, semantic_type=SemanticTypeEnum.CATEGORICAL, sample_values=["Widget A", "Widget B"]),
            ColumnMetadata(index=2, name="Units", source_column_letter="C", data_type=DataTypeEnum.INTEGER, semantic_type=SemanticTypeEnum.NUMERIC_MEASURE, sample_values=["10", "5", "8"]),
            ColumnMetadata(index=3, name="UnitPrice", source_column_letter="D", data_type=DataTypeEnum.FLOAT, semantic_type=SemanticTypeEnum.NUMERIC_MEASURE, sample_values=["15.00", "20.00"]),
            ColumnMetadata(index=4, name="Revenue", source_column_letter="E", data_type=DataTypeEnum.FLOAT, semantic_type=SemanticTypeEnum.NUMERIC_MEASURE, sample_values=["150.00", "100.00"]),
        ],
    )


@pytest.mark.anyio
async def test_planner_translates_scalar_sum_query(sales_table_region):
    """Verifies that a simple sum query produces a valid SUM AnalyticalInstruction."""
    planner = QwenQueryPlanner()
    mock_llm_json = {
        "type": "INSTRUCTION",
        "intent_summary": "Calculate total revenue across all sales records",
        "instruction": {
            "operation": "SUM",
            "target_column": "Revenue",
            "filters": [],
        },
    }

    with patch("app.engine.ai.planner.qwen_client.generate_json", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_llm_json
        status, intent, instruction, clarification, error = await planner.plan_query(
            query="What is the total revenue?",
            dataset_id="ds_123",
            sheet_name="Sales",
            table_region=sales_table_region,
        )

        assert status == AIQueryStatus.EXECUTION_READY
        assert instruction is not None
        assert instruction.operation.value == "SUM"
        assert instruction.target_column == "Revenue"
        assert clarification is None
        assert error is None


@pytest.mark.anyio
async def test_planner_detects_ambiguity_and_returns_clarification(sales_table_region):
    """Verifies that an ambiguous query produces a structured ClarificationRequest."""
    planner = QwenQueryPlanner()
    mock_llm_json = {
        "type": "CLARIFICATION",
        "intent_summary": "User asked for total without specifying which numeric metric",
        "question": "Which column would you like to total? The table contains Units, UnitPrice, and Revenue.",
        "reason": "Multiple numeric measures available.",
        "target_parameter": "target_column",
        "options": ["Units", "UnitPrice", "Revenue"],
    }

    with patch("app.engine.ai.planner.qwen_client.generate_json", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_llm_json
        status, intent, instruction, clarification, error = await planner.plan_query(
            query="What is the total?",
            dataset_id="ds_123",
            sheet_name="Sales",
            table_region=sales_table_region,
        )

        assert status == AIQueryStatus.CLARIFICATION_REQUIRED
        assert instruction is None
        assert clarification is not None
        assert clarification.target_parameter == "target_column"
        assert "Revenue" in clarification.options
        assert "Units" in clarification.options


@pytest.mark.anyio
async def test_planner_handles_group_by_query(sales_table_region):
    """Verifies that a breakdown query plans a GROUP_BY operation."""
    planner = QwenQueryPlanner()
    mock_llm_json = {
        "type": "INSTRUCTION",
        "intent_summary": "Group sales by region and sum revenue",
        "instruction": {
            "operation": "GROUP_BY",
            "group_by_columns": ["Region"],
            "aggregations": [
                {"column": "Revenue", "operation": "SUM", "alias": "Total_Revenue"}
            ],
            "sort": {"column": "Total_Revenue", "ascending": False},
        },
    }

    with patch("app.engine.ai.planner.qwen_client.generate_json", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_llm_json
        status, intent, instruction, clarification, error = await planner.plan_query(
            query="Show me total revenue by region sorted highest to lowest",
            dataset_id="ds_123",
            sheet_name="Sales",
            table_region=sales_table_region,
        )

        assert status == AIQueryStatus.EXECUTION_READY
        assert instruction is not None
        assert instruction.operation.value == "GROUP_BY"
        assert instruction.group_by_columns == ["Region"]
        assert len(instruction.aggregations) == 1
        assert instruction.aggregations[0].column == "Revenue"
        assert instruction.sort is not None
        assert instruction.sort.ascending is False


@pytest.mark.anyio
async def test_planner_handles_unsupported_query(sales_table_region):
    """Verifies that an unanswerable question returns UNSUPPORTED_QUERY."""
    planner = QwenQueryPlanner()
    mock_llm_json = {
        "type": "UNSUPPORTED",
        "intent_summary": "User asked for weather forecasts not in the dataset",
        "reason": "The dataset contains sales transactions, not meteorological data.",
    }

    with patch("app.engine.ai.planner.qwen_client.generate_json", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_llm_json
        status, intent, instruction, clarification, error = await planner.plan_query(
            query="What will the temperature be tomorrow in Paris?",
            dataset_id="ds_123",
            sheet_name="Sales",
            table_region=sales_table_region,
        )

        assert status == AIQueryStatus.UNSUPPORTED_QUERY
        assert instruction is None
        assert error == "The dataset contains sales transactions, not meteorological data."


@pytest.mark.anyio
async def test_planner_handles_provider_error_gracefully(sales_table_region):
    """Verifies that LLM timeouts/errors return PROVIDER_ERROR without crashing."""
    planner = QwenQueryPlanner()

    with patch("app.engine.ai.planner.qwen_client.generate_json", new_callable=AsyncMock) as mock_gen:
        mock_gen.side_effect = AIProviderError("Connection to AI provider timed out.")
        status, intent, instruction, clarification, error = await planner.plan_query(
            query="What is total revenue?",
            dataset_id="ds_123",
            sheet_name="Sales",
            table_region=sales_table_region,
        )

        assert status == AIQueryStatus.PROVIDER_ERROR
        assert instruction is None
        assert "timed out" in error
