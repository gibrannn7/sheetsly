"""Data quality assessment engine detecting missing values, duplicates, mixed types, broken formulas, and anomalies."""

from typing import Any, List, Set, Tuple
from openpyxl.utils import get_column_letter

from app.engine.parser.sheet_reader import RawSheetGrid
from app.models.schemas import (
    DataQualityIssue,
    DataQualityReport,
    DataTypeEnum,
    IssueSeverityEnum,
    SemanticTypeEnum,
    TableRegion,
)
from .type_detector import TypeDetector

EXCEL_ERROR_VALUES = {"#VALUE!", "#REF!", "#DIV/0!", "#N/A", "#NAME?", "#NUM!", "#NULL!"}


class DataQualityEngine:
    """Evaluates workbook, sheet, and table data hygiene deterministically."""

    @classmethod
    def evaluate_sheet_quality(
        cls,
        grid: RawSheetGrid,
        tables: List[TableRegion],
    ) -> DataQualityReport:
        """
        Executes comprehensive data quality checks on a sheet and its detected tables.
        """
        issues: List[DataQualityIssue] = []

        # 1. Check for Broken Formulas across sheet
        broken_formula_cells: List[str] = []
        for (r, c), cell in grid.cells.items():
            val_str = str(cell.original_value or "").strip().upper()
            if val_str in EXCEL_ERROR_VALUES:
                broken_formula_cells.append(cell.coordinate.cell_ref)

        if broken_formula_cells:
            issues.append(
                DataQualityIssue(
                    issue_type="BROKEN_FORMULAS",
                    severity=IssueSeverityEnum.CRITICAL,
                    message=f"Found {len(broken_formula_cells)} cells containing Excel calculation errors ({', '.join(set(str(grid.cells[(int(ref[1:]), 1)].original_value) for ref in broken_formula_cells[:3])) if False else 'e.g. #REF!, #VALUE!'}).",
                    sheet_name=grid.sheet_name,
                    affected_cells_count=len(broken_formula_cells),
                    sample_locations=broken_formula_cells[:5],
                )
            )

        # 2. Table-Specific Quality Checks
        for table in tables:
            cls._check_table_quality(grid, table, issues)

        # 3. Compute overall score
        score = 100.0
        for issue in issues:
            if issue.severity == IssueSeverityEnum.CRITICAL:
                score -= 15.0
            elif issue.severity == IssueSeverityEnum.WARNING:
                score -= 5.0
            elif issue.severity == IssueSeverityEnum.INFO:
                score -= 2.0

        final_score = round(max(0.0, min(100.0, score)), 1)

        summary = (
            f"Quality check passed with score {final_score}/100. No major issues detected."
            if not issues
            else f"Quality assessment completed ({final_score}/100) with {len(issues)} issue(s) detected."
        )

        return DataQualityReport(
            overall_score=final_score,
            total_issues=len(issues),
            issues=issues,
            summary=summary,
        )

    @classmethod
    def _check_table_quality(
        cls,
        grid: RawSheetGrid,
        table: TableRegion,
        issues: List[DataQualityIssue],
    ) -> None:
        """Runs checks for missing values, duplicates, mixed types, and inconsistencies on a single table."""
        # Parse table row span
        if not table.data_range:
            return

        # Get rows in data range
        try:
            start_ref, end_ref = table.data_range.split(":")
            # Extract row numbers
            start_row = int("".join(ch for ch in start_ref if ch.isdigit()))
            end_row = int("".join(ch for ch in end_ref if ch.isdigit()))
        except Exception:
            return

        table_data_rows = list(range(start_row, end_row + 1))
        if not table_data_rows:
            return

        # -------------------------------------------------------------
        # A. Missing Values & Mixed Data Types per Column
        # -------------------------------------------------------------
        for col in table.columns:
            try:
                # Find column number from letter
                from openpyxl.utils import column_index_from_string
                col_idx = column_index_from_string(col.source_column_letter)
            except Exception:
                continue

            missing_cells: List[str] = []
            type_mismatch_cells: List[str] = []

            for r in table_data_rows:
                cell = grid.get_cell(r, col_idx)
                if cell.is_empty:
                    missing_cells.append(cell.coordinate.cell_ref)
                else:
                    # Check type mismatch
                    cell_type, _ = TypeDetector.detect_value_type(cell.original_value)
                    if col.data_type in {DataTypeEnum.INTEGER, DataTypeEnum.FLOAT, DataTypeEnum.CURRENCY, DataTypeEnum.PERCENTAGE}:
                        if cell_type == DataTypeEnum.STRING:
                            type_mismatch_cells.append(cell.coordinate.cell_ref)
                    elif col.data_type in {DataTypeEnum.DATE, DataTypeEnum.DATETIME}:
                        if cell_type not in {DataTypeEnum.DATE, DataTypeEnum.DATETIME}:
                            type_mismatch_cells.append(cell.coordinate.cell_ref)

            # Report missing values
            if missing_cells:
                null_pct = len(missing_cells) / len(table_data_rows)
                severity = IssueSeverityEnum.WARNING if null_pct > 0.15 else IssueSeverityEnum.INFO
                issues.append(
                    DataQualityIssue(
                        issue_type="MISSING_VALUES",
                        severity=severity,
                        message=f"Column '{col.name}' has {len(missing_cells)} empty cells ({null_pct:.1%}).",
                        sheet_name=grid.sheet_name,
                        table_id=table.table_id,
                        column_name=col.name,
                        affected_cells_count=len(missing_cells),
                        sample_locations=missing_cells[:5],
                    )
                )

            # Report type mismatch
            if type_mismatch_cells:
                issues.append(
                    DataQualityIssue(
                        issue_type="MIXED_DATA_TYPES",
                        severity=IssueSeverityEnum.WARNING,
                        message=f"Column '{col.name}' is expected to be {col.data_type.value}, but contains {len(type_mismatch_cells)} text/incompatible value(s).",
                        sheet_name=grid.sheet_name,
                        table_id=table.table_id,
                        column_name=col.name,
                        affected_cells_count=len(type_mismatch_cells),
                        sample_locations=type_mismatch_cells[:5],
                    )
                )

            # -------------------------------------------------------------
            # B. Duplicate Identifiers
            # -------------------------------------------------------------
            if col.semantic_type == SemanticTypeEnum.IDENTIFIER:
                seen_ids: Set[str] = set()
                duplicate_ids: List[str] = []
                for r in table_data_rows:
                    cell = grid.get_cell(r, col_idx)
                    if not cell.is_empty:
                        val_str = str(cell.original_value).strip()
                        if val_str in seen_ids:
                            duplicate_ids.append(cell.coordinate.cell_ref)
                        else:
                            seen_ids.add(val_str)

                if duplicate_ids:
                    issues.append(
                        DataQualityIssue(
                            issue_type="DUPLICATE_IDENTIFIERS",
                            severity=IssueSeverityEnum.CRITICAL,
                            message=f"Identifier column '{col.name}' contains {len(duplicate_ids)} duplicate value(s).",
                            sheet_name=grid.sheet_name,
                            table_id=table.table_id,
                            column_name=col.name,
                            affected_cells_count=len(duplicate_ids),
                            sample_locations=duplicate_ids[:5],
                        )
                    )

        # -------------------------------------------------------------
        # C. Duplicate Rows in Table
        # -------------------------------------------------------------
        seen_row_tuples: Set[Tuple[Any, ...]] = set()
        duplicate_row_indices: List[int] = []

        for r in table_data_rows:
            row_values = []
            for col in table.columns:
                try:
                    from openpyxl.utils import column_index_from_string
                    col_idx = column_index_from_string(col.source_column_letter)
                    c = grid.get_cell(r, col_idx)
                    row_values.append(str(c.original_value).strip() if c.original_value is not None else "")
                except Exception:
                    continue
            row_tuple = tuple(row_values)
            if row_tuple in seen_row_tuples:
                duplicate_row_indices.append(r)
            else:
                seen_row_tuples.add(row_tuple)

        if duplicate_row_indices:
            issues.append(
                DataQualityIssue(
                    issue_type="DUPLICATE_ROWS",
                    severity=IssueSeverityEnum.WARNING,
                    message=f"Table contains {len(duplicate_row_indices)} exact duplicate row(s).",
                    sheet_name=grid.sheet_name,
                    table_id=table.table_id,
                    affected_cells_count=len(duplicate_row_indices),
                    sample_locations=[f"Row {r}" for r in duplicate_row_indices[:5]],
                )
            )
