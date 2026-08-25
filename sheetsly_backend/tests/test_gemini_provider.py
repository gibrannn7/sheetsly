"""Comprehensive tests for Gemini API provider, client request formatting, error classification, guardrails, and routing."""

import io
import json
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.engine.ai.client import AIProviderError, GeminiClient, ai_client, gemini_client, qwen_client
from app.engine.ai.explainer import evidence_explainer
from app.engine.ai.guardrail import ai_guardrail
from app.engine.ai.models import (
    ALLOWED_AI_MODELS,
    SUPPORTED_AI_MODELS,
    AIQueryStatus,
    get_provider_for_model,
)
from app.engine.ai.planner import query_planner
from app.engine.analytics.engine import analytical_engine
from app.engine.analytics.instruction_model import AnalyticalInstruction, OperationEnum
from app.main import app
from app.models.schemas import ColumnMetadata, DataTypeEnum, SemanticTypeEnum, TableRegion

client = TestClient(app)


@pytest.fixture
def mock_table_region() -> TableRegion:
    """Fixture returning a mock table region with sales columns."""
    return TableRegion(
        table_id="tbl_sales_test",
        name="Sales Table",
        sheet_name="Sheet1",
        range_address="A1:E6",
        header_range="A1:E1",
        data_range="A2:E6",
        row_count=5,
        column_count=3,
        columns=[
            ColumnMetadata(
                name="Region",
                index=0,
                source_column_letter="A",
                data_type=DataTypeEnum.STRING,
                semantic_type=SemanticTypeEnum.CATEGORICAL,
                null_count=0,
                unique_count=3,
                sample_values=["West", "East", "North"],
            ),
            ColumnMetadata(
                name="Product",
                index=1,
                source_column_letter="B",
                data_type=DataTypeEnum.STRING,
                semantic_type=SemanticTypeEnum.CATEGORICAL,
                null_count=0,
                unique_count=3,
                sample_values=["Widget A", "Widget B", "Widget C"],
            ),
            ColumnMetadata(
                name="Revenue",
                index=4,
                source_column_letter="E",
                data_type=DataTypeEnum.FLOAT,
                semantic_type=SemanticTypeEnum.NUMERIC_MEASURE,
                null_count=0,
                unique_count=5,
                sample_values=["150.0", "100.0", "160.0"],
            ),
        ],
    )


# ============================================================================
# 1. Gemini Configuration & Provider Resolution Tests
# ============================================================================

def test_gemini_client_configuration_detection():
    """Verifies that GeminiClient correctly detects configured vs unconfigured state."""
    gem_client = GeminiClient()

    with patch.object(settings, "GEMINI_API_KEY", "test-gemini-api-key"):
        assert gem_client.is_configured is True
        assert gem_client.get_sanitized_key_prefix() == "AQ.Ab8****"

    with patch.object(settings, "GEMINI_API_KEY", ""):
        assert gem_client.is_configured is False
        assert gem_client.get_sanitized_key_prefix() == "(not configured)"

    with patch.object(settings, "GEMINI_API_KEY", "your_gemini_api_key_here"):
        assert gem_client.is_configured is False


def test_provider_resolution_for_models():
    """Verifies get_provider_for_model maps models to expected provider strings."""
    assert get_provider_for_model("gemini-2.5-flash") == "gemini"
    assert get_provider_for_model("gemini-3.1-flash-lite") == "gemini"
    assert get_provider_for_model("gemini-3.5-flash-lite") == "gemini"
    assert get_provider_for_model("gemini-3.5-flash") == "gemini"
    assert get_provider_for_model("gemini-3.6-flash") == "gemini"
    assert get_provider_for_model("qwen3.5-plus") == "qwen"
    assert get_provider_for_model("deepseek-v4-flash") == "deepseek"
    assert get_provider_for_model(None) == "qwen"


