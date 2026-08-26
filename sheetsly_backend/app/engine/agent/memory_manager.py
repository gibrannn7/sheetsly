"""Authoritative Structured Memory Manager enforcing hierarchy, scopes, and invalidation rules."""

from datetime import datetime, timezone
import hashlib
from typing import Any, Dict, List, Optional, Tuple

from app.engine.agent.memory_model import (
    ConversationTurn,
    MemoryScopeEnum,
    StructuredMemoryState,
    UserPreferenceProfile,
    WorkbookPreference,
)
from app.engine.agent.transaction_model import TransactionAuditRecord
from app.engine.profiler.workbook_index import (
    ColumnIndexEntry,
    SheetIndexEntry,
    TableIndexEntry,
    WorkbookMetadataIndex,
)


class MemoryManager:
    """Manages structured session, workbook, and user preferences with deterministic invalidation."""

    def __init__(self, state: Optional[StructuredMemoryState] = None):
        self.state = state or StructuredMemoryState()

    @classmethod
    def compute_schema_fingerprint(cls, workbook_index: WorkbookMetadataIndex) -> str:
        """Computes a deterministic SHA-256 hash of workbook sheets, tables, and column signatures."""
        sig_parts = [workbook_index.dataset_id]
        for s_name in sorted(workbook_index.sheet_names):
            sig_parts.append(f"sheet:{s_name}")
            s_entry = workbook_index.sheets.get(s_name)
            if s_entry:
                for tbl in s_entry.tables:
                    sig_parts.append(f"tbl:{tbl.table_id}:{tbl.range_address}")
                    for col in tbl.columns:
                        sig_parts.append(f"col:{col.index}:{col.name}:{col.source_column_letter}:{col.data_type.value}")
        raw_str = "|".join(sig_parts)
        return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()

    def get_valid_workbook_memory(self, workbook_index: WorkbookMetadataIndex) -> Optional[WorkbookPreference]:
        """
        Retrieves workbook memory if and only if the current schema fingerprint matches.
        If the schema has changed (column deleted/renamed, sheet renamed), invalidates stale mappings.
        """
        pref = self.state.workbook_memory.get(workbook_index.dataset_id)
        if not pref:
            return None

        current_fp = self.compute_schema_fingerprint(workbook_index)
        if pref.schema_version_hash != current_fp:
            # Schema changed -> Invalidate stale column mappings
            pref.confirmed_column_mappings.clear()
            pref.schema_version_hash = current_fp
            return None

        # Verify confirmed columns actually exist in active sheet
        active_sheet = workbook_index.sheets.get(pref.sheet_name)
        if not active_sheet or not active_sheet.tables:
            return None

        table_col_names = {c.name.lower() for c in active_sheet.tables[0].columns}
        stale_keys = [k for k, target_col in pref.confirmed_column_mappings.items() if target_col.lower() not in table_col_names]
        for k in stale_keys:
            pref.confirmed_column_mappings.pop(k, None)

        return pref

    def record_confirmed_mapping(
        self,
        workbook_index: WorkbookMetadataIndex,
        sheet_name: str,
        alias: str,
        column_name: str,
    ):
        """Records a user-confirmed column mapping (e.g. 'penjualan' -> 'Sales') for a workbook."""
        fp = self.compute_schema_fingerprint(workbook_index)
        if workbook_index.dataset_id not in self.state.workbook_memory:
            self.state.workbook_memory[workbook_index.dataset_id] = WorkbookPreference(
                dataset_id=workbook_index.dataset_id,
                sheet_name=sheet_name,
                schema_version_hash=fp,
                updated_at=datetime.now(timezone.utc).isoformat(),
            )
        pref = self.state.workbook_memory[workbook_index.dataset_id]
        pref.confirmed_column_mappings[alias.lower().strip()] = column_name
        pref.schema_version_hash = fp
        pref.updated_at = datetime.now(timezone.utc).isoformat()

    def record_turn(self, user_query: str, agent_intent: str, status: str):
        """Appends a turn to conversation memory (capped at 20 turns)."""
        turn = ConversationTurn(
            turn_id=f"turn_{len(self.state.conversation_memory) + 1}",
            user_query=user_query,
            agent_intent=agent_intent,
            status=status,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self.state.conversation_memory.append(turn)
        if len(self.state.conversation_memory) > 20:
            self.state.conversation_memory.pop(0)

    def record_task_history(self, audit_record: TransactionAuditRecord):
        """Appends an executed transaction audit record to task history."""
        self.state.task_history.append(audit_record)
        if len(self.state.task_history) > 20:
            self.state.task_history.pop(0)

    def resolve_advisory_context(
        self,
        user_query: str,
        workbook_index: WorkbookMetadataIndex,
    ) -> Dict[str, str]:
        """
        Extracts valid advisory column aliases respecting the precedence hierarchy:
        CURRENT WORKBOOK REALITY > CURRENT USER REQUEST > CONFIRMED CONTEXT > MEMORY
        """
        valid_pref = self.get_valid_workbook_memory(workbook_index)
        if not valid_pref:
            return {}
        return dict(valid_pref.confirmed_column_mappings)
