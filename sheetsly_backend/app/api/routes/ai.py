"""FastAPI routes for Phase 8 AI Natural Language Query Planning & Explanation."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from app.core.config import settings
from app.engine.ai import (
    NaturalLanguageQueryRequest,
    NaturalLanguageQueryResponse,
    QueryPlanOnlyResponse,
    SuggestedQueriesResponse,
    ai_orchestrator,
    qwen_client,
)

router = APIRouter(tags=["AI Natural Language Query Planner"])


@router.get("/status")
async def get_ai_status():
    """Returns AI configuration readiness status without exposing secrets."""
    return {
        "configured": qwen_client.is_configured,
        "model": settings.QWEN_MODEL,
        "enable_thinking": settings.QWEN_ENABLE_THINKING,
        "provider": "DashScope / Qwen (OpenAI-compatible)",
    }


@router.get("/diagnostics")
async def get_ai_diagnostics():
    """Returns safe provider connectivity diagnostics (for development only)."""
    return await qwen_client.test_connectivity()


@router.post("/query", response_model=NaturalLanguageQueryResponse)
async def execute_natural_language_query(
    request: NaturalLanguageQueryRequest,
) -> NaturalLanguageQueryResponse:
    """
    Executes an end-to-end natural-language analytical query:
    1. Qwen Query Planner translates question to AnalyticalInstruction.
    2. AI Guardrail strictly validates schema and operations before execution.
    3. Deterministic Python engine executes calculation.
    4. Deterministic visualization engine renders chart if requested.
    5. Evidence-based explainer summarizes factual result citing exact cell coordinates.
    """
    return await ai_orchestrator.execute_query(request)


@router.post("/plan-only", response_model=QueryPlanOnlyResponse)
async def plan_natural_language_query(
    request: NaturalLanguageQueryRequest,
) -> QueryPlanOnlyResponse:
    """
    Generates a planned AnalyticalInstruction or ClarificationRequest without running calculations.
    Useful for inspecting AI interpretation before execution.
    """
    return await ai_orchestrator.plan_only(request)


@router.get("/suggest/{dataset_id}", response_model=SuggestedQueriesResponse)
async def get_suggested_queries(
    dataset_id: str,
    sheet_name: Optional[str] = Query(None, description="Optional worksheet name"),
) -> SuggestedQueriesResponse:
    """
    Generates 3-5 schema-derived analytical questions for a given dataset/worksheet.
    """
    return await ai_orchestrator.generate_suggested_queries(dataset_id, sheet_name)
