"""Phase 8 AI Natural Language Query Planning & Guardrail module."""

from .client import AIProviderError, GeminiClient, QwenClient, AIProviderRouter, ai_client, gemini_client, qwen_client
from .explainer import EvidenceExplainer, evidence_explainer
from .guardrail import AIGuardrail, ai_guardrail
from .models import (
    ALLOWED_AI_MODELS,
    DEFAULT_AI_MODEL,
    SUPPORTED_AI_MODELS,
    AIQueryStatus,
    ClarificationRequest,
    EvidenceExplanation,
    NaturalLanguageQueryRequest,
    NaturalLanguageQueryResponse,
    QueryPlanOnlyResponse,
    SuggestedQueriesResponse,
    get_provider_for_model,
)
from .orchestrator import AIOrchestrator, ai_orchestrator
from .planner import QwenQueryPlanner, query_planner
from .prompts import EXPLAINER_SYSTEM_PROMPT, PLANNER_SYSTEM_PROMPT, SUGGESTION_PROMPT

__all__ = [
    "ALLOWED_AI_MODELS",
    "DEFAULT_AI_MODEL",
    "SUPPORTED_AI_MODELS",
    "get_provider_for_model",
    "AIProviderError",
    "GeminiClient",
    "gemini_client",
    "QwenClient",
    "qwen_client",
    "AIProviderRouter",
    "ai_client",
    "EvidenceExplainer",
    "evidence_explainer",
    "AIGuardrail",
    "ai_guardrail",
    "AIQueryStatus",
    "ClarificationRequest",
    "EvidenceExplanation",
    "NaturalLanguageQueryRequest",
    "NaturalLanguageQueryResponse",
    "QueryPlanOnlyResponse",
    "SuggestedQueriesResponse",
    "AIOrchestrator",
    "ai_orchestrator",
    "QwenQueryPlanner",
    "query_planner",
    "PLANNER_SYSTEM_PROMPT",
    "EXPLAINER_SYSTEM_PROMPT",
    "SUGGESTION_PROMPT",
]
