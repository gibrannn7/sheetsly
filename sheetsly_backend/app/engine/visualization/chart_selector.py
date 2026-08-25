"""Deterministic chart recommendation and compatibility validation engine."""

import re
from typing import Any, Dict, List, Optional, Tuple

from app.core.errors import SheetslyError
from app.engine.analytics.result_model import AnalyticalResult, ResultTypeEnum
from app.engine.profiler.orientation_detector import PERIOD_HEADER_REGEX
from app.engine.profiler.type_detector import TypeDetector
from app.models.schemas import DataTypeEnum
from .chart_model import (
    ChartMetadata,
    ChartRecommendation,
    ChartSeriesSpec,
    ChartTypeEnum,
)


class IncompatibleChartError(SheetslyError):
    """Raised when a requested chart type is incompatible with the provided AnalyticalResult."""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(
            message=message,
            code="INCOMPATIBLE_CHART_TYPE",
            status_code=422,
            details=details or {},
        )


class ChartSelector:
    """Determines chart compatibility and provides conservative, rule-based recommendations."""

    @staticmethod
    def _safe_to_float(v: Any) -> Optional[float]:
        """Safely extracts a float value from numeric types or currency/formatted numeric strings, rejecting temporal/categorical strings."""
        if v is None or isinstance(v, bool):
            return None
        if isinstance(v, (int, float)):
            return float(v)
        
        v_str = str(v).strip()
        if not v_str:
            return None
        
        # Explicitly reject temporal strings from numeric conversion
        if re.match(r"^\d{4}[-/]\d{2}(?:[-/]\d{2})?$", v_str) or re.match(r"^(?:Q[1-4]|\d{4}\s+Q[1-4])$", v_str, re.IGNORECASE):
            return None
        if v_str.lower() in {"january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december",
                             "januari", "februari", "maret", "april", "mei", "juni", "juli", "agustus", "september", "oktober", "november", "desember",
                             "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
                             "senin", "selasa", "rabu", "kamis", "jumat", "sabtu", "minggu"}:
            return None

        dt, parsed = TypeDetector.detect_value_type(v)
        if dt in {DataTypeEnum.INTEGER, DataTypeEnum.FLOAT, DataTypeEnum.CURRENCY, DataTypeEnum.PERCENTAGE} and parsed is not None:
            try:
                return float(parsed)
            except (ValueError, TypeError):
                pass

        try:
            clean = v_str.replace("$", "").replace("Rp", "").replace(",", "").replace("%", "").strip()
            return float(clean)
        except (ValueError, TypeError):
            return None

    @classmethod
    def recommend(cls, result: AnalyticalResult) -> ChartRecommendation:
        """
        Deterministically evaluates an AnalyticalResult and returns recommended & compatible chart types.
        """
        # 1. SCALAR Result
        if result.result_type == ResultTypeEnum.SCALAR:
            val = cls._safe_to_float(result.scalar_value)
            if val is not None:
                return ChartRecommendation(
                    preferred_type=ChartTypeEnum.BAR,
                    compatible_types=[ChartTypeEnum.BAR],
                    reason="Scalar numeric result can be presented as a single-metric bar or KPI gauge.",
                    confidence=0.8,
                )
            return ChartRecommendation(
                preferred_type=None,
                compatible_types=[],
                reason="Non-numeric or null scalar result is not visualizable on standard axes.",
                confidence=1.0,
            )

        # 2. Extract tabular columns & types
        columns, rows = cls._extract_tabular_data(result)
        if not rows or not columns:
            return ChartRecommendation(
                preferred_type=None,
                compatible_types=[],
                reason="Analytical result contains no records.",
                confidence=1.0,
            )

        group_dims = [g for g in result.lineage.grouping_applied] if (result.lineage and result.lineage.grouping_applied) else []
        group_dims_set = set(group_dims)
        col_types = cls._profile_result_columns(columns, rows)
        numeric_cols = [
            c for c in columns
            if c not in group_dims_set and col_types[c] in {DataTypeEnum.INTEGER, DataTypeEnum.FLOAT, DataTypeEnum.CURRENCY, DataTypeEnum.PERCENTAGE}
        ]
        non_numeric_cols = [c for c in columns if c not in numeric_cols]

        compatible: List[ChartTypeEnum] = []
        preferred: Optional[ChartTypeEnum] = None
        reason: str = ""

        # Case A: 1 or more Categorical/Temporal column + 1 or more Numeric columns
        if len(non_numeric_cols) >= 1 and len(numeric_cols) >= 1:
            dim_col = non_numeric_cols[0]
            dim_values = [str(r.get(dim_col, "")) for r in rows]
            is_temporal = cls._is_temporal_dimension(dim_col, dim_values) or any("year" in str(g).lower() or "quarter" in str(g).lower() or "month" in str(g).lower() for g in group_dims)

            # BAR is universally compatible for categorical/temporal + numeric
            compatible.append(ChartTypeEnum.BAR)

            # LINE is compatible if temporal or ordered
            if is_temporal or len(rows) >= 3:
                compatible.append(ChartTypeEnum.LINE)

            # AREA is compatible if temporal and non-negative
            all_non_negative = True
            for num_col in numeric_cols:
                if any(cls._safe_to_float(r.get(num_col)) is not None and cls._safe_to_float(r.get(num_col)) < 0 for r in rows):
                    all_non_negative = False
                    break

            if is_temporal and all_non_negative:
                compatible.append(ChartTypeEnum.AREA)

            # PIE is compatible strictly when 1 metric, 2 <= N <= 10, and all non-negative
            if len(numeric_cols) == 1 and 2 <= len(rows) <= 10 and all_non_negative:
                compatible.append(ChartTypeEnum.PIE)

            # Preferred selection
            if is_temporal:
                preferred = ChartTypeEnum.LINE
                reason = f"Temporal dimension '{dim_col}' with numeric measure(s) is best visualized as a LINE chart."
            else:
                preferred = ChartTypeEnum.BAR
                reason = f"Categorical dimension '{dim_col}' with numeric measure(s) is best visualized as a BAR chart."

            return ChartRecommendation(
                preferred_type=preferred,
                compatible_types=compatible,
                reason=reason,
                confidence=0.9,
            )

        # Case B: 2 or more Numeric Columns (no categorical dimension)
        if len(numeric_cols) >= 2 and len(non_numeric_cols) == 0:
            compatible.append(ChartTypeEnum.SCATTER)
            compatible.append(ChartTypeEnum.LINE)
            compatible.append(ChartTypeEnum.BAR)
            compatible.append(ChartTypeEnum.HISTOGRAM)

            return ChartRecommendation(
                preferred_type=ChartTypeEnum.SCATTER,
                compatible_types=compatible,
                reason=f"Multiple continuous numeric variables ({', '.join(numeric_cols[:2])}) are suitable for a SCATTER plot.",
                confidence=0.85,
            )

        # Case C: 1 Numeric Column only
        if len(numeric_cols) == 1 and len(non_numeric_cols) == 0:
            compatible.append(ChartTypeEnum.HISTOGRAM)
            compatible.append(ChartTypeEnum.BAR)

            return ChartRecommendation(
                preferred_type=ChartTypeEnum.HISTOGRAM,
                compatible_types=compatible,
                reason=f"Single continuous numeric variable '{numeric_cols[0]}' is suitable for a HISTOGRAM distribution.",
                confidence=0.85,
            )

        # Case D: No Numeric Measures
        return ChartRecommendation(
            preferred_type=None,
            compatible_types=[],
            reason="Result contains no numeric columns suitable for charting.",
            confidence=1.0,
        )

    @classmethod
    def validate_and_extract_plot_data(
        cls,
        result: AnalyticalResult,
        requested_type: ChartTypeEnum,
        x_col_override: Optional[str] = None,
        y_col_override: Optional[str] = None,
        title_override: Optional[str] = None,
    ) -> Tuple[List[str], List[ChartSeriesSpec], Optional[str], Optional[str], str, List[str]]:
        """
        Validates compatibility of the requested ChartTypeEnum against AnalyticalResult.
        Extracts plot categories, series vectors, axis labels, title, and warnings.
        Raises IncompatibleChartError if structurally incompatible.
        Returns:
            (x_categories, series_list, x_axis_label, y_axis_label, chart_title, warnings)
        """
        warnings: List[str] = []

        # Handle SCALAR result
        if result.result_type == ResultTypeEnum.SCALAR:
            if requested_type != ChartTypeEnum.BAR:
                raise IncompatibleChartError(
                    f"Chart type '{requested_type.value}' is incompatible with a SCALAR analytical result. Only single-metric BAR is supported.",
                    details={"result_type": "SCALAR", "requested_type": requested_type.value},
                )
            metric_label = (result.lineage.source_columns[0] if result.lineage.source_columns else None) or result.operation
            val = cls._safe_to_float(result.scalar_value) or 0.0
            title = title_override or f"{result.operation} ({metric_label})"
            return (
                [metric_label],
                [ChartSeriesSpec(name=metric_label, values=[val])],
                None,
                metric_label,
                title,
                warnings,
            )

        columns, rows = cls._extract_tabular_data(result)
        if not rows or not columns:
            raise IncompatibleChartError("Cannot generate chart from an empty AnalyticalResult.")

        group_dims = [g for g in result.lineage.grouping_applied] if (result.lineage and result.lineage.grouping_applied) else []
        group_dims_set = set(group_dims)
        col_types = cls._profile_result_columns(columns, rows)
        numeric_cols = [
            c for c in columns
            if c not in group_dims_set and col_types[c] in {DataTypeEnum.INTEGER, DataTypeEnum.FLOAT, DataTypeEnum.CURRENCY, DataTypeEnum.PERCENTAGE}
        ]
        non_numeric_cols = [c for c in columns if c not in numeric_cols]

        # -------------------------------------------------------------
        # 1. SCATTER Validation
        # -------------------------------------------------------------
        if requested_type == ChartTypeEnum.SCATTER:
            if len(numeric_cols) < 2:
                raise IncompatibleChartError(
                    f"SCATTER chart requires 2 continuous numeric columns. Available numeric columns: {numeric_cols}, categorical columns: {non_numeric_cols}.",
                    details={"numeric_columns_count": len(numeric_cols), "available_numeric": numeric_cols},
                )
            x_col = x_col_override or numeric_cols[0]
            y_col = y_col_override or numeric_cols[1]
            if x_col not in numeric_cols or y_col not in numeric_cols:
                raise IncompatibleChartError(
                    f"SCATTER chart columns '{x_col}' and '{y_col}' must both be numeric.",
                    details={"x_col": x_col, "y_col": y_col},
                )

            x_vals = [str(r.get(x_col, 0)) for r in rows]
            y_vals = [cls._safe_to_float(r.get(y_col)) for r in rows]
            title = title_override or f"{y_col} vs {x_col}"
            return (
                x_vals,
                [ChartSeriesSpec(name=y_col, values=y_vals)],
                x_col,
                y_col,
                title,
                warnings,
            )

        # -------------------------------------------------------------
        # 2. HISTOGRAM Validation
        # -------------------------------------------------------------
        if requested_type == ChartTypeEnum.HISTOGRAM:
            if not numeric_cols:
                raise IncompatibleChartError(
                    f"HISTOGRAM requires a continuous numeric column. None of the columns {columns} are numeric.",
                    details={"columns": columns},
                )
            target_num_col = y_col_override or numeric_cols[0]
            if target_num_col not in numeric_cols:
                raise IncompatibleChartError(
                    f"HISTOGRAM column '{target_num_col}' must be numeric (detected type: {col_types.get(target_num_col, 'unknown').value}).",
                    details={"column": target_num_col},
                )
            y_vals = [cls._safe_to_float(r.get(target_num_col)) for r in rows if r.get(target_num_col) is not None]
            title = title_override or f"Distribution of {target_num_col}"
            return (
                [],
                [ChartSeriesSpec(name=target_num_col, values=y_vals)],
                target_num_col,
                "Frequency",
                title,
                warnings,
            )

        # -------------------------------------------------------------
        # 3. PIE Validation
        # -------------------------------------------------------------
        if requested_type == ChartTypeEnum.PIE:
            if not numeric_cols:
                raise IncompatibleChartError("PIE chart requires at least one numeric measure column.")
            if len(rows) > 10:
                raise IncompatibleChartError(
                    f"PIE chart is limited to at most 10 categories for visual integrity (found {len(rows)} categories). Use a BAR chart instead.",
                    details={"category_count": len(rows)},
                )
            metric_col = y_col_override or numeric_cols[0]
            dim_col = x_col_override or (non_numeric_cols[0] if non_numeric_cols else columns[0])

            y_vals = []
            for r in rows:
                v = r.get(metric_col)
                num_v = cls._safe_to_float(v) or 0.0
                if num_v < 0:
                    raise IncompatibleChartError(
                        f"PIE chart cannot display negative values (found {num_v} in category '{r.get(dim_col)}').",
                        details={"negative_value": num_v},
                    )
                y_vals.append(num_v)

            if len(group_dims) > 1 and not x_col_override:
                x_cats = [" ".join(str(r.get(g, "")) for g in group_dims if g in r) for r in rows]
                dim_col = " ".join(group_dims)
            else:
                x_cats = [str(r.get(dim_col, "")) for r in rows]

            title = title_override or f"{metric_col} by {dim_col}"
            return (
                x_cats,
                [ChartSeriesSpec(name=metric_col, values=y_vals)],
                dim_col,
                metric_col,
                title,
                warnings,
            )

        # -------------------------------------------------------------
        # 4. BAR, LINE, AREA Validation
        # -------------------------------------------------------------
        if not numeric_cols:
            raise IncompatibleChartError(f"{requested_type.value} chart requires at least one numeric measure column.")

        dim_col = x_col_override or (non_numeric_cols[0] if non_numeric_cols else columns[0])
        metric_cols_to_plot = [y_col_override] if (y_col_override and y_col_override in numeric_cols) else numeric_cols

        if len(group_dims) > 1 and not x_col_override:
            x_cats = [" ".join(str(r.get(g, "")) for g in group_dims if g in r) for r in rows]
            dim_col = " ".join(group_dims)
        else:
            x_cats = [str(r.get(dim_col, "")) for r in rows]

        series_list: List[ChartSeriesSpec] = []

        for m_col in metric_cols_to_plot:
            vals = [cls._safe_to_float(r.get(m_col)) for r in rows]
            series_list.append(ChartSeriesSpec(name=m_col, values=vals))

        if requested_type == ChartTypeEnum.AREA:
            for s in series_list:
                if any(v is not None and v < 0 for v in s.values):
                    warnings.append("AREA chart contains negative values which may cause overlapping baseline regions.")

        if len(metric_cols_to_plot) == 1:
            title = title_override or f"{metric_cols_to_plot[0]} by {dim_col}"
            y_label = metric_cols_to_plot[0]
        else:
            title = title_override or f"{', '.join(metric_cols_to_plot)} by {dim_col}"
            y_label = "Value"

        return x_cats, series_list, dim_col, y_label, title, warnings

    @classmethod
    def _extract_tabular_data(cls, result: AnalyticalResult) -> Tuple[List[str], List[Dict[str, Any]]]:
        """Extracts column list and row records from TableResultData or series_data."""
        if result.table_data and result.table_data.rows:
            return result.table_data.columns, result.table_data.rows
        if result.series_data:
            metric_name = (result.lineage.source_columns[0] if result.lineage.source_columns else None) or "Value"
            cols = ["Category", metric_name]
            rows = [{"Category": p.label, metric_name: p.value} for p in result.series_data]
            return cols, rows
        return [], []

    @classmethod
    def _profile_result_columns(cls, columns: List[str], rows: List[Dict[str, Any]]) -> Dict[str, DataTypeEnum]:
        """Infers physical data types for result columns."""
        col_types: Dict[str, DataTypeEnum] = {}
        for col in columns:
            vals = [r.get(col) for r in rows]
            best_type, _, _, _, _, _ = TypeDetector.profile_column_vector(vals, column_name=col)
            col_types[col] = best_type
        return col_types

    @classmethod
    def _is_temporal_dimension(cls, col_name: str, values: List[str]) -> bool:
        """True if column name or values indicate a time/period series."""
        col_clean = col_name.lower().replace("_", " ").replace("-", " ")
        if any(kw in col_clean for kw in ["date", "tanggal", "month", "bulan", "year", "tahun", "period", "periode", "quarter"]):
            return True
        period_matches = sum(1 for v in values if PERIOD_HEADER_REGEX.match(v.strip()))
        return period_matches >= 3 or (len(values) > 0 and (period_matches / len(values)) >= 0.5)

    validate_and_extract = validate_and_extract_plot_data
