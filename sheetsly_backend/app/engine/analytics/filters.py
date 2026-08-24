"""Deterministic row filtering engine supporting all comparison operators and AND/OR logic."""

from datetime import date, datetime
from typing import Any, List, Optional, Tuple
import pandas as pd

from app.engine.profiler.type_detector import TypeDetector
from app.models.schemas import DataTypeEnum
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

        total_rows = len(df)
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
        """Evaluates one FilterCondition against a DataFrame column and returns (boolean_mask, description)."""
        col = condition.column
        op = condition.operator
        target_val = condition.value
        case_sensitive = condition.case_sensitive

        series = df[col]

        # 1. IS_EMPTY / IS_NOT_EMPTY
        if op == FilterOperatorEnum.IS_EMPTY:
            mask = series.isna() | (series.astype(str).str.strip() == "") | (series.astype(str).str.lower() == "none")
            return mask, f"{col} IS EMPTY"

        if op == FilterOperatorEnum.IS_NOT_EMPTY:
            mask = ~(series.isna() | (series.astype(str).str.strip() == "") | (series.astype(str).str.lower() == "none"))
            return mask, f"{col} IS NOT EMPTY"

        # Normalize target comparison operand
        norm_target_type, norm_target_val = TypeDetector.detect_value_type(target_val)
        cmp_val = norm_target_val if norm_target_val is not None else target_val

        # 2. EQUALS & NOT_EQUALS
        if op == FilterOperatorEnum.EQUALS:
            if isinstance(cmp_val, (int, float)):
                # Numeric equality
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

        # 3. TEXT PATTERNS (CONTAINS, NOT_CONTAINS, STARTS_WITH, ENDS_WITH)
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

        # 4. ORDERABLE COMPARISONS (>, <, >=, <=, BETWEEN)
        num_series = pd.to_numeric(series, errors="coerce")

        if op == FilterOperatorEnum.GREATER_THAN:
            mask = num_series > float(cmp_val)
            return mask, f"{col} > {target_val}"

        if op == FilterOperatorEnum.LESS_THAN:
            mask = num_series < float(cmp_val)
            return mask, f"{col} < {target_val}"

        if op == FilterOperatorEnum.GREATER_OR_EQUAL:
            mask = num_series >= float(cmp_val)
            return mask, f"{col} >= {target_val}"

        if op == FilterOperatorEnum.LESS_OR_EQUAL:
            mask = num_series <= float(cmp_val)
            return mask, f"{col} <= {target_val}"

        if op == FilterOperatorEnum.BETWEEN:
            min_v, max_v = target_val[0], target_val[1]
            min_n = TypeDetector.detect_value_type(min_v)[1]
            max_n = TypeDetector.detect_value_type(max_v)[1]
            mask = (num_series >= float(min_n)) & (num_series <= float(max_n))
            return mask, f"{col} BETWEEN [{min_v}, {max_v}]"

        # 5. IN_LIST
        if op == FilterOperatorEnum.IN_LIST:
            normalized_list = []
            for item in target_val:
                _, norm_v = TypeDetector.detect_value_type(item)
                normalized_list.append(norm_v if norm_v is not None else item)

            # Check string or numeric match
            if all(isinstance(x, (int, float)) for x in normalized_list):
                mask = num_series.isin([float(x) for x in normalized_list])
            else:
                str_targets = [str(x).strip().lower() if not case_sensitive else str(x) for x in target_val]
                str_series = series.astype(str).str.strip().str.lower() if not case_sensitive else series.astype(str)
                mask = str_series.isin(str_targets)
            return mask, f"{col} IN {target_val}"

        # Default fallback
        return pd.Series(True, index=df.index), f"{col} [unsupported filter]"