def test_gemini_models_present_in_allowlist():
    """Verifies all five Gemini models are allowlisted and gemini-3.7-flash is excluded."""
    for model_id in [
        "gemini-2.5-flash",
        "gemini-3.1-flash-lite",
        "gemini-3.5-flash-lite",
        "gemini-3.5-flash",
        "gemini-3.6-flash",
    ]:
        assert model_id in ALLOWED_AI_MODELS
    assert "gemini-3.7-flash" not in ALLOWED_AI_MODELS


# ============================================================================
# 2. Request Construction & Headers Tests
# ============================================================================

def test_gemini_endpoint_and_headers_generation():
    """Verifies endpoint URL and X-goog-api-key header format."""
    gem_client = GeminiClient()
    with patch.object(settings, "GEMINI_API_KEY", "AQ_TEST_KEY_123"):
        endpoint = gem_client.get_endpoint("gemini-3.5-flash")
        assert endpoint == "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent"
        
        headers = gem_client._get_headers()
        assert headers["Content-Type"] == "application/json"
        assert headers["X-goog-api-key"] == "AQ_TEST_KEY_123"


def test_gemini_headers_raises_when_unconfigured():
    """Verifies calling _get_headers when unconfigured raises actionable AIProviderError."""
    gem_client = GeminiClient()
    with patch.object(settings, "GEMINI_API_KEY", ""):
        with pytest.raises(AIProviderError) as exc_info:
            gem_client._get_headers()
        assert "GEMINI_API_KEY is not configured" in str(exc_info.value)
        assert exc_info.value.is_configured is False


# ============================================================================
# 3. Response Normalization & JSON Extraction Tests
# ============================================================================

def test_gemini_generate_json_success():
    """Verifies generate_json parses candidates structure correctly."""
    import asyncio
    gem_client = GeminiClient()
    mock_response_data = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": json.dumps({
                                "type": "INSTRUCTION",
                                "intent_summary": "Calculate total revenue",
                                "instruction": {
                                    "operation": "SUM",
                                    "target_column": "Revenue",
                                    "filters": [],
                                }
                            })
                        }
                    ],
                    "role": "model",
                },
                "finishReason": "STOP",
                "index": 0,
            }
        ]
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_response_data

    with patch.object(settings, "GEMINI_API_KEY", "AQ_TEST_KEY_123"):
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_resp
            result = asyncio.run(gem_client.generate_json(
                system_prompt="Test system prompt",
                user_prompt="What is total revenue?",
                model="gemini-3.5-flash",
            ))
            assert result["type"] == "INSTRUCTION"
            assert result["instruction"]["operation"] == "SUM"
            assert result["instruction"]["target_column"] == "Revenue"


def test_gemini_generate_json_with_markdown_fences():
    """Verifies generate_json strips markdown ```json fences if returned by model."""
    import asyncio
    gem_client = GeminiClient()
    raw_markdown = (
        "```json\n"
        "{\n"
        '  "type": "INSTRUCTION",\n'
        '  "intent_summary": "Average revenue",\n'
        '  "instruction": {"operation": "AVERAGE", "target_column": "Revenue"}\n'
        "}\n"
        "```"
    )
    mock_response_data = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": raw_markdown}],
                    "role": "model",
                }
            }
        ]
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_response_data

    with patch.object(settings, "GEMINI_API_KEY", "AQ_TEST_KEY_123"):
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_resp
            result = asyncio.run(gem_client.generate_json(
                system_prompt="Test",
                user_prompt="Test",
                model="gemini-3.6-flash",
            ))
            assert result["type"] == "INSTRUCTION"
            assert result["instruction"]["operation"] == "AVERAGE"


# ============================================================================
# 4. Error Handling & Actionable Messages Tests
# ============================================================================

