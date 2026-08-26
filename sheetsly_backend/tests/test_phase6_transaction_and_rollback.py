"""Comprehensive unit and integration test suite for Phase 6:
Transaction Manager, State Diff, Verification Report, Atomic Rollback, Persistence Safety & Undo.
"""

from datetime import datetime, timezone
import pytest

from app.engine.agent import (
    ActionTypeEnum,
    AgentExecutionResult,
    AgentResponseStatusEnum,
    FormattingStyle,
    MutationTransaction,
    RollbackEngine,
    SpreadsheetAction,
    TransactionManager,
    TransactionStatusEnum,
)
from app.engine.parser.sheet_reader import RawSheetGrid
from app.engine.profiler.workbook_index import (
    ColumnIndexEntry,
    SheetIndexEntry,
    TableIndexEntry,
    WorkbookMetadataIndex,
)
from app.models.schemas import CellCoordinate, CellData, DataTypeEnum, SemanticTypeEnum


def _create_test_environment(row_count: int = 5):
    """Builds a test workbook index and populated grid."""
    cells_orders = {}
    for r in range(1, row_count + 2):
        for c in range(1, 6):
            col_let = chr(ord("A") + c - 1)
            val = f"H_{col_let}" if r == 1 else (100.0 * r if c == 4 else f"D_{r}_{c}")
            dt = DataTypeEnum.STRING if (r == 1 or c != 4) else DataTypeEnum.FLOAT
            cells_orders[(r, c)] = CellData(
                coordinate=CellCoordinate(row=r, column=c, cell_ref=f"{col_let}{r}", col_letter=col_let),
                original_value=val,
                parsed_value=val,
                data_type=dt,
                is_empty=False,
            )

    grid_orders = RawSheetGrid(
        sheet_name="Orders", min_row=1, max_row=row_count + 1, min_col=1, max_col=5,
        cells=cells_orders,
    )

    grid_summary = RawSheetGrid(
        sheet_name="Summary", min_row=1, max_row=5, min_col=1, max_col=5,
        cells={
            (1, 1): CellData(coordinate=CellCoordinate(row=1, column=1, cell_ref="A1", col_letter="A"), original_value="Title", parsed_value="Title", data_type=DataTypeEnum.STRING, is_empty=False)
        },
    )

    tbl = TableIndexEntry(
        table_id="tbl_orders", name="Orders Data", sheet_name="Orders",
        range_address=f"A1:E{row_count+1}", header_range="A1:E1", data_range=f"A2:E{row_count+1}",
        row_count=row_count, column_count=5,
        columns=[
            ColumnIndexEntry(index=3, name="Sales", normalized_name="sales", source_column_letter="D", data_type=DataTypeEnum.FLOAT, semantic_type=SemanticTypeEnum.NUMERIC_MEASURE, total_count=row_count, unique_count=row_count, sample_values=[100.0]),
        ],
    )
    sheet_orders = SheetIndexEntry(name="Orders", index=0, total_rows=row_count+1, total_columns=5, used_range=f"A1:E{row_count+1}", tables=[tbl])
    sheet_summary = SheetIndexEntry(name="Summary", index=1, total_rows=5, total_columns=5, used_range="A1:E5", tables=[])

    index = WorkbookMetadataIndex(
        dataset_id="ds_tx_test", filename="Store.xlsx", sheet_count=2,
        sheet_names=["Orders", "Summary"], active_sheet_name="Orders",
        sheets={"Orders": sheet_orders, "Summary": sheet_summary},
    )

    return index, grid_orders, grid_summary


# ============================================================================
# 1. HAPPY PATH TRANSACTION EXECUTION & AUDIT RECORDING
# ============================================================================

