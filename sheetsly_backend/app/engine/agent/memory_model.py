"""Structured Memory models, scopes, precedence contracts, and invalidation rules."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.engine.agent.transaction_model import TransactionAuditRecord


class MemoryScopeEnum(str, Enum):
    """Defined structured memory scopes."""

    CONVERSATION = "CONVERSATION"
    WORKBOOK = "WORKBOOK"
    USER_PREFERENCE = "USER_PREFERENCE"
    TASK_HISTORY = "TASK_HISTORY"


class ConversationTurn(BaseModel):
    """A single conversational turn in the grid AI chat session."""

    turn_id: str = Field(..., description="Unique turn identifier")
    user_query: str = Field(..., description="User request")
    agent_intent: str = Field(..., description="Agent resolved intent")
    status: str = Field(..., description="Outcome status")
    timestamp: str = Field(..., description="ISO-8601 timestamp")


class WorkbookPreference(BaseModel):
    """User-confirmed preferences and semantic mappings specific to a workbook."""

    dataset_id: str = Field(..., description="Workbook dataset ID")
    sheet_name: str = Field(..., description="Worksheet name")
    confirmed_column_mappings: Dict[str, str] = Field(
        default_factory=dict,
        description="Confirmed user mappings, e.g. {'penjualan': 'Sales', 'omset': 'Revenue'}",
    )
    preferred_summary_anchors: Dict[str, str] = Field(
        default_factory=dict,
        description="Preferred summary output locations, e.g. {'Sales': 'bottom'}",
    )
    last_active_table_id: Optional[str] = Field(None, description="Last active table ID")
    schema_version_hash: Optional[str] = Field(None, description="Hash of columns to detect schema invalidation")
    updated_at: str = Field(..., description="ISO-8601 timestamp")


class UserPreferenceProfile(BaseModel):
    """Cross-session user formatting and localization preferences."""

    user_id: Optional[str] = Field(None, description="Optional user identifier")
    locale: str = Field("id-ID", description="Preferred locale: 'id-ID' or 'en-US'")
    currency_symbol: str = Field("Rp", description="Default currency symbol e.g. '$' or 'Rp'")
    default_number_format: str = Field("#,##0.00", description="Default number format code")
    preferred_theme: str = Field("system", description="UI theme preference")


class StructuredMemoryState(BaseModel):
    """In-memory structured container for all active session memory scopes."""

    conversation_memory: List[ConversationTurn] = Field(default_factory=list, description="Recent conversation turns")
    workbook_memory: Dict[str, WorkbookPreference] = Field(default_factory=dict, description="Workbook preferences by dataset_id")
    user_preferences: UserPreferenceProfile = Field(default_factory=UserPreferenceProfile, description="User preferences")
    task_history: List[TransactionAuditRecord] = Field(default_factory=list, description="Undoable transaction audit log")
