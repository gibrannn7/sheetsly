"""Comprehensive unit test suite for Phase 1 Canonical Architecture Contracts.
Tests action models, transaction models, verification contracts, memory interfaces,
serialization roundtrips, invalid inputs, edge cases, and backward compatibility.
"""

import json
import pytest
from pydantic import ValidationError

from app.engine.agent import (
    ActionTypeEnum,
    AgentExecutionResult,
    AgentResponseStatusEnum,
    CellSnapshot,
    ConversationTurn,
    FormattingStyle,
    MemoryScopeEnum,
    MutationTransaction,
    NumberFormatSpec,
    SpreadsheetAction,
    StateDiff,
    StructuredMemoryState,
    SUPPORTED_ACTION_REGISTRY,
    TransactionAuditRecord,
    TransactionStatusEnum,
    UserPreferenceProfile,
    VerificationFailureReason,
    VerificationReport,
    WorkbookPreference,
)
from app.models.schemas import DataTypeEnum, TableRegion
from app.engine.analytics.instruction_model import OperationEnum, AnalyticalInstruction


# ============================================================================
# 1. ACTION REGISTRY & CANONICAL ACTIONS
# ============================================================================

def test_action_registry_contains_all_8_canonical_actions():
    """Verify registry contains all supported canonical actions including Phase 16 chart lifecycle & dashboard actions."""
    expected_actions = {
        "WRITE_VALUE",
        "WRITE_FORMULA",
        "INSERT_ROW",
        "INSERT_COLUMN",
        "FORMAT_CELL",
        "FORMAT_RANGE",
        "SET_NUMBER_FORMAT",
        "CLEAR_CONTENT",
        "CREATE_CHART",
        "UPDATE_CHART",
        "MOVE_CHART",
        "RESIZE_CHART",
        "DELETE_CHART",
        "CREATE_KPI",
        "CREATE_WORKSHEET",
    }
    actual_actions = {a.value for a in SUPPORTED_ACTION_REGISTRY}
    assert actual_actions == expected_actions
    assert len(SUPPORTED_ACTION_REGISTRY) == 15


def test_valid_spreadsheet_actions():
    """Test instantiation of valid actions across action types."""
    # WRITE_VALUE
    act_val = SpreadsheetAction(
        action_id="act_01",
        action_type=ActionTypeEnum.WRITE_VALUE,
        sheet_name="Sales",
        target_cell="C102",
        value="Total Sales",
        description="Write Total label",
    )
    assert act_val.action_type == ActionTypeEnum.WRITE_VALUE
    assert act_val.target_cell == "C102"
    assert act_val.value == "Total Sales"

    # WRITE_FORMULA
    act_form = SpreadsheetAction(
        action_id="act_02",
        action_type=ActionTypeEnum.WRITE_FORMULA,
        sheet_name="Sales",
        target_cell="D102",
        formula="SUM(D2:D101)",  # Automatically prefixes '='
        expected_result=250000.0,
    )
    assert act_form.formula == "=SUM(D2:D101)"

    # INSERT_ROW
    act_row = SpreadsheetAction(
        action_id="act_03",
        action_type=ActionTypeEnum.INSERT_ROW,
        sheet_name="Sales",
        row_index=102,
    )
    assert act_row.row_index == 102

    # FORMAT_RANGE
    act_fmt = SpreadsheetAction(
        action_id="act_04",
        action_type=ActionTypeEnum.FORMAT_RANGE,
        sheet_name="Sales",
        target_range="C102:D102",
        style=FormattingStyle(bold=True, fill_color="#F1F5F9", font_color="#0F172A", alignment="center"),
    )
    assert act_fmt.style.bold is True
    assert act_fmt.style.fill_color == "#F1F5F9"
    assert act_fmt.style.alignment == "center"


def test_malformed_action_rejections():
    """Verify validation errors for invalid action attributes."""
    # Invalid cell coordinate
    with pytest.raises(ValidationError) as exc:
        SpreadsheetAction(
            action_id="act_err_1",
            action_type=ActionTypeEnum.WRITE_VALUE,
            sheet_name="Sheet1",
            target_cell="102D",  # Invalid A1 notation
            value="Test",
        )
    assert "Invalid cell reference" in str(exc.value)

    # Invalid range coordinate
    with pytest.raises(ValidationError) as exc:
        SpreadsheetAction(
            action_id="act_err_2",
            action_type=ActionTypeEnum.FORMAT_RANGE,
            sheet_name="Sheet1",
            target_range="InvalidRangeFormat",
        )
    assert "Invalid range reference" in str(exc.value)

    # Unknown action type
    with pytest.raises(ValidationError) as exc:
        SpreadsheetAction(
            action_id="act_err_3",
            action_type="DELETE_DATABASE",  # Unsupported
            sheet_name="Sheet1",
        )
    assert "Input should be" in str(exc.value) or "Unsupported action type" in str(exc.value)


