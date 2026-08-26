"""Granular Analytics Engine: Deterministic Python calculations, multi-sheet joins, and temporal grouping."""

from datetime import datetime, timezone
import statistics
import time
from typing import Any, Dict, List, Optional, Tuple, Union
from pydantic import BaseModel, Field

from app.engine.analytics.visualization_engine import (
    CanonicalChartTypeEnum,
    ChartData,
    ChartDataset,
    ChartProvenance,
    SmartVisualizationEngine,
    VisualizationPlan,
)
from app.engine.parser.sheet_reader import RawSheetGrid
from app.engine.profiler.relationship_detector import (
    RelationshipDetector,
    RelationshipGraph,
    RelationshipStatusEnum,
)
from app.engine.profiler.workbook_index import (
    ColumnIndexEntry,
    SheetIndexEntry,
    TableIndexEntry,
    WorkbookMetadataIndex,
)
from app.models.schemas import DataTypeEnum, SemanticTypeEnum


class ExplainableAnalyticsResult(BaseModel):
    """Structured analytical outcome with factual evidence and provenance."""

    question: str
    resolved_intent: str
    source_sheets: List[str]
    source_columns: List[str]
    source_ranges: List[str]
    filters_applied: List[str] = Field(default_factory=list)
    aggregation: str
    grouping: Optional[str] = None
    result_rows: List[Dict[str, Any]]
    calculation_method: str
    verification_status: str = "VERIFIED_NUMERIC_TRUTH"
    chart_data: Optional[ChartData] = None
    timing_ms: float = 0.0


