"""Analytical expression model and deterministic parser for allowlisted derived dimensions."""

from enum import Enum
import re
from typing import Any, Dict, List, Optional, Tuple, Union
import pandas as pd
from pydantic import BaseModel, Field

from app.models.schemas import DataTypeEnum, SemanticTypeEnum


class DateDimensionOpEnum(str, Enum):
    """Explicit allowlist of deterministic temporal dimension operations."""

    YEAR = "YEAR"
    QUARTER = "QUARTER"
    YEAR_QUARTER = "YEAR_QUARTER"
    MONTH = "MONTH"
    MONTH_NAME = "MONTH_NAME"
    YEAR_MONTH = "YEAR_MONTH"
    WEEK = "WEEK"
    DAY = "DAY"
    DAY_OF_WEEK = "DAY_OF_WEEK"


class DerivedDimensionSpec(BaseModel):
    """Structured representation of a validated derived analytical dimension."""

    raw_expression: str = Field(..., description="Original raw expression, e.g. 'YEAR(Order Date)'")
    source_column: str = Field(..., description="Physical source column name, e.g. 'Order Date'")
    operation: DateDimensionOpEnum = Field(..., description="Allowlisted temporal operation")
    alias: Optional[str] = Field(None, description="Optional result column alias")


RE_DATE_DIMENSION = re.compile(
    r"^(YEAR|QUARTER|YEAR_QUARTER|YEAR-QUARTER|MONTH|MONTH_NAME|YEAR_MONTH|YEAR-MONTH|WEEK|DAY|DAY_OF_WEEK|DAYOFWEEK)\s*\(\s*(.+?)\s*\)$",
    re.IGNORECASE,
)

_OP_NORMALIZATION = {
    "year": DateDimensionOpEnum.YEAR,
    "quarter": DateDimensionOpEnum.QUARTER,
    "year_quarter": DateDimensionOpEnum.YEAR_QUARTER,
    "year-quarter": DateDimensionOpEnum.YEAR_QUARTER,
    "yearquarter": DateDimensionOpEnum.YEAR_QUARTER,
    "month": DateDimensionOpEnum.MONTH,
    "month_name": DateDimensionOpEnum.MONTH_NAME,
    "monthname": DateDimensionOpEnum.MONTH_NAME,
    "year_month": DateDimensionOpEnum.YEAR_MONTH,
    "year-month": DateDimensionOpEnum.YEAR_MONTH,
    "yearmonth": DateDimensionOpEnum.YEAR_MONTH,
    "week": DateDimensionOpEnum.WEEK,
    "day": DateDimensionOpEnum.DAY,
    "day_of_week": DateDimensionOpEnum.DAY_OF_WEEK,
    "dayofweek": DateDimensionOpEnum.DAY_OF_WEEK,
}

_MONTH_NAME_TO_INT = {
    "january": 1, "jan": 1, "januari": 1,
    "february": 2, "feb": 2, "februari": 2,
    "march": 3, "mar": 3, "maret": 3,
    "april": 4, "apr": 4,
    "may": 5, "mei": 5,
    "june": 6, "jun": 6, "juni": 6,
    "july": 7, "jul": 7, "juli": 7,
    "august": 8, "aug": 8, "agustus": 8,
    "september": 9, "sep": 9, "sept": 9,
    "october": 10, "oct": 10, "oktober": 10, "okt": 10,
    "november": 11, "nov": 11,
    "december": 12, "dec": 12, "desember": 12, "des": 12,
}

_QUARTER_TO_INT = {
    "q1": 1, "kuartal 1": 1, "k1": 1, "1": 1,
    "q2": 2, "kuartal 2": 2, "k2": 2, "2": 2,
    "q3": 3, "kuartal 3": 3, "k3": 3, "3": 3,
    "q4": 4, "kuartal 4": 4, "k4": 4, "4": 4,
}

_DAY_NAME_TO_INT = {
    "monday": 0, "senin": 0,
    "tuesday": 1, "selasa": 1,
    "wednesday": 2, "rabu": 2,
    "thursday": 3, "kamis": 3,
    "friday": 4, "jumat": 4, "jum'at": 4,
    "saturday": 5, "sabtu": 5,
    "sunday": 6, "minggu": 6,
}


class DimensionParser:
    """Strict deterministic parser for analytical expressions."""

    @classmethod
    def parse(cls, expr: str) -> Optional[DerivedDimensionSpec]:
        """
        Parses a raw dimension string.
        Returns DerivedDimensionSpec if it matches a valid allowlisted temporal operation,
        or None if it does not match or contains unsafe/unapproved syntax.
        """
        if not expr or not isinstance(expr, str):
            return None

        clean_expr = expr.strip()
        match = RE_DATE_DIMENSION.match(clean_expr)
        if not match:
            return None

        raw_op = match.group(1).lower().replace("-", "_").strip()
        source_col = match.group(2).strip()

        if not source_col or any(ch in source_col for ch in [";", "\n", "\r", "\t", "{", "}", "[", "]"]):
            return None

        if (source_col.startswith("'") and source_col.endswith("'")) or (source_col.startswith('"') and source_col.endswith('"')):
            source_col = source_col[1:-1].strip()

        if not source_col:
            return None

        op_enum = _OP_NORMALIZATION.get(raw_op)
        if not op_enum:
            return None

        canonical_raw = f"{op_enum.value}({source_col})"
        return DerivedDimensionSpec(
            raw_expression=canonical_raw,
            source_column=source_col,
            operation=op_enum,
        )

    @classmethod
    def is_derived_expression(cls, expr: str) -> bool:
        """Returns True if the expression matches the derived dimension syntax."""
        return cls.parse(expr) is not None


