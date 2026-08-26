import re
from typing import Any, Dict, List, Optional, Tuple
from openpyxl.utils.cell import coordinate_from_string

from app.engine.agent.action_model import (
    ActionTypeEnum,
    FormattingStyle,
    SpreadsheetAction,
)
from app.engine.agent.action_validator import ActionValidator
from app.engine.agent.formula_evaluator import FormulaEvaluator
from app.engine.agent.placement_policy import PlacementPolicy
from app.engine.agent.transaction_model import AgentResponseStatusEnum
from app.engine.ai.models import ClarificationRequest
from app.engine.analytics.ambiguity_resolver import GeneralizedAmbiguityResolver
from app.engine.parser.sheet_reader import RawSheetGrid
from app.engine.profiler.workbook_index import (
    ColumnIndexEntry,
    SheetIndexEntry,
    TableIndexEntry,
    WorkbookMetadataIndex,
)
from app.models.schemas import SemanticTypeEnum


class SpreadsheetAgentPlanner:
    """Plans canonical spreadsheet actions from natural language user instructions."""

    @classmethod
    def plan_agent_actions(
        cls,
        user_request: str,
        workbook_index: WorkbookMetadataIndex,
        grid: RawSheetGrid,
        active_sheet_name: Optional[str] = None,
    ) -> Tuple[List[SpreadsheetAction], AgentResponseStatusEnum, Optional[ClarificationRequest], str]:
        """
        Translates a request like 'buatkan total penjualan' into an atomic, validated action sequence.
        """
        cur_sheet = active_sheet_name or workbook_index.active_sheet_name
        sheet_entry = workbook_index.sheets.get(cur_sheet)
        if not sheet_entry or not sheet_entry.tables:
            return [], AgentResponseStatusEnum.VALIDATION_ERROR, None, f"Sheet '{cur_sheet}' does not contain structured tables."

        table_entry = sheet_entry.tables[0]
        q_norm = user_request.strip().lower()

        # Scope guard: Verify request relates to spreadsheet operations or table columns
        spreadsheet_keywords = [
            "total", "sum", "jumlah", "rata-rata", "average", "mean", "hitung", "count",
            "min", "max", "median", "buatkan", "buat", "tambahkan", "tambah", "tampilkan",
            "rekap", "summary", "format", "bold", "clear", "hapus", "sisipkan", "insert",
            "rumus", "formula", "baris", "kolom", "row", "column", "cell", "sel"
        ]
        has_kw = any(kw in q_norm for kw in spreadsheet_keywords)
        has_col = any(c.normalized_name in q_norm or c.source_column_letter.lower() == q_norm for c in table_entry.columns)

        if not has_kw and not has_col:
            return [], AgentResponseStatusEnum.UNSUPPORTED, None, "Permintaan di luar cakupan operasi spreadsheet yang didukung."

        # 1. Resolve Column Ambiguity
        col_res = GeneralizedAmbiguityResolver.resolve_column_ambiguity(
            query=user_request,
            columns=table_entry.columns,
            target_role=SemanticTypeEnum.NUMERIC_MEASURE,
        )
        if col_res.clarification_needed:
            return [], AgentResponseStatusEnum.CLARIFICATION, col_res.clarification_request, col_res.reason
        if col_res.is_unsupported or not col_res.resolved_candidate:
            measure_cols = [c for c in table_entry.columns if c.semantic_type == SemanticTypeEnum.NUMERIC_MEASURE]
            has_metric_kw = any(c.normalized_name in q_norm for c in measure_cols)
            has_agg_kw = any(kw in q_norm for kw in ["total", "sum", "jumlah", "rata-rata", "average", "mean", "hitung", "count", "min", "max", "median", "rekap"])
            if not has_metric_kw and not has_agg_kw:
                return [], AgentResponseStatusEnum.UNSUPPORTED, None, "Permintaan tidak memuat operasi spreadsheet atau metrik yang valid."

            # Fallback to metric ambiguity
            metric_res = GeneralizedAmbiguityResolver.resolve_metric_ambiguity(
                query=user_request,
                measure_columns=measure_cols,
            )
            if metric_res.clarification_needed:
                return [], AgentResponseStatusEnum.CLARIFICATION, metric_res.clarification_request, metric_res.reason
            if not metric_res.resolved_candidate:
                return [], AgentResponseStatusEnum.UNSUPPORTED, None, "No suitable measure column found for summary."
            target_col = metric_res.resolved_candidate
        else:
            target_col = col_res.resolved_candidate

        # 2. Determine Placement
        placement = PlacementPolicy.determine_placement(
            table=table_entry,
            measure_col=target_col,
            grid=grid,
            query=user_request,
        )

        if not placement.is_safe:
            req = ClarificationRequest(
                question=f"Target sel '{placement.target_cell}' sudah terisi data. Apakah ingin menimpa atau menaruh di baris lain?",
                reason="Placement collision detected at target cell.",
                target_parameter="placement_collision",
                options=["Timpa data", "Batalkan"],
            )
            return [], AgentResponseStatusEnum.CLARIFICATION, req, "Placement collision detected."

        # 3. Formulate Formula & Calculate Python Truth
        col_letter = target_col.source_column_letter.upper()
        # Find start and end data rows
        start_row = 2
        end_row = 101
        if table_entry.data_range and ":" in table_entry.data_range:
            try:
                s_cell, e_cell = table_entry.data_range.split(":")
                _, start_row = coordinate_from_string(s_cell)
                _, end_row = coordinate_from_string(e_cell)
            except Exception:
                pass

        formula_str = f"=SUM({col_letter}{start_row}:{col_letter}{end_row})"
        expected_val, _ = FormulaEvaluator.evaluate(formula_str, grid)

        # 4. Build Action Sequence
        actions: List[SpreadsheetAction] = []
        action_idx = 1

        # Action 1: Write Label (if label cell specified)
        if placement.label_cell and placement.label_value:
            actions.append(
                SpreadsheetAction(
                    action_id=f"act_{action_idx}",
                    action_type=ActionTypeEnum.WRITE_VALUE,
                    sheet_name=cur_sheet,
                    target_cell=placement.label_cell,
                    value=placement.label_value,
                    description=f"Write label '{placement.label_value}'",
                )
            )
            action_idx += 1

        # Action 2: Write Formula
        actions.append(
            SpreadsheetAction(
                action_id=f"act_{action_idx}",
                action_type=ActionTypeEnum.WRITE_FORMULA,
                sheet_name=cur_sheet,
                target_cell=placement.target_cell,
                formula=formula_str,
                expected_result=expected_val,
                description=f"Write formula '{formula_str}'",
            )
        )
        action_idx += 1

        # Action 3: Format Range (Bold summary row)
        summary_range = f"{placement.label_cell or placement.target_cell}:{placement.target_cell}"
        actions.append(
            SpreadsheetAction(
                action_id=f"act_{action_idx}",
                action_type=ActionTypeEnum.FORMAT_RANGE,
                sheet_name=cur_sheet,
                target_range=summary_range,
                style=FormattingStyle(bold=True, fill_color="#F1F5F9"),
                description="Format summary row with bold text and subtle fill",
            )
        )
        action_idx += 1

        # Action 4: Set Number Format
        if placement.number_format:
            actions.append(
                SpreadsheetAction(
                    action_id=f"act_{action_idx}",
                    action_type=ActionTypeEnum.SET_NUMBER_FORMAT,
                    sheet_name=cur_sheet,
                    target_cell=placement.target_cell,
                    number_format=placement.number_format,
                    description=f"Apply number format '{placement.number_format}'",
                )
            )

        # 5. Validate Action Sequence
        val_res = ActionValidator.validate_sequence(actions, workbook_index, grid)
        if not val_res.is_valid:
            return [], val_res.status, val_res.clarification_request, val_res.error_message or "Validation failed."

        return actions, AgentResponseStatusEnum.SUCCESS, None, f"Planned {len(actions)} actions for '{user_request}'."
