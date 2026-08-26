"""Authoritative Excel formula syntax, security, reference, circularity, and semantic validator."""

import re
from typing import Any, Dict, List, Optional, Set, Tuple
from openpyxl.utils.cell import column_index_from_string, coordinate_from_string
from pydantic import BaseModel, Field

from app.engine.profiler.workbook_index import (
    ColumnIndexEntry,
    SheetIndexEntry,
    TableIndexEntry,
    WorkbookMetadataIndex,
)
from app.models.schemas import DataTypeEnum, SemanticTypeEnum


SUPPORTED_FORMULA_FUNCTIONS: Set[str] = frozenset({
    "SUM", "AVERAGE", "COUNT", "COUNTA", "COUNTBLANK", "COUNTIF", "COUNTIFS",
    "SUMIF", "SUMIFS", "MIN", "MAX", "MEDIAN", "PRODUCT", "ROUND", "ROUNDUP", "ROUNDDOWN",
    "ABS", "SQRT", "POWER", "MOD", "IF", "AND", "OR", "NOT", "VLOOKUP", "HLOOKUP",
    "INDEX", "MATCH", "CONCATENATE", "LEFT", "RIGHT", "MID", "LEN", "TRIM", "UPPER", "LOWER",
    "TEXT", "DATE", "YEAR", "MONTH", "DAY", "HOUR", "MINUTE", "SECOND", "TODAY", "NOW",
})

DANGEROUS_PATTERNS = [
    re.compile(r"^[=+\-@]?\s*(cmd|powershell|bash|sh|cscript|wscript|mshta|regsvr32)\b", re.IGNORECASE),
    re.compile(r"\|\s*['\"]?\s*(cmd|powershell|bash|sh)", re.IGNORECASE),
    re.compile(r"=\s*HYPERLINK\s*\(\s*['\"](cmd|powershell|bash|http|file|ftp)", re.IGNORECASE),
    re.compile(r"=\s*WEBSERVICE\s*\(", re.IGNORECASE),
    re.compile(r"\[.+\]", re.IGNORECASE),
]


class FormulaValidationResult(BaseModel):
    """Detailed factual report of formula security, syntax, and reference validation."""

    is_valid: bool = False
    is_safe: bool = True
    formula: str
    function_name: Optional[str] = None
    target_cell: Optional[str] = None
    referenced_ranges: List[str] = Field(default_factory=list)
    referenced_sheets: List[str] = Field(default_factory=list)
    is_circular: bool = False
    error_message: Optional[str] = None
    security_warnings: List[str] = Field(default_factory=list)


