"""Tests for Phase 8 Evidence-Based Explainer."""

from unittest.mock import AsyncMock, patch
import pytest

from app.engine.ai.explainer import EvidenceExplainer
from app.engine.analytics.result_model import AnalyticalResult, CalculationLineage


@pytest.fixture
def scalar_result() -> AnalyticalResult:
    return AnalyticalResult(
        operation="SUM",
        result_type="SCALAR",
        scalar_value=790.0,
        scalar_formatted="$790.00",
        lineage=CalculationLineage(
            dataset_id="ds_123",
            sheet_name="Sales",
            table_id="T1",
            source_range="E2:E6",
            source_columns=["Revenue"],
            total_table_rows=5,
            rows_included=5,
            rows_excluded=0,
            filters_applied=[],
            calculation_steps=[
                "Selected target column 'Revenue'",
                "Included 5 rows from range E2:E6",
                "Calculated arithmetic SUM = 790.0",
            ],
            execution_time_ms=1.42,
        ),
    )


@pytest.mark.anyio
async def test_explainer_uses_llm_when_available(scalar_result):
    """Verifies that the explainer formats prompt and outputs grounded summary."""
    explainer = EvidenceExplainer()
    mock_llm_json = {
        "summary": "Total revenue across all 5 recorded sales transactions is $790.00.",
        "factual_statement": "The arithmetic SUM of Revenue is $790.00.",
        "source_evidence": "Sales!E2:E6 across 5 rows",
        "calculation_steps": scalar_result.lineage.calculation_steps,
        "warnings": [],
    }

    with patch("app.engine.ai.client.settings.DASHSCOPE_API_KEY", "sk-test12345"):
        with patch("app.engine.ai.explainer.qwen_client.generate_json", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = mock_llm_json
            explanation = await explainer.explain_result(scalar_result, "What is the total revenue?")

            assert explanation.factual_statement == "The arithmetic SUM of Revenue is $790.00."
            assert "Sales!E2:E6" in explanation.source_evidence
            assert len(explanation.calculation_steps) == 3


@pytest.mark.anyio
async def test_explainer_fallback_when_offline(scalar_result):
    """Verifies that the deterministic explanation fallback works perfectly without LLM."""
    explainer = EvidenceExplainer()

    with patch("app.engine.ai.client.settings.DASHSCOPE_API_KEY", ""):
        explanation = await explainer.explain_result(scalar_result, "What is the total revenue?")

        assert explanation.factual_statement == "The SUM of Revenue is $790.00."
        assert "Sales!E2:E6" in explanation.source_evidence
        assert "5 of 5 rows" in explanation.source_evidence
        assert len(explanation.calculation_steps) == 3
