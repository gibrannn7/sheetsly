"""Transactional mutation lifecycle, before/after diffs, verification reports, and execution results."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.engine.agent.action_model import FormattingStyle, SpreadsheetAction


class TransactionStatusEnum(str, Enum):
    """Deterministic transaction lifecycle states."""

    PENDING = "PENDING"
    VALIDATED = "VALIDATED"
    EXECUTING = "EXECUTING"
    VERIFIED = "VERIFIED"
    COMMITTED = "COMMITTED"
    ROLLED_BACK = "ROLLED_BACK"
    FAILED = "FAILED"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"
    PERSISTENCE_FAILED = "PERSISTENCE_FAILED"


class AgentResponseStatusEnum(str, Enum):
    """Explicit, unambiguous response statuses for user-facing agent operations."""

    SUCCESS = "SUCCESS"
    CLARIFICATION = "CLARIFICATION"
    UNSUPPORTED = "UNSUPPORTED"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    EXECUTION_ERROR = "EXECUTION_ERROR"
    VERIFICATION_ERROR = "VERIFICATION_ERROR"
    PERSISTENCE_ERROR = "PERSISTENCE_ERROR"
    ROLLBACK_SUCCESS = "ROLLBACK_SUCCESS"
    ROLLBACK_FAILURE = "ROLLBACK_FAILURE"


class VerificationFailureReason(str, Enum):
    """Specific failure classifications for post-execution verification."""

    FORMULA_SYNTAX_ERROR = "FORMULA_SYNTAX_ERROR"
    FORMULA_RESULT_MISMATCH = "FORMULA_RESULT_MISMATCH"
    CIRCULAR_REFERENCE = "CIRCULAR_REFERENCE"
    UNINTENDED_CELL_MODIFIED = "UNINTENDED_CELL_MODIFIED"
    TARGET_CELL_MISSING = "TARGET_CELL_MISSING"
    SOURCE_DATA_CORRUPTED = "SOURCE_DATA_CORRUPTED"
    OVERWRITE_COLLISION = "OVERWRITE_COLLISION"
    STYLE_APPLICATION_FAILED = "STYLE_APPLICATION_FAILED"
    PERSISTENCE_MISMATCH = "PERSISTENCE_MISMATCH"


class CellSnapshot(BaseModel):
    """Point-in-time snapshot of a cell before or after an action."""

    coordinate: str = Field(..., description="A1 cell reference e.g. 'D102'")
    row: int = Field(..., description="1-indexed row number")
    col: int = Field(..., description="1-indexed column number")
    original_value: Optional[Any] = Field(None, description="Raw display value")
    parsed_value: Optional[Any] = Field(None, description="Evaluated typed value")
    data_type: str = Field("null", description="Physical data type string")
    formula: Optional[str] = Field(None, description="Formula string if present")
    is_empty: bool = Field(True, description="True if cell has no content")
    style: Optional[FormattingStyle] = Field(None, description="Formatting styling applied")


class StateDiff(BaseModel):
    """Atomic delta of a single cell across a transaction."""

    target_ref: str = Field(..., description="Cell coordinate e.g. 'D102'")
    before: Optional[CellSnapshot] = Field(None, description="State before transaction")
    after: Optional[CellSnapshot] = Field(None, description="State after transaction")


class VerificationReport(BaseModel):
    """Authoritative factual report of post-execution verification."""

    is_verified: bool = Field(..., description="True if all verification checks passed cleanly")
    total_cells_checked: int = Field(0, description="Total cells inspected during verification")
    planned_modifications_count: int = Field(0, description="Number of cells planned for modification")
    actual_modifications_count: int = Field(0, description="Number of cells actually modified")
    diff_matches_plan: bool = Field(True, description="True if actual diff matches planned actions exactly")
    failures: List[str] = Field(default_factory=list, description="List of verification failure descriptions")
    failure_reasons: List[VerificationFailureReason] = Field(default_factory=list, description="Categorized failure reason codes")
    verified_expected_value: Optional[Any] = Field(None, description="Expected calculated result by Python")
    actual_evaluated_value: Optional[Any] = Field(None, description="Result evaluated on grid")
    source_integrity_intact: bool = Field(True, description="True if source data cells were unmodified")


class MutationTransaction(BaseModel):
    """Transactional container managing the lifecycle of one or more spreadsheet mutations."""

    transaction_id: str = Field(..., description="Unique transaction ID e.g. 'tx_20260826_001'")
    dataset_id: str = Field(..., description="Target dataset identifier")
    sheet_name: str = Field(..., description="Primary worksheet name")
    user_request: str = Field(..., description="Original user prompt")
    resolved_intent: str = Field(..., description="Canonical interpretation summary")
    status: TransactionStatusEnum = Field(TransactionStatusEnum.PENDING, description="Current transaction lifecycle status")
    actions: List[SpreadsheetAction] = Field(default_factory=list, description="Sequential list of actions in transaction")
    before_state: Dict[str, CellSnapshot] = Field(default_factory=dict, description="Snapshot of affected cells prior to execution")
    after_state: Dict[str, CellSnapshot] = Field(default_factory=dict, description="Snapshot of affected cells after execution")
    diff: List[StateDiff] = Field(default_factory=list, description="Computed cell-by-cell diff")
    verification_report: Optional[VerificationReport] = Field(None, description="Verification report if executed")
    created_at: str = Field(..., description="ISO-8601 creation timestamp")
    committed_at: Optional[str] = Field(None, description="ISO-8601 commit timestamp")
    version_after: Optional[int] = Field(None, description="Workbook version after commit")
    rolled_back_at: Optional[str] = Field(None, description="ISO-8601 rollback timestamp")
    rollback_reason: Optional[str] = Field(None, description="Reason for rollback if triggered")


class TransactionAuditRecord(BaseModel):
    """Immutable audit trail record of an executed transaction."""

    transaction_id: str = Field(..., description="Transaction identifier")
    dataset_id: str = Field(..., description="Dataset identifier")
    sheet_name: str = Field(..., description="Sheet name")
    timestamp: str = Field(..., description="Execution timestamp")
    user_request: str = Field(..., description="User query")
    resolved_intent: str = Field(..., description="Intent")
    action_types: List[str] = Field(default_factory=list, description="List of action types executed")
    affected_cells: List[str] = Field(default_factory=list, description="List of modified cell coordinates")
    status: str = Field(..., description="Final status")
    verified: bool = Field(False, description="Verification pass flag")
    rolled_back: bool = Field(False, description="Rollback flag")


class AgentExecutionResult(BaseModel):
    """Complete response payload from Spreadsheet Agent to caller / UI."""

    status: AgentResponseStatusEnum = Field(..., description="Explicit outcome status")
    transaction: Optional[MutationTransaction] = Field(None, description="Transaction container if planned/executed")
    message: str = Field(..., description="Concise, professional user-facing summary")
    affected_ranges: List[str] = Field(default_factory=list, description="List of affected A1 ranges")
    clarification: Optional[Any] = Field(None, description="Structured ClarificationRequest if status is CLARIFICATION")
    error_detail: Optional[str] = Field(None, description="Technical error detail if status is an error")
    execution_time_ms: float = Field(0.0, description="Total execution duration in milliseconds")
