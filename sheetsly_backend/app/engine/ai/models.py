"""Pydantic data models and schemas for Phase 8 AI Query Planner and Guardrails."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator

from app.engine.analytics.instruction_model import AnalyticalInstruction
from app.engine.analytics.result_model import AnalyticalResult
from app.engine.visualization.chart_model import VisualizationResponse


SUPPORTED_AI_MODELS = [
    # Qwen (Alibaba Cloud Model Studio)
    {"id": "qwen3.5-397b-a17b", "label": "Qwen 3.5 397B", "provider": "qwen", "provider_label": "Qwen", "is_default": True},
    {"id": "qwen3.5-flash", "label": "Qwen 3.5 Flash", "provider": "qwen", "provider_label": "Qwen"},
    {"id": "qwen3.6-plus", "label": "Qwen 3.6 Plus", "provider": "qwen", "provider_label": "Qwen"},
    {"id": "qwen3.7-plus", "label": "Qwen 3.7 Plus", "provider": "qwen", "provider_label": "Qwen"},
    {"id": "qwen3.6-flash", "label": "Qwen 3.6 Flash", "provider": "qwen", "provider_label": "Qwen"},
    {"id": "qwen3.7-flash", "label": "Qwen 3.7 Flash", "provider": "qwen", "provider_label": "Qwen"},
    # DeepSeek
    {"id": "deepseek-v4-flash", "label": "DeepSeek V4 Flash", "provider": "deepseek", "provider_label": "DeepSeek"},
    # Google Gemini
    {"id": "gemini-2.5-flash", "label": "Gemini 2.5 Flash", "provider": "gemini", "provider_label": "Google Gemini"},
    {"id": "gemini-3.1-flash-lite", "label": "Gemini 3.1 Flash Lite", "provider": "gemini", "provider_label": "Google Gemini"},
    {"id": "gemini-3.5-flash-lite", "label": "Gemini 3.5 Flash Lite", "provider": "gemini", "provider_label": "Google Gemini"},
    {"id": "gemini-3.5-flash", "label": "Gemini 3.5 Flash", "provider": "gemini", "provider_label": "Google Gemini"},
    {"id": "gemini-3.6-flash", "label": "Gemini 3.6 Flash", "provider": "gemini", "provider_label": "Google Gemini"},
]
ALLOWED_AI_MODELS = {m["id"] for m in SUPPORTED_AI_MODELS}
DEFAULT_AI_MODEL = "qwen3.5-397b-a17b"


def get_provider_for_model(model_id: Optional[str]) -> str:
    """Resolves provider identifier ('gemini', 'deepseek', or 'qwen') for a given model ID."""
    if not model_id:
        return "qwen"
    m = model_id.strip().lower()
    if m.startswith("gemini-"):
        return "gemini"
    if m.startswith("deepseek-"):
        return "deepseek"
    return "qwen"



class AIQueryStatus(str, Enum):
    """Lifecycle status of a natural language analytical query."""
    EXECUTION_READY = "EXECUTION_READY"
    CLARIFICATION_REQUIRED = "CLARIFICATION_REQUIRED"
    UNSUPPORTED_QUERY = "UNSUPPORTED_QUERY"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    EXECUTION_ERROR = "EXECUTION_ERROR"


class ClarificationRequest(BaseModel):
    """Structured clarification payload returned when a query is ambiguous."""
    question: str = Field(..., description="Actionable clarification question presented to user")
    reason: str = Field(..., description="Technical rationale why clarification is required")
    target_parameter: str = Field(..., description="Parameter requiring clarification (e.g. 'target_column', 'sheet_name')")
    options: List[str] = Field(default_factory=list, description="Explicit schema-derived options for user selection")


class EvidenceExplanation(BaseModel):
    """Factual explanation grounded strictly in the verified AnalyticalResult and CalculationLineage."""
    summary: str = Field(..., description="Concise, one-sentence plain English summary of the result")
    factual_statement: str = Field(..., description="Exact numerical statement matching verified Python result")
    source_evidence: str = Field(..., description="Cell coordinates and dataset range citation (e.g. 'Sales!E2:E6 (5 rows)')")
    calculation_steps: List[str] = Field(default_factory=list, description="Numbered deterministic execution trace steps")
    warnings: List[str] = Field(default_factory=list, description="Data hygiene or coverage warnings from calculation")


class TimingBreakdown(BaseModel):
    """Accurate latency measurements (in milliseconds) for each execution phase."""
    schema_resolution_ms: float = Field(0.0, description="Time spent reading dataset and resolving table schema")
    qwen_planning_ms: float = Field(0.0, description="Time spent in Qwen AI natural language query planning")
    guardrail_validation_ms: float = Field(0.0, description="Time spent validating planned instruction against schema")
    deterministic_execution_ms: float = Field(0.0, description="Time spent in Python calculation engine")
    visualization_ms: float = Field(0.0, description="Time spent rendering visualization artifact")
    evidence_explanation_ms: float = Field(0.0, description="Time spent generating evidence summary")
    total_duration_ms: float = Field(0.0, description="Total wall-clock duration of the request")


class NaturalLanguageQueryRequest(BaseModel):
    """Incoming request payload from user to natural language query planner."""
    query: str = Field(..., min_length=1, max_length=1000, description="Natural language analytical question")
    dataset_id: str = Field(..., description="Target dataset UUID")
    sheet_name: Optional[str] = Field(None, description="Specific worksheet name (defaults to active/first sheet)")
    table_id: Optional[str] = Field(None, description="Specific table ID within worksheet")
    model: Optional[str] = Field(
        None,
        description="Requested AI model identifier (must be an allowlisted model: qwen3.5-397b-a17b, qwen3.6-plus, etc.)",
    )
    generate_visualization: bool = Field(True, description="Whether to automatically generate a deterministic chart")
    clarification_selection: Optional[Dict[str, str]] = Field(
        None,
        description="User response to a previous ClarificationRequest (e.g. {'target_column': 'Revenue'})",
    )
    preplanned_instruction: Optional[AnalyticalInstruction] = Field(
        None,
        description="Pre-planned instruction from plan-only endpoint, skipping LLM planning stage if already computed",
    )

    @field_validator("model")
    @classmethod
    def validate_model_allowlist(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_clean = v.strip().lower()
            if v_clean not in ALLOWED_AI_MODELS:
                raise ValueError(
                    f"Unsupported AI model '{v}'. Allowed models: {', '.join(sorted(ALLOWED_AI_MODELS))}"
                )
            return v_clean
        return v


class QueryPlanOnlyResponse(BaseModel):
    """Inspection response returning the compiled plan without executing calculations."""
    model_config = {"protected_namespaces": ()}

    status: AIQueryStatus
    user_query: str
    intent_summary: str
    model_used: Optional[str] = None
    planned_instruction: Optional[AnalyticalInstruction] = None
    clarification: Optional[ClarificationRequest] = None
    sub_plans: Optional[List["QueryPlanOnlyResponse"]] = None
    error_message: Optional[str] = None
    timing: Optional[TimingBreakdown] = None


class NaturalLanguageQueryResponse(BaseModel):
    """Complete end-to-end response for natural language query execution."""
    model_config = {"protected_namespaces": ()}

    status: AIQueryStatus
    user_query: str
    intent_summary: str
    model_used: Optional[str] = None
    planned_instruction: Optional[AnalyticalInstruction] = None
    clarification: Optional[ClarificationRequest] = None
    analytical_result: Optional[AnalyticalResult] = None
    visualization: Optional[VisualizationResponse] = None
    explanation: Optional[EvidenceExplanation] = None
    sub_analyses: Optional[List["NaturalLanguageQueryResponse"]] = None
    suggested_next_queries: List[str] = Field(default_factory=list)
    error_message: Optional[str] = None
    timing: Optional[TimingBreakdown] = None


class SuggestedQueriesResponse(BaseModel):
    """Schema-derived sample analytical questions."""
    dataset_id: str
    sheet_name: str
    suggested_queries: List[str]