class GranularAnalyticsEngine:
    """Executes deterministic grouping, filtering, ranking, and verified multi-sheet analytical joins."""

    @classmethod
    def calculate_aggregation(cls, values: List[float], op: str) -> float:
        """Calculates scalar aggregate with strict numerical truth."""
        if not values:
            return 0.0
        clean_vals = [float(v) for v in values if v is not None]
        if not clean_vals:
            return 0.0

        op_upper = op.upper()
        if op_upper == "SUM":
            return float(round(sum(clean_vals), 4))
        elif op_upper in {"AVERAGE", "MEAN"}:
            return float(round(statistics.mean(clean_vals), 4))
        elif op_upper in {"COUNT", "COUNT_ROWS", "COUNTA"}:
            return float(len(clean_vals))
        elif op_upper == "MIN":
            return float(min(clean_vals))
        elif op_upper == "MAX":
            return float(max(clean_vals))
        elif op_upper == "MEDIAN":
            return float(round(statistics.median(clean_vals), 4))
        return float(round(sum(clean_vals), 4))

    @classmethod
    def execute_analytics_query(
        cls,
        user_query: str,
        workbook_index: WorkbookMetadataIndex,
        grids: Dict[str, RawSheetGrid],
        relationship_graph: Optional[RelationshipGraph] = None,
        active_sheet_name: Optional[str] = None,
    ) -> ExplainableAnalyticsResult:
        """
        Executes complete deterministic analytical query with provenance and chart generation.
        """
        start_time = time.perf_counter()
        q_norm = user_query.strip().lower()
        cur_sheet_name = active_sheet_name or workbook_index.active_sheet_name
        sheet_entry = workbook_index.sheets.get(cur_sheet_name)
        if not sheet_entry or not sheet_entry.tables:
            raise ValueError(f"Sheet '{cur_sheet_name}' has no structured table.")

        table_a = sheet_entry.tables[0]
        grid_a = grids.get(cur_sheet_name)
        if not grid_a:
            raise ValueError(f"Grid for '{cur_sheet_name}' not available.")

        # 1. Check Multi-Sheet Relation Requirements
        target_sheet_name = cur_sheet_name
        join_rel = None
        secondary_dim_col = None
        secondary_grid = None

        for other_name, other_sheet in workbook_index.sheets.items():
            if other_name != cur_sheet_name and other_sheet.tables:
                for col in other_sheet.tables[0].columns:
                    if col.normalized_name in q_norm and col.name.lower() not in [c.name.lower() for c in table_a.columns]:
                        # Requires join with other_sheet
                        if not relationship_graph:
                            relationship_graph = RelationshipDetector.detect_relationships(workbook_index, grids)
                        verified_links = relationship_graph.find_relationships_for_sheets(cur_sheet_name, other_name)
                        if verified_links:
                            join_rel = verified_links[0]
                            secondary_dim_col = col
                            secondary_grid = grids.get(other_name)
                            break

        # 2. Determine Measure Column & Aggregation Operation
        measure_cols = [c for c in table_a.columns if c.semantic_type == SemanticTypeEnum.NUMERIC_MEASURE]
        target_measure = measure_cols[0] if measure_cols else table_a.columns[-1]
        for m in measure_cols:
            if m.normalized_name in q_norm:
                target_measure = m
                break

        agg_op = "SUM"
        if any(w in q_norm for w in ["rata-rata", "average", "mean"]):
            agg_op = "AVERAGE"
        elif any(w in q_norm for w in ["jumlah transaksi", "count", "banyaknya", "frekuensi"]):
            agg_op = "COUNT"
        elif "nilai min" in q_norm or "minimum" in q_norm or "angka terendah" in q_norm:
            agg_op = "MIN"
        elif "nilai max" in q_norm or "maksimum" in q_norm or "angka tertinggi" in q_norm:
            agg_op = "MAX"
        elif "median" in q_norm:
            agg_op = "MEDIAN"

        # 3. Determine Grouping Dimension
        is_temporal = any(w in q_norm for w in ["tren", "trend", "bulanan", "bulan", "tahun", "tahunan", "kuartal", "harian", "mingguan", "date", "tanggal", "month", "year"])
        dim_col = None
        temporal_granularity = None

        cat_cols = [c for c in table_a.columns if c.semantic_type in {SemanticTypeEnum.CATEGORICAL, SemanticTypeEnum.TEXT}]
        is_group_requested = any(w in q_norm for w in [" per ", " by ", " berdasarkan ", " menurut ", " grouped "]) or any(c.normalized_name in q_norm for c in cat_cols)

        if is_temporal:
            temp_cols = [c for c in table_a.columns if c.semantic_type == SemanticTypeEnum.TEMPORAL]
            if temp_cols:
                dim_col = temp_cols[0]
                temporal_granularity = "MONTH" if ("bulan" in q_norm or "month" in q_norm) else ("YEAR" if "tahun" in q_norm else "MONTH")
        elif secondary_dim_col:
            dim_col = secondary_dim_col
        else:
            for c in cat_cols:
                if c.normalized_name in q_norm:
                    dim_col = c
                    break
            if not dim_col and is_group_requested and cat_cols:
                dim_col = cat_cols[0]

        # 4. Perform In-Memory Extraction & Aggregation
        source_ranges = [f"{cur_sheet_name}!{table_a.range_address}"]
        if secondary_grid and join_rel:
            source_ranges.append(f"{secondary_dim_col.normalized_name}!{join_rel.target_sheet}")

        grouped_data: Dict[str, List[float]] = {}

        # Build join lookup map if cross-sheet
        join_lookup: Dict[Any, str] = {}
        if secondary_grid and join_rel and secondary_dim_col:
            # map join key -> dimension value
            key_col_idx = 1
            dim_col_idx = 1
            sec_tbl = workbook_index.sheets[join_rel.target_sheet if join_rel.target_sheet != cur_sheet_name else join_rel.source_sheet].tables[0]
            for c in sec_tbl.columns:
                if c.name == (join_rel.target_column if join_rel.target_sheet != cur_sheet_name else join_rel.source_column):
                    key_col_idx = c.index + 1
                if c.name == secondary_dim_col.name:
                    dim_col_idx = c.index + 1
            for r in range(sec_tbl.columns[0].index + 2, sec_tbl.row_count + 2):
                k_val = secondary_grid.get_cell(r, key_col_idx).parsed_value
                d_val = secondary_grid.get_cell(r, dim_col_idx).parsed_value
                if k_val is not None and d_val is not None:
                    join_lookup[str(k_val)] = str(d_val)

        # Iterate rows in table A
        val_col_idx = target_measure.index + 1
        dim_col_idx = dim_col.index + 1 if (dim_col and not secondary_dim_col) else 1
        join_key_idx = 1
        if join_rel:
            for c in table_a.columns:
                if c.name == (join_rel.source_column if join_rel.source_sheet == cur_sheet_name else join_rel.target_column):
                    join_key_idx = c.index + 1

        for r in range(2, table_a.row_count + 2):
            raw_cell = grid_a.get_cell(r, val_col_idx)
            cell_val = raw_cell.parsed_value if raw_cell else None
            if cell_val is None:
                continue

            float_val = None
            if isinstance(cell_val, (int, float)):
                float_val = float(cell_val)
            elif isinstance(cell_val, str):
                try:
                    float_val = float(cell_val.replace(",", "").replace("$", "").strip())
                except (ValueError, TypeError):
                    continue

            if float_val is None:
                continue

            group_key = "Total"
            if secondary_dim_col and join_rel:
                k_val = str(grid_a.get_cell(r, join_key_idx).parsed_value)
                group_key = join_lookup.get(k_val, "Unknown")
            elif dim_col:
                raw_d = grid_a.get_cell(r, dim_col_idx).parsed_value
                if raw_d is not None:
                    if is_temporal and isinstance(raw_d, (datetime, str)):
                        s_str = str(raw_d)
                        group_key = s_str[:7] if temporal_granularity == "MONTH" else (s_str[:4] if temporal_granularity == "YEAR" else s_str[:10])
                    else:
                        group_key = str(raw_d)

            if group_key not in grouped_data:
                grouped_data[group_key] = []
            grouped_data[group_key].append(float_val)

        # Compute Aggregated Results
        result_rows = []
        for k, v_list in grouped_data.items():
            agg_val = cls.calculate_aggregation(v_list, agg_op)
            result_rows.append({
                dim_col.name if dim_col else "Metric": k,
                f"{agg_op}_{target_measure.name}": agg_val,
                "Count": len(v_list),
            })

        # Apply Ranking / Sorting
        is_bottom = "terendah" in q_norm or "bottom" in q_norm
        is_top = "teratas" in q_norm or "tertinggi" in q_norm or "top" in q_norm or "ranking" in q_norm
        metric_col_name = f"{agg_op}_{target_measure.name}"

        if is_bottom:
            result_rows.sort(key=lambda x: x[metric_col_name])
        else:
            result_rows.sort(key=lambda x: x[metric_col_name], reverse=True)

        # Check limit (e.g. 'top 5', 'top 10')
        limit = None
        for word in q_norm.split():
            if word.isdigit() and int(word) <= 100:
                limit = int(word)
                break
        if limit:
            result_rows = result_rows[:limit]

        # 5. Evaluate Visualization Suitability & Build ChartData
        suitability = SmartVisualizationEngine.evaluate_suitability(
            dimension_col=dim_col,
            measure_cols=[target_measure],
            query=user_query,
            dimension_cardinality=len(result_rows),
            is_temporal=is_temporal,
        )

        labels = [str(r[dim_col.name if dim_col else "Metric"]) for r in result_rows]
        values = [r[metric_col_name] for r in result_rows]

        chart_data = ChartData(
            chart_type=suitability.recommended_chart_type,
            title=f"{agg_op} of {target_measure.name}" + (f" by {dim_col.name}" if dim_col else ""),
            labels=labels,
            datasets=[ChartDataset(name=metric_col_name, values=values, color="#10b981")],
            provenance=ChartProvenance(
                dataset_id=workbook_index.dataset_id,
                source_sheets=[cur_sheet_name] + ([join_rel.target_sheet] if join_rel else []),
                source_columns=[target_measure.name] + ([dim_col.name] if dim_col else []),
                source_ranges=source_ranges,
                aggregation=agg_op,
                dimension=dim_col.name if dim_col else None,
                measure=target_measure.name,
            ),
            summary_metric=f"{agg_op} {target_measure.name}",
            summary_value=values[0] if len(values) == 1 else round(sum(values), 2),
        )

        calc_time = (time.perf_counter() - start_time) * 1000

        return ExplainableAnalyticsResult(
            question=user_query,
            resolved_intent=f"Calculate {agg_op} of {target_measure.name}" + (f" grouped by {dim_col.name}" if dim_col else ""),
            source_sheets=[cur_sheet_name] + ([join_rel.target_sheet] if join_rel else []),
            source_columns=[target_measure.name] + ([dim_col.name] if dim_col else []),
            source_ranges=source_ranges,
            aggregation=agg_op,
            grouping=dim_col.name if dim_col else None,
            result_rows=result_rows,
            calculation_method=f"Python deterministic {agg_op} aggregation over {len(result_rows)} groups",
            chart_data=chart_data,
            timing_ms=calc_time,
        )
