"""Deterministic Smart Chart Generation Engine.

Analyzes dataset & table schema to discover, score, rank, and render
meaningful visualizations without requiring manual user configuration or LLM inference.
"""

from typing import Any, Dict, List, Optional, Set, Tuple
from app.engine.analytics import analytical_engine
from app.engine.analytics.instruction_model import AggregationSpec, AnalyticalInstruction, SortSpec
from app.engine.pipeline import ingestion_pipeline
from app.engine.profiler.type_detector import IDENTIFIER_KEYWORDS, TEMPORAL_KEYWORDS, TypeDetector
from app.models.schemas import ColumnMetadata, DataTypeEnum, SemanticTypeEnum, TableRegion
from .chart_model import (
    ChartMetadata,
    ChartTypeEnum,
    SmartChartItem,
    SmartGenerateRequest,
    SmartGenerateResponse,
    VisualizationRequest,
)
from .engine import visualization_engine


class CandidateChart:
    """Internal candidate representation with ranking heuristics."""

    def __init__(
        self,
        chart_type: ChartTypeEnum,
        title: str,
        dimension_col: Optional[str],
        metric_col: Optional[str],
        analytical_intent: str,
        why_this_chart: str,
        score: float,
        instruction: AnalyticalInstruction,
    ):
        self.chart_type = chart_type
        self.title = title
        self.dimension_col = dimension_col
        self.metric_col = metric_col
        self.analytical_intent = analytical_intent
        self.why_this_chart = why_this_chart
        self.score = score
        self.instruction = instruction


