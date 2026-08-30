"""Unit tests for Phase 13: Model Selector, Propagation, and Retired Model Isolation."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_ai_status_default_model_and_catalog():
    res = client.get("/api/v1/ai/status")
    assert res.status_code == 200
    data = res.json()
    
    # 1. Default model must be gemini-3.1-flash-lite
    assert data["default_model"] == "gemini-3.1-flash-lite"
    
    # 2. Retired qwen3.5-plus must NOT be in available models
    models = [m["id"] for m in data["available_models"]]
    assert "qwen3.5-plus" not in models
    assert "gemini-3.1-flash-lite" in models
    assert "qwen3.5-122b-a10b" in models
    assert "qwen3.5-flash" in models


def test_agent_action_accepts_model_override():
    # Verify AgentActionRequest schema accepts model_id
    from app.api.routes.agent import AgentActionRequest
    req = AgentActionRequest(
        dataset_id="test_ds",
        user_request="buatkan total",
        model_id="qwen3.5-flash"
    )
    assert req.model_id == "qwen3.5-flash"
