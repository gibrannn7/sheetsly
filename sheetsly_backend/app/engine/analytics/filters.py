"""Deterministic row filtering engine supporting all comparison operators, physical date comparisons, and derived temporal dimensions."""

from datetime import date, datetime
from typing import Any, List, Optional, Tuple, Union
import pandas as pd

from app.engine.profiler.type_detector import TypeDetector
from app.models.schemas import DataTypeEnum
from .expressions import DateDimensionOpEnum, DimensionEvaluator, DimensionParser
from .instruction_model import (
    FilterCombinationEnum,
    FilterCondition,
    FilterOperatorEnum,
)


class DeterministicFilterEngine:
    """Evaluates filter conditions on DataFrames while tracking row inclusion and exclusion lineage."""

    @classmethod
    def apply_filters(
        cls,
        df: pd.DataFrame,
        filters: List[FilterCondition],
        combination: FilterCombinationEnum = FilterCombinationEnum.AND,
    ) -> Tuple[pd.DataFrame, List[int], List[int], List[str]]:
        """
        Applies filter conditions deterministically.
        Returns:
            (filtered_df, retained_original_indices, excluded_original_indices, filter_descriptions)
        """
        if df.empty or not filters:
            all_indices = list(df.index)
            return df, all_indices, [], []

        all_original_indices = list(df.index)

        # Build boolean mask for each filter
        filter_masks: List[pd.Series] = []
        descriptions: List[str] = []

        for f in filters:
            mask, desc = cls._evaluate_single_filter(df, f)
            filter_masks.append(mask)
            descriptions.append(desc)

        if not filter_masks:
            return df, all_original_indices, [], []

        # Combine masks
        if combination == FilterCombinationEnum.OR:
            combined_mask = filter_masks[0]
            for m in filter_masks[1:]:
                combined_mask = combined_mask | m
        else:
            combined_mask = filter_masks[0]
            for m in filter_masks[1:]:
                combined_mask = combined_mask & m

        filtered_df = df[combined_mask]
        retained_indices = list(filtered_df.index)
        excluded_indices = [idx for idx in all_original_indices if idx not in retained_indices]

        return filtered_df, retained_indices, excluded_indices, descriptions

    @classmethod
    def _evaluate_single_filter(cls, df: pd.DataFrame, condition: FilterCondition) -> Tuple[pd.Series, str]:
        """Evaluates one FilterCondition against a DataFrame column (physical or derived) and returns (boolean_mask, description)."""
        col = condition.column
        op = condition.operator
        target_val = condition.value
        case_sensitive = condition.case_sensitive

        # -------------------------------------------------------------
        # Case A: Derived Temporal Dimension Filter (e.g. YEAR(Order Date), MONTH(Order Date))
        # -------------------------------------------------------------
        dim_spec = DimensionParser.parse(col)
        if dim_spec is not None:
            source_col = dim_spec.source_column
            if source_col not in df.columns:
                return pd.Series(True, index=df.index), f"{col} [source column missing]"

            disp_series, sort_k_series = DimensionEvaluator.evaluate(df[source_col], dim_spec.operation)
            norm_operand = DimensionEvaluator.normalize_filter_operand(dim_spec.operation, target_val)

            # Use numeric/sort key series if operand is numeric, otherwise display series
            use_sort_key = sort_k_series is not None and (
                isinstance(norm_operand, (int, float))
                or (isinstance(norm_operand, list) and all(isinstance(x, (int, float)) for x in norm_operand))
            )
            target_series = sort_k_series if use_sort_key else disp_series

            if op == FilterOperatorEnum.IS_EMPTY:
                mask = target_series.isna()
                return mask, f"{col} IS EMPTY"

            if op == FilterOperatorEnum.IS_NOT_EMPTY:
                mask = target_series.notna()
                return mask, f"{col} IS NOT EMPTY"

            if op == FilterOperatorEnum.EQUALS:
                if use_sort_key:
                    mask = (sort_k_series == norm_operand) | (disp_series.astype(str).str.strip().str.lower() == str(target_val).strip().lower())
                else:
                    if case_sensitive:
                        mask = disp_series.astype(str) == str(target_val)
                    else:
                        mask = disp_series.astype(str).str.strip().str.lower() == str(target_val).strip().lower()
                return mask, f"{col} == {target_val}"

            if op == FilterOperatorEnum.NOT_EQUALS:
                if use_sort_key:
                    mask = (sort_k_series != norm_operand) & (disp_series.astype(str).str.strip().str.lower() != str(target_val).strip().lower())
                else:
                    if case_sensitive:
                        mask = disp_series.astype(str) != str(target_val)
                    else:
                        mask = disp_series.astype(str).str.strip().str.lower() != str(target_val).strip().lower()
                return mask, f"{col} != {target_val}"

            if op == FilterOperatorEnum.GREATER_THAN:
                if use_sort_key and isinstance(norm_operand, (int, float)):
                    mask = sort_k_series > norm_operand
                else:
                    cmp_num = pd.to_numeric(norm_operand, errors="coerce")
                    if pd.notna(cmp_num):
                        mask = pd.to_numeric(target_series, errors="coerce") > cmp_num
                    else:
                        mask = disp_series.astype(str) > str(target_val)
                return mask, f"{col} > {target_val}"

            if op == FilterOperatorEnum.LESS_THAN:
                if use_sort_key and isinstance(norm_operand, (int, float)):
                    mask = sort_k_series < norm_operand
                else:
                    cmp_num = pd.to_numeric(norm_operand, errors="coerce")
                    if pd.notna(cmp_num):
                        mask = pd.to_numeric(target_series, errors="coerce") < cmp_num
                    else:
                        mask = disp_series.astype(str) < str(target_val)
                return mask, f"{col} < {target_val}"

            if op == FilterOperatorEnum.GREATER_OR_EQUAL:
                if use_sort_key and isinstance(norm_operand, (int, float)):
                    mask = sort_k_series >= norm_operand
                else:
                    cmp_num = pd.to_numeric(norm_operand, errors="coerce")
                    if pd.notna(cmp_num):
                        mask = pd.to_numeric(target_series, errors="coerce") >= cmp_num
                    else:
                        mask = disp_series.astype(str) >= str(target_val)
                return mask, f"{col} >= {target_val}"

            if op == FilterOperatorEnum.LESS_OR_EQUAL:
                if use_sort_key and isinstance(norm_operand, (int, float)):
                    mask = sort_k_series <= norm_operand
                else:
                    cmp_num = pd.to_numeric(norm_operand, errors="coerce")
                    if pd.notna(cmp_num):
                        mask = pd.to_numeric(target_series, errors="coerce") <= cmp_num
                    else:
                        mask = disp_series.astype(str) <= str(target_val)
                return mask, f"{col} <= {target_val}"

            if op == FilterOperatorEnum.BETWEEN:
                min_v, max_v = norm_operand[0], norm_operand[1]
                if use_sort_key and isinstance(min_v, (int, float)) and isinstance(max_v, (int, float)):
                    mask = (sort_k_series >= min_v) & (sort_k_series <= max_v)
                else:
                    num_min = pd.to_numeric(min_v, errors="coerce")
                    num_max = pd.to_numeric(max_v, errors="coerce")
                    if pd.notna(num_min) and pd.notna(num_max):
                        num_series = pd.to_numeric(target_series, errors="coerce")
                        mask = (num_series >= num_min) & (num_series <= num_max)
                    else:
                        str_series = disp_series.astype(str)
                        mask = (str_series >= str(min_v)) & (str_series <= str(max_v))
                return mask, f"{col} BETWEEN [{target_val[0]}, {target_val[1]}]"

            if op == FilterOperatorEnum.IN_LIST:
                if use_sort_key and isinstance(norm_operand, list):
                    mask = sort_k_series.isin(norm_operand)
                else:
                    str_targets = [str(x).strip().lower() for x in (target_val if isinstance(target_val, list) else [target_val])]
                    mask = disp_series.astype(str).str.strip().str.lower().isin(str_targets)
                return mask, f"{col} IN {target_val}"

            return pd.Series(True, index=df.index), f"{col} {op.value} {target_val}"

        # -------------------------------------------------------------
        # Case B: Physical Column Filter
        # -------------------------------------------------------------
        if col not in df.columns:
            return pd.Series(True, index=df.index), f"{col} [missing column]"

        series = df[col]

        # 1. IS_EMPTY / IS_NOT_EMPTY
        if op == FilterOperatorEnum.IS_EMPTY:
            mask = series.isna() | (series.astype(str).str.strip() == "") | (series.astype(str).str.lower() == "none")
            return mask, f"{col} IS EMPTY"

        if op == FilterOperatorEnum.IS_NOT_EMPTY:
            mask = ~(series.isna() | (series.astype(str).str.strip() == "") | (series.astype(str).str.lower() == "none"))
            return mask, f"{col} IS NOT EMPTY"

        # Check if physical column contains date/datetime values
        is_date_col = (
            pd.api.types.is_datetime64_any_dtype(series)
            or any(kw in col.lower() for kw in ["date", "tanggal", "time", "period"])
        )

        # 2. Date Column Comparisons (Avoids float conversion crash)
        if is_date_col and op in {
            FilterOperatorEnum.GREATER_THAN,
            FilterOperatorEnum.LESS_THAN,
            FilterOperatorEnum.GREATER_OR_EQUAL,
            FilterOperatorEnum.LESS_OR_EQUAL,
            FilterOperatorEnum.BETWEEN,
        }:
            dt_series = pd.to_datetime(series, errors="coerce")

            if op == FilterOperatorEnum.GREATER_THAN:
                target_dt = pd.to_datetime(target_val, errors="coerce")
                mask = dt_series > target_dt
                return mask, f"{col} > {target_val}"

            if op == FilterOperatorEnum.LESS_THAN:
                target_dt = pd.to_datetime(target_val, errors="coerce")
                mask = dt_series < target_dt
                return mask, f"{col} < {target_val}"

            if op == FilterOperatorEnum.GREATER_OR_EQUAL:
                target_dt = pd.to_datetime(target_val, errors="coerce")
                mask = dt_series >= target_dt
                return mask, f"{col} >= {target_val}"

            if op == FilterOperatorEnum.LESS_OR_EQUAL:
                target_dt = pd.to_datetime(target_val, errors="coerce")
                mask = dt_series <= target_dt
                return mask, f"{col} <= {target_val}"

            if op == FilterOperatorEnum.BETWEEN:
                min_dt = pd.to_datetime(target_val[0], errors="coerce")
                max_dt = pd.to_datetime(target_val[1], errors="coerce")
                mask = (dt_series >= min_dt) & (dt_series <= max_dt)
                return mask, f"{col} BETWEEN [{target_val[0]}, {target_val[1]}]"

        # 3. Standard EQUALS & NOT_EQUALS
        norm_target_type, norm_target_val = TypeDetector.detect_value_type(target_val)
        cmp_val = norm_target_val if norm_target_val is not None else target_val

        if op == FilterOperatorEnum.EQUALS:
            if isinstance(cmp_val, (int, float)):
                mask = pd.to_numeric(series, errors="coerce") == cmp_val
            else:
                if case_sensitive:
                    mask = series.astype(str) == str(target_val)
                else:
                    mask = series.astype(str).str.strip().str.lower() == str(target_val).strip().lower()
            return mask, f"{col} == {target_val}"

        if op == FilterOperatorEnum.NOT_EQUALS:
            if isinstance(cmp_val, (int, float)):
                mask = pd.to_numeric(series, errors="coerce") != cmp_val
            else:
                if case_sensitive:
                    mask = series.astype(str) != str(target_val)
                else:
                    mask = series.astype(str).str.strip().str.lower() != str(target_val).strip().lower()
            return mask, f"{col} != {target_val}"

        # 4. Text Patterns (CONTAINS, NOT_CONTAINS, STARTS_WITH, ENDS_WITH)
        if op == FilterOperatorEnum.CONTAINS:
            str_series = series.astype(str)
            mask = str_series.str.contains(str(target_val), case=case_sensitive, na=False, regex=False)
            return mask, f"{col} CONTAINS '{target_val}'"

        if op == FilterOperatorEnum.NOT_CONTAINS:
            str_series = series.astype(str)
            mask = ~str_series.str.contains(str(target_val), case=case_sensitive, na=False, regex=False)
            return mask, f"{col} NOT CONTAINS '{target_val}'"

        if op == FilterOperatorEnum.STARTS_WITH:
            str_series = series.astype(str)
            if not case_sensitive:
                str_series = str_series.str.lower()
                cmp_str = str(target_val).lower()
            else:
                cmp_str = str(target_val)
            mask = str_series.str.startswith(cmp_str, na=False)
            return mask, f"{col} STARTS WITH '{target_val}'"

        if op == FilterOperatorEnum.ENDS_WITH:
            str_series = series.astype(str)
            if not case_sensitive:
                str_series = str_series.str.lower()
                cmp_str = str(target_val).lower()
            else:
                cmp_str = str(target_val)
            mask = str_series.str.endswith(cmp_str, na=False)
            return mask, f"{col} ENDS WITH '{target_val}'"

        # 5. Standard Numeric Comparisons (>, <, >=, <=, BETWEEN)
        num_series = pd.to_numeric(series, errors="coerce")

        try:
            num_cmp_val = float(cmp_val) if cmp_val is not None else 0.0
        except (ValueError, TypeError):
            num_cmp_val = 0.0

        if op == FilterOperatorEnum.GREATER_THAN:
            mask = num_series > num_cmp_val
            return mask, f"{col} > {target_val}"

        if op == FilterOperatorEnum.LESS_THAN:
            mask = num_series < num_cmp_val
            return mask, f"{col} < {target_val}"

        if op == FilterOperatorEnum.GREATER_OR_EQUAL:
            mask = num_series >= num_cmp_val
            return mask, f"{col} >= {target_val}"

        if op == FilterOperatorEnum.LESS_OR_EQUAL:
            mask = num_series <= num_cmp_val
            return mask, f"{col} <= {target_val}"

        if op == FilterOperatorEnum.BETWEEN:
            try:
                min_n = float(TypeDetector.detect_value_type(target_val[0])[1])
                max_n = float(TypeDetector.detect_value_type(target_val[1])[1])
                mask = (num_series >= min_n) & (num_series <= max_n)
            except Exception:
                mask = pd.Series(True, index=df.index)
            return mask, f"{col} BETWEEN [{target_val[0]}, {target_val[1]}]"

        # 6. IN_LIST
        if op == FilterOperatorEnum.IN_LIST:
            normalized_list = []
            for item in target_val:
                _, norm_v = TypeDetector.detect_value_type(item)
                normalized_list.append(norm_v if norm_v is not None else item)

            if all(isinstance(x, (int, float)) for x in normalized_list):
                mask = num_series.isin([float(x) for x in normalized_list])
            else:
                str_targets = [str(x).strip().lower() if not case_sensitive else str(x) for x in target_val]
                str_series = series.astype(str).str.strip().str.lower() if not case_sensitive else series.astype(str)
                mask = str_series.isin(str_targets)
            return mask, f"{col} IN {target_val}"

        return pd.Series(True, index=df.index), f"{col} [unsupported filter]"
