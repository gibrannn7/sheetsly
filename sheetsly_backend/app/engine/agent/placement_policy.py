"""Deterministic placement policy for formula and summary block destinations."""

import re
from typing import Any, Dict, List, Optional, Tuple
from openpyxl.utils.cell import column_index_from_string, coordinate_from_string, get_column_letter
from pydantic import BaseModel, Field

from app.engine.parser.sheet_reader import RawSheetGrid
from app.engine.profiler.workbook_index import (
    ColumnIndexEntry,
    SheetIndexEntry,
    TableIndexEntry,
    WorkbookMetadataIndex,
)
from app.models.schemas import DataTypeEnum, SemanticTypeEnum


class PlacementDecision(BaseModel):
    """Deterministic placement decision for summary formulas and labels."""

    sheet_name: str
    target_cell: str
    target_row: int
    target_col: int
    label_cell: Optional[str] = None
    label_value: Optional[str] = None
    label_col: Optional[int] = None
    placement_type: str = "SAFE_SUMMARY_ROW_BELOW"
    is_safe: bool = True
    confidence: float = 1.0
    number_format: Optional[str] = None
    reason: str = ""


class PlacementPolicy:
    """Calculates safe, collision-free destination cell coordinates for formulas and labels."""

    @classmethod
    def determine_placement(
        cls,
        table: TableIndexEntry,
        measure_col: ColumnIndexEntry,
        grid: Optional[RawSheetGrid] = None,
        explicit_target_cell: Optional[str] = None,
        query: str = "",
    ) -> PlacementDecision:
        """
        Determines the optimal, collision-free placement for a summary calculation.
        Hierarchy:
        1. Explicit user target
        2. Safe summary row below data
        3. Safe summary column right of data
        4. Dedicated summary block
        """
        # Priority 1: Explicit Target Cell in query or parameter
        target_override = explicit_target_cell
        if not target_override and query:
            explicit_match = re.search(r"\b(?:di|in|cell|sel)\s+([A-Z]{1,3}\d+)\b", query, re.IGNORECASE)
            if explicit_match:
                target_override = explicit_match.group(1).upper()

        if target_override:
            col_str, row_int = coordinate_from_string(target_override.upper())
            col_int = column_index_from_string(col_str)
            is_safe = True
            if grid and (row_int, col_int) in grid.cells:
                c_data = grid.cells[(row_int, col_int)]
                if not c_data.is_empty and c_data.original_value is not None and str(c_data.original_value).strip():
                    is_safe = False

            return PlacementDecision(
                sheet_name=table.sheet_name,
                target_cell=target_override.upper(),
                target_row=row_int,
                target_col=col_int,
                placement_type="EXPLICIT_TARGET",
                is_safe=is_safe,
                confidence=1.0,
                number_format=cls._inherit_number_format(measure_col),
                reason=f"Explicit target cell '{target_override}' requested by user.",
            )

        # Priority 2: Safe Summary Row immediately below table data
        target_col_letter = measure_col.source_column_letter.upper()
        target_col_int = column_index_from_string(target_col_letter)

        # Extract max data row from table data_range (e.g. 'A2:E101' -> 101)
        max_row = 101
        if table.data_range and ":" in table.data_range:
            try:
                _, end_cell = table.data_range.split(":")
                _, max_row = coordinate_from_string(end_cell)
            except Exception:
                max_row = table.row_count + 1
        elif table.range_address and ":" in table.range_address:
            try:
                _, end_cell = table.range_address.split(":")
                _, max_row = coordinate_from_string(end_cell)
            except Exception:
                max_row = table.row_count + 1

        summary_row = max_row + 1
        target_cell = f"{target_col_letter}{summary_row}"

        # Choose Label location (adjacent column to the left if available, or column A)
        label_col_int = max(1, target_col_int - 1)
        label_col_letter = get_column_letter(label_col_int)
        label_cell = f"{label_col_letter}{summary_row}" if label_col_int != target_col_int else None

        # Check collision on grid
        is_safe = True
        if grid:
            if cls._is_occupied(grid, summary_row, target_col_int):
                # Try 1 row further down
                summary_row += 1
                target_cell = f"{target_col_letter}{summary_row}"
                label_cell = f"{label_col_letter}{summary_row}" if label_col_int != target_col_int else None
                if cls._is_occupied(grid, summary_row, target_col_int):
                    is_safe = False

        label_text = f"Total {measure_col.name}" if "total" in query.lower() or "sum" in query.lower() else f"Summary {measure_col.name}"

        return PlacementDecision(
            sheet_name=table.sheet_name,
            target_cell=target_cell,
            target_row=summary_row,
            target_col=target_col_int,
            label_cell=label_cell,
            label_value=label_text if label_cell else None,
            label_col=label_col_int,
            placement_type="SAFE_SUMMARY_ROW_BELOW",
            is_safe=is_safe,
            confidence=0.95,
            number_format=cls._inherit_number_format(measure_col),
            reason=f"Placed summary formula at safe row {summary_row} immediately below {table.name}.",
        )

    @classmethod
    def _is_occupied(cls, grid: RawSheetGrid, row: int, col: int) -> bool:
        if (row, col) in grid.cells:
            cell = grid.cells[(row, col)]
            return not cell.is_empty and cell.original_value is not None and str(cell.original_value).strip() != ""
        return False

    @classmethod
    def _inherit_number_format(cls, col_meta: ColumnIndexEntry) -> str:
        """Determines inherited Excel number format string based on column metadata."""
        if col_meta.data_type == DataTypeEnum.CURRENCY:
            # Check samples for currency symbol
            sample_str = "".join([str(s) for s in col_meta.sample_values])
            if "Rp" in sample_str:
                return "Rp#,##0.00"
            return "$#,##0.00"
        elif col_meta.data_type == DataTypeEnum.PERCENTAGE:
            return "0.0%"
        elif col_meta.data_type == DataTypeEnum.INTEGER:
            return "#,##0"
        elif col_meta.data_type == DataTypeEnum.FLOAT:
            return "#,##0.00"
        return "#,##0.00"