def test_transaction_happy_path_commit():
    """Verify standard multi-action transaction completes with COMMITTED status and valid audit record."""
    index, grid_orders, _ = _create_test_environment(row_count=5)
    tx_manager = TransactionManager(max_history=10)

    tx = MutationTransaction(
        transaction_id="tx_001",
        dataset_id="ds_tx_test",
        sheet_name="Orders",
        user_request="buatkan total penjualan",
        resolved_intent="Calculate total sales and format result",
        created_at=datetime.now(timezone.utc).isoformat(),
        actions=[
            SpreadsheetAction(action_id="a1", action_type=ActionTypeEnum.WRITE_VALUE, sheet_name="Orders", target_cell="C7", value="Total Sales"),
            SpreadsheetAction(action_id="a2", action_type=ActionTypeEnum.WRITE_FORMULA, sheet_name="Orders", target_cell="D7", formula="=SUM(D2:D6)", expected_result=2000.0),
            SpreadsheetAction(action_id="a3", action_type=ActionTypeEnum.FORMAT_RANGE, sheet_name="Orders", target_range="C7:D7", style=FormattingStyle(bold=True)),
        ],
    )

    result = tx_manager.execute_transaction(tx, grid_orders, index)

    assert result.status == AgentResponseStatusEnum.SUCCESS
    assert tx.status == TransactionStatusEnum.COMMITTED
    assert tx_manager.current_version == 2
    assert len(tx_manager.committed_transactions) == 1
    assert len(tx_manager.history) == 1
    assert tx_manager.history[0].status == "COMMITTED"
    assert grid_orders.get_cell(7, 4).parsed_value == 2000.0


# ============================================================================
# 2. ATOMIC ROLLBACK ON ACTION EXECUTION FAILURE
# ============================================================================

def test_transaction_atomic_rollback_on_middle_action_failure():
    """Verify that when action 2 of 3 fails, action 1 is completely rolled back leaving zero partial state."""
    index, grid_orders, _ = _create_test_environment(row_count=5)
    tx_manager = TransactionManager()

    # Initial state of cell C7 (empty)
    assert grid_orders.get_cell(7, 3).is_empty is True

    # Action 2 targets non-existent sheet or invalid coordinate causing failure during execution
    tx = MutationTransaction(
        transaction_id="tx_fail_002",
        dataset_id="ds_tx_test",
        sheet_name="Orders",
        user_request="test atomic failure",
        resolved_intent="Test partial rollback",
        created_at=datetime.now(timezone.utc).isoformat(),
        actions=[
            SpreadsheetAction(action_id="a1", action_type=ActionTypeEnum.WRITE_VALUE, sheet_name="Orders", target_cell="C7", value="Temporary Label"),
            # Malformed formula without sheet validation will raise in grid mutator
            SpreadsheetAction(action_id="a2", action_type=ActionTypeEnum.WRITE_FORMULA, sheet_name="NonExistentSheet", target_cell="D7", formula="=SUM(D2:D6)"),
        ],
    )

    result = tx_manager.execute_transaction(tx, grid_orders, index)

    assert result.status in {AgentResponseStatusEnum.EXECUTION_ERROR, AgentResponseStatusEnum.VALIDATION_ERROR}
    # VERIFY ATOMICITY: Cell C7 must remain empty (no partial state left!)
    assert grid_orders.get_cell(7, 3).is_empty is True
    assert (7, 3) not in grid_orders.cells or grid_orders.cells[(7, 3)].is_empty is True


# ============================================================================
# 3. ATOMIC ROLLBACK ON POST-EXECUTION VERIFICATION FAILURE
# ============================================================================

def test_transaction_rollback_on_verification_mismatch():
    """Verify rollback when expected formula result does not match actual evaluated value."""
    index, grid_orders, _ = _create_test_environment(row_count=5)
    tx_manager = TransactionManager()

    tx = MutationTransaction(
        transaction_id="tx_verify_fail",
        dataset_id="ds_tx_test",
        sheet_name="Orders",
        user_request="test verification failure",
        resolved_intent="Test formula result mismatch",
        created_at=datetime.now(timezone.utc).isoformat(),
        actions=[
            SpreadsheetAction(
                action_id="a1", action_type=ActionTypeEnum.WRITE_FORMULA,
                sheet_name="Orders", target_cell="D7", formula="=SUM(D2:D6)",
                expected_result=999999.0,  # Deliberate mismatch (actual is 1400.0)
            ),
        ],
    )

    result = tx_manager.execute_transaction(tx, grid_orders, index)

    assert result.status == AgentResponseStatusEnum.VERIFICATION_ERROR
    assert tx.status == TransactionStatusEnum.ROLLED_BACK
    # Cell D7 must be restored to empty
    assert grid_orders.get_cell(7, 4).is_empty is True


