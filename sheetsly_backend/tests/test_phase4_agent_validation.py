"""Comprehensive unit and matrix test suite for Phase 4:
Spreadsheet Agent Action DSL, Action Validator, Formula Validator, Security Boundaries & Scope Preservation.
"""

import pytest

from app.engine.agent import (
    ActionTypeEnum,
    FormattingStyle,
    SpreadsheetAction,
    SUPPORTED_ACTION_REGISTRY,
)
from app.engine.agent.action_validator import (
    ActionSequenceValidationResult,
    ActionValidationResult,
    ActionValidator,
)
from app.engine.agent.formula_validator import (
    FormulaValidationResult,
    FormulaValidator,
    SUPPORTED_FORMULA_FUNCTIONS,
)
from app.engine.agent.transaction_model import AgentResponseStatusEnum
from app.engine.parser.sheet_reader import RawSheetGrid
from app.engine.profiler.workbook_index import (
    ColumnIndexEntry,
    SheetIndexEntry,
    TableIndexEntry,
    WorkbookMetadataIndex,
)
from app.models.schemas import CellCoordinate, CellData, DataTypeEnum, SemanticTypeEnum


def _create_mock_index_and_grid():
    """Builds a test workbook index with Sales (float) and CustomerName (string) columns and a mock grid."""
    col_sales = ColumnIndexEntry(
        index=0, name="Sales", normalized_name="sales", source_column_letter="D",
        data_type=DataTypeEnum.FLOAT, semantic_type=SemanticTypeEnum.NUMERIC_MEASURE,
        total_count=100, unique_count=90, sample_values=[100.0, 200.0],
    )
    col_cust = ColumnIndexEntry(
        index=1, name="CustomerName", normalized_name="customername", source_column_letter="B",
        data_type=DataTypeEnum.STRING, semantic_type=SemanticTypeEnum.TEXT,
        total_count=100, unique_count=50, sample_values=["Alice", "Bob"],
    )
    tbl = TableIndexEntry(
        table_id="tbl_orders", name="Orders Table", sheet_name="Orders",
        range_address="A1:E101", header_range="A1:E1", data_range="A2:E101",
        row_count=100, column_count=5, columns=[col_sales, col_cust],
    )
    sheet = SheetIndexEntry(
        name="Orders", index=0, total_rows=101, total_columns=5,
        used_range="A1:E101", tables=[tbl],
    )
    index = WorkbookMetadataIndex(
        dataset_id="ds_agent_test", filename="Store.xlsx",
        sheet_count=1, sheet_names=["Orders"], active_sheet_name="Orders",
        sheets={"Orders": sheet},
    )

    # Mock RawSheetGrid with an occupied cell at D50
    grid = RawSheetGrid(
        sheet_name="Orders", min_row=1, max_row=101, min_col=1, max_col=5,
        cells={
            (50, 4): CellData(coordinate=CellCoordinate(row=50, column=4, cell_ref="D50", col_letter="D"), original_value=999.5, is_empty=False),
        }
    )

    return index, grid


# ============================================================================
# 1. FORMULA VALIDATION & SECURITY TESTS
# ============================================================================

def test_formula_valid_sum():
    """Verify valid SUM formula passes validation cleanly."""
    index, _ = _create_mock_index_and_grid()
    res = FormulaValidator.validate_formula(
        formula="=SUM(D2:D101)",
        target_cell="D102",
        sheet_name="Orders",
        workbook_index=index,
        table_entry=index.sheets["Orders"].tables[0],
    )
    assert res.is_valid is True
    assert res.is_safe is True
    assert res.function_name == "SUM"
    assert res.referenced_ranges == ["D2:D101"]


def test_formula_circular_reference_rejected():
    """Verify formula referencing its own target cell is detected as circular and rejected."""
    index, _ = _create_mock_index_and_grid()
    res = FormulaValidator.validate_formula(
        formula="=SUM(D2:D150)",  # Target D102 is inside D2:D150
        target_cell="D102",
        sheet_name="Orders",
        workbook_index=index,
    )
    assert res.is_valid is False
    assert res.is_circular is True
    assert "Circular reference" in res.error_message


def test_formula_security_dde_injection_rejected():
    """Verify DDE injection payloads are rejected unconditionally."""
    res = FormulaValidator.validate_formula(
        formula="=cmd|'/C calc'!A0",
        target_cell="D102",
        sheet_name="Orders",
    )
    assert res.is_valid is False
    assert res.is_safe is False
    assert "POTENTIAL_FORMULA_INJECTION_OR_DDE" in res.security_warnings


def test_formula_security_external_workbook_rejected():
    """Verify references to external workbooks are rejected."""
    res = FormulaValidator.validate_formula(
        formula="=SUM([OtherBook.xlsx]Sheet1!A1:A10)",
        target_cell="D102",
        sheet_name="Orders",
    )
    assert res.is_valid is False
    assert res.is_safe is False


def test_formula_arithmetic_on_text_column_rejected():
    """Verify arithmetic aggregation (SUM) on text column is rejected by semantic check."""
    index, _ = _create_mock_index_and_grid()
    res = FormulaValidator.validate_formula(
        formula="=SUM(B2:B101)",  # Column B is CustomerName (String/Text)
        target_cell="B102",
        sheet_name="Orders",
        workbook_index=index,
        table_entry=index.sheets["Orders"].tables[0],
    )
    assert res.is_valid is False
    assert "non-numeric text column" in res.error_message


# ============================================================================
# 2. ACTION VALIDATOR PER-ACTION TESTS
# ============================================================================