class DimensionEvaluator:
    """Deterministic vectorized evaluator that projects temporal dimensions from source Series."""

    @classmethod
    def evaluate(
        cls,
        series: pd.Series,
        operation: DateDimensionOpEnum,
    ) -> Tuple[pd.Series, Optional[pd.Series]]:
        """
        Evaluates a temporal dimension on a pandas Series.
        Returns:
            (display_series, sort_key_series)
        """
        if pd.api.types.is_datetime64_any_dtype(series):
            dt_series = series
        else:
            dt_series = pd.to_datetime(series, errors="coerce", format="mixed")

        if operation == DateDimensionOpEnum.YEAR:
            display = dt_series.apply(lambda d: int(d.year) if pd.notna(d) else None)
            return display, display

        elif operation == DateDimensionOpEnum.QUARTER:
            display = dt_series.apply(lambda d: f"Q{int(d.quarter)}" if pd.notna(d) else None)
            sort_key = dt_series.apply(lambda d: int(d.quarter) if pd.notna(d) else None)
            return display, sort_key

        elif operation == DateDimensionOpEnum.YEAR_QUARTER:
            display = dt_series.apply(lambda d: f"{int(d.year)} Q{int(d.quarter)}" if pd.notna(d) else None)
            sort_key = dt_series.apply(lambda d: (int(d.year) * 10 + int(d.quarter)) if pd.notna(d) else None)
            return display, sort_key

        elif operation == DateDimensionOpEnum.MONTH:
            display = dt_series.apply(lambda d: int(d.month) if pd.notna(d) else None)
            return display, display

        elif operation == DateDimensionOpEnum.MONTH_NAME:
            display = dt_series.apply(lambda d: str(d.strftime("%B")) if pd.notna(d) else None)
            sort_key = dt_series.apply(lambda d: int(d.month) if pd.notna(d) else None)
            return display, sort_key

        elif operation == DateDimensionOpEnum.YEAR_MONTH:
            display = dt_series.apply(lambda d: str(d.strftime("%Y-%m")) if pd.notna(d) else None)
            sort_key = dt_series.apply(lambda d: (int(d.year) * 100 + int(d.month)) if pd.notna(d) else None)
            return display, sort_key

        elif operation == DateDimensionOpEnum.WEEK:
            display = dt_series.apply(lambda d: int(d.isocalendar().week) if pd.notna(d) else None)
            return display, display

        elif operation == DateDimensionOpEnum.DAY:
            display = dt_series.apply(lambda d: int(d.day) if pd.notna(d) else None)
            return display, display

        elif operation == DateDimensionOpEnum.DAY_OF_WEEK:
            display = dt_series.apply(lambda d: str(d.strftime("%A")) if pd.notna(d) else None)
            sort_key = dt_series.apply(lambda d: int(d.dayofweek) if pd.notna(d) else None)
            return display, sort_key

        raise ValueError(f"Unsupported temporal dimension operation: {operation}")

    @classmethod
    def normalize_filter_operand(
        cls,
        operation: DateDimensionOpEnum,
        value: Any,
    ) -> Any:
        """
        Normalizes filter operand for a derived temporal dimension into a canonical comparison value.
        """
        if isinstance(value, (list, tuple)):
            return [cls.normalize_filter_operand(operation, v) for v in value]

        if value is None:
            return None

        val_str = str(value).strip().lower()

        if operation in {DateDimensionOpEnum.MONTH, DateDimensionOpEnum.MONTH_NAME}:
            if val_str in _MONTH_NAME_TO_INT:
                return _MONTH_NAME_TO_INT[val_str]
            if val_str.isdigit():
                m_int = int(val_str)
                if 1 <= m_int <= 12:
                    return m_int

        elif operation == DateDimensionOpEnum.QUARTER:
            if val_str in _QUARTER_TO_INT:
                return _QUARTER_TO_INT[val_str]
            if val_str.isdigit():
                q_int = int(val_str)
                if 1 <= q_int <= 4:
                    return q_int

        elif operation == DateDimensionOpEnum.YEAR_QUARTER:
            # Handle formats like "2015 Q1", "2015-Q1", "2015/Q1"
            yq_m = re.search(r"(20\d\d|19\d\d)\s*[-/]?\s*q([1-4])", val_str)
            if yq_m:
                return int(yq_m.group(1)) * 10 + int(yq_m.group(2))

        elif operation == DateDimensionOpEnum.YEAR_MONTH:
            # Handle formats like "2018-07", "2018/07"
            clean_ym = val_str.replace("/", "-")
            ym_parts = clean_ym.split("-")
            if len(ym_parts) == 2 and ym_parts[0].isdigit() and ym_parts[1].isdigit():
                return int(ym_parts[0]) * 100 + int(ym_parts[1])
            ym_m = re.search(r"(20\d\d|19\d\d)[-/](0[1-9]|1[0-2])", val_str)
            if ym_m:
                return int(ym_m.group(1)) * 100 + int(ym_m.group(2))

        elif operation == DateDimensionOpEnum.YEAR:
            if val_str.isdigit():
                return int(val_str)
                yr, mo = int(ym_parts[0]), int(ym_parts[1])
                return yr * 100 + mo
            if val_str.isdigit() and len(val_str) == 6:
                return int(val_str)

        elif operation == DateDimensionOpEnum.DAY_OF_WEEK:
            if val_str in _DAY_NAME_TO_INT:
                return _DAY_NAME_TO_INT[val_str]

        return value