# ============================================================================
# 4. PERSISTENCE / SAVE SAFETY AND ROLLBACK
# ============================================================================

def test_transaction_rollback_on_persistence_failure():
    """Verify rollback when save hook fails, preventing false SUCCESS claims."""
    index, grid_orders, _ = _create_test_environment(row_count=5)
    tx_manager = TransactionManager()

    def failing_save_hook():
        raise IOError("Disk full or permission denied during workbook save.")

    tx = MutationTransaction(
        transaction_id="tx_persist_fail",
        dataset_id="ds_tx_test",
        sheet_name="Orders",
        user_request="save failure test",
        resolved_intent="Test save safety",
        created_at=datetime.now(timezone.utc).isoformat(),
        actions=[
            SpreadsheetAction(action_id="a1", action_type=ActionTypeEnum.WRITE_VALUE, sheet_name="Orders", target_cell="C7", value="Test"),
        ],
    )

    result = tx_manager.execute_transaction(tx, grid_orders, index, save_hook=failing_save_hook)

    assert result.status == AgentResponseStatusEnum.PERSISTENCE_ERROR
    assert tx.status == TransactionStatusEnum.ROLLED_BACK
    # State rolled back
    assert grid_orders.get_cell(7, 3).is_empty is True


# ============================================================================
# 5. UNDO FUNCTIONALITY
# ============================================================================

def test_transaction_undo_execution():
    """Verify undo_last_transaction restores previous state and logs an UNDO audit entry."""
    index, grid_orders, _ = _create_test_environment(row_count=5)
    tx_manager = TransactionManager()

    tx = MutationTransaction(
        transaction_id="tx_to_undo",
        dataset_id="ds_tx_test",
        sheet_name="Orders",
        user_request="add total",
        resolved_intent="Add total label",
        created_at=datetime.now(timezone.utc).isoformat(),
        actions=[
            SpreadsheetAction(action_id="a1", action_type=ActionTypeEnum.WRITE_VALUE, sheet_name="Orders", target_cell="C7", value="Total Sales"),
        ],
    )

    # 1. Commit transaction
    res_commit = tx_manager.execute_transaction(tx, grid_orders, index)
    assert res_commit.status == AgentResponseStatusEnum.SUCCESS
    assert grid_orders.get_cell(7, 3).original_value == "Total Sales"

    # 2. Undo transaction
    res_undo = tx_manager.undo_last_transaction(grid_orders)
    assert res_undo.status == AgentResponseStatusEnum.ROLLBACK_SUCCESS
    assert grid_orders.get_cell(7, 3).is_empty is True
    assert len(tx_manager.history) == 2
    assert tx_manager.history[-1].action_types == ["UNDO"]


# ============================================================================
# 6. STALE-STATE PROTECTION
# ============================================================================

def test_transaction_stale_version_rejection():
    """Verify transaction is rejected if expected version does not match current version."""
    index, grid_orders, _ = _create_test_environment(row_count=5)
    tx_manager = TransactionManager()
    tx_manager.current_version = 5

    tx = MutationTransaction(
        transaction_id="tx_stale",
        dataset_id="ds_tx_test",
        sheet_name="Orders",
        user_request="stale test",
        resolved_intent="Stale version test",
        created_at=datetime.now(timezone.utc).isoformat(),
        actions=[
            SpreadsheetAction(action_id="a1", action_type=ActionTypeEnum.WRITE_VALUE, sheet_name="Orders", target_cell="C7", value="Test"),
        ],
    )

    res = tx_manager.execute_transaction(tx, grid_orders, index, expected_version=3)
    assert res.status == AgentResponseStatusEnum.VALIDATION_ERROR
    assert "stale version" in res.message


# ============================================================================
# 7. MULTI-SHEET TRANSACTION ATOMICITY
# ============================================================================

