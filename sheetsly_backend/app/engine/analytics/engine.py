"""Core deterministic Analytical Engine executing validated instructions."""

import time
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
from openpyxl.utils import column_index_from_string

from app.core.errors import SheetNotFoundError
from app.engine.parser.sheet_reader import RawSheetGrid
from app.engine.pipeline import ingestion_pipeline
from app.engine.profiler.type_detector import TypeDetector
from app.models.schemas import DataTypeEnum, TableRegion
from .aggregations import DeterministicAggregator
from .filters import DeterministicFilterEngine
from .instruction_model import (
    AggregationOpEnum,
    AggregationSpec,
    AnalyticalInstruction,
    OperationEnum,
)
from .lineage import LineageBuilder
from .result_model import (
    AnalyticalResult,
    ResultTypeEnum,
    SeriesDataPoint,
    TableResultData,
)
from .validator import AnalyticalValidationError, InstructionValidator


class AnalyticalEngine:
    """Authoritative deterministic analytical execution engine."""

    def __init__(self):
        pass

    def execute(self, instruction: AnalyticalInstruction) -> AnalyticalResult:
        """
        Validates and executes an AnalyticalInstruction deterministically.
        Produces a structured AnalyticalResult with complete lineage.
        """
        start_time = time.perf_counter()
        dataset_id = instruction.dataset_id
        sheet_name = instruction.sheet_name

        # 1. Resolve Sheet and Table
        grid = ingestion_pipeline.get_sheet_grid(dataset_id, sheet_name)
        overview = ingestion_pipeline.get_overview(dataset_id)
        sheet_meta = next((s for s in overview.sheets if s.name == sheet_name), None)

        if not sheet_meta:
            raise SheetNotFoundError(sheet_name)

        if not sheet_meta.tables:
            raise AnalyticalValidationError(f"Worksheet '{sheet_name}' contains no detected tabular data regions.")

        # Find target table
        if instruction.table_id:
            table = next((t for t in sheet_meta.tables if t.table_id == instruction.table_id), None)
            if not table:
                raise AnalyticalValidationError(
                    f"Table with ID '{instruction.table_id}' not found in sheet '{sheet_name}'.",
                    details={"table_id": instruction.table_id},
                )
        else:
            table = sheet_meta.tables[0]

        # 2. Schema and Type Validation
        InstructionValidator.validate(instruction, table)

        # 3. Build DataFrame from TableRegion
        df, original_row_numbers = self._table_to_dataframe(grid, table)
        total_table_rows = len(df)
        calculation_steps: List[str] = [
            f"Loaded table '{table.name}' ({table.range_address}) with {total_table_rows} records and {len(table.columns)} columns."
        ]
        operations_performed: List[str] = []

        # 4. Apply Filters
        filtered_df = df
        retained_row_indices = list(df.index)
        excluded_row_indices = []
        filter_descriptions = []

        if instruction.filters:
            filtered_df, retained_row_indices, excluded_row_indices, filter_descriptions = (
                DeterministicFilterEngine.apply_filters(
                    df, instruction.filters, instruction.filter_combination
                )
            )
            comb_str = f" {instruction.filter_combination.value} "
            step_desc = f"Applied filter(s) [{comb_str.join(filter_descriptions)}]: retained {len(retained_row_indices)} of {total_table_rows} rows."
            calculation_steps.append(step_desc)
            operations_performed.append("FILTER")

        # 5. Route to Operation Handler
        op = instruction.operation

        # A. Scalar Calculations (SUM, AVG, MIN, MAX, MEDIAN, DISTINCT_COUNT, COUNT_VALUES, COUNT_ROWS)
        # Composed operations (SUMIF, SUMIFS, COUNTIF, COUNTIFS) evaluate identically after filtering
        if op in {
            OperationEnum.SUM,
            OperationEnum.COUNT_ROWS,
            OperationEnum.COUNT_VALUES,
            OperationEnum.DISTINCT_COUNT,
            OperationEnum.AVERAGE,
            OperationEnum.MIN,
            OperationEnum.MAX,
            OperationEnum.MEDIAN,
            OperationEnum.SUMIF,
            OperationEnum.SUMIFS,
            OperationEnum.COUNTIF,
            OperationEnum.COUNTIFS,
        }:
            target_col = instruction.target_column

            # Map composed conditional ops to underlying aggregator primitive
            agg_op = op
            if op in {OperationEnum.SUMIF, OperationEnum.SUMIFS}:
                agg_op = OperationEnum.SUM
                operations_performed.append("SUM")
            elif op in {OperationEnum.COUNTIF, OperationEnum.COUNTIFS}:
                agg_op = OperationEnum.COUNT_VALUES if target_col else OperationEnum.COUNT_ROWS
                operations_performed.append(agg_op.value)
            else:
                operations_performed.append(op.value)

            series_to_calc = filtered_df[target_col] if target_col and target_col in filtered_df.columns else pd.Series([], dtype=object)

            raw_val, formatted_val, op_notes = DeterministicAggregator.calculate_scalar(
                series_to_calc, agg_op, total_rows_in_selection=len(filtered_df)
            )
            calculation_steps.extend(op_notes)

            lineage = LineageBuilder.build_lineage(
                dataset_id=dataset_id,
                sheet_name=sheet_name,
                table=table,
                target_column=target_col,
                total_table_rows=total_table_rows,
                retained_row_indices=retained_row_indices,
                excluded_row_indices=excluded_row_indices,
                filters_applied=filter_descriptions,
                grouping_applied=[],
                operations_performed=operations_performed,
                calculation_steps=calculation_steps,
                start_time_seconds=start_time,
            )

            return AnalyticalResult(
                result_type=ResultTypeEnum.SCALAR,
                operation=op.value,
                scalar_value=raw_val,
                scalar_formatted=formatted_val,
                series_data=None,
                table_data=None,
                lineage=lineage,
            )

        # B. GROUP_BY Operation
        if op == OperationEnum.GROUP_BY:
            operations_performed.append("GROUP_BY")
            group_cols = instruction.group_by_columns
            aggs = instruction.aggregations

            grouped_records = self._execute_group_by(filtered_df, group_cols, aggs)
            calculation_steps.append(
                f"Grouped by {', '.join(group_cols)} with {len(aggs)} aggregation(s): produced {len(grouped_records)} group records."
            )

            result_df = pd.DataFrame(grouped_records)

            # Apply Sort if specified
            if instruction.sort and not result_df.empty:
                sort_col = instruction.sort.column
                if sort_col in result_df.columns:
                    result_df = result_df.sort_values(by=sort_col, ascending=instruction.sort.ascending)
                    order_label = "ASC" if instruction.sort.ascending else "DESC"
                    calculation_steps.append(f"Sorted results by '{sort_col}' {order_label}.")
                    operations_performed.append("SORT")

            # Apply Limit if specified
            if instruction.limit and not result_df.empty:
                result_df = result_df.head(instruction.limit)
                calculation_steps.append(f"Limited results to top {instruction.limit} records.")
                operations_performed.append("LIMIT")

            # Format Table Data & Series Data
            cols_list = list(result_df.columns)
            rows_list = result_df.to_dict(orient="records")

            # Check if suitable for 1D series (1 group col)
            series_points = None
            if len(group_cols) == 1 and len(aggs) >= 1 and not result_df.empty:
                g_col = group_cols[0]
                primary_metric_col = aggs[0].alias or f"{aggs[0].operation.value}_{aggs[0].column}"
                if primary_metric_col in result_df.columns:
                    series_points = [
                        SeriesDataPoint(label=str(r[g_col]), value=r[primary_metric_col]) for r in rows_list
                    ]

            lineage = LineageBuilder.build_lineage(
                dataset_id=dataset_id,
                sheet_name=sheet_name,
                table=table,
                target_column=None,
                total_table_rows=total_table_rows,
                retained_row_indices=retained_row_indices,
                excluded_row_indices=excluded_row_indices,
                filters_applied=filter_descriptions,
                grouping_applied=group_cols,
                operations_performed=operations_performed,
                calculation_steps=calculation_steps,
                start_time_seconds=start_time,
            )

            return AnalyticalResult(
                result_type=ResultTypeEnum.TABLE,
                operation=op.value,
                scalar_value=None,
                scalar_formatted=None,
                series_data=series_points,
                table_data=TableResultData(
                    columns=cols_list,
                    rows=rows_list,
                    total_rows=len(rows_list),
                ),
                lineage=lineage,
            )

        # C. FILTER / SORT (Tabular slices)
        if op in {OperationEnum.FILTER, OperationEnum.SORT}:
            result_df = filtered_df

            if instruction.sort and not result_df.empty:
                sort_col = instruction.sort.column
                if sort_col in result_df.columns:
                    result_df = result_df.sort_values(by=sort_col, ascending=instruction.sort.ascending)
                    order_label = "ASC" if instruction.sort.ascending else "DESC"
                    calculation_steps.append(f"Sorted by '{sort_col}' {order_label}.")
                    operations_performed.append("SORT")

            if instruction.limit and not result_df.empty:
                result_df = result_df.head(instruction.limit)
                calculation_steps.append(f"Limited results to {instruction.limit} records.")
                operations_performed.append("LIMIT")

            cols_list = list(result_df.columns)
            rows_list = result_df.to_dict(orient="records")

            lineage = LineageBuilder.build_lineage(
                dataset_id=dataset_id,
                sheet_name=sheet_name,
                table=table,
                target_column=instruction.target_column,
                total_table_rows=total_table_rows,
                retained_row_indices=retained_row_indices,
                excluded_row_indices=excluded_row_indices,
                filters_applied=filter_descriptions,
                grouping_applied=[],
                operations_performed=operations_performed,
                calculation_steps=calculation_steps,
                start_time_seconds=start_time,
            )

            return AnalyticalResult(
                result_type=ResultTypeEnum.TABLE,
                operation=op.value,
                scalar_value=None,
                scalar_formatted=None,
                series_data=None,
                table_data=TableResultData(
                    columns=cols_list,
                    rows=rows_list,
                    total_rows=len(rows_list),
                ),
                lineage=lineage,
            )

        raise AnalyticalValidationError(f"Unsupported analytical operation '{op}'.")

    def _table_to_dataframe(
        self, grid: RawSheetGrid, table: TableRegion
    ) -> Tuple[pd.DataFrame, List[int]]:
        """Converts table data rows from a RawSheetGrid into a typed pandas DataFrame."""
        if not table.data_range:
            return pd.DataFrame(), []

        try:
            start_ref, end_ref = table.data_range.split(":")
            start_row = int("".join(ch for ch in start_ref if ch.isdigit()))
            end_row = int("".join(ch for ch in end_ref if ch.isdigit()))
        except Exception:
            return pd.DataFrame(), []

        rows_data = []
        original_row_indices = []

        # Map column letters to column metadata
        col_accessors = []
        for col in table.columns:
            c_idx = column_index_from_string(col.source_column_letter)
            col_accessors.append((col.name, c_idx, col.data_type))

        for r in range(start_row, end_row + 1):
            row_dict = {}
            for col_name, c_idx, dt in col_accessors:
                cell = grid.get_cell(r, c_idx)
                raw_val = cell.original_value
                if raw_val is not None:
                    _, parsed_val = TypeDetector.detect_value_type(raw_val)
                    row_dict[col_name] = parsed_val if parsed_val is not None else raw_val
                else:
                    row_dict[col_name] = None
            rows_data.append(row_dict)
            original_row_indices.append(r)

        df = pd.DataFrame(rows_data, index=original_row_indices)
        return df, original_row_indices

    def _execute_group_by(
        self,
        df: pd.DataFrame,
        group_cols: List[str],
        aggs: List[AggregationSpec],
    ) -> List[Dict[str, Any]]:
        """Calculates multi-column group aggregations with precise aggregation semantics."""
        if df.empty:
            return []

        # Group rows by tuple of group values
        grouped = df.groupby(group_cols, dropna=False, as_index=False)
        result_rows = []

        for group_keys, group_sub_df in grouped:
            row_res: Dict[str, Any] = {}

            # Assign group keys (handle single key vs tuple)
            if len(group_cols) == 1:
                key_val = group_keys[0] if isinstance(group_keys, tuple) else group_keys
                row_res[group_cols[0]] = key_val
            else:
                for idx, g_col in enumerate(group_cols):
                    row_res[g_col] = group_keys[idx]

            # Calculate each aggregation
            for agg in aggs:
                col_name = agg.column
                agg_op = agg.operation
                res_col_name = agg.alias or f"{agg_op.value}_{col_name}"

                series = group_sub_df[col_name]
                raw_val, _, _ = DeterministicAggregator.calculate_scalar(
                    series, agg_op, total_rows_in_selection=len(group_sub_df)
                )
                row_res[res_col_name] = raw_val

            result_rows.append(row_res)

        return result_rows


analytical_engine = AnalyticalEngine()
