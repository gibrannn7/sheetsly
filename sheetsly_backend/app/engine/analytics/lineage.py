"""Provenance and calculation lineage builder for full auditability."""

import time
from typing import List, Optional
from openpyxl.utils import get_column_letter

from app.models.schemas import TableRegion
from .result_model import CalculationLineage


class LineageBuilder:
    """Constructs auditable calculation lineage preserving source ranges, row counts, and steps."""

    @staticmethod
    def build_lineage(
        dataset_id: str,
        sheet_name: str,
        table: TableRegion,
        target_column: Optional[str],
        total_table_rows: int,
        retained_row_indices: List[int],
        excluded_row_indices: List[int],
        filters_applied: List[str],
        grouping_applied: List[str],
        operations_performed: List[str],
        calculation_steps: List[str],
        start_time_seconds: float,
    ) -> CalculationLineage:
        """Assembles a complete CalculationLineage object."""
        elapsed_ms = round((time.perf_counter() - start_time_seconds) * 1000.0, 2)

        # Determine physical source range
        source_range = table.range_address
        if target_column:
            # Find column letter for target column
            matching_col = next((c for c in table.columns if c.name == target_column), None)
            if matching_col and table.data_range:
                # E.g. If data range is A5:F50, target column is E, then E5:E50
                try:
                    start_ref, end_ref = table.data_range.split(":")
                    start_row = "".join(ch for ch in start_ref if ch.isdigit())
                    end_row = "".join(ch for ch in end_ref if ch.isdigit())
                    source_range = f"{matching_col.source_column_letter}{start_row}:{matching_col.source_column_letter}{end_row}"
                except Exception:
                    source_range = table.data_range

        source_columns = []
        if target_column:
            source_columns.append(target_column)
        if grouping_applied:
            for g in grouping_applied:
                if g not in source_columns:
                    source_columns.append(g)

        return CalculationLineage(
            dataset_id=dataset_id,
            sheet_name=sheet_name,
            table_id=table.table_id,
            source_range=source_range,
            source_columns=source_columns,
            total_table_rows=total_table_rows,
            rows_included=len(retained_row_indices),
            rows_excluded=len(excluded_row_indices),
            filters_applied=filters_applied,
            grouping_applied=grouping_applied,
            operations_performed=operations_performed,
            calculation_steps=calculation_steps,
            execution_time_ms=elapsed_ms,
        )