class FormulaValidator:
    """Validates formula string against security rules, Excel syntax, circular references, and schema bounds."""

    @classmethod
    def validate_formula(
        cls,
        formula: str,
        target_cell: str,
        sheet_name: str,
        workbook_index: Optional[WorkbookMetadataIndex] = None,
        table_entry: Optional[TableIndexEntry] = None,
    ) -> FormulaValidationResult:
        """
        Executes complete 5-stage deterministic validation on an Excel formula string.
        """
        raw_formula = formula.strip()
        if not raw_formula.startswith("="):
            raw_formula = f"={raw_formula}"

        # 1. Security Check (DDE, Shell, External links)
        for pat in DANGEROUS_PATTERNS:
            if pat.search(raw_formula):
                return FormulaValidationResult(
                    is_valid=False,
                    is_safe=False,
                    formula=raw_formula,
                    target_cell=target_cell,
                    error_message=f"Formula rejected for security: dangerous external reference or command payload detected in '{raw_formula}'.",
                    security_warnings=["POTENTIAL_FORMULA_INJECTION_OR_DDE"],
                )

        # 2. Syntax & Function Name Extraction
        func_match = re.match(r"^=\s*([A-Z0-9_]+)\s*\((.*)\)$", raw_formula, re.IGNORECASE)
        if not func_match:
            # Check if simple arithmetic like =A1+B1
            if re.match(r"^=\s*[A-Z]{1,3}\d+\s*[\+\-\*\/]\s*[A-Z]{1,3}\d+", raw_formula, re.IGNORECASE):
                func_name = "ARITHMETIC_EXPR"
                args_str = raw_formula[1:]
            else:
                return FormulaValidationResult(
                    is_valid=False,
                    is_safe=True,
                    formula=raw_formula,
                    target_cell=target_cell,
                    error_message=f"Malformed formula syntax: '{raw_formula}'.",
                )
        else:
            func_name = func_match.group(1).upper()
            args_str = func_match.group(2).strip()

            if func_name not in SUPPORTED_FORMULA_FUNCTIONS:
                return FormulaValidationResult(
                    is_valid=False,
                    is_safe=True,
                    formula=raw_formula,
                    function_name=func_name,
                    target_cell=target_cell,
                    error_message=f"Unsupported formula function: '{func_name}'. Supported functions: {sorted(list(SUPPORTED_FORMULA_FUNCTIONS))[:10]}...",
                )

        # 3. Extract Referenced Ranges & Sheets
        # Matches: Sheet1!A1:B10 or 'My Sheet'!A1:B10 or A1:B10 or A1
        range_pattern = re.compile(
            r"(?:(?:'([^']+)'|([A-Za-z0-9_]+))!)?(\$?[A-Z]{1,3}\$?\d+(?::\$?[A-Z]{1,3}\$?\d+)?)",
            re.IGNORECASE,
        )
        matches = range_pattern.findall(args_str)

        ref_ranges: List[str] = []
        ref_sheets: List[str] = []

        for m in matches:
            sh_quoted, sh_plain, rng = m
            r_sheet = sh_quoted or sh_plain or sheet_name
            ref_sheets.append(r_sheet)
            clean_rng = rng.replace("$", "").upper()
            ref_ranges.append(clean_rng)

        # 4. Circular Reference Detection
        # Check if target_cell is contained inside any referenced range on the same sheet
        if target_cell:
            t_clean = target_cell.replace("$", "").upper()
            try:
                t_col_str, t_row_int = coordinate_from_string(t_clean)
                t_col_int = column_index_from_string(t_col_str)

                for r_sheet, r_rng in zip(ref_sheets, ref_ranges):
                    if r_sheet == sheet_name:
                        if ":" in r_rng:
                            start_ref, end_ref = r_rng.split(":")
                            s_col_str, s_row_int = coordinate_from_string(start_ref)
                            e_col_str, e_row_int = coordinate_from_string(end_ref)
                            s_col_int = column_index_from_string(s_col_str)
                            e_col_int = column_index_from_string(e_col_str)

                            min_c = min(s_col_int, e_col_int)
                            max_c = max(s_col_int, e_col_int)
                            min_r = min(s_row_int, e_row_int)
                            max_r = max(s_row_int, e_row_int)

                            if min_r <= t_row_int <= max_r and min_c <= t_col_int <= max_c:
                                return FormulaValidationResult(
                                    is_valid=False,
                                    is_safe=True,
                                    formula=raw_formula,
                                    function_name=func_name,
                                    target_cell=target_cell,
                                    referenced_ranges=ref_ranges,
                                    referenced_sheets=ref_sheets,
                                    is_circular=True,
                                    error_message=f"Circular reference detected: target cell '{target_cell}' is contained within referenced range '{r_rng}'.",
                                )
                        else:
                            if r_rng == t_clean:
                                return FormulaValidationResult(
                                    is_valid=False,
                                    is_safe=True,
                                    formula=raw_formula,
                                    function_name=func_name,
                                    target_cell=target_cell,
                                    referenced_ranges=ref_ranges,
                                    referenced_sheets=ref_sheets,
                                    is_circular=True,
                                    error_message=f"Circular reference detected: target cell '{target_cell}' references itself directly.",
                                )
            except Exception as e:
                return FormulaValidationResult(
                    is_valid=False,
                    is_safe=True,
                    formula=raw_formula,
                    function_name=func_name,
                    target_cell=target_cell,
                    error_message=f"Invalid cell coordinate parsing: {e}",
                )

        # 5. Schema Reference & Type Validation (if WorkbookMetadataIndex supplied)
        if workbook_index and ref_sheets:
            for sh in ref_sheets:
                if sh not in workbook_index.sheets:
                    return FormulaValidationResult(
                        is_valid=False,
                        is_safe=True,
                        formula=raw_formula,
                        function_name=func_name,
                        target_cell=target_cell,
                        referenced_ranges=ref_ranges,
                        referenced_sheets=ref_sheets,
                        error_message=f"Referenced worksheet '{sh}' does not exist in workbook.",
                    )

        # 6. Numeric Aggregation Semantic Type Check (e.g. SUM on text column)
        if table_entry and func_name in {"SUM", "AVERAGE", "MIN", "MAX", "MEDIAN", "PRODUCT"}:
            for r_rng in ref_ranges:
                start_ref = r_rng.split(":")[0] if ":" in r_rng else r_rng
                try:
                    c_letter, _ = coordinate_from_string(start_ref)
                    matching_cols = [c for c in table_entry.columns if c.source_column_letter.upper() == c_letter.upper()]
                    if matching_cols:
                        col_meta = matching_cols[0]
                        if col_meta.data_type in {DataTypeEnum.STRING, DataTypeEnum.UNKNOWN} and col_meta.semantic_type != SemanticTypeEnum.NUMERIC_MEASURE:
                            return FormulaValidationResult(
                                is_valid=False,
                                is_safe=True,
                                formula=raw_formula,
                                function_name=func_name,
                                target_cell=target_cell,
                                referenced_ranges=ref_ranges,
                                referenced_sheets=ref_sheets,
                                error_message=f"Cannot execute arithmetic function '{func_name}' on non-numeric text column '{col_meta.name}' ({c_letter}).",
                            )
                except Exception:
                    pass

        return FormulaValidationResult(
            is_valid=True,
            is_safe=True,
            formula=raw_formula,
            function_name=func_name,
            target_cell=target_cell,
            referenced_ranges=ref_ranges,
            referenced_sheets=ref_sheets,
            is_circular=False,
        )
