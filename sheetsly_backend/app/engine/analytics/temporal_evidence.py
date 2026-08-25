"""Deterministic calculation of extreme periods (highest/lowest) and evidence-based seasonality."""

from typing import Any, Dict, List, Optional, Tuple
import pandas as pd


class TemporalEvidenceCalculator:
    """Calculates deterministic extreme periods and statistical seasonality evidence for analytical results."""

    @classmethod
    def calculate_evidence(
        cls,
        result_df: pd.DataFrame,
        group_cols: List[str],
        primary_metric_col: str,
        is_ranked_limit: bool = False,
        is_top_per_group: bool = False,
        top_n: Optional[int] = None,
        has_temporal_dimension: bool = False,
    ) -> List[str]:
        """
        Analyzes the grouped result DataFrame to extract deterministic, strictly-scoped evidence:
        1. Context-aware highest/lowest labeling (distinguishing global dataset extremes from Top-N rankings and group-wise leaders).
        2. Strictly-gated seasonal pattern analysis (only on multi-year temporal trends).
        Returns a list of factual calculation step statements.
        """
        if result_df.empty or primary_metric_col not in result_df.columns:
            return []

        evidence_notes: List[str] = []

        # -------------------------------------------------------------
        # Case A: Top-N Per Group (e.g. Top 1 Category per Region)
        # -------------------------------------------------------------
        if is_top_per_group:
            primary_group_col = group_cols[0] if group_cols else "Group"
            evidence_notes.append(
                f"Identified top {top_n or 1} item(s) for each of the {len(result_df)} '{primary_group_col}' groups."
            )
            return evidence_notes

        valid_metric_rows = result_df[pd.to_numeric(result_df[primary_metric_col], errors="coerce").notna()].copy()
        if valid_metric_rows.empty:
            return []

        valid_metric_rows["_num_val"] = pd.to_numeric(valid_metric_rows[primary_metric_col])

        max_val = valid_metric_rows["_num_val"].max()
        min_val = valid_metric_rows["_num_val"].min()

        max_rows = valid_metric_rows[valid_metric_rows["_num_val"] == max_val]
        min_rows = valid_metric_rows[valid_metric_rows["_num_val"] == min_val]

        def _format_period_label(row: pd.Series) -> str:
            vals = [str(row[g]) for g in group_cols if g in row and pd.notna(row[g])]
            return " ".join(vals) if vals else "Record"

        def _format_num(v: float) -> str:
            if abs(v) >= 1000:
                return f"{v:,.2f}"
            return f"{v:.2f}" if isinstance(v, float) else str(v)

        max_periods = [_format_period_label(r) for _, r in max_rows.iterrows()]
        min_periods = [_format_period_label(r) for _, r in min_rows.iterrows()]

        # -------------------------------------------------------------
        # Case B: Ranked Top-N Limit (e.g. Top 5 months/products)
        # -------------------------------------------------------------
        if is_ranked_limit:
            if len(valid_metric_rows) == 1:
                evidence_notes.append(
                    f"Top period identified: '{max_periods[0]}' with {primary_metric_col} = {_format_num(max_val)}."
                )
            elif max_val == min_val:
                evidence_notes.append(
                    f"All {len(valid_metric_rows)} items in top ranking have identical {primary_metric_col} = {_format_num(max_val)}."
                )
            else:
                evidence_notes.append(
                    f"Top 1 in ranking: '{max_periods[0]}' with {primary_metric_col} = {_format_num(max_val)}."
                )
                evidence_notes.append(
                    f"Lowest within returned Top {len(valid_metric_rows)}: '{min_periods[0]}' with {primary_metric_col} = {_format_num(min_val)}."
                )
            return evidence_notes

        # -------------------------------------------------------------
        # Case C: Temporal Series (e.g. Monthly, Quarterly, Annual Trends)
        # -------------------------------------------------------------
        if has_temporal_dimension:
            if len(valid_metric_rows) == 1:
                evidence_notes.append(
                    f"Top period identified: '{max_periods[0]}' with {primary_metric_col} = {_format_num(max_val)}."
                )
            elif max_val == min_val:
                evidence_notes.append(
                    f"All {len(valid_metric_rows)} periods have identical {primary_metric_col} = {_format_num(max_val)}."
                )
            else:
                if len(max_periods) == 1:
                    evidence_notes.append(
                        f"Highest period in series: '{max_periods[0]}' with {primary_metric_col} = {_format_num(max_val)}."
                    )
                else:
                    joined = ", ".join([f"'{p}'" for p in max_periods])
                    evidence_notes.append(
                        f"Highest period in series (tie between {len(max_periods)} periods): {joined} with {primary_metric_col} = {_format_num(max_val)}."
                    )

                if len(min_periods) == 1:
                    evidence_notes.append(
                        f"Lowest period in series: '{min_periods[0]}' with {primary_metric_col} = {_format_num(min_val)}."
                    )
                else:
                    joined = ", ".join([f"'{p}'" for p in min_periods])
                    evidence_notes.append(
                        f"Lowest period (tie between {len(min_periods)} periods): {joined} with {primary_metric_col} = {_format_num(min_val)}."
                    )

            # Evaluate seasonality ONLY on multi-year temporal series with >= 12 periods
            if len(valid_metric_rows) >= 12:
                seasonality_note = cls._evaluate_seasonality(valid_metric_rows, group_cols, primary_metric_col)
                if seasonality_note:
                    evidence_notes.append(seasonality_note)

            return evidence_notes

        # -------------------------------------------------------------
        # Case D: Categorical Grouping (e.g. By Region, Category)
        # -------------------------------------------------------------
        if len(valid_metric_rows) == 1:
            evidence_notes.append(
                f"Leading category: '{max_periods[0]}' with {primary_metric_col} = {_format_num(max_val)}."
            )
        elif max_val == min_val:
            evidence_notes.append(
                f"All {len(valid_metric_rows)} categories have identical {primary_metric_col} = {_format_num(max_val)}."
            )
        else:
            evidence_notes.append(
                f"Leading category: '{max_periods[0]}' with {primary_metric_col} = {_format_num(max_val)}."
            )
            evidence_notes.append(
                f"Trailing category: '{min_periods[0]}' with {primary_metric_col} = {_format_num(min_val)}."
            )

        return evidence_notes

    @classmethod
    def _evaluate_seasonality(
        cls,
        df: pd.DataFrame,
        group_cols: List[str],
        metric_col: str,
    ) -> Optional[str]:
        """
        Evaluates multi-year seasonal patterns across calendar months deterministically.
        Only emits positive findings when strong recurring patterns exist.
        """
        year_col = next((c for c in group_cols if "year" in c.lower() and "month" not in c.lower()), None)
        month_col = next((c for c in group_cols if "month" in c.lower() and "year" not in c.lower()), None)
        ym_col = next((c for c in group_cols if "year_month" in c.lower() or "year-month" in c.lower()), None)

        work_df = df.copy()

        if ym_col and ym_col in work_df.columns:
            work_df["_cal_year"] = work_df[ym_col].astype(str).str.slice(0, 4)
            work_df["_cal_month"] = work_df[ym_col].astype(str).str.slice(5, 7)
            year_col = "_cal_year"
            month_col = "_cal_month"

        if not year_col or not month_col or year_col not in work_df.columns or month_col not in work_df.columns:
            return None

        unique_years = work_df[year_col].dropna().unique()
        if len(unique_years) < 2:
            return None

        pivot = work_df.pivot_table(
            index=month_col,
            columns=year_col,
            values="_num_val",
            aggfunc="sum",
        ).fillna(0)

        if pivot.empty or pivot.shape[0] < 3:
            return None

        total_years = len(pivot.columns)
        month_means = pivot.mean(axis=1)
        overall_mean = month_means.mean()

        if overall_mean <= 0:
            return None

        month_pct_diff = ((month_means - overall_mean) / overall_mean) * 100.0
        year_ranks = pivot.rank(ascending=False, axis=0)

        top_months = []
        for m_name, row in year_ranks.iterrows():
            top3_count = sum(1 for r in row if r <= 3)
            if top3_count >= (total_years * 0.7) and month_pct_diff.get(m_name, 0) > 15:
                top_months.append((str(m_name), round(month_pct_diff.get(m_name, 0), 1), top3_count))

        bottom_months = []
        for m_name, row in year_ranks.iterrows():
            bottom3_count = sum(1 for r in row if r >= (len(pivot) - 2))
            if bottom3_count >= (total_years * 0.7) and month_pct_diff.get(m_name, 0) < -15:
                bottom_months.append((str(m_name), round(month_pct_diff.get(m_name, 0), 1), bottom3_count))

        if top_months:
            top_desc = ", ".join([f"Month {m[0]} (+{m[1]}% vs avg, top 3 in {m[2]}/{total_years} years)" for m in top_months])
            bottom_desc = (
                f"; lowest recurring activity in {', '.join([f'Month {b[0]} ({b[1]}%)' for b in bottom_months])}"
                if bottom_months
                else ""
            )
            return (
                f"Seasonality evidence: Recurring seasonal pattern identified across {total_years} years. "
                f"Peak periods: {top_desc}{bottom_desc}."
            )

        return None
