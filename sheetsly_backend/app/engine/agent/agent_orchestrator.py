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
    ) -> AgentExecutionResult:
        """
        Executes end-to-end request:
        USER REQUEST -> WORKBOOK REALITY + MEMORY ADVISORY -> PLANNER -> TRANSACTION MANAGER -> VERIFY -> COMMIT / ROLLBACK -> MEMORY RECORD.
        """
        start_time = time.perf_counter()
        cur_sheet = active_sheet_name or workbook_index.active_sheet_name

        # 1. Plan Agent Actions
        actions, plan_status, req, plan_msg = SpreadsheetAgentPlanner.plan_agent_actions(
            user_request=user_request,
            workbook_index=workbook_index,
            grid=grid,
            active_sheet_name=cur_sheet,
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

        # 2. Build Mutation Transaction
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

        # 3. Execute Transaction
        exec_res = self.tx_manager.execute_transaction(
            transaction=tx,
            grid=grid,
            workbook_index=workbook_index,
            sheet_grids=sheet_grids,
            save_hook=save_hook,
            expected_version=expected_version,
        )

        # 4. Update Memory & Task History
        self.memory.record_turn(
            user_query=user_request,
            agent_intent=plan_msg,
            status=exec_res.status.value,
        )
        if self.tx_manager.history:
            self.memory.record_task_history(self.tx_manager.history[-1])

        return exec_res

    def undo_last_transaction(
        self,
        grid: RawSheetGrid,
        sheet_grids: Optional[Dict[str, RawSheetGrid]] = None,
    ) -> AgentExecutionResult:
        """Undoes the most recent committed transaction and syncs task history."""
        res = self.tx_manager.undo_last_transaction(grid, sheet_grids)
        if res.status == AgentResponseStatusEnum.ROLLBACK_SUCCESS and self.tx_manager.history:
            self.memory.record_task_history(self.tx_manager.history[-1])
        return res

    def undo_last(
        self,
        grid: RawSheetGrid,
        sheet_grids: Optional[Dict[str, RawSheetGrid]] = None,
    ) -> AgentExecutionResult:
        """Convenience alias for undo_last_transaction."""
        return self.undo_last_transaction(grid, sheet_grids)