# ============================================================================
# 2. FORMATTING STYLE VALIDATION
# ============================================================================

def test_formatting_style_colors_and_alignments():
    """Test valid and invalid colors and alignments in FormattingStyle."""
    # Valid hex and named colors
    style_valid = FormattingStyle(
        bold=True,
        italic=False,
        font_size=12,
        font_color="#1E293B",
        fill_color="yellow",
        alignment="left",
        border_top="thin",
        border_bottom="double",
    )
    assert style_valid.font_color == "#1E293B"
    assert style_valid.fill_color == "yellow"

    # Invalid hex color
    with pytest.raises(ValidationError) as exc:
        FormattingStyle(font_color="not_a_hex_or_named_color_123")
    assert "Invalid color format" in str(exc.value)

    # Invalid alignment
    with pytest.raises(ValidationError) as exc:
        FormattingStyle(alignment="diagonal")
    assert "Invalid alignment" in str(exc.value)

    # Invalid font size
    with pytest.raises(ValidationError):
        FormattingStyle(font_size=150)  # Exceeds max 72


# ============================================================================
# 3. TRANSACTION MODEL & LIFECYCLE
# ============================================================================

def test_mutation_transaction_lifecycle():
    """Test full lifecycle state representations of a MutationTransaction."""
    action = SpreadsheetAction(
        action_id="act_1",
        action_type=ActionTypeEnum.WRITE_VALUE,
        sheet_name="Orders",
        target_cell="E100",
        value="Subtotal",
    )
    
    # 1. Creation in PENDING status
    tx = MutationTransaction(
        transaction_id="tx_test_001",
        dataset_id="ds_123",
        sheet_name="Orders",
        user_request="Buatkan subtotal",
        resolved_intent="Write subtotal label in cell E100",
        status=TransactionStatusEnum.PENDING,
        actions=[action],
        created_at="2026-08-26T00:00:00Z",
    )
    assert tx.status == TransactionStatusEnum.PENDING
    assert len(tx.actions) == 1

    # 2. Transition to VALIDATED & EXECUTING
    tx.status = TransactionStatusEnum.VALIDATED
    assert tx.status == TransactionStatusEnum.VALIDATED

    # 3. Snapshotting before and after states
    before_snap = CellSnapshot(coordinate="E100", row=100, col=5, original_value=None, is_empty=True)
    after_snap = CellSnapshot(coordinate="E100", row=100, col=5, original_value="Subtotal", is_empty=False)
    
    tx.before_state["E100"] = before_snap
    tx.after_state["E100"] = after_snap
    tx.diff.append(StateDiff(target_ref="E100", before=before_snap, after=after_snap))

    assert len(tx.diff) == 1
    assert tx.diff[0].before.is_empty is True
    assert tx.diff[0].after.original_value == "Subtotal"

    # 4. Attach Verification Report
    v_report = VerificationReport(
        is_verified=True,
        total_cells_checked=1,
        planned_modifications_count=1,
        actual_modifications_count=1,
        diff_matches_plan=True,
        failures=[],
        verified_expected_value="Subtotal",
        actual_evaluated_value="Subtotal",
        source_integrity_intact=True,
    )
    tx.verification_report = v_report
    tx.status = TransactionStatusEnum.COMMITTED
    tx.committed_at = "2026-08-26T00:00:01Z"

    assert tx.status == TransactionStatusEnum.COMMITTED
    assert tx.verification_report.is_verified is True


def test_transaction_rollback_representation():
    """Test failed verification and atomic rollback representation."""
    tx = MutationTransaction(
        transaction_id="tx_rollback_001",
        dataset_id="ds_123",
        sheet_name="Orders",
        user_request="Buatkan total",
        resolved_intent="Write formula in D100",
        status=TransactionStatusEnum.VERIFICATION_FAILED,
        created_at="2026-08-26T00:00:00Z",
    )
    
    # Mark rollback
    tx.status = TransactionStatusEnum.ROLLED_BACK
    tx.rolled_back_at = "2026-08-26T00:00:02Z"
    tx.rollback_reason = "Verification failure: evaluated value 0.0 does not match expected 250000.0"

    assert tx.status == TransactionStatusEnum.ROLLED_BACK
    assert "Verification failure" in tx.rollback_reason


# ============================================================================
# 4. VERIFICATION FAILURE REASONS & AGENT RESULTS
# ============================================================================

def test_verification_failure_reasons():
    """Verify all verification failure reasons are explicitly defined."""
    reasons = {
        VerificationFailureReason.FORMULA_SYNTAX_ERROR,
        VerificationFailureReason.FORMULA_RESULT_MISMATCH,
        VerificationFailureReason.CIRCULAR_REFERENCE,
        VerificationFailureReason.UNINTENDED_CELL_MODIFIED,
        VerificationFailureReason.TARGET_CELL_MISSING,
        VerificationFailureReason.SOURCE_DATA_CORRUPTED,
        VerificationFailureReason.OVERWRITE_COLLISION,
        VerificationFailureReason.STYLE_APPLICATION_FAILED,
        VerificationFailureReason.PERSISTENCE_MISMATCH,
    }
    assert len(reasons) == 9


