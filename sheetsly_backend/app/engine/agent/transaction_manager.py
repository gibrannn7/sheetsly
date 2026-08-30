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
        self.undone_transactions: List[MutationTransaction] = []
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
        v_report = self._verify_transaction(transaction, grid, sheet_grids)
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

        # 7. Commit Phase
        transaction.status = TransactionStatusEnum.COMMITTED
        transaction.committed_at = datetime.now(timezone.utc).isoformat()
        self.committed_transactions.append(transaction)
        if len(self.committed_transactions) > self.max_history:
            self.committed_transactions.pop(0)

        # New forward mutation invalidates previous redo stack
        self.undone_transactions.clear()

        self.current_version += 1
        transaction.version_after = self.current_version
        self._record_audit(transaction, "COMMITTED", verified=True, rolled_back=False)

        affected = [d.target_ref for d in diffs]
        return AgentExecutionResult(
            status=AgentResponseStatusEnum.SUCCESS,
            transaction=transaction,
            message=transaction.resolved_intent or "Operasi spreadsheet berhasil dieksekusi dan diverifikasi.",
            affected_ranges=affected,
            execution_time_ms=(time.perf_counter() - start_time) * 1000,
        )

    def undo_last_transaction(
        self,
        grid: RawSheetGrid,
        sheet_grids: Optional[Dict[str, RawSheetGrid]] = None,
        is_english: bool = False,
    ) -> AgentExecutionResult:
        """Rolls back the most recently committed transaction atomically and saves to redo stack."""
        if not self.committed_transactions:
            msg = "Nothing to undo." if is_english else "Tidak ada transaksi yang dapat di-undo."
            return AgentExecutionResult(
                status=AgentResponseStatusEnum.ROLLBACK_FAILURE,
                message=msg,
            )

        last_tx = self.committed_transactions.pop()
        success = RollbackEngine.rollback_transaction(last_tx, grid, sheet_grids)
        if not success:
            err_msg = f"Failed to undo transaction '{last_tx.transaction_id}'." if is_english else f"Gagal melakukan undo untuk transaksi '{last_tx.transaction_id}'."
            return AgentExecutionResult(
                status=AgentResponseStatusEnum.ROLLBACK_FAILURE,
                transaction=last_tx,
                message=err_msg,
            )

        last_tx.status = TransactionStatusEnum.ROLLED_BACK
        last_tx.rolled_back_at = datetime.now(timezone.utc).isoformat()
        last_tx.rollback_reason = "User requested undo operation."

        # Add to redo stack
        self.undone_transactions.append(last_tx)
        if len(self.undone_transactions) > self.max_history:
            self.undone_transactions.pop(0)

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

        affected = [d.target_ref for d in last_tx.diff]
        success_msg = "Undone. The last spreadsheet change was reverted." if is_english else "Selesai. Perubahan terakhir telah dibatalkan."

        return AgentExecutionResult(
            status=AgentResponseStatusEnum.ROLLBACK_SUCCESS,
            transaction=last_tx,
            message=success_msg,
            affected_ranges=affected,
        )

    def redo_last_transaction(
        self,
        grid: RawSheetGrid,
        workbook_index: Optional[WorkbookMetadataIndex] = None,
        sheet_grids: Optional[Dict[str, RawSheetGrid]] = None,
        save_hook: Optional[Callable[[], bool]] = None,
        is_english: bool = False,
    ) -> AgentExecutionResult:
        """Re-applies the most recently undone transaction atomically."""
        if not self.undone_transactions:
            msg = "Nothing to redo." if is_english else "Tidak ada transaksi yang dapat di-redo."
            return AgentExecutionResult(
                status=AgentResponseStatusEnum.SUCCESS,
                message=msg,
            )

        tx_to_redo = self.undone_transactions.pop()
        start_time = time.perf_counter()

        # Execute actions afresh
        diffs: List[StateDiff] = []
        try:
            for act in tx_to_redo.actions:
                target_g = grid
                if sheet_grids and act.sheet_name in sheet_grids:
                    target_g = sheet_grids[act.sheet_name]

                d = GridMutator.execute_action(act, target_g, workbook_index, sheet_grids)
                diffs.append(d)

            tx_to_redo.diff = diffs
        except Exception as exec_err:
            tx_to_redo.status = TransactionStatusEnum.FAILED
            err_msg = f"Redo failed: {str(exec_err)}" if is_english else f"Redo gagal: {str(exec_err)}"
            return AgentExecutionResult(
                status=AgentResponseStatusEnum.EXECUTION_ERROR,
                transaction=tx_to_redo,
                message=err_msg,
                error_detail=str(exec_err),
            )

        # Post-execution verification
        v_report = self._verify_transaction(tx_to_redo, grid, sheet_grids)
        tx_to_redo.verification_report = v_report

        if not v_report.is_verified:
            err_msg = f"Redo verification failed: {', '.join(v_report.failures)}" if is_english else f"Verifikasi redo gagal: {', '.join(v_report.failures)}"
            return AgentExecutionResult(
                status=AgentResponseStatusEnum.VERIFICATION_ERROR,
                transaction=tx_to_redo,
                message=err_msg,
            )

        tx_to_redo.status = TransactionStatusEnum.COMMITTED
        tx_to_redo.committed_at = datetime.now(timezone.utc).isoformat()
        self.committed_transactions.append(tx_to_redo)
        if len(self.committed_transactions) > self.max_history:
            self.committed_transactions.pop(0)

        self.current_version += 1
        tx_to_redo.version_after = self.current_version

        redo_audit = TransactionAuditRecord(
            transaction_id=f"redo_{tx_to_redo.transaction_id}",
            dataset_id=tx_to_redo.dataset_id,
            sheet_name=tx_to_redo.sheet_name,
            timestamp=datetime.now(timezone.utc).isoformat(),
            user_request=f"Redo transaction '{tx_to_redo.transaction_id}'",
            resolved_intent=f"Reapplied transaction '{tx_to_redo.transaction_id}'",
            action_types=["REDO"],
            affected_cells=[d.target_ref for d in diffs],
            status="COMMITTED",
            verified=True,
            rolled_back=False,
        )
        self.history.append(redo_audit)
        if len(self.history) > self.max_history:
            self.history.pop(0)

        affected = [d.target_ref for d in diffs]
        success_msg = "Redone. The last reverted change was reapplied." if is_english else "Selesai. Perubahan yang dibatalkan telah diterapkan kembali."

        return AgentExecutionResult(
            status=AgentResponseStatusEnum.SUCCESS,
            transaction=tx_to_redo,
            message=success_msg,
            affected_ranges=affected,
            execution_time_ms=(time.perf_counter() - start_time) * 1000,
        )

    def _verify_transaction(
        self,
        transaction: MutationTransaction,
        grid: RawSheetGrid,
        sheet_grids: Optional[Dict[str, RawSheetGrid]] = None,
    ) -> VerificationReport:
        """Performs deterministic verification comparing actual diff against planned modifications."""
        failures = []
        failure_reasons = []

        if len(transaction.diff) != len(transaction.actions):
            failures.append(f"Diff count ({len(transaction.diff)}) does not match planned action count ({len(transaction.actions)}).")
            failure_reasons.append(VerificationFailureReason.TARGET_CELL_MISSING)

        for act in transaction.actions:
            target_g = sheet_grids.get(act.sheet_name, grid) if (sheet_grids and act.sheet_name in sheet_grids) else grid

            # 1. Formula Verification
            if act.action_type == ActionTypeEnum.WRITE_FORMULA and act.target_cell:
                col_s, row_i = coordinate_from_string(act.target_cell.upper())
                col_i = column_index_from_string(col_s)
                c_data = target_g.get_cell(row_i, col_i)
                if c_data.formula != act.formula:
                    failures.append(f"Formula at {act.target_cell} ('{c_data.formula}') does not match expected '{act.formula}'.")
                    failure_reasons.append(VerificationFailureReason.FORMULA_SYNTAX_ERROR)
                if act.expected_result is not None and c_data.parsed_value != act.expected_result:
                    failures.append(f"Evaluated formula value ({c_data.parsed_value}) does not match expected ({act.expected_result}).")
                    failure_reasons.append(VerificationFailureReason.FORMULA_RESULT_MISMATCH)

            # 2. Value Verification
            elif act.action_type == ActionTypeEnum.WRITE_VALUE and act.target_cell:
                col_s, row_i = coordinate_from_string(act.target_cell.upper())
                col_i = column_index_from_string(col_s)
                c_data = target_g.get_cell(row_i, col_i)
                if c_data.is_empty and act.value is not None:
                    failures.append(f"Cell {act.target_cell} is empty, expected value '{act.value}'.")
                    failure_reasons.append(VerificationFailureReason.TARGET_CELL_MISSING)

            # 3. Chart Creation Verification
            elif act.action_type == ActionTypeEnum.CREATE_CHART and act.chart_spec:
                cid = act.chart_spec.chart_id
                if cid not in target_g.charts:
                    failures.append(f"Chart '{cid}' was not found in worksheet grid charts.")
                    failure_reasons.append(VerificationFailureReason.TARGET_CELL_MISSING)
                else:
                    c_entry = target_g.charts[cid]
                    dest_actual = c_entry.get("destination_cell") if isinstance(c_entry, dict) else c_entry.destination_cell
                    if dest_actual != act.chart_spec.destination_cell:
                        failures.append(f"Chart anchor '{dest_actual}' does not match requested destination '{act.chart_spec.destination_cell}'.")
                        failure_reasons.append(VerificationFailureReason.TARGET_CELL_COLLISION)

            # 4. Chart Movement Verification
            elif act.action_type == ActionTypeEnum.MOVE_CHART:
                dest = act.target_cell or (act.chart_spec.destination_cell if act.chart_spec else None)
                if dest and target_g.charts:
                    found = False
                    for cid, c_entry in target_g.charts.items():
                        c_dest = c_entry.get("destination_cell") if isinstance(c_entry, dict) else c_entry.destination_cell
                        if c_dest == dest:
                            found = True
                            break
                    if not found:
                        failures.append(f"Moved chart was not anchored at target destination '{dest}'.")
                        failure_reasons.append(VerificationFailureReason.TARGET_CELL_MISSING)

            # 5. KPI Verification
            elif act.action_type == ActionTypeEnum.CREATE_KPI and act.kpi_spec:
                kpid = act.kpi_spec.kpi_id
                if kpid not in target_g.kpis:
                    failures.append(f"KPI '{kpid}' was not found in worksheet grid KPIs.")
                    failure_reasons.append(VerificationFailureReason.TARGET_CELL_MISSING)

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
