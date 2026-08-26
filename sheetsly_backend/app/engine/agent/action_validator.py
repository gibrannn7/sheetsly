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
        if workbook_index and action.sheet_name not in workbook_index.sheets:
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
            res = cls.validate_action(act, workbook_index, target_grid)
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
        if grid and not allow_overwrite:
            collision = cls._check_cell_collision(grid, action.target_cell)
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
        if grid and not allow_overwrite:
            collision = cls._check_cell_collision(grid, action.target_cell)
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
    def _check_cell_collision(cls, grid: RawSheetGrid, cell_coord: str) -> Optional[str]:
        """Checks if cell contains existing value or formula."""
        try:
            col_str, row_int = coordinate_from_string(cell_coord.upper())
            col_int = column_index_from_string(col_str)
            if (row_int, col_int) in grid.cells:
                cell = grid.cells[(row_int, col_int)]
                if cell.formula:
                    return f"formula: {cell.formula}"
                if cell.original_value is not None and str(cell.original_value).strip() != "":
                    return str(cell.original_value).strip()
        except Exception:
            pass
        return None
