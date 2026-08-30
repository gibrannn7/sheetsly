"""Comprehensive validator for canonical spreadsheet mutation actions and action sequences."""

import re
from typing import Any, Dict, List, Optional, Set, Tuple
from openpyxl.utils.cell import column_index_from_string, coordinate_from_string
from pydantic import BaseModel, Field

from app.engine.agent.action_model import (
    ActionTypeEnum,
    FormattingStyle,
    NumberFormatSpec,
    SpreadsheetAction,
    SUPPORTED_ACTION_REGISTRY,
)
from app.engine.agent.formula_validator import FormulaValidator
from app.engine.agent.transaction_model import AgentResponseStatusEnum
from app.engine.ai.models import ClarificationRequest
from app.engine.parser.sheet_reader import RawSheetGrid
from app.engine.profiler.workbook_index import (
    SheetIndexEntry,
    TableIndexEntry,
    WorkbookMetadataIndex,
)


class ActionValidationResult(BaseModel):
    """Authoritative validation result for an individual spreadsheet action."""

    is_valid: bool = False
    status: AgentResponseStatusEnum = AgentResponseStatusEnum.VALIDATION_ERROR
    action_id: str
    action_type: ActionTypeEnum
    target_ref: Optional[str] = None
    error_message: Optional[str] = None
    clarification_request: Optional[ClarificationRequest] = None
    security_warnings: List[str] = Field(default_factory=list)


class ActionSequenceValidationResult(BaseModel):
    """Validation result for an ordered sequence of actions in a transaction."""

    is_valid: bool = False
    status: AgentResponseStatusEnum = AgentResponseStatusEnum.VALIDATION_ERROR
    total_actions: int = 0
    valid_actions_count: int = 0
    action_results: List[ActionValidationResult] = Field(default_factory=list)
    error_message: Optional[str] = None
    clarification_request: Optional[ClarificationRequest] = None