def test_agent_execution_result_statuses():
    """Test AgentExecutionResult across outcome statuses."""
    res_success = AgentExecutionResult(
        status=AgentResponseStatusEnum.SUCCESS,
        message="Total sales formula created in D102 and verified.",
        affected_ranges=["C102:D102"],
        execution_time_ms=45.2,
    )
    assert res_success.status == AgentResponseStatusEnum.SUCCESS

    res_clarify = AgentExecutionResult(
        status=AgentResponseStatusEnum.CLARIFICATION,
        message="Multiple candidate sales columns found: 'Sales' and 'Net Sales'.",
        clarification={"candidates": ["Sales", "Net Sales"]},
    )
    assert res_clarify.status == AgentResponseStatusEnum.CLARIFICATION
    assert res_clarify.clarification["candidates"] == ["Sales", "Net Sales"]


# ============================================================================
# 5. STRUCTURED MEMORY CONTRACT
# ============================================================================

def test_structured_memory_state():
    """Test structured memory model scopes and serialization."""
    turn = ConversationTurn(
        turn_id="turn_01",
        user_query="Berapa penjualan 2018?",
        agent_intent="Calculate total sales in 2018",
        status="SUCCESS",
        timestamp="2026-08-26T00:00:00Z",
    )
    wb_pref = WorkbookPreference(
        dataset_id="ds_superstore",
        sheet_name="Orders",
        confirmed_column_mappings={"penjualan": "Sales", "omset": "Sales"},
        preferred_summary_anchors={"Sales": "bottom"},
        updated_at="2026-08-26T00:00:00Z",
    )
    user_pref = UserPreferenceProfile(
        locale="id-ID",
        currency_symbol="Rp",
        default_number_format="Rp#,##0",
        preferred_theme="dark",
    )
    audit = TransactionAuditRecord(
        transaction_id="tx_01",
        dataset_id="ds_superstore",
        sheet_name="Orders",
        timestamp="2026-08-26T00:00:00Z",
        user_request="Total sales",
        resolved_intent="Write total",
        action_types=["WRITE_VALUE", "WRITE_FORMULA"],
        affected_cells=["C102", "D102"],
        status="COMMITTED",
        verified=True,
        rolled_back=False,
    )

    mem_state = StructuredMemoryState(
        conversation_memory=[turn],
        workbook_memory={"ds_superstore": wb_pref},
        user_preferences=user_pref,
        task_history=[audit],
    )

    assert len(mem_state.conversation_memory) == 1
    assert mem_state.workbook_memory["ds_superstore"].confirmed_column_mappings["penjualan"] == "Sales"
    assert mem_state.user_preferences.currency_symbol == "Rp"
    assert mem_state.task_history[0].verified is True


# ============================================================================
# 6. JSON SERIALIZATION & BACKWARD COMPATIBILITY
# ============================================================================

def test_json_roundtrip_serialization():
    """Test JSON serialization and deserialization across all Phase 1 models."""
    action = SpreadsheetAction(
        action_id="act_json",
        action_type=ActionTypeEnum.WRITE_FORMULA,
        sheet_name="Orders",
        target_cell="D102",
        formula="=SUM(D2:D101)",
        style=FormattingStyle(bold=True, fill_color="#FFFF00"),
        expected_result=12345.67,
    )
    json_str = action.model_dump_json()
    action_recovered = SpreadsheetAction.model_validate_json(json_str)

    assert action_recovered.action_id == action.action_id
    assert action_recovered.formula == "=SUM(D2:D101)"
    assert action_recovered.style.fill_color == "yellow" or action_recovered.style.fill_color == "#FFFF00"
    assert action_recovered.expected_result == 12345.67


def test_backward_compatibility_with_existing_schemas():
    """Verify that importing and using new Phase 1 models causes zero conflicts with existing analytical models."""
    # Existing TableRegion and AnalyticalInstruction
    existing_inst = AnalyticalInstruction(
        operation=OperationEnum.SUM,
        dataset_id="ds_test",
        sheet_name="Sheet1",
        target_column="Sales",
    )
    assert existing_inst.operation == OperationEnum.SUM

    # Coexistence with SpreadsheetAction
    agent_action = SpreadsheetAction(
        action_id="act_coexist",
        action_type=ActionTypeEnum.WRITE_VALUE,
        sheet_name="Sheet1",
        target_cell="A1",
        value="Header",
    )
    assert agent_action.action_type == ActionTypeEnum.WRITE_VALUE