def test_multi_sheet_transaction_atomicity():
    """Verify cross-sheet transaction reverts both sheets when a later action fails."""
    index, grid_orders, grid_summary = _create_test_environment(row_count=5)
    sheet_grids = {"Orders": grid_orders, "Summary": grid_summary}
    tx_manager = TransactionManager()

    tx = MutationTransaction(
        transaction_id="tx_multi_fail",
        dataset_id="ds_tx_test",
        sheet_name="Orders",
        user_request="multi-sheet atomic test",
        resolved_intent="Cross-sheet transaction",
        created_at=datetime.now(timezone.utc).isoformat(),
        actions=[
            SpreadsheetAction(action_id="a1", action_type=ActionTypeEnum.WRITE_VALUE, sheet_name="Orders", target_cell="C7", value="Total Orders"),
            SpreadsheetAction(action_id="a2", action_type=ActionTypeEnum.WRITE_VALUE, sheet_name="Summary", target_cell="B2", value="Summary Header"),
            # Third action deliberately fails
            SpreadsheetAction(action_id="a3", action_type=ActionTypeEnum.WRITE_FORMULA, sheet_name="NonExistentSheet", target_cell="C2", formula="=SUM(D2:D6)"),
        ],
    )

    res = tx_manager.execute_transaction(tx, grid_orders, index, sheet_grids=sheet_grids)

    assert res.status in {AgentResponseStatusEnum.EXECUTION_ERROR, AgentResponseStatusEnum.VALIDATION_ERROR}
    # Both sheets must be completely restored
    assert grid_orders.get_cell(7, 3).is_empty is True
    assert grid_summary.get_cell(2, 2).is_empty is True


# ============================================================================
# 8. HISTORY LIMIT PURGE BEHAVIOR
# ============================================================================

def test_transaction_history_limit_purge():
    """Verify history and committed transactions purge oldest entries when max_history exceeded."""
    index, grid_orders, _ = _create_test_environment(row_count=5)
    tx_manager = TransactionManager(max_history=3)

    for i in range(1, 6):
        tx = MutationTransaction(
            transaction_id=f"tx_loop_{i}",
            dataset_id="ds_tx_test",
            sheet_name="Orders",
            user_request=f"query {i}",
            resolved_intent=f"intent {i}",
            created_at=datetime.now(timezone.utc).isoformat(),
            actions=[
                SpreadsheetAction(action_id=f"a_{i}", action_type=ActionTypeEnum.WRITE_VALUE, sheet_name="Orders", target_cell=f"C{7+i}", value=f"Val_{i}"),
            ],
        )
        tx_manager.execute_transaction(tx, grid_orders, index)

    assert len(tx_manager.history) == 3
    assert len(tx_manager.committed_transactions) == 3
    assert tx_manager.history[-1].transaction_id == "tx_loop_5"
    assert tx_manager.history[0].transaction_id == "tx_loop_3"


# ============================================================================
# 9. INSERT ROW & CLEAR CONTENT ROLLBACK RESTORATION
# ============================================================================

def test_insert_row_and_clear_content_rollback():
    """Verify rollback properly reverses INSERT_ROW and CLEAR_CONTENT mutations."""
    index, grid_orders, _ = _create_test_environment(row_count=5)
    initial_d3_val = grid_orders.get_cell(3, 4).parsed_value
    tx_manager = TransactionManager()

    tx = MutationTransaction(
        transaction_id="tx_ins_clr_rollback",
        dataset_id="ds_tx_test",
        sheet_name="Orders",
        user_request="insert and clear",
        resolved_intent="Insert and clear test",
        created_at=datetime.now(timezone.utc).isoformat(),
        actions=[
            SpreadsheetAction(action_id="a1", action_type=ActionTypeEnum.INSERT_ROW, sheet_name="Orders", row_index=3),
            SpreadsheetAction(action_id="a2", action_type=ActionTypeEnum.CLEAR_CONTENT, sheet_name="Orders", target_cell="D2"),
            # Deliberate failure on action 3
            SpreadsheetAction(action_id="a3", action_type=ActionTypeEnum.WRITE_FORMULA, sheet_name="NonExistentSheet", target_cell="C2", formula="=SUM(D2:D6)"),
        ],
    )

    res = tx_manager.execute_transaction(tx, grid_orders, index)
    assert res.status in {AgentResponseStatusEnum.EXECUTION_ERROR, AgentResponseStatusEnum.VALIDATION_ERROR}

    # Verify D3 restored to original position and value
    assert grid_orders.get_cell(3, 4).parsed_value == initial_d3_val
    # Verify D2 not cleared
    assert grid_orders.get_cell(2, 4).is_empty is False