class ActionValidator:
    """Validates individual actions and action sequences against safety, collision, and scope invariants."""

    @classmethod
    def validate_action(
        cls,
        action: SpreadsheetAction,
        workbook_index: Optional[WorkbookMetadataIndex] = None,
        grid: Optional[RawSheetGrid] = None,
        allow_overwrite: bool = False,
    ) -> ActionValidationResult:
        """Validates a single SpreadsheetAction according to canonical rules."""
        # 1. Action Type Registry Check
        if action.action_type not in SUPPORTED_ACTION_REGISTRY:
            return ActionValidationResult(
                is_valid=False,
                status=AgentResponseStatusEnum.UNSUPPORTED,
                action_id=action.action_id,
                action_type=action.action_type,
                error_message=f"Unsupported action type: '{action.action_type}'.",
            )

        # 2. Sheet Existence Check
        # Allow dynamically planned sheets such as 'Dashboard' or 'Sheetsly_Calc'
        allowed_virtual_sheets = {"Dashboard", "Sheetsly_Calc", "Dasbor"}
        if workbook_index and action.sheet_name not in workbook_index.sheets and action.sheet_name not in allowed_virtual_sheets and action.action_type != ActionTypeEnum.CREATE_WORKSHEET:
            return ActionValidationResult(
                is_valid=False,
                status=AgentResponseStatusEnum.VALIDATION_ERROR,
                action_id=action.action_id,
                action_type=action.action_type,
                error_message=f"Target worksheet '{action.sheet_name}' does not exist in workbook.",
            )

        # 3. Action-Specific Validation
        if action.action_type == ActionTypeEnum.WRITE_VALUE:
            return cls._validate_write_value(action, grid, allow_overwrite)
        elif action.action_type == ActionTypeEnum.WRITE_FORMULA:
            return cls._validate_write_formula(action, workbook_index, grid, allow_overwrite)
        elif action.action_type == ActionTypeEnum.INSERT_ROW:
            return cls._validate_insert_row(action)
        elif action.action_type == ActionTypeEnum.INSERT_COLUMN:
            return cls._validate_insert_column(action)
        elif action.action_type == ActionTypeEnum.FORMAT_CELL:
            return cls._validate_format_cell(action)
        elif action.action_type == ActionTypeEnum.FORMAT_RANGE:
            return cls._validate_format_range(action, workbook_index)
        elif action.action_type == ActionTypeEnum.SET_NUMBER_FORMAT:
            return cls._validate_set_number_format(action)
        elif action.action_type == ActionTypeEnum.CLEAR_CONTENT:
            return cls._validate_clear_content(action, workbook_index)
        elif action.action_type == ActionTypeEnum.CREATE_CHART:
            return cls._validate_create_chart(action, workbook_index, grid)
        elif action.action_type == ActionTypeEnum.UPDATE_CHART:
            return cls._validate_update_chart(action, workbook_index)
        elif action.action_type == ActionTypeEnum.MOVE_CHART:
            return cls._validate_move_chart(action, workbook_index)
        elif action.action_type == ActionTypeEnum.RESIZE_CHART:
            return cls._validate_resize_chart(action, workbook_index)
        elif action.action_type == ActionTypeEnum.DELETE_CHART:
            return cls._validate_delete_chart(action, workbook_index)
        elif action.action_type == ActionTypeEnum.CREATE_KPI:
            return cls._validate_create_kpi(action, workbook_index)
        elif action.action_type == ActionTypeEnum.CREATE_WORKSHEET:
            return cls._validate_create_worksheet(action, workbook_index)

        return ActionValidationResult(
            is_valid=True,
            status=AgentResponseStatusEnum.SUCCESS,
            action_id=action.action_id,
            action_type=action.action_type,
        )

    @classmethod
    def validate_sequence(
        cls,
        actions: List[SpreadsheetAction],
        workbook_index: Optional[WorkbookMetadataIndex] = None,
        grid: Optional[RawSheetGrid] = None,
        sheet_grids: Optional[Dict[str, RawSheetGrid]] = None,
        allow_overwrite: bool = False,
    ) -> ActionSequenceValidationResult:
        """Validates an entire sequential list of actions within a mutation transaction."""
        if not actions:
            return ActionSequenceValidationResult(
                is_valid=False,
                status=AgentResponseStatusEnum.VALIDATION_ERROR,
                error_message="Empty action list: transaction contains zero actions.",
            )

        seen_ids = set()
        results: List[ActionValidationResult] = []

        for act in actions:
            # Duplicate Action ID check
            if act.action_id in seen_ids:
                return ActionSequenceValidationResult(
                    is_valid=False,
                    status=AgentResponseStatusEnum.VALIDATION_ERROR,
                    total_actions=len(actions),
                    error_message=f"Duplicate action_id detected in transaction: '{act.action_id}'.",
                )
            seen_ids.add(act.action_id)

            target_grid = sheet_grids.get(act.sheet_name, grid) if sheet_grids else grid
            res = cls.validate_action(act, workbook_index, target_grid, allow_overwrite=allow_overwrite)
            results.append(res)
            if not res.is_valid:
                return ActionSequenceValidationResult(
                    is_valid=False,
                    status=res.status,
                    total_actions=len(actions),
                    valid_actions_count=len([r for r in results if r.is_valid]),
                    action_results=results,
                    error_message=f"Action '{act.action_id}' ({act.action_type.value}) validation failed: {res.error_message}",
                    clarification_request=res.clarification_request,
                )

        return ActionSequenceValidationResult(
            is_valid=True,
            status=AgentResponseStatusEnum.SUCCESS,
            total_actions=len(actions),
            valid_actions_count=len(actions),
            action_results=results,
        )

    # ------------------------------------------------------------------------
    # Internal Action Checkers
    # ------------------------------------------------------------------------
    @classmethod
    def _validate_write_value(
        cls,
        action: SpreadsheetAction,
        grid: Optional[RawSheetGrid],
        allow_overwrite: bool,
    ) -> ActionValidationResult:
        if not action.target_cell:
            return ActionValidationResult(
                is_valid=False,
                status=AgentResponseStatusEnum.VALIDATION_ERROR,
                action_id=action.action_id,
                action_type=action.action_type,
                error_message="WRITE_VALUE action requires target_cell.",
            )

        # Overwrite collision check
        if grid and grid.sheet_name == action.sheet_name and not allow_overwrite:
            collision = cls._check_cell_collision(grid, action.target_cell, expected_value=action.value)
            if collision:
                req = ClarificationRequest(
                    question=f"Target sel '{action.target_cell}' sudah berisi data ('{collision}'). Apakah ingin menimpa sel ini?",
                    reason="Target cell already contains user data or formulas.",
                    target_parameter="overwrite_confirmation",
                    options=["Ya, timpa", "Tidak, batalkan"],
                )
                return ActionValidationResult(
                    is_valid=False,
                    status=AgentResponseStatusEnum.CLARIFICATION,
                    action_id=action.action_id,
                    action_type=action.action_type,
                    target_ref=action.target_cell,
                    clarification_request=req,
                )

        return ActionValidationResult(
            is_valid=True,
            status=AgentResponseStatusEnum.SUCCESS,
            action_id=action.action_id,
            action_type=action.action_type,
            target_ref=action.target_cell,
        )

    @classmethod
    def _validate_write_formula(
        cls,
        action: SpreadsheetAction,
        workbook_index: Optional[WorkbookMetadataIndex],
        grid: Optional[RawSheetGrid],
        allow_overwrite: bool,
    ) -> ActionValidationResult:
        if not action.target_cell:
            return ActionValidationResult(
                is_valid=False,
                status=AgentResponseStatusEnum.VALIDATION_ERROR,
                action_id=action.action_id,
                action_type=action.action_type,
                error_message="WRITE_FORMULA action requires target_cell.",
            )
        if not action.formula:
            return ActionValidationResult(
                is_valid=False,
                status=AgentResponseStatusEnum.VALIDATION_ERROR,
                action_id=action.action_id,
                action_type=action.action_type,
                error_message="WRITE_FORMULA action requires formula string.",
            )

        # Formula Validation
        table_entry = None
        if workbook_index and action.sheet_name in workbook_index.sheets:
            s_entry = workbook_index.sheets[action.sheet_name]
            if s_entry.tables:
                table_entry = s_entry.tables[0]

        f_res = FormulaValidator.validate_formula(
            formula=action.formula,
            target_cell=action.target_cell,
            sheet_name=action.sheet_name,
            workbook_index=workbook_index,
            table_entry=table_entry,
        )
        if not f_res.is_valid:
            return ActionValidationResult(
                is_valid=False,
                status=AgentResponseStatusEnum.VALIDATION_ERROR,
                action_id=action.action_id,
                action_type=action.action_type,
                target_ref=action.target_cell,
                error_message=f_res.error_message,
                security_warnings=f_res.security_warnings,
            )

        # Overwrite collision check
        if grid and grid.sheet_name == action.sheet_name and not allow_overwrite:
            collision = cls._check_cell_collision(grid, action.target_cell, expected_formula=action.formula)
            if collision:
                req = ClarificationRequest(
                    question=f"Target sel '{action.target_cell}' sudah berisi data ('{collision}'). Apakah ingin menimpa sel ini?",
                    reason="Target cell already contains user data or formulas.",
                    target_parameter="overwrite_confirmation",
                    options=["Ya, timpa", "Tidak, batalkan"],
                )
                return ActionValidationResult(
                    is_valid=False,
                    status=AgentResponseStatusEnum.CLARIFICATION,
                    action_id=action.action_id,
                    action_type=action.action_type,
                    target_ref=action.target_cell,
                    error_message=f"Overwrite collision at cell '{action.target_cell}'.",
                    clarification_request=req,
                )

        return ActionValidationResult(
            is_valid=True,
            status=AgentResponseStatusEnum.SUCCESS,
            action_id=action.action_id,
            action_type=action.action_type,
            target_ref=action.target_cell,
        )

    @classmethod
    def _validate_insert_row(cls, action: SpreadsheetAction) -> ActionValidationResult:
        if action.row_index is None or action.row_index < 1:
            return ActionValidationResult(
                is_valid=False,
                status=AgentResponseStatusEnum.VALIDATION_ERROR,
                action_id=action.action_id,
                action_type=action.action_type,
                error_message=f"Invalid row_index: {action.row_index}. Must be >= 1.",
            )
        return ActionValidationResult(
            is_valid=True,
            status=AgentResponseStatusEnum.SUCCESS,
            action_id=action.action_id,
            action_type=action.action_type,
            target_ref=f"Row {action.row_index}",
        )

    @classmethod
    def _validate_insert_column(cls, action: SpreadsheetAction) -> ActionValidationResult:
        if action.column_index is None or action.column_index < 1:
            return ActionValidationResult(
                is_valid=False,
                status=AgentResponseStatusEnum.VALIDATION_ERROR,
                action_id=action.action_id,
                action_type=action.action_type,
                error_message=f"Invalid column_index: {action.column_index}. Must be >= 1.",
            )
        return ActionValidationResult(
            is_valid=True,
            status=AgentResponseStatusEnum.SUCCESS,
            action_id=action.action_id,
            action_type=action.action_type,
            target_ref=f"Col {action.column_index}",
        )

    @classmethod
    def _validate_format_cell(cls, action: SpreadsheetAction) -> ActionValidationResult:
        if not action.target_cell:
            return ActionValidationResult(
                is_valid=False,
                status=AgentResponseStatusEnum.VALIDATION_ERROR,
                action_id=action.action_id,
                action_type=action.action_type,
                error_message="FORMAT_CELL requires target_cell.",
            )
        if not action.style:
            return ActionValidationResult(
                is_valid=False,
                status=AgentResponseStatusEnum.VALIDATION_ERROR,
                action_id=action.action_id,
                action_type=action.action_type,
                error_message="FORMAT_CELL requires style attributes.",
            )
        return ActionValidationResult(
            is_valid=True,
            status=AgentResponseStatusEnum.SUCCESS,
            action_id=action.action_id,
            action_type=action.action_type,
            target_ref=action.target_cell,
        )

    @classmethod
    def _validate_format_range(
        cls,
        action: SpreadsheetAction,
        workbook_index: Optional[WorkbookMetadataIndex],
    ) -> ActionValidationResult:
        if not action.target_range:
            return ActionValidationResult(
                is_valid=False,
                status=AgentResponseStatusEnum.VALIDATION_ERROR,
                action_id=action.action_id,
                action_type=action.action_type,
                error_message="FORMAT_RANGE requires target_range.",
            )
        # Scope preservation: Reject massive out-of-scope formatting e.g. A1:Z10000
        if ":" in action.target_range:
            start_c, end_c = action.target_range.split(":")
            try:
                _, r1 = coordinate_from_string(start_c)
                _, r2 = coordinate_from_string(end_c)
                span = abs(r2 - r1) + 1
                if span > 2000 and (not workbook_index or span > workbook_index.sheets[action.sheet_name].total_rows * 2):
                    return ActionValidationResult(
                        is_valid=False,
                        status=AgentResponseStatusEnum.VALIDATION_ERROR,
                        action_id=action.action_id,
                        action_type=action.action_type,
                        target_ref=action.target_range,
                        error_message=f"Scope violation: formatting range '{action.target_range}' ({span} rows) exceeds safe boundary.",
                    )
            except Exception:
                pass

        return ActionValidationResult(
            is_valid=True,
            status=AgentResponseStatusEnum.SUCCESS,
            action_id=action.action_id,
            action_type=action.action_type,
            target_ref=action.target_range,
        )

    @classmethod
    def _validate_set_number_format(cls, action: SpreadsheetAction) -> ActionValidationResult:
        if not action.target_cell and not action.target_range:
            return ActionValidationResult(
                is_valid=False,
                status=AgentResponseStatusEnum.VALIDATION_ERROR,
                action_id=action.action_id,
                action_type=action.action_type,
                error_message="SET_NUMBER_FORMAT requires target_cell or target_range.",
            )
        if not action.number_format:
            return ActionValidationResult(
                is_valid=False,
                status=AgentResponseStatusEnum.VALIDATION_ERROR,
                action_id=action.action_id,
                action_type=action.action_type,
                error_message="SET_NUMBER_FORMAT requires number_format string.",
            )
        return ActionValidationResult(
            is_valid=True,
            status=AgentResponseStatusEnum.SUCCESS,
            action_id=action.action_id,
            action_type=action.action_type,
            target_ref=action.target_range or action.target_cell,
        )

    @classmethod
    def _validate_clear_content(
        cls,
        action: SpreadsheetAction,
        workbook_index: Optional[WorkbookMetadataIndex],
    ) -> ActionValidationResult:
        if not action.target_cell and not action.target_range:
            return ActionValidationResult(
                is_valid=False,
                status=AgentResponseStatusEnum.VALIDATION_ERROR,
                action_id=action.action_id,
                action_type=action.action_type,
                error_message="CLEAR_CONTENT requires target_cell or target_range.",
            )
        # Protect against unconfirmed entire sheet clearing
        if action.target_range and ":" in action.target_range and workbook_index:
            s_entry = workbook_index.sheets.get(action.sheet_name)
            if s_entry and action.target_range == s_entry.used_range and s_entry.total_rows > 10:
                req = ClarificationRequest(
                    question=f"Instruksi akan menghapus seluruh data pada sheet '{action.sheet_name}' ({s_entry.used_range}). Apakah Anda yakin?",
                    reason="Destructive whole-sheet clear operation detected.",
                    target_parameter="clear_sheet_confirmation",
                    options=["Ya, hapus seluruh sheet", "Batalkan"],
                )
                return ActionValidationResult(
                    is_valid=False,
                    status=AgentResponseStatusEnum.CLARIFICATION,
                    action_id=action.action_id,
                    action_type=action.action_type,
                    target_ref=action.target_range,
                    error_message=f"Whole-sheet clear requires explicit confirmation.",
                    clarification_request=req,
                )
        return ActionValidationResult(
            is_valid=True,
            status=AgentResponseStatusEnum.SUCCESS,
            action_id=action.action_id,
            action_type=action.action_type,
            target_ref=action.target_range or action.target_cell,
        )

    @classmethod
    def _validate_create_chart(
        cls,
        action: SpreadsheetAction,
        workbook_index: Optional[WorkbookMetadataIndex] = None,
        grid: Optional[RawSheetGrid] = None,
    ) -> ActionValidationResult:
        """Validates CREATE_CHART action parameters, destination, and source column availability."""
        if not action.chart_spec:
            return ActionValidationResult(
                is_valid=False,
                status=AgentResponseStatusEnum.VALIDATION_ERROR,
                action_id=action.action_id,
                action_type=action.action_type,
                error_message="CREATE_CHART requires chart_spec.",
            )

        spec = action.chart_spec
        dest = spec.destination_cell or action.target_cell
        if not dest:
            return ActionValidationResult(
                is_valid=False,
                status=AgentResponseStatusEnum.VALIDATION_ERROR,
                action_id=action.action_id,
                action_type=action.action_type,
                error_message="CREATE_CHART requires destination_cell coordinate.",
            )

        # Validate destination format
        dest_clean = dest.strip().upper()
        if not re.match(r"^[A-Z]{1,3}\d+$", dest_clean):
            return ActionValidationResult(
                is_valid=False,
                status=AgentResponseStatusEnum.VALIDATION_ERROR,
                action_id=action.action_id,
                action_type=action.action_type,
                error_message=f"Invalid destination cell coordinate: '{dest}'.",
            )

        # If workbook_index provided, verify sheet and columns if specified
        allowed_virtual_sheets = {"Dashboard", "Sheetsly_Calc", "Dasbor"}
        if workbook_index and action.sheet_name not in allowed_virtual_sheets:
            s_entry = workbook_index.sheets.get(action.sheet_name)
            if not s_entry:
                return ActionValidationResult(
                    is_valid=False,
                    status=AgentResponseStatusEnum.VALIDATION_ERROR,
                    action_id=action.action_id,
                    action_type=action.action_type,
                    error_message=f"Sheet '{action.sheet_name}' not found.",
                )

        # Spatial Collision Check against existing charts on the same sheet
        if grid and grid.charts and action.chart_spec:
            try:
                dest_col_str, dest_row = coordinate_from_string(dest_clean)
                dest_col = column_index_from_string(dest_col_str)
                w = action.chart_spec.width_cols
                h = action.chart_spec.height_rows
                new_box = (dest_col, dest_row, dest_col + w - 1, dest_row + h - 1)

                for existing_id, existing_c in grid.charts.items():
                    if existing_id == action.chart_spec.chart_id:
                        continue
                    ex_dest = existing_c.get("destination_cell") or existing_c.get("anchor_cell")
                    if not ex_dest:
                        continue
                    ex_col_str, ex_row = coordinate_from_string(ex_dest.strip().upper())
                    ex_col = column_index_from_string(ex_col_str)
                    ex_w = existing_c.get("width_cols", 7)
                    ex_h = existing_c.get("height_rows", 14)
                    ex_box = (ex_col, ex_row, ex_col + ex_w - 1, ex_row + ex_h - 1)

                    # Bounding box overlap check:
                    is_disjoint = (
                        new_box[2] < ex_box[0]
                        or new_box[0] > ex_box[2]
                        or new_box[3] < ex_box[1]
                        or new_box[1] > ex_box[3]
                    )
                    if not is_disjoint:
                        chart_name = existing_c.get("title") or "Chart"
                        req = ClarificationRequest(
                            question=f"Target sel '{dest_clean}' tumpang tindih dengan chart '{chart_name}' di '{ex_dest}'. Silakan pilih sel tujuan lain yang kosong.",
                            reason="Chart spatial collision: requested area overlaps an existing chart.",
                            target_parameter="chart_placement_collision",
                            options=["Pilih lokasi lain", "Batalkan"],
                        )
                        return ActionValidationResult(
                            is_valid=False,
                            status=AgentResponseStatusEnum.CLARIFICATION,
                            action_id=action.action_id,
                            action_type=action.action_type,
                            target_ref=dest_clean,
                            clarification_request=req,
                            error_message=f"Target chart region '{dest_clean}' overlaps with existing chart '{chart_name}' at '{ex_dest}'.",
                        )
            except Exception:
                pass

        return ActionValidationResult(
            is_valid=True,
            status=AgentResponseStatusEnum.SUCCESS,
            action_id=action.action_id,
            action_type=action.action_type,
            target_ref=dest_clean,
        )

    @classmethod
    def _validate_update_chart(
        cls,
        action: SpreadsheetAction,
        workbook_index: Optional[WorkbookMetadataIndex] = None,
    ) -> ActionValidationResult:
        """Validates UPDATE_CHART action parameters."""
        if not action.chart_spec:
            return ActionValidationResult(
                is_valid=False,
                status=AgentResponseStatusEnum.VALIDATION_ERROR,
                action_id=action.action_id,
                action_type=action.action_type,
                error_message="UPDATE_CHART requires chart_spec.",
            )
        return ActionValidationResult(
            is_valid=True,
            status=AgentResponseStatusEnum.SUCCESS,
            action_id=action.action_id,
            action_type=action.action_type,
            target_ref=action.chart_spec.destination_cell if action.chart_spec else None,
        )

    @classmethod
    def _validate_move_chart(
        cls,
        action: SpreadsheetAction,
        workbook_index: Optional[WorkbookMetadataIndex] = None,
    ) -> ActionValidationResult:
        """Validates MOVE_CHART target destination cell."""
        dest = action.target_cell or (action.chart_spec.destination_cell if action.chart_spec else None)
        if not dest or not re.match(r"^[A-Z]{1,3}\d+$", dest.strip().upper()):
            return ActionValidationResult(
                is_valid=False,
                status=AgentResponseStatusEnum.VALIDATION_ERROR,
                action_id=action.action_id,
                action_type=action.action_type,
                error_message=f"Invalid chart move destination: '{dest}'.",
            )
        return ActionValidationResult(
            is_valid=True,
            status=AgentResponseStatusEnum.SUCCESS,
            action_id=action.action_id,
            action_type=action.action_type,
            target_ref=dest.strip().upper(),
        )

    @classmethod
    def _validate_resize_chart(
        cls,
        action: SpreadsheetAction,
        workbook_index: Optional[WorkbookMetadataIndex] = None,
    ) -> ActionValidationResult:
        """Validates RESIZE_CHART dimension bounds."""
        if not action.chart_spec or action.chart_spec.width_cols < 2 or action.chart_spec.height_rows < 2:
            return ActionValidationResult(
                is_valid=False,
                status=AgentResponseStatusEnum.VALIDATION_ERROR,
                action_id=action.action_id,
                action_type=action.action_type,
                error_message="RESIZE_CHART requires valid width_cols >= 2 and height_rows >= 2.",
            )
        return ActionValidationResult(
            is_valid=True,
            status=AgentResponseStatusEnum.SUCCESS,
            action_id=action.action_id,
            action_type=action.action_type,
            target_ref=action.chart_spec.destination_cell,
        )

    @classmethod
    def _validate_create_worksheet(
        cls,
        action: SpreadsheetAction,
        workbook_index: Optional[WorkbookMetadataIndex] = None,
    ) -> ActionValidationResult:
        """Validates CREATE_WORKSHEET parameters."""
        sheet_name = action.sheet_name.strip()
        if not sheet_name:
            return ActionValidationResult(
                is_valid=False,
                status=AgentResponseStatusEnum.VALIDATION_ERROR,
                action_id=action.action_id,
                action_type=action.action_type,
                error_message="Worksheet name cannot be empty.",
            )
        return ActionValidationResult(
            is_valid=True,
            status=AgentResponseStatusEnum.SUCCESS,
            action_id=action.action_id,
            action_type=action.action_type,
            target_ref=sheet_name,
        )

    @classmethod
    def _validate_delete_chart(
        cls,
        action: SpreadsheetAction,
        workbook_index: Optional[WorkbookMetadataIndex] = None,
    ) -> ActionValidationResult:
        """Validates DELETE_CHART action parameters."""
        return ActionValidationResult(
            is_valid=True,
            status=AgentResponseStatusEnum.SUCCESS,
            action_id=action.action_id,
            action_type=action.action_type,
            target_ref=action.target_cell or (action.chart_spec.destination_cell if action.chart_spec else None),
        )

    @classmethod
    def _validate_create_kpi(
        cls,
        action: SpreadsheetAction,
        workbook_index: Optional[WorkbookMetadataIndex] = None,
    ) -> ActionValidationResult:
        """Validates CREATE_KPI action parameters and destination cell."""
        if not action.kpi_spec:
            return ActionValidationResult(
                is_valid=False,
                status=AgentResponseStatusEnum.VALIDATION_ERROR,
                action_id=action.action_id,
                action_type=action.action_type,
                error_message="CREATE_KPI requires kpi_spec.",
            )
        dest = action.kpi_spec.destination_cell
        if not dest or not re.match(r"^[A-Z]{1,3}\d+$", dest.strip().upper()):
            return ActionValidationResult(
                is_valid=False,
                status=AgentResponseStatusEnum.VALIDATION_ERROR,
                action_id=action.action_id,
                action_type=action.action_type,
                error_message=f"Invalid KPI destination cell: '{dest}'.",
            )
        return ActionValidationResult(
            is_valid=True,
            status=AgentResponseStatusEnum.SUCCESS,
            action_id=action.action_id,
            action_type=action.action_type,
            target_ref=dest.strip().upper(),
        )

    @classmethod
    def _check_cell_collision(
        cls,
        grid: RawSheetGrid,
        cell_coord: str,
        expected_formula: Optional[str] = None,
        expected_value: Optional[Any] = None,
    ) -> Optional[str]:
        """Checks if cell contains conflicting existing value or formula."""
        try:
            col_str, row_int = coordinate_from_string(cell_coord.upper())
            col_int = column_index_from_string(col_str)
            if (row_int, col_int) in grid.cells:
                cell = grid.cells[(row_int, col_int)]
                # If cell is empty, no collision
                if cell.is_empty and not cell.formula and (cell.original_value is None or str(cell.original_value).strip() == ""):
                    return None

                # Check if cell already satisfies expected formula
                if expected_formula and cell.formula:
                    norm_existing = cell.formula.strip().upper().replace(" ", "")
                    norm_expected = expected_formula.strip().upper().replace(" ", "")
                    if norm_existing == norm_expected:
                        return None

                # Check if cell already satisfies expected value
                if expected_value is not None and not cell.formula:
                    if str(cell.parsed_value).strip().lower() == str(expected_value).strip().lower() or str(cell.original_value).strip().lower() == str(expected_value).strip().lower():
                        return None

                if cell.formula:
                    return f"formula: {cell.formula}"
                if cell.original_value is not None and str(cell.original_value).strip() != "":
                    return str(cell.original_value).strip()
        except Exception:
            pass
        return None