@pytest.mark.parametrize(
    "status_code, response_body, expected_phrase",
    [
        (400, "Invalid argument: model not supported", "Invalid request to Gemini API (HTTP 400)"),
        (401, "API key not valid", "Authentication failed (HTTP 401)"),
        (403, "Permission denied", "Authentication failed (HTTP 403)"),
        (404, "Model not found", "Model or endpoint not found (HTTP 404)"),
        (429, "Resource exhausted", "Rate limit or quota exceeded (HTTP 429)"),
        (500, "Internal error", "Google Gemini AI service encountered an internal error (HTTP 500)"),
    ],
)
def test_gemini_http_error_classification(status_code, response_body, expected_phrase):
    """Verifies that Gemini HTTP error codes are classified into actionable messages."""
    import asyncio
    gem_client = GeminiClient()
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.text = response_body

    with patch.object(settings, "GEMINI_API_KEY", "AQ_TEST_KEY_123"):
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_resp
            with pytest.raises(AIProviderError) as exc_info:
                asyncio.run(gem_client.generate_json(
                    system_prompt="Test",
                    user_prompt="Test",
                    model="gemini-3.5-flash",
                ))
            assert expected_phrase in str(exc_info.value)


# ============================================================================
# 5. Guardrail Enforcement with Gemini-Planned Instructions
# ============================================================================

def test_guardrail_rejects_gemini_plan_with_hallucinated_column(mock_table_region):
    """Verifies that if Gemini outputs a nonexistent column name, AI Guardrail rejects it immediately."""
    hallucinated_instruction = AnalyticalInstruction(
        dataset_id="ds_test",
        sheet_name="Sheet1",
        operation=OperationEnum.SUM,
        target_column="ProfitMargin",  # NOT in schema
        filters=[],
    )

    is_valid, error = ai_guardrail.validate_instruction(hallucinated_instruction, mock_table_region)
    assert is_valid is False
    assert "ProfitMargin" in error


def test_guardrail_rejects_gemini_plan_with_type_mismatch(mock_table_region):
    """Verifies that if Gemini attempts SUM on a string column (e.g. Region), Guardrail blocks it."""
    invalid_type_instruction = AnalyticalInstruction(
        dataset_id="ds_test",
        sheet_name="Sheet1",
        operation=OperationEnum.SUM,
        target_column="Region",  # String column
        filters=[],
    )

    is_valid, error = ai_guardrail.validate_instruction(invalid_type_instruction, mock_table_region)
    assert is_valid is False
    assert "numeric" in error.lower()


# ============================================================================
# 6. Diagnostics Endpoint Tests
# ============================================================================

def test_gemini_connectivity_probe_healthy():
    """Verifies gemini_client.test_connectivity returns HEALTHY on 200 response."""
    import asyncio
    mock_resp = MagicMock()
    mock_resp.status_code = 200

    with patch.object(settings, "GEMINI_API_KEY", "AQ_TEST_KEY_123"):
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_resp
            diag = asyncio.run(gemini_client.test_connectivity("gemini-3.5-flash"))
            assert diag["configured"] is True
            assert diag["connectivity"] == "HEALTHY"
            assert diag["model"] == "gemini-3.5-flash"
            assert diag["key_prefix"] == "AQ_TES****"
            assert "AQ_TEST_KEY_123" not in str(diag)  # Key not leaked


def test_diagnostics_endpoint_via_api():
    """Verifies /api/v1/ai/diagnostics endpoint works with provider parameter."""
    with patch("app.engine.ai.client.gemini_client.test_connectivity", new_callable=AsyncMock) as mock_gem:
        mock_gem.return_value = {
            "configured": True,
            "provider": "Google Gemini",
            "model": "gemini-3.5-flash",
            "connectivity": "HEALTHY",
            "latency_ms": 120.5,
        }
        res = client.get("/api/v1/ai/diagnostics?provider=gemini")
        assert res.status_code == 200
        data = res.json()
        assert data["provider"] == "Google Gemini"
        assert data["connectivity"] == "HEALTHY"