def test_action_write_value_valid_and_collision():
    """Test WRITE_VALUE validation and collision detection on occupied cells."""
    index, grid = _create_mock_index_and_grid()

    # Empty cell -> valid
    act_empty = SpreadsheetAction(
        action_id="act_val_1",
        action_type=ActionTypeEnum.WRITE_VALUE,
        sheet_name="Orders",
        target_cell="C102",
        value="Total",
    )
    res_empty = ActionValidator.validate_action(act_empty, index, grid)
    assert res_empty.is_valid is True
    assert res_empty.status == AgentResponseStatusEnum.SUCCESS

    # Occupied cell D50 -> triggers clarification request
    act_occupied = SpreadsheetAction(
        action_id="act_val_2",
        action_type=ActionTypeEnum.WRITE_VALUE,
        sheet_name="Orders",
        target_cell="D50",
        value="Override",
    )
    res_occupied = ActionValidator.validate_action(act_occupied, index, grid)
    assert res_occupied.is_valid is False
    assert res_occupied.status == AgentResponseStatusEnum.CLARIFICATION
    assert res_occupied.clarification_request is not None


def test_action_write_formula_validation():
    """Test WRITE_FORMULA action validation."""
    index, grid = _create_mock_index_and_grid()
    act = SpreadsheetAction(
        action_id="act_f_1",
        action_type=ActionTypeEnum.WRITE_FORMULA,
        sheet_name="Orders",
        target_cell="D102",
        formula="=SUM(D2:D101)",
    )
    res = ActionValidator.validate_action(act, index, grid)
    assert res.is_valid is True


def test_action_insert_row_and_column_validation():
    """Test INSERT_ROW and INSERT_COLUMN index validation."""
    act_row_valid = SpreadsheetAction(
        action_id="act_r_1", action_type=ActionTypeEnum.INSERT_ROW,
        sheet_name="Orders", row_index=10,
    )
    assert ActionValidator.validate_action(act_row_valid).is_valid is True

    act_col_valid = SpreadsheetAction(
        action_id="act_c_1", action_type=ActionTypeEnum.INSERT_COLUMN,
        sheet_name="Orders", column_index=3,
    )
    assert ActionValidator.validate_action(act_col_valid).is_valid is True


def test_action_format_range_scope_preservation():
    """Verify FORMAT_RANGE rejects oversized ranges that violate scope preservation."""
    index, _ = _create_mock_index_and_grid()
    act_massive = SpreadsheetAction(
        action_id="act_fmt_massive",
        action_type=ActionTypeEnum.FORMAT_RANGE,
        sheet_name="Orders",
        target_range="A1:Z50000",  # Massive 50,000 row scope
        style=FormattingStyle(bold=True),
    )
    res = ActionValidator.validate_action(act_massive, index)
    assert res.is_valid is False
    assert "Scope violation" in res.error_message


def test_action_clear_content_whole_sheet_clarification():
    """Verify CLEAR_CONTENT on entire sheet data range triggers clarification."""
    index, _ = _create_mock_index_and_grid()
    act_clear_all = SpreadsheetAction(
        action_id="act_clear_1",
        action_type=ActionTypeEnum.CLEAR_CONTENT,
        sheet_name="Orders",
        target_range="A1:E101",  # Whole sheet used range
    )
    res = ActionValidator.validate_action(act_clear_all, index)
    assert res.is_valid is False
    assert res.status == AgentResponseStatusEnum.CLARIFICATION


# ============================================================================
# 3. ACTION SEQUENCE VALIDATION TESTS
# ============================================================================

def test_action_sequence_valid():
    """Verify ordered multi-action sequence validates cleanly."""
    index, grid = _create_mock_index_and_grid()
    actions = [
        SpreadsheetAction(action_id="a1", action_type=ActionTypeEnum.WRITE_VALUE, sheet_name="Orders", target_cell="C102", value="Total Sales"),
        SpreadsheetAction(action_id="a2", action_type=ActionTypeEnum.WRITE_FORMULA, sheet_name="Orders", target_cell="D102", formula="=SUM(D2:D101)"),
        SpreadsheetAction(action_id="a3", action_type=ActionTypeEnum.FORMAT_RANGE, sheet_name="Orders", target_range="C102:D102", style=FormattingStyle(bold=True, fill_color="#F1F5F9")),
        SpreadsheetAction(action_id="a4", action_type=ActionTypeEnum.SET_NUMBER_FORMAT, sheet_name="Orders", target_cell="D102", number_format="$#,##0.00"),
    ]
    res = ActionValidator.validate_sequence(actions, index, grid)
    assert res.is_valid is True
    assert res.total_actions == 4
    assert res.valid_actions_count == 4


def test_action_sequence_duplicate_action_id_rejected():
    """Verify sequence with duplicate action_id is rejected."""
    actions = [
        SpreadsheetAction(action_id="dup_id", action_type=ActionTypeEnum.WRITE_VALUE, sheet_name="Orders", target_cell="C102", value="Total"),
        SpreadsheetAction(action_id="dup_id", action_type=ActionTypeEnum.WRITE_FORMULA, sheet_name="Orders", target_cell="D102", formula="=SUM(D2:D101)"),
    ]
    res = ActionValidator.validate_sequence(actions)
    assert res.is_valid is False
    assert "Duplicate action_id" in res.error_message


def test_action_sequence_empty_rejected():
    """Verify empty action list is rejected."""
    res = ActionValidator.validate_sequence([])
    assert res.is_valid is False
    assert "Empty action list" in res.error_message
