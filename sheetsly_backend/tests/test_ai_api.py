"""End-to-end API integration tests for Phase 8 AI Natural Language endpoints."""

import io
from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.fixture
def uploaded_sales_dataset_id() -> str:
    """Helper fixture that uploads a real sales spreadsheet to FastAPI test server."""
    csv_content = (
        "Region,Product,Units,UnitPrice,Revenue\n"
        "West,Widget A,10,15.00,150.00\n"
        "East,Widget B,5,20.00,100.00\n"
        "West,Widget B,8,20.00,160.00\n"
        "East,Widget A,12,15.00,180.00\n"
        "North,Widget C,4,50.00,200.00\n"
    )
    file_bytes = io.BytesIO(csv_content.encode("utf-8"))
    response = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("sales_test.csv", file_bytes, "text/csv")},
    )
    assert response.status_code in [200, 201]
    return response.json()["dataset_id"]


def test_ai_status_endpoint():
    """Verifies that /api/v1/ai/status reports provider readiness."""
    res = client.get("/api/v1/ai/status")
    assert res.status_code == 200
    data = res.json()
    assert "configured" in data
    assert "model" in data
    assert "provider" in data


def test_ai_plan_only_endpoint(uploaded_sales_dataset_id):
    """Verifies plan-only endpoint inspects query without running calculations."""
    mock_llm_json = {
        "type": "INSTRUCTION",
        "intent_summary": "Calculate total revenue across all sales rows",
        "instruction": {
            "operation": "SUM",
            "target_column": "Revenue",
            "filters": [],
        },
    }

    with patch("app.engine.ai.planner.qwen_client.generate_json", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_llm_json
        payload = {
            "query": "What is the total revenue?",
            "dataset_id": uploaded_sales_dataset_id,
        }
        res = client.post("/api/v1/ai/plan-only", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "EXECUTION_READY"
        assert data["planned_instruction"]["operation"] == "SUM"
        assert data["planned_instruction"]["target_column"] == "Revenue"


def test_ai_query_full_execution_pipeline(uploaded_sales_dataset_id):
    """Verifies full execution pipeline: NL query -> plan -> validate -> calculate -> explain."""
    mock_planner_json = {
        "type": "INSTRUCTION",
        "intent_summary": "Sum total revenue",
        "instruction": {
            "operation": "SUM",
            "target_column": "Revenue",
            "filters": [],
        },
    }

    with patch("app.engine.ai.planner.qwen_client.generate_json", new_callable=AsyncMock) as mock_plan:
        mock_plan.return_value = mock_planner_json
        payload = {
            "query": "Total revenue please",
            "dataset_id": uploaded_sales_dataset_id,
            "generate_visualization": True,
        }
        res = client.post("/api/v1/ai/query", json=payload)
        assert res.status_code == 200
        data = res.json()

        assert data["status"] == "EXECUTION_READY"
        assert data["analytical_result"] is not None
        assert data["analytical_result"]["scalar_value"] == 790.0
        assert data["explanation"] is not None
        assert "E2:E6" in data["explanation"]["source_evidence"]


def test_ai_suggested_queries_endpoint(uploaded_sales_dataset_id):
    """Verifies suggestion generation on dataset."""
    with patch("app.engine.ai.client.qwen_client.generate_json", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = {"suggested_queries": ["What is total revenue?", "Average units by region?"]}
        res = client.get(f"/api/v1/ai/suggest/{uploaded_sales_dataset_id}")
        assert res.status_code == 200
        data = res.json()
        assert data["dataset_id"] == uploaded_sales_dataset_id
        assert len(data["suggested_queries"]) >= 1


def test_ai_status_endpoint_returns_available_models():
    """Verifies that /status returns full list of 7 allowlisted models."""
    res = client.get("/api/v1/ai/status")
    assert res.status_code == 200
    data = res.json()
    assert "available_models" in data
    assert len(data["available_models"]) == 7
    model_ids = [m["id"] for m in data["available_models"]]
    assert "qwen3.5-plus" in model_ids
    assert "qwen3.6-plus" in model_ids
    assert "qwen3.7-plus" in model_ids
    assert "qwen3.5-flash" in model_ids
    assert "qwen3.6-flash" in model_ids
    assert "qwen3.7-flash" in model_ids
    assert "deepseek-v4-flash" in model_ids


def test_ai_model_allowlist_validation(uploaded_sales_dataset_id):
    """Verifies that unapproved model names are rejected before execution."""
    invalid_payload = {
        "query": "Total revenue",
        "dataset_id": uploaded_sales_dataset_id,
        "model": "unsupported-rogue-model-xyz",
    }
    res = client.post("/api/v1/ai/query", json=invalid_payload)
    assert res.status_code == 422


def test_ai_model_propagation_to_planner_and_explainer(uploaded_sales_dataset_id):
    """Verifies that selected model propagates to Qwen client and response."""
    mock_planner_json = {
        "type": "INSTRUCTION",
        "intent_summary": "Sum total revenue",
        "instruction": {
            "operation": "SUM",
            "target_column": "Revenue",
            "filters": [],
        },
    }

    with patch("app.engine.ai.planner.qwen_client.generate_json", new_callable=AsyncMock) as mock_plan:
        mock_plan.return_value = mock_planner_json
        payload = {
            "query": "Total revenue with DeepSeek",
            "dataset_id": uploaded_sales_dataset_id,
            "model": "deepseek-v4-flash",
        }
        res = client.post("/api/v1/ai/query", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "EXECUTION_READY"
        assert data["model_used"] == "deepseek-v4-flash"
        
        # Verify model was passed to generate_json call
        mock_plan.assert_called()
        call_kwargs = mock_plan.call_args.kwargs
        assert call_kwargs.get("model") == "deepseek-v4-flash"
