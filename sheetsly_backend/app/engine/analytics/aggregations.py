"""Deterministic aggregation primitives for scalar calculations and group aggregations."""

from typing import Any, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from app.engine.profiler.type_detector import TypeDetector
from app.models.schemas import DataTypeEnum
from .instruction_model import AggregationOpEnum, OperationEnum


class DeterministicAggregator:
    """Calculates deterministic numerical and categorical aggregations with explicit COUNT semantics."""

    @classmethod
    def calculate_scalar(
        cls,
        series: pd.Series,
        operation: Union[OperationEnum, AggregationOpEnum],
        total_rows_in_selection: int,
    ) -> Tuple[Optional[Union[float, int, str]], Optional[str], List[str]]:
        """
        Executes a scalar aggregation on a pandas Series.
        Returns:
            (raw_value, formatted_string, calculation_notes)
        """
        notes: List[str] = []
        op_name = operation.value if hasattr(operation, "value") else str(operation)

        # 1. COUNT_ROWS: Total records in current filtered selection
        if op_name == "COUNT_ROWS":
            count_val = total_rows_in_selection
            notes.append(f"Counted total records in selection: {count_val}")
            return count_val, f"{count_val:,}", notes

        # 2. COUNT_VALUES: Non-null values in column
        if op_name == "COUNT_VALUES":
            non_null_count = 0
            for v in series:
                if v is None:
                    continue
                dt, _ = TypeDetector.detect_value_type(v)
                if dt != DataTypeEnum.NULL:
                    non_null_count += 1
            null_count = total_rows_in_selection - non_null_count
            notes.append(f"Counted non-null values: {non_null_count} (excluded {null_count} null/empty cells)")
            return non_null_count, f"{non_null_count:,}", notes

        # 3. DISTINCT_COUNT: Unique non-null values
        if op_name == "DISTINCT_COUNT":
            distinct_set = set()
            for v in series:
                if v is None:
                    continue
                dt, parsed = TypeDetector.detect_value_type(v)
                if dt != DataTypeEnum.NULL and parsed is not None:
                    distinct_set.add(parsed if isinstance(parsed, (int, float, bool)) else str(parsed).strip().lower())
            distinct_val = len(distinct_set)
            notes.append(f"Counted distinct unique values: {distinct_val}")
            return distinct_val, f"{distinct_val:,}", notes

        # For numeric aggregations (SUM, AVERAGE, MIN, MAX, MEDIAN)
        numeric_vals: List[float] = []
        for v in series:
            if v is None:
                continue
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                numeric_vals.append(float(v))
            else:
                dt, parsed = TypeDetector.detect_value_type(v)
                if dt in {DataTypeEnum.INTEGER, DataTypeEnum.FLOAT, DataTypeEnum.CURRENCY, DataTypeEnum.PERCENTAGE}:
                    if parsed is not None:
                        numeric_vals.append(float(parsed))

        valid_count = len(numeric_vals)
        excluded_count = total_rows_in_selection - valid_count

        if valid_count == 0:
            if op_name == "SUM":
                notes.append("No numeric rows found in selection; SUM defaulted to 0.")
                return 0.0, "0.00", notes
            notes.append("No numeric rows available for aggregation; result is null.")
            return None, "N/A", notes

        if excluded_count > 0:
            notes.append(f"Computed over {valid_count} valid numeric values (excluded {excluded_count} null/non-numeric cells).")

        num_series = pd.Series(numeric_vals)

        # 4. SUM
        if op_name == "SUM":
            val = float(num_series.sum())
            val = round(val, 4)
            formatted = f"{val:,.2f}"
            notes.append(f"Calculated sum of {valid_count} values = {formatted}")
            return val, formatted, notes

        # 5. AVERAGE
        if op_name == "AVERAGE":
            val = float(num_series.mean())
            val = round(val, 4)
            formatted = f"{val:,.2f}"
            notes.append(f"Calculated arithmetic mean: {formatted}")
            return val, formatted, notes

        # 6. MEDIAN
        if op_name == "MEDIAN":
            val = float(num_series.median())
            val = round(val, 4)
            formatted = f"{val:,.2f}"
            notes.append(f"Calculated median (50th percentile): {formatted}")
            return val, formatted, notes

        # 7. MIN
        if op_name == "MIN":
            val = float(num_series.min())
            val = round(val, 4)
            formatted = f"{val:,.2f}"
            notes.append(f"Found minimum value: {formatted}")
            return val, formatted, notes

        # 8. MAX
        if op_name == "MAX":
            val = float(num_series.max())
            val = round(val, 4)
            formatted = f"{val:,.2f}"
            notes.append(f"Found maximum value: {formatted}")
            return val, formatted, notes

        raise ValueError(f"Unsupported scalar operation: {op_name}")