class SmartChartGenerator:
    """
    Deterministic rule-based generator that evaluates table column semantics,
    generates chart candidates, filters redundant/inappropriate charts,
    and returns the top ranked visualization set.
    """

    @classmethod
    def generate(cls, dataset_id: str, request: SmartGenerateRequest) -> SmartGenerateResponse:
        """
        Executes end-to-end smart chart generation for a table in a dataset.
        """
        overview = ingestion_pipeline.get_overview(dataset_id)
        if not overview.sheets:
            return SmartGenerateResponse(
                dataset_id=dataset_id,
                sheet_name="",
                table_id="",
                total_candidates_evaluated=0,
                selected_charts_count=0,
                charts=[],
                empty_reason="The dataset does not contain any worksheets.",
            )

        # 1. Resolve Target Sheet & Table
        target_sheet_name = request.sheet_name or overview.sheets[0].name
        target_sheet = next((s for s in overview.sheets if s.name == target_sheet_name), overview.sheets[0])

        if not target_sheet.tables:
            return SmartGenerateResponse(
                dataset_id=dataset_id,
                sheet_name=target_sheet.name,
                table_id="",
                total_candidates_evaluated=0,
                selected_charts_count=0,
                charts=[],
                empty_reason="The selected worksheet does not contain any detected tabular data regions.",
            )

        target_table_id = request.table_id or target_sheet.tables[0].table_id
        target_table = next((t for t in target_sheet.tables if t.table_id == target_table_id), target_sheet.tables[0])

        # 2. Classify Columns
        numeric_measures = [c for c in target_table.columns if cls._is_numeric_measure(c)]
        temporal_dims = [c for c in target_table.columns if cls._is_temporal_dimension(c)]
        categorical_dims = [c for c in target_table.columns if cls._is_categorical_dimension(c)]

        # 3. Generate Candidate Charts
        candidates: List[CandidateChart] = []

        # A. Temporal Trend Candidates (Line Charts) - Highest business value
        for t_col in temporal_dims:
            if t_col.unique_count >= 2:
                for m_col in numeric_measures:
                    inst = AnalyticalInstruction(
                        operation="GROUP_BY",
                        dataset_id=dataset_id,
                        sheet_name=target_sheet.name,
                        table_id=target_table.table_id,
                        group_by_columns=[t_col.name],
                        aggregations=[
                            AggregationSpec(
                                column=m_col.name,
                                operation="SUM",
                                alias=f"Total_{m_col.name}",
                            )
                        ],
                        sort=SortSpec(
                            column=t_col.name,
                            ascending=True,
                        ),
                        limit=30,
                    )
                    candidates.append(
                        CandidateChart(
                            chart_type=ChartTypeEnum.LINE,
                            title=f"Trend of {m_col.name} over {t_col.name}",
                            dimension_col=t_col.name,
                            metric_col=m_col.name,
                            analytical_intent=f"Analyze temporal trend of {m_col.name} grouped by {t_col.name}",
                            why_this_chart=f"'{t_col.name}' is a temporal dimension and '{m_col.name}' is a quantitative metric. A line chart reveals chronological patterns and trends.",
                            score=95.0,
                            instruction=inst,
                        )
                    )

        # B. Categorical Comparison Candidates (Bar Charts)
        for c_col in categorical_dims:
            if 2 <= c_col.unique_count <= 35:
                for m_col in numeric_measures:
                    score = 90.0
                    if 3 <= c_col.unique_count <= 15:
                        score += 5.0  # Optimal category density bonus
                    elif c_col.unique_count > 20:
                        score -= 10.0  # High category count penalty

                    inst = AnalyticalInstruction(
                        operation="GROUP_BY",
                        dataset_id=dataset_id,
                        sheet_name=target_sheet.name,
                        table_id=target_table.table_id,
                        group_by_columns=[c_col.name],
                        aggregations=[
                            AggregationSpec(
                                column=m_col.name,
                                operation="SUM",
                                alias=f"Total_{m_col.name}",
                            )
                        ],
                        sort=SortSpec(
                            column=f"Total_{m_col.name}",
                            ascending=False,
                        ),
                        limit=10,
                    )
                    candidates.append(
                        CandidateChart(
                            chart_type=ChartTypeEnum.BAR,
                            title=f"Total {m_col.name} by {c_col.name}",
                            dimension_col=c_col.name,
                            metric_col=m_col.name,
                            analytical_intent=f"Compare total {m_col.name} across {c_col.name} categories",
                            why_this_chart=f"'{c_col.name}' contains {c_col.unique_count} distinct categories and '{m_col.name}' is a primary metric. A ranked bar chart provides direct category comparison.",
                            score=score,
                            instruction=inst,
                        )
                    )

        # C. Categorical Part-to-Whole Share (Pie Charts) - Strictly for 2 to 7 categories
        for c_col in categorical_dims:
            if 2 <= c_col.unique_count <= 7:
                for m_col in numeric_measures:
                    # Verify sample non-negativity
                    if not any(isinstance(v, (int, float)) and v < 0 for v in m_col.sample_values):
                        inst = AnalyticalInstruction(
                            operation="GROUP_BY",
                            dataset_id=dataset_id,
                            sheet_name=target_sheet.name,
                            table_id=target_table.table_id,
                            group_by_columns=[c_col.name],
                            aggregations=[
                                AggregationSpec(
                                    column=m_col.name,
                                    operation="SUM",
                                    alias=f"Total_{m_col.name}",
                                )
                            ],
                            sort=SortSpec(
                                column=f"Total_{m_col.name}",
                                ascending=False,
                            ),
                            limit=7,
                        )
                        candidates.append(
                            CandidateChart(
                                chart_type=ChartTypeEnum.PIE,
                                title=f"{m_col.name} Share by {c_col.name}",
                                dimension_col=c_col.name,
                                metric_col=m_col.name,
                                analytical_intent=f"Show proportional distribution of {m_col.name} across {c_col.name}",
                                why_this_chart=f"'{c_col.name}' has {c_col.unique_count} distinct categories (ideal for <=7 categories), making a pie chart suitable for part-to-whole share analysis.",
                                score=78.0,
                                instruction=inst,
                            )
                        )

        # D. Continuous Numeric Correlation (Scatter Plot)
        if len(numeric_measures) >= 2:
            for i in range(len(numeric_measures)):
                for j in range(i + 1, min(len(numeric_measures), i + 3)):
                    m1 = numeric_measures[i]
                    m2 = numeric_measures[j]
                    inst = AnalyticalInstruction(
                        operation="FILTER",
                        dataset_id=dataset_id,
                        sheet_name=target_sheet.name,
                        table_id=target_table.table_id,
                        limit=500,
                    )
                    candidates.append(
                        CandidateChart(
                            chart_type=ChartTypeEnum.SCATTER,
                            title=f"{m2.name} vs {m1.name}",
                            dimension_col=m1.name,
                            metric_col=m2.name,
                            analytical_intent=f"Examine correlation and dispersion between {m1.name} and {m2.name}",
                            why_this_chart=f"'{m1.name}' and '{m2.name}' are continuous numeric variables. A scatter plot reveals relationship strength, clusters, and bivariate variance.",
                            score=72.0,
                            instruction=inst,
                        )
                    )

        # E. Univariate Continuous Distribution (Histogram)
        for m_col in numeric_measures:
            if m_col.unique_count >= 4:
                inst = AnalyticalInstruction(
                    operation="FILTER",
                    dataset_id=dataset_id,
                    sheet_name=target_sheet.name,
                    table_id=target_table.table_id,
                    target_column=m_col.name,
                    limit=1000,
                )
                candidates.append(
                    CandidateChart(
                        chart_type=ChartTypeEnum.HISTOGRAM,
                        title=f"Distribution of {m_col.name}",
                        dimension_col=m_col.name,
                        metric_col=m_col.name,
                        analytical_intent=f"Inspect frequency distribution and skewness of {m_col.name}",
                        why_this_chart=f"'{m_col.name}' is a continuous metric. A histogram visualizes value frequency, spread, skewness, and central tendency.",
                        score=68.0,
                        instruction=inst,
                    )
                )

        # F. Categorical Frequency Distribution (Count Bar) - Fallback when measures are limited
        if len(numeric_measures) == 0:
            for c_col in categorical_dims:
                if 2 <= c_col.unique_count <= 25:
                    inst = AnalyticalInstruction(
                        operation="GROUP_BY",
                        dataset_id=dataset_id,
                        sheet_name=target_sheet.name,
                        table_id=target_table.table_id,
                        group_by_columns=[c_col.name],
                        aggregations=[
                            AggregationSpec(
                                column=c_col.name,
                                operation="COUNT_ROWS",
                                alias="Record_Count",
                            )
                        ],
                        sort=SortSpec(
                            column="Record_Count",
                            ascending=False,
                        ),
                        limit=10,
                    )
                    candidates.append(
                        CandidateChart(
                            chart_type=ChartTypeEnum.BAR,
                            title=f"Record Count by {c_col.name}",
                            dimension_col=c_col.name,
                            metric_col="Record_Count",
                            analytical_intent=f"Analyze frequency of occurrences across {c_col.name}",
                            why_this_chart=f"'{c_col.name}' contains discrete categories. Counting records highlights transaction frequency across categories without requiring a separate measure.",
                            score=60.0,
                            instruction=inst,
                        )
                    )

        total_evaluated = len(candidates)
        if not candidates:
            return SmartGenerateResponse(
                dataset_id=dataset_id,
                sheet_name=target_sheet.name,
                table_id=target_table.table_id,
                total_candidates_evaluated=0,
                selected_charts_count=0,
                charts=[],
                empty_reason="The dataset does not contain a suitable categorical, temporal, or numeric relationship for the available chart types.",
            )

        # 4. Redundancy & Diversity Filtering
        filtered_candidates = cls._filter_and_rank_candidates(candidates, max_charts=request.max_charts)

        # 5. Execute and Render Selected Charts
        rendered_items: List[SmartChartItem] = []
        for cand in filtered_candidates:
            try:
                # Step 5a: Execute calculation deterministically in Python/Pandas
                result = analytical_engine.execute(cand.instruction)

                # Step 5b: Render to chart image artifact
                x_override = cand.dimension_col if cand.chart_type == ChartTypeEnum.SCATTER else None
                y_override = cand.metric_col if cand.chart_type == ChartTypeEnum.SCATTER else None

                viz_req = VisualizationRequest(
                    dataset_id=dataset_id,
                    analytical_result=result,
                    chart_type=cand.chart_type,
                    title=cand.title,
                    x_column=x_override,
                    y_column=y_override,
                )
                viz_res = visualization_engine.render(viz_req)

                rendered_items.append(
                    SmartChartItem(
                        chart_id=viz_res.chart_metadata.chart_id,
                        title=cand.title,
                        chart_type=cand.chart_type,
                        dimension_column=cand.dimension_col,
                        metric_column=cand.metric_col,
                        analytical_intent=cand.analytical_intent,
                        why_this_chart=cand.why_this_chart,
                        rank_score=cand.score,
                        instruction=cand.instruction,
                        visualization=viz_res,
                    )
                )
            except Exception as ex:
                # If a specific chart rendering encounters data incompatibility, skip gracefully
                continue

        if not rendered_items:
            return SmartGenerateResponse(
                dataset_id=dataset_id,
                sheet_name=target_sheet.name,
                table_id=target_table.table_id,
                total_candidates_evaluated=total_evaluated,
                selected_charts_count=0,
                charts=[],
                empty_reason="Calculations completed, but data distributions were incompatible with presentation chart constraints.",
            )

        return SmartGenerateResponse(
            dataset_id=dataset_id,
            sheet_name=target_sheet.name,
            table_id=target_table.table_id,
            total_candidates_evaluated=total_evaluated,
            selected_charts_count=len(rendered_items),
            charts=rendered_items,
        )

    @classmethod
    def _filter_and_rank_candidates(
        cls,
        candidates: List[CandidateChart],
        max_charts: int = 5,
    ) -> List[CandidateChart]:
        """
        Ranks candidates and applies diversity and redundancy filtering.
        Ensures max 5 charts, with varied dimensions and metrics.
        """
        # Sort by score descending
        candidates.sort(key=lambda c: c.score, reverse=True)

        selected: List[CandidateChart] = []
        dim_counts: Dict[str, int] = {}
        metric_counts: Dict[str, int] = {}
        seen_pairs: Set[Tuple[str, str, ChartTypeEnum]] = set()

        max_limit = min(5, max(1, max_charts))

        for cand in candidates:
            if len(selected) >= max_limit:
                break

            dim_key = cand.dimension_col or ""
            metric_key = cand.metric_col or ""
            pair_key = (dim_key, metric_key, cand.chart_type)

            # Avoid exact duplicate chart intent
            if pair_key in seen_pairs:
                continue

            # Diversity heuristic: cap any single dimension at 2 charts
            if dim_key and dim_counts.get(dim_key, 0) >= 2 and len(candidates) > max_limit:
                continue

            # Diversity heuristic: cap any single metric at 3 charts
            if metric_key and metric_counts.get(metric_key, 0) >= 3 and len(candidates) > max_limit:
                continue

            selected.append(cand)
            seen_pairs.add(pair_key)
            if dim_key:
                dim_counts[dim_key] = dim_counts.get(dim_key, 0) + 1
            if metric_key:
                metric_counts[metric_key] = metric_counts.get(metric_key, 0) + 1

        # If strict diversity left us with fewer than max_limit, backfill with remaining best candidates
        if len(selected) < max_limit:
            for cand in candidates:
                if len(selected) >= max_limit:
                    break
                if cand not in selected:
                    pair_key = (cand.dimension_col or "", cand.metric_col or "", cand.chart_type)
                    if pair_key not in seen_pairs:
                        selected.append(cand)
                        seen_pairs.add(pair_key)

        return selected[:max_limit]

    @classmethod
    def _is_identifier_column(cls, col: ColumnMetadata) -> bool:
        """True if column is a primary key, reference code, or unique identifier."""
        if col.semantic_type == SemanticTypeEnum.IDENTIFIER:
            return True

        col_lower = col.name.lower().strip()
        col_clean = col_lower.replace("_", " ").replace("-", " ")

        # Keyword checks
        for kw in IDENTIFIER_KEYWORDS:
            if kw == col_lower or f"{kw} " in col_clean or f" {kw}" in col_clean or col_clean.endswith(f" {kw}"):
                return True

        if col_lower.endswith("_id") or col_lower.endswith(" id") or col_lower == "id":
            return True

        # Uniqueness check on non-trivial tables (100% unique strings/integers with total_count > 15)
        if col.total_count > 15 and col.unique_count == col.total_count and col.data_type in {DataTypeEnum.STRING, DataTypeEnum.INTEGER}:
            return True

        return False

    @classmethod
    def _is_temporal_dimension(cls, col: ColumnMetadata) -> bool:
        """True if column is a date/time or period series."""
        if col.semantic_type == SemanticTypeEnum.TEMPORAL:
            return True
        if col.data_type in {DataTypeEnum.DATE, DataTypeEnum.DATETIME}:
            return True

        col_clean = col.name.lower().replace("_", " ").replace("-", " ")
        if any(kw in col_clean.split() for kw in TEMPORAL_KEYWORDS):
            return True
        if any(kw in col_clean for kw in ["date", "tanggal", "month", "bulan", "year", "tahun", "period", "periode", "quarter"]):
            return True

        return False

    @classmethod
    def _is_numeric_measure(cls, col: ColumnMetadata) -> bool:
        """True if column is a quantitative numerical measure suitable for summation/averages."""
        if cls._is_identifier_column(col):
            return False
        if cls._is_temporal_dimension(col):
            return False
        if col.semantic_type == SemanticTypeEnum.NUMERIC_MEASURE:
            return True
        if col.data_type in {DataTypeEnum.INTEGER, DataTypeEnum.FLOAT, DataTypeEnum.CURRENCY, DataTypeEnum.PERCENTAGE}:
            if col.unique_count <= 1:
                return False
            return True
        return False

    @classmethod
    def _is_categorical_dimension(cls, col: ColumnMetadata) -> bool:
        """True if column represents discrete grouping categories."""
        if cls._is_identifier_column(col):
            return False
        if cls._is_temporal_dimension(col):
            return False
        if col.semantic_type == SemanticTypeEnum.CATEGORICAL:
            return True
        if col.data_type == DataTypeEnum.STRING:
            if col.unique_count > 35:
                return False  # Exclude high-cardinality strings from becoming 35+ category charts
            if col.unique_count < 2:
                return False
            return True
        if col.data_type in {DataTypeEnum.INTEGER, DataTypeEnum.BOOLEAN} and 2 <= col.unique_count <= 10:
            if not cls._is_numeric_measure(col):
                return True
        return False
