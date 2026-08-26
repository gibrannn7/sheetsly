"""Independent Python execution and evaluation engine for spreadsheet formulas."""

import re
from typing import Any, Dict, List, Optional, Tuple
from openpyxl.utils.cell import column_index_from_string, coordinate_from_string

from app.engine.parser.sheet_reader import RawSheetGrid
from app.models.schemas import DataTypeEnum


class FormulaEvaluator:
    """Deterministically calculates the expected truth value of an Excel formula using Python."""

    @classmethod
    def evaluate(
        cls,
        formula: str,
        grid: RawSheetGrid,
        sheet_grids: Optional[Dict[str, RawSheetGrid]] = None,
    ) -> Tuple[Any, DataTypeEnum]:
        """
        Evaluates a formula string (e.g. '=SUM(D2:D101)') directly against the RawSheetGrid.
        Returns (evaluated_value, DataTypeEnum).
        """
        clean = formula.strip()
        if clean.startswith("="):
            clean = clean[1:].strip()

        match = re.match(r"^([A-Z0-9_]+)\s*\((.*)\)$", clean, re.IGNORECASE)
        if not match:
            return None, DataTypeEnum.UNKNOWN

        func_name = match.group(1).upper()
        args_str = match.group(2).strip()

        # Extract cells values
        values = cls._extract_values_from_range(args_str, grid, sheet_grids)

        if func_name == "SUM":
            numeric_vals = [float(v) for v in values if cls._is_number(v)]
            res = sum(numeric_vals) if numeric_vals else 0.0
            return (int(res) if res.is_integer() else round(res, 4)), DataTypeEnum.FLOAT

        elif func_name == "AVERAGE":
            numeric_vals = [float(v) for v in values if cls._is_number(v)]
            if not numeric_vals:
                return 0.0, DataTypeEnum.FLOAT
            res = sum(numeric_vals) / len(numeric_vals)
            return round(res, 4), DataTypeEnum.FLOAT

        elif func_name == "COUNT":
            numeric_vals = [v for v in values if cls._is_number(v)]
            return len(numeric_vals), DataTypeEnum.INTEGER

        elif func_name == "COUNTA":
            non_empty = [v for v in values if v is not None and str(v).strip() != ""]
            return len(non_empty), DataTypeEnum.INTEGER

        elif func_name == "MIN":
            numeric_vals = [float(v) for v in values if cls._is_number(v)]
            res = min(numeric_vals) if numeric_vals else 0.0
            return (int(res) if res.is_integer() else round(res, 4)), DataTypeEnum.FLOAT

        elif func_name == "MAX":
            numeric_vals = [float(v) for v in values if cls._is_number(v)]
            res = max(numeric_vals) if numeric_vals else 0.0
            return (int(res) if res.is_integer() else round(res, 4)), DataTypeEnum.FLOAT

        elif func_name == "MEDIAN":
            numeric_vals = sorted([float(v) for v in values if cls._is_number(v)])
            if not numeric_vals:
                return 0.0, DataTypeEnum.FLOAT
            n = len(numeric_vals)
            mid = n // 2
            res = (numeric_vals[mid] + numeric_vals[mid - 1]) / 2.0 if n % 2 == 0 else numeric_vals[mid]
            return (int(res) if res.is_integer() else round(res, 4)), DataTypeEnum.FLOAT

        return None, DataTypeEnum.UNKNOWN

    @classmethod
    def _extract_values_from_range(
        cls,
        range_str: str,
        grid: RawSheetGrid,
        sheet_grids: Optional[Dict[str, RawSheetGrid]],
    ) -> List[Any]:
        """Extracts cell values from an Excel range reference (e.g. 'D2:D101' or 'Sheet1!D2:D101')."""
        target_grid = grid
        clean_range = range_str.replace("$", "").strip()

        if "!" in clean_range:
            sheet_part, clean_range = clean_range.split("!")
            sheet_part = sheet_part.strip("'")
            if sheet_grids and sheet_part in sheet_grids:
                target_grid = sheet_grids[sheet_part]

        values = []
        if ":" in clean_range:
            start_ref, end_ref = clean_range.split(":")
            s_col_str, s_row = coordinate_from_string(start_ref)
            e_col_str, e_row = coordinate_from_string(end_ref)
            s_col = column_index_from_string(s_col_str)
            e_col = column_index_from_string(e_col_str)

            min_r, max_r = min(s_row, e_row), max(s_row, e_row)
            min_c, max_c = min(s_col, e_col), max(s_col, e_col)

            for r in range(min_r, max_r + 1):
                for c in range(min_c, max_c + 1):
                    cell = target_grid.get_cell(r, c)
                    if not cell.is_empty and cell.original_value is not None:
                        values.append(cell.parsed_value if cell.parsed_value is not None else cell.original_value)
        else:
            col_str, row_int = coordinate_from_string(clean_range)
            col_int = column_index_from_string(col_str)
            cell = target_grid.get_cell(row_int, col_int)
            if not cell.is_empty and cell.original_value is not None:
                values.append(cell.parsed_value if cell.parsed_value is not None else cell.original_value)

        return values

    @classmethod
    def _is_number(cls, val: Any) -> bool:
        if val is None:
            return False
        try:
            float(val)
            return True
        except (ValueError, TypeError):
            return False
