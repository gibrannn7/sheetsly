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
from .expressions import DimensionEvaluator, DimensionParser
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
from .temporal_evidence import TemporalEvidenceCalculator
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

        # 2. Schema and Type Validation (enforces strict allowlist & date compatibility)
        InstructionValidator.validate(instruction, table)

        # 3. Build DataFrame from TableRegion (Fast vectorized conversion)
        df, original_row_numbers = self._table_to_dataframe(grid, table)
        total_table_rows = len(df)
        calculation_steps: List[str] = [
            f"Loaded table '{table.name}' ({table.range_address}) with {total_table_rows} records and {len(table.columns)} columns."
        ]
        operations_performed: List[str] = []

        # 4. Apply Filters (Physical & Derived Dimensions)
        filtered_df = df
        retained_row_indices = list(df.index)
        excluded_row_indices = []
        filter_descriptions = []
        filter_cols = [f.column for f in instruction.filters]

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
                filter_columns=filter_cols,
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

        # B. GROUP_BY Operation (Supports physical columns and derived temporal dimensions)
        if op == OperationEnum.GROUP_BY:
            operations_performed.append("GROUP_BY")
            group_cols = instruction.group_by_columns
            aggs = instruction.aggregations

            # Materialize derived dimensions and their internal chronological sort keys
            exec_df = filtered_df.copy()
            internal_group_cols = []
            sort_key_cols = []
            has_temporal_dimension = False

            for g_col in group_cols:
                dim_parsed = DimensionParser.parse(g_col)
                if dim_parsed:
                    has_temporal_dimension = True
                    source_col = dim_parsed.source_column
                    if source_col in exec_df.columns:
                        disp_series, sort_series = DimensionEvaluator.evaluate(
                            exec_df[source_col], dim_parsed.operation
                        )
                        exec_df[g_col] = disp_series
                        sk_col = f"__sort_key_{g_col}"
                        exec_df[sk_col] = sort_series if sort_series is not None else disp_series
                        internal_group_cols.append(g_col)
                        internal_group_cols.append(sk_col)
                        sort_key_cols.append(sk_col)
                        calculation_steps.append(
                            f"Projected temporal dimension '{g_col}' from source column '{source_col}'."
                        )
                else:
                    internal_group_cols.append(g_col)

            grouped_records = self._execute_group_by(exec_df, internal_group_cols, aggs)
            calculation_steps.append(
                f"Grouped by {', '.join(group_cols)} with {len(aggs)} aggregation(s): produced {len(grouped_records)} group records."
            )

            result_df = pd.DataFrame(grouped_records)

            # Apply Sort (User-Specified or Default Chronological Ordering)
            if instruction.sort and not result_df.empty:
                sort_col = instruction.sort.column
                effective_sort_col = f"__sort_key_{sort_col}" if f"__sort_key_{sort_col}" in result_df.columns else sort_col
                if effective_sort_col in result_df.columns:
                    result_df = result_df.sort_values(by=effective_sort_col, ascending=instruction.sort.ascending)
                    order_label = "ASC" if instruction.sort.ascending else "DESC"
                    calculation_steps.append(f"Sorted results by '{sort_col}' {order_label}.")
                    operations_performed.append("SORT")
                elif sort_col in result_df.columns:
                    result_df = result_df.sort_values(by=sort_col, ascending=instruction.sort.ascending)
                    order_label = "ASC" if instruction.sort.ascending else "DESC"
                    calculation_steps.append(f"Sorted results by '{sort_col}' {order_label}.")
                    operations_performed.append("SORT")
            elif has_temporal_dimension and sort_key_cols and not result_df.empty:
                # Default chronological ordering for time-series trend analysis
                result_df = result_df.sort_values(by=sort_key_cols, ascending=True)
                calculation_steps.append("Chronologically ordered time-series results.")
                operations_performed.append("CHRONOLOGICAL_SORT")

            # Apply Top-N Per Group if specified (e.g. top 1 Category per Region)
            if instruction.top_n_per_group and not result_df.empty and len(group_cols) >= 2:
                primary_dim = group_cols[0]
                secondary_dim = group_cols[1]
                primary_metric = aggs[0].alias or f"{aggs[0].operation.value}_{aggs[0].column}"
                if primary_metric in result_df.columns and secondary_dim in result_df.columns:
                    result_df = result_df.sort_values(
                        by=[primary_dim, primary_metric, secondary_dim],
                        ascending=[True, False, True],
                    )
                    result_df = result_df.groupby(primary_dim, as_index=False, group_keys=False).head(instruction.top_n_per_group)
                    calculation_steps.append(
                        f"Filtered to top {instruction.top_n_per_group} record(s) per '{primary_dim}' with deterministic tie-breaking on '{secondary_dim}'."
                    )
                    operations_performed.append("TOP_PER_GROUP")

            # Apply Limit if specified
            if instruction.limit and not result_df.empty:
                result_df = result_df.head(instruction.limit)
                calculation_steps.append(f"Limited results to top {instruction.limit} records.")
                operations_performed.append("LIMIT")

            # Calculate deterministic extreme periods & seasonality evidence
            primary_metric_col = aggs[0].alias or f"{aggs[0].operation.value}_{aggs[0].column}"
            is_ranked_limit = bool(instruction.limit and instruction.sort and not instruction.sort.ascending)
            evidence_notes = TemporalEvidenceCalculator.calculate_evidence(
                result_df,
                group_cols,
                primary_metric_col,
                is_ranked_limit=is_ranked_limit,
                is_top_per_group=bool(instruction.top_n_per_group),
                top_n=instruction.top_n_per_group,
                has_temporal_dimension=has_temporal_dimension,
            )
            calculation_steps.extend(evidence_notes)

            # Drop internal sort keys from user-facing result columns
            clean_cols = [c for c in result_df.columns if not c.startswith("__sort_key_")]
            clean_result_df = result_df[clean_cols].copy()

            # Format Table Data & Series Data
            cols_list = list(clean_result_df.columns)
            rows_list = clean_result_df.to_dict(orient="records")

            # Build SeriesDataPoint list for 1D or composite 2D temporal series
            series_points = None
            if len(aggs) >= 1 and not clean_result_df.empty and primary_metric_col in clean_result_df.columns:
                if len(group_cols) == 1:
                    g_col = group_cols[0]
                    series_points = [
                        SeriesDataPoint(label=str(r[g_col]), value=r[primary_metric_col]) for r in rows_list
                    ]
                elif len(group_cols) == 2:
                    g1, g2 = group_cols[0], group_cols[1]
                    series_points = [
                        SeriesDataPoint(label=f"{r[g1]} {r[g2]}", value=r[primary_metric_col]) for r in rows_list
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
                aggregation_columns=[agg.column for agg in aggs],
                filter_columns=filter_cols,
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
                filter_columns=filter_cols,
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
        """Converts table data rows from a RawSheetGrid into a typed pandas DataFrame with fast direct access."""
        if not table.data_range:
            return pd.DataFrame(), []

        try:
            start_ref, end_ref = table.data_range.split(":")
            start_row = int("".join(ch for ch in start_ref if ch.isdigit()))
            end_row = int("".join(ch for ch in end_ref if ch.isdigit()))
        except Exception:
            return pd.DataFrame(), []

        num_rows = end_row - start_row + 1
        original_row_indices = list(range(start_row, end_row + 1))
        cells_dict = grid.cells

        col_data = {}
        for col in table.columns:
            c_idx = column_index_from_string(col.source_column_letter)
            vals = [None] * num_rows
            for i, r in enumerate(original_row_indices):
                cell = cells_dict.get((r, c_idx))
                if cell is not None:
                    vals[i] = cell.parsed_value if cell.parsed_value is not None else cell.original_value
            col_data[col.name] = vals

        df = pd.DataFrame(col_data, index=original_row_indices)
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
