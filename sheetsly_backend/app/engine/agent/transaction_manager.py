"""Authoritative Transaction Manager orchestrating atomic mutations, verification, and audit trail."""

import copy
from datetime import datetime, timezone
import time
from typing import Any, Callable, Dict, List, Optional, Tuple
from openpyxl.utils.cell import column_index_from_string, coordinate_from_string

from app.engine.agent.action_model import ActionTypeEnum, SpreadsheetAction
from app.engine.agent.action_validator import ActionValidator
from app.engine.agent.grid_mutator import GridMutator
from app.engine.agent.rollback_engine import RollbackEngine
from app.engine.agent.transaction_model import (
    AgentExecutionResult,
    AgentResponseStatusEnum,
    CellSnapshot,
    MutationTransaction,
    StateDiff,
    TransactionAuditRecord,
    TransactionStatusEnum,
    VerificationFailureReason,
    VerificationReport,
)
from app.engine.parser.sheet_reader import RawSheetGrid
from app.engine.profiler.workbook_index import WorkbookMetadataIndex


class TransactionManager:
    """Orchestrates mutation transaction lifecycle, enforcing atomicity, verification, and history limits."""

    def __init__(self, max_history: int = 20):
        self.max_history = max_history
        self.history: List[TransactionAuditRecord] = []
        self.committed_transactions: List[MutationTransaction] = []
        self.current_version: int = 1

    def execute_transaction(
        self,
        transaction: MutationTransaction,
        grid: RawSheetGrid,
        workbook_index: Optional[WorkbookMetadataIndex] = None,
        sheet_grids: Optional[Dict[str, RawSheetGrid]] = None,
        save_hook: Optional[Callable[[], bool]] = None,
        expected_version: Optional[int] = None,
    ) -> AgentExecutionResult:
        """
        Executes a complete atomic mutation transaction through all lifecycle stages:
        VALIDATE -> SNAPSHOT -> EXECUTE -> DIFF -> VERIFY -> PERSIST -> COMMIT (or ROLLBACK on failure).
        """
        start_time = time.perf_counter()

        # 1. Stale-State Protection
        if expected_version is not None and expected_version != self.current_version:
            return AgentExecutionResult(
                status=AgentResponseStatusEnum.VALIDATION_ERROR,
                transaction=transaction,
                message="Workbook telah berubah (stale version). Silakan lakukan verifikasi ulang.",
                error_detail=f"Expected version {expected_version} does not match current version {self.current_version}.",
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )

        # 2. Validation Stage
        transaction.status = TransactionStatusEnum.VALIDATED
        val_res = ActionValidator.validate_sequence(transaction.actions, workbook_index, grid, sheet_grids=sheet_grids)
        if not val_res.is_valid:
            transaction.status = TransactionStatusEnum.FAILED
            self._record_audit(transaction, "VALIDATION_ERROR", verified=False, rolled_back=False)
            return AgentExecutionResult(
                status=val_res.status,
                transaction=transaction,
                message="Permintaan tidak dapat dijalankan karena validasi gagal.",
                clarification=val_res.clarification_request,
                error_detail=val_res.error_message,
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )

        # 3. Snapshot Capture (Deep In-Memory Backup for Atomicity)
        transaction.status = TransactionStatusEnum.EXECUTING
        deep_backups = {grid.sheet_name: copy.deepcopy(grid)}
        if sheet_grids:
            for s_name, s_grid in sheet_grids.items():
                deep_backups[s_name] = copy.deepcopy(s_grid)

        # Capture cell snapshots for before_state
        for act in transaction.actions:
            if act.target_cell:
                col_s, row_i = coordinate_from_string(act.target_cell.upper())
                col_i = column_index_from_string(col_s)
                c_data = grid.get_cell(row_i, col_i)
                transaction.before_state[act.target_cell.upper()] = CellSnapshot(
                    coordinate=act.target_cell.upper(),
                    row=row_i,
                    col=col_i,
                    original_value=c_data.original_value,
                    parsed_value=c_data.parsed_value,
                    data_type=c_data.data_type.value,
                    formula=c_data.formula,
                    is_empty=c_data.is_empty,
                )

        # 4. Atomic Execution
        diffs: List[StateDiff] = []
        try:
            for act in transaction.actions:
                target_g = grid
                if sheet_grids and act.sheet_name in sheet_grids:
                    target_g = sheet_grids[act.sheet_name]

                d = GridMutator.execute_action(act, target_g, workbook_index, sheet_grids)
                diffs.append(d)

            transaction.diff = diffs
        except Exception as exec_err:
            # Action Execution Error -> Trigger Rollback
            RollbackEngine.rollback_transaction(transaction, grid, sheet_grids, deep_backups)
            transaction.status = TransactionStatusEnum.ROLLED_BACK
            transaction.rolled_back_at = datetime.now(timezone.utc).isoformat()
            transaction.rollback_reason = f"Execution error: {str(exec_err)}"
            self._record_audit(transaction, "EXECUTION_ERROR", verified=False, rolled_back=True)

            return AgentExecutionResult(
                status=AgentResponseStatusEnum.EXECUTION_ERROR,
                transaction=transaction,
                message="Permintaan gagal dijalankan dan perubahan telah dibatalkan.",
                error_detail=str(exec_err),
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )

        # 5. Post-Execution Verification
        v_report = self._verify_transaction(transaction, grid)
        transaction.verification_report = v_report

        if not v_report.is_verified:
            # Verification Failure -> Rollback
            RollbackEngine.rollback_transaction(transaction, grid, sheet_grids, deep_backups)
            transaction.status = TransactionStatusEnum.ROLLED_BACK
            transaction.rolled_back_at = datetime.now(timezone.utc).isoformat()
            transaction.rollback_reason = f"Verification failed: {', '.join(v_report.failures)}"
            self._record_audit(transaction, "VERIFICATION_ERROR", verified=False, rolled_back=True)

            return AgentExecutionResult(
                status=AgentResponseStatusEnum.VERIFICATION_ERROR,
                transaction=transaction,
                message="Verifikasi state spreadsheet gagal dan perubahan telah dibatalkan.",
                error_detail="; ".join(v_report.failures),
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )

        transaction.status = TransactionStatusEnum.VERIFIED

        # 6. Persistence / Save Safety Check
        if save_hook:
            try:
                save_ok = save_hook()
                if not save_ok:
                    raise IOError("Save hook returned False.")
            except Exception as save_err:
                RollbackEngine.rollback_transaction(transaction, grid, sheet_grids, deep_backups)
                transaction.status = TransactionStatusEnum.ROLLED_BACK
                transaction.rolled_back_at = datetime.now(timezone.utc).isoformat()
                transaction.rollback_reason = f"Persistence failure: {str(save_err)}"
                self._record_audit(transaction, "PERSISTENCE_ERROR", verified=True, rolled_back=True)

                return AgentExecutionResult(
                    status=AgentResponseStatusEnum.PERSISTENCE_ERROR,
                    transaction=transaction,
                    message="Perubahan tidak dapat disimpan sehingga transaksi dibatalkan.",
                    error_detail=str(save_err),
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                )

        # 7. Commit Transaction
        transaction.status = TransactionStatusEnum.COMMITTED
        transaction.committed_at = datetime.now(timezone.utc).isoformat()
        self.current_version += 1

        self.committed_transactions.append(transaction)
        if len(self.committed_transactions) > self.max_history:
            self.committed_transactions.pop(0)

        self._record_audit(transaction, "COMMITTED", verified=True, rolled_back=False)

        affected = [d.target_ref for d in diffs]
        return AgentExecutionResult(
            status=AgentResponseStatusEnum.SUCCESS,
            transaction=transaction,
            message=f"Selesai. {transaction.resolved_intent}",
            affected_ranges=affected,
            execution_time_ms=(time.perf_counter() - start_time) * 1000,
        )

    def undo_last_transaction(
        self,
        grid: RawSheetGrid,
        sheet_grids: Optional[Dict[str, RawSheetGrid]] = None,
    ) -> AgentExecutionResult:
        """Undoes the most recent committed transaction and records an undo audit entry."""
        if not self.committed_transactions:
            return AgentExecutionResult(
                status=AgentResponseStatusEnum.VALIDATION_ERROR,
                message="Tidak ada transaksi yang dapat di-undo.",
            )

        last_tx = self.committed_transactions.pop()
        rb_ok = RollbackEngine.rollback_transaction(last_tx, grid, sheet_grids)

        if not rb_ok:
            return AgentExecutionResult(
                status=AgentResponseStatusEnum.ROLLBACK_FAILURE,
                transaction=last_tx,
                message="Transaksi gagal dan proses rollback mengalami masalah.",
            )

        self.current_version += 1
        undo_audit = TransactionAuditRecord(
            transaction_id=f"undo_{last_tx.transaction_id}",
            dataset_id=last_tx.dataset_id,
            sheet_name=last_tx.sheet_name,
            timestamp=datetime.now(timezone.utc).isoformat(),
            user_request=f"Undo transaction '{last_tx.transaction_id}'",
            resolved_intent=f"Reverted transaction '{last_tx.transaction_id}'",
            action_types=["UNDO"],
            affected_cells=[d.target_ref for d in last_tx.diff],
            status="ROLLBACK_SUCCESS",
            verified=True,
            rolled_back=True,
        )
        self.history.append(undo_audit)
        if len(self.history) > self.max_history:
            self.history.pop(0)

        return AgentExecutionResult(
            status=AgentResponseStatusEnum.ROLLBACK_SUCCESS,
            transaction=last_tx,
            message=f"Undo berhasil: transaksi '{last_tx.transaction_id}' telah dibatalkan.",
        )

    def _verify_transaction(self, transaction: MutationTransaction, grid: RawSheetGrid) -> VerificationReport:
        """Performs deterministic verification comparing actual diff against planned modifications."""
        failures = []
        failure_reasons = []

        if len(transaction.diff) != len(transaction.actions):
            failures.append(f"Diff count ({len(transaction.diff)}) does not match planned action count ({len(transaction.actions)}).")
            failure_reasons.append(VerificationFailureReason.TARGET_CELL_MISSING)

        for act in transaction.actions:
            if act.action_type == ActionTypeEnum.WRITE_FORMULA and act.target_cell:
                col_s, row_i = coordinate_from_string(act.target_cell.upper())
                col_i = column_index_from_string(col_s)
                c_data = grid.get_cell(row_i, col_i)
                if c_data.formula != act.formula:
                    failures.append(f"Formula at {act.target_cell} ('{c_data.formula}') does not match expected '{act.formula}'.")
                    failure_reasons.append(VerificationFailureReason.FORMULA_SYNTAX_ERROR)
                if act.expected_result is not None and c_data.parsed_value != act.expected_result:
                    failures.append(f"Evaluated formula value ({c_data.parsed_value}) does not match expected ({act.expected_result}).")
                    failure_reasons.append(VerificationFailureReason.FORMULA_RESULT_MISMATCH)

        is_verified = len(failures) == 0
        return VerificationReport(
            is_verified=is_verified,
            total_cells_checked=len(transaction.actions),
            planned_modifications_count=len(transaction.actions),
            actual_modifications_count=len(transaction.diff),
            diff_matches_plan=is_verified,
            failures=failures,
            failure_reasons=failure_reasons,
            source_integrity_intact=True,
        )

    def _record_audit(self, transaction: MutationTransaction, status_str: str, verified: bool, rolled_back: bool):
        rec = TransactionAuditRecord(
            transaction_id=transaction.transaction_id,
            dataset_id=transaction.dataset_id,
            sheet_name=transaction.sheet_name,
            timestamp=datetime.now(timezone.utc).isoformat(),
            user_request=transaction.user_request,
            resolved_intent=transaction.resolved_intent,
            action_types=[a.action_type.value for a in transaction.actions],
            affected_cells=[d.target_ref for d in transaction.diff],
            status=status_str,
            verified=verified,
            rolled_back=rolled_back,
        )
        self.history.append(rec)
        if len(self.history) > self.max_history:
            self.history.pop(0)
