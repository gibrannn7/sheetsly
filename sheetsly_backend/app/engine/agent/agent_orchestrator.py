"""Authoritative Agent Orchestrator integrating Memory, Planning, Validation, and Transaction Management."""

from datetime import datetime, timezone
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from app.engine.agent.action_model import SpreadsheetAction
from app.engine.agent.agent_planner import SpreadsheetAgentPlanner
from app.engine.agent.memory_manager import MemoryManager
from app.engine.agent.memory_model import StructuredMemoryState
from app.engine.agent.transaction_manager import TransactionManager
from app.engine.agent.transaction_model import (
    AgentExecutionResult,
    AgentResponseStatusEnum,
    MutationTransaction,
    TransactionStatusEnum,
)
from app.engine.parser.sheet_reader import RawSheetGrid
from app.engine.profiler.workbook_index import WorkbookMetadataIndex


class AgentOrchestrator:
    """Coordinates end-to-end spreadsheet agent actions with memory context, transactional execution, and rollback."""

    def __init__(
        self,
        memory_manager: Optional[MemoryManager] = None,
        transaction_manager: Optional[TransactionManager] = None,
    ):
        self.memory = memory_manager or MemoryManager()
        self.tx_manager = transaction_manager or TransactionManager(max_history=20)

    def process_request(
        self,
        user_request: str,
        workbook_index: WorkbookMetadataIndex,
        grid: RawSheetGrid,
        sheet_grids: Optional[Dict[str, RawSheetGrid]] = None,
        save_hook: Optional[Callable[[], bool]] = None,
        expected_version: Optional[int] = None,
        active_sheet_name: Optional[str] = None,
        selected_range: Optional[str] = None,
    ) -> AgentExecutionResult:
        """
        Executes end-to-end request:
        USER REQUEST -> NATURAL-LANGUAGE TRANSACTION CONTROL -> WORKBOOK REALITY -> PLANNER -> TRANSACTION MANAGER -> VERIFY -> COMMIT / ROLLBACK -> MEMORY RECORD.
        """
        import re
        start_time = time.perf_counter()
        cur_sheet = active_sheet_name or workbook_index.active_sheet_name
        q_norm = user_request.strip().lower()
        q_clean = re.sub(r'[^\w\s]', ' ', q_norm).strip()
        q_tokens = [w for w in q_clean.split() if w]

        is_english = any(w in q_tokens for w in ["what", "this", "dataset", "data", "explain", "describe", "contain", "calculate", "sum", "average", "in", "of", "undo", "redo", "cancel", "where", "show"]) and not any(w in q_tokens for w in ["ini", "apa", "tentang", "jelaskan", "jelasin", "sebenarnya", "isinya", "hitung", "buatkan", "tulis", "selesai", "di", "ke", "pada", "rentang", "batalkan", "batal", "ulangi"])

        # -------------------------------------------------------------
        # 1. NATURAL-LANGUAGE TRANSACTION CONTROL (Undo, Redo, Cancel, Inspection)
        # -------------------------------------------------------------
        # A. UNDO
        is_undo = (
            "undo" in q_tokens
            or "revert" in q_tokens
            or "rollback" in q_tokens
            or any(phrase in q_clean for phrase in [
                "undo langkah", "undo perubahan", "undo aksi", "undo tindakan", "undo operasi", "undo itu", "undo ini", "undo tadi",
                "batalkan langkah", "batalkan perubahan", "batalkan aksi", "batalkan tindakan", "batalkan yang tadi", "batalkan tadi", "batalkan itu", "batalkan tersebut",
                "kembalikan seperti sebelumnya", "kembalikan seperti semula", "kembalikan ke sebelumnya", "kembalikan ke semula", "kembalikan data sebelumnya", "kembalikan perubahan",
                "revert that", "revert last", "reverse the last", "reverse that", "undo that", "undo the last", "undo last", "undo previous", "undo operation",
            ])
            or (q_clean.startswith("batalkan") and not any(kw in q_clean for kw in ["filter", "sort", "kolom", "baris", "sheet", "operasi"]))
        ) and not any(kw in q_clean for kw in ["buat", "tulis", "hitung", "create", "write", "calculate", "sum", "average", "pie", "bar", "line"])

        if is_undo:
            return self.undo_last_transaction(grid, sheet_grids, is_english=is_english)

        # B. REDO
        is_redo = (
            "redo" in q_tokens
            or any(phrase in q_clean for phrase in [
                "redo langkah", "redo perubahan", "redo aksi", "redo tindakan", "redo operasi", "redo itu", "redo ini", "redo tadi",
                "ulangi langkah", "ulangi perubahan", "ulangi aksi", "ulangi tindakan", "ulangi operasi", "ulangi yang tadi", "ulangi tadi", "ulangi itu", "ulangi tersebut", "ulangi lagi",
                "terapkan kembali", "reapply that", "reapply last", "repeat the last", "restore the previous", "restore that", "redo that", "reapply",
            ])
            or (q_clean.startswith("ulangi") and not any(kw in q_clean for kw in ["filter", "sort", "kolom", "baris", "sheet", "rumus", "formula"]))
        ) and not any(kw in q_clean for kw in ["buat", "tulis", "hitung", "create", "write", "calculate", "sum", "average", "pie", "bar", "line"])

        if is_redo:
            return self.redo_last_transaction(grid, workbook_index, sheet_grids, save_hook, is_english=is_english)

        # C. CANCEL
        cancel_patterns = [
            r'\bcancel\b', r'\bcancel that\b', r'\bcancel the operation\b', r'\bcancel operation\b',
            r'\babort\b', r'\bstop\b', r'\bbatalkan operasi\b', r'\bbatalin\b', r'\bjangan jadi\b',
            r'\bjangan lakukan\b', r'\bbatal\b'
        ]
        is_cancel = any(re.search(pat, q_clean) for pat in cancel_patterns) and not any(kw in q_clean for kw in ["buat", "tulis", "hitung", "create", "write", "calculate", "sum", "average", "pie", "bar", "line"])

        if is_cancel:
            cancel_msg = "Operation cancelled. No changes were made to the worksheet." if is_english else "Operasi dibatalkan. Tidak ada perubahan yang dilakukan pada lembar kerja."
            return AgentExecutionResult(
                status=AgentResponseStatusEnum.SUCCESS,
                message=cancel_msg,
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )

        # D. INSPECTION OF RECENT CHANGES
        inspect_change_patterns = [
            r'what\s+(?:did\s+you\s+change|was\s+changed|did\s+you\s+do)',
            r'where\s+did\s+you\s+put\s+it',
            r'show\s+formula',
            r'perubahan\s+apa\s+yang\s+dilakukan',
            r'hasilnya\s+ada\s+di\s+mana',
            r'tampilkan\s+rumus',
            r'apa\s+yang\s+diubah',
        ]
        if any(re.search(pat, q_clean) for pat in inspect_change_patterns):
            if not self.tx_manager.committed_transactions:
                msg = "No spreadsheet changes have been made yet in this session." if is_english else "Belum ada perubahan lembar kerja yang dilakukan pada sesi ini."
                return AgentExecutionResult(status=AgentResponseStatusEnum.SUCCESS, message=msg)
            last_tx = self.tx_manager.committed_transactions[-1]
            diff_summaries = []
            for d in last_tx.diff:
                if d.after and d.after.formula:
                    diff_summaries.append(f"{d.target_ref}: rumus '{d.after.formula}' (nilai: {d.after.parsed_value})")
                elif d.after:
                    diff_summaries.append(f"{d.target_ref}: nilai '{d.after.parsed_value}'")
                else:
                    diff_summaries.append(f"{d.target_ref}")
            detail = "; ".join(diff_summaries)
            if is_english:
                msg = f"Last operation ('{last_tx.user_request}') changed: {detail}."
            else:
                msg = f"Perubahan terakhir ('{last_tx.user_request}') mengubah: {detail}."
            return AgentExecutionResult(
                status=AgentResponseStatusEnum.SUCCESS,
                message=msg,
                affected_ranges=[d.target_ref for d in last_tx.diff],
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )

        # 2. Plan Agent Actions
        actions, plan_status, req, plan_msg = SpreadsheetAgentPlanner.plan_agent_actions(
            user_request=user_request,
            workbook_index=workbook_index,
            grid=grid,
            active_sheet_name=cur_sheet,
            selected_range=selected_range,
        )

        if plan_status != AgentResponseStatusEnum.SUCCESS or not actions:
            self.memory.record_turn(
                user_query=user_request,
                agent_intent=plan_msg,
                status=plan_status.value,
            )
            return AgentExecutionResult(
                status=plan_status,
                message=plan_msg,
                clarification=req,
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )

        # 3. Build Mutation Transaction
        tx_id = f"tx_{int(time.time() * 1000)}"
        tx = MutationTransaction(
            transaction_id=tx_id,
            dataset_id=workbook_index.dataset_id,
            sheet_name=cur_sheet,
            user_request=user_request,
            resolved_intent=plan_msg,
            created_at=datetime.now(timezone.utc).isoformat(),
            actions=actions,
        )

        # 4. Execute Transaction
        exec_res = self.tx_manager.execute_transaction(
            transaction=tx,
            grid=grid,
            workbook_index=workbook_index,
            sheet_grids=sheet_grids,
            save_hook=save_hook,
            expected_version=expected_version,
        )

        # 5. Update Memory & Task History
        self.memory.record_turn(
            user_query=user_request,
            agent_intent=plan_msg,
            status=exec_res.status.value,
        )
        if self.tx_manager.history:
            self.memory.record_task_history(self.tx_manager.history[-1])

        return exec_res

    # Alias for API uniformity
    execute_request = process_request

    def undo_last_transaction(
        self,
        grid: RawSheetGrid,
        sheet_grids: Optional[Dict[str, RawSheetGrid]] = None,
        is_english: bool = False,
    ) -> AgentExecutionResult:
        """Undoes the most recent committed transaction and syncs task history."""
        res = self.tx_manager.undo_last_transaction(grid, sheet_grids, is_english=is_english)
        if res.status == AgentResponseStatusEnum.ROLLBACK_SUCCESS and self.tx_manager.history:
            self.memory.record_task_history(self.tx_manager.history[-1])
        return res

    def undo_last(
        self,
        grid: RawSheetGrid,
        sheet_grids: Optional[Dict[str, RawSheetGrid]] = None,
        is_english: bool = False,
    ) -> AgentExecutionResult:
        """Convenience alias for undo_last_transaction."""
        return self.undo_last_transaction(grid, sheet_grids, is_english=is_english)

    def redo_last_transaction(
        self,
        grid: RawSheetGrid,
        workbook_index: Optional[WorkbookMetadataIndex] = None,
        sheet_grids: Optional[Dict[str, RawSheetGrid]] = None,
        save_hook: Optional[Callable[[], bool]] = None,
        is_english: bool = False,
    ) -> AgentExecutionResult:
        """Redoes the most recently undone transaction and syncs task history."""
        res = self.tx_manager.redo_last_transaction(grid, workbook_index, sheet_grids, save_hook, is_english=is_english)
        if res.status == AgentResponseStatusEnum.SUCCESS and self.tx_manager.history:
            self.memory.record_task_history(self.tx_manager.history[-1])
        return res

    def redo_last(
        self,
        grid: RawSheetGrid,
        workbook_index: Optional[WorkbookMetadataIndex] = None,
        sheet_grids: Optional[Dict[str, RawSheetGrid]] = None,
        save_hook: Optional[Callable[[], bool]] = None,
        is_english: bool = False,
    ) -> AgentExecutionResult:
        """Convenience alias for redo_last_transaction."""
        return self.redo_last_transaction(grid, workbook_index, sheet_grids, save_hook, is_english=is_english)

