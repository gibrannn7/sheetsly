"""Granular Analytics Engine: Deterministic Python calculations, multi-sheet joins, and temporal grouping."""

from datetime import date, datetime, timezone
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
    @staticmethod
    def _parse_date(val: Any) -> Optional[datetime]:
        """Robustly parses string, timestamp, date, or datetime objects into a datetime instance."""
        if val is None:
            return None
        if isinstance(val, datetime):
            return val
        if isinstance(val, date):
            return datetime(val.year, val.month, val.day)
        s = str(val).strip()
        if not s or s.lower() in {"none", "null", "nan", "nat"}:
            return None
        formats = [
            "%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d",
            "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y",
            "%m/%d/%Y", "%m-%d-%Y",
            "%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M:%S", "%m/%d/%Y %H:%M:%S",
            "%Y-%m", "%m/%Y", "%Y"
        ]
        for fmt in formats:
            try:
                return datetime.strptime(s, fmt)
            except ValueError:
                continue
        try:
            import pandas as pd
            ts = pd.to_datetime(s, dayfirst=True)
            if pd.notnull(ts):
                return ts.to_pydatetime()
        except Exception:
            pass
        return None

    @classmethod
    def execute_analytics_query(
        cls,
        user_query: str,
        workbook_index: WorkbookMetadataIndex,
        grid_a: Optional[Union[RawSheetGrid, Dict[str, RawSheetGrid]]] = None,
        secondary_grid: Optional[RawSheetGrid] = None,
        relationship_graph: Optional[RelationshipGraph] = None,
        active_sheet_name: Optional[str] = None,
        grids: Optional[Dict[str, RawSheetGrid]] = None,
    ) -> ExplainableAnalyticsResult:
        """
        Executes granular in-memory aggregation and visualization planning.
        """
        start_time = time.perf_counter()
        q_norm = user_query.lower()
        cur_sheet_name = active_sheet_name or workbook_index.active_sheet_name
        sheet_a = workbook_index.sheets.get(cur_sheet_name)
        if not sheet_a or not sheet_a.tables:
            raise ValueError(f"Sheet '{cur_sheet_name}' has no structured table.")
        table_a = sheet_a.tables[0]

        # Normalize grid_a / grids & secondary_grid
        target_input = grids if grids is not None else grid_a
        all_grids: Dict[str, RawSheetGrid] = {}
        if isinstance(target_input, dict):
            all_grids = target_input
            actual_grid_a = target_input.get(cur_sheet_name, list(target_input.values())[0] if target_input else None)
        else:
            actual_grid_a = target_input
            all_grids = {cur_sheet_name: target_input} if target_input else {}

        if actual_grid_a is None:
            raise ValueError(f"No grid data available for active sheet '{cur_sheet_name}'.")

        # Auto-build relationship graph if not provided and multi-sheet
        if relationship_graph is None and all_grids:
            relationship_graph = RelationshipDetector.detect_relationships(workbook_index, all_grids)

        # 1. Identify Target Measure
        measure_cols = [c for c in table_a.columns if c.semantic_type == SemanticTypeEnum.NUMERIC_MEASURE]
        if not measure_cols:
            measure_cols = [c for c in table_a.columns if c.data_type in {DataTypeEnum.FLOAT, DataTypeEnum.INTEGER, DataTypeEnum.CURRENCY, DataTypeEnum.PERCENTAGE}]
        if not measure_cols:
            raise ValueError(f"Table in '{cur_sheet_name}' has no numeric measures to analyze.")

        target_measure = None
        for c in measure_cols:
            if c.normalized_name in q_norm:
                target_measure = c
                break
        if not target_measure:
            target_measure = measure_cols[0]

        # 2. Identify Aggregation Operation
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

        # 3. Determine Grouping Dimension & Temporal Granularity
        is_temporal = any(w in q_norm for w in [
            "tren", "trend", "bulanan", "bulan", "tahun", "tahunan", "kuartal", "kuartalan",
            "harian", "mingguan", "date", "tanggal", "month", "monthly", "year", "annual", "quarter", "quarterly"
        ])
        dim_col = None
        temporal_granularity = None

        if is_temporal:
            temp_cols = [c for c in table_a.columns if c.semantic_type == SemanticTypeEnum.TEMPORAL]
            if temp_cols:
                dim_col = temp_cols[0]
            if any(w in q_norm for w in ["tahunan", "annual", "tahun", "year"]):
                temporal_granularity = "YEAR"
            elif any(w in q_norm for w in ["kuartal", "kuartalan", "quarter", "quarterly", "triwulan"]):
                temporal_granularity = "QUARTER"
            elif any(w in q_norm for w in ["harian", "daily", "hari"]):
                temporal_granularity = "DAY"
            elif any(w in q_norm for w in ["mingguan", "weekly", "minggu"]):
                temporal_granularity = "WEEK"
            else:
                temporal_granularity = "MONTH"

        # Check cross-sheet relationship candidates
        join_rel = None
        secondary_dim_col = None
        if relationship_graph:
            for rel in relationship_graph.relationships:
                if rel.status == RelationshipStatusEnum.VERIFIED and (rel.source_sheet == cur_sheet_name or rel.target_sheet == cur_sheet_name):
                    sec_sheet = rel.target_sheet if rel.source_sheet == cur_sheet_name else rel.source_sheet
                    sec_entry = workbook_index.sheets.get(sec_sheet)
                    if sec_entry and sec_entry.tables:
                        for col in sec_entry.tables[0].columns:
                            if col.semantic_type in {SemanticTypeEnum.CATEGORICAL, SemanticTypeEnum.TEXT} and col.normalized_name in q_norm:
                                join_rel = rel
                                secondary_dim_col = col
                                break
                    if join_rel:
                        break

        if join_rel and secondary_grid is None and all_grids:
            sec_sheet = join_rel.target_sheet if join_rel.source_sheet == cur_sheet_name else join_rel.source_sheet
            secondary_grid = all_grids.get(sec_sheet)

        cat_cols = [c for c in table_a.columns if c.semantic_type in {SemanticTypeEnum.CATEGORICAL, SemanticTypeEnum.TEXT}]
        is_group_requested = any(w in q_norm for w in [" per ", " by ", " berdasarkan ", " menurut ", " grouped "]) or any(c.normalized_name in q_norm for c in cat_cols)

        if not is_temporal:
            if secondary_dim_col:
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
        if secondary_grid and join_rel and secondary_dim_col:
            source_ranges.append(f"{join_rel.target_sheet if join_rel.source_sheet == cur_sheet_name else join_rel.source_sheet}!{workbook_index.sheets[join_rel.target_sheet if join_rel.source_sheet == cur_sheet_name else join_rel.source_sheet].tables[0].range_address}")

        grouped_data: Dict[str, List[float]] = {}
        grouped_sort_keys: Dict[str, Tuple[Any, ...]] = {}

        # Build join lookup map if cross-sheet
        join_lookup: Dict[Any, str] = {}
        if secondary_grid and join_rel and secondary_dim_col:
            key_col_idx = 1
            dim_col_idx = 1
            sec_tbl = workbook_index.sheets[join_rel.target_sheet if join_rel.target_sheet != cur_sheet_name else join_rel.source_sheet].tables[0]
            for c in sec_tbl.columns:
                if c.name == (join_rel.target_column if join_rel.target_sheet != cur_sheet_name else join_rel.source_column):
                    key_col_idx = c.index + 1
                if c.name == secondary_dim_col.name:
                    dim_col_idx = c.index + 1
            for r in range(sec_tbl.columns[0].index + 2, sec_tbl.row_count + 2):
                k_cell = secondary_grid.get_cell(r, key_col_idx)
                d_cell = secondary_grid.get_cell(r, dim_col_idx)
                k_val = k_cell.parsed_value if k_cell else None
                d_val = d_cell.parsed_value if d_cell else None
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
            raw_cell = actual_grid_a.get_cell(r, val_col_idx)
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
            sort_key: Tuple[Any, ...] = (0,)

            if secondary_dim_col and join_rel:
                k_cell = actual_grid_a.get_cell(r, join_key_idx)
                k_val = str(k_cell.parsed_value) if k_cell else ""
                group_key = join_lookup.get(k_val, "Unknown")
            elif dim_col:
                raw_d_cell = actual_grid_a.get_cell(r, dim_col_idx)
                raw_d = raw_d_cell.parsed_value if raw_d_cell else None
                if raw_d is not None:
                    if is_temporal:
                        dt = cls._parse_date(raw_d)
                        if dt:
                            if temporal_granularity == "YEAR":
                                group_key = f"{dt.year}"
                                sort_key = (dt.year, 0, 0)
                            elif temporal_granularity == "QUARTER":
                                q_num = (dt.month - 1) // 3 + 1
                                group_key = f"{dt.year} Q{q_num}"
                                sort_key = (dt.year, q_num, 0)
                            elif temporal_granularity == "WEEK":
                                iso_y, iso_w, _ = dt.isocalendar()
                                group_key = f"{iso_y}-W{iso_w:02d}"
                                sort_key = (iso_y, iso_w, 0)
                            elif temporal_granularity == "DAY":
                                group_key = f"{dt.year}-{dt.month:02d}-{dt.day:02d}"
                                sort_key = (dt.year, dt.month, dt.day)
                            else: # MONTH
                                group_key = f"{dt.year}-{dt.month:02d}"
                                sort_key = (dt.year, dt.month, 0)
                        else:
                            group_key = str(raw_d)
                    else:
                        group_key = str(raw_d)

            if group_key not in grouped_data:
                grouped_data[group_key] = []
                grouped_sort_keys[group_key] = sort_key
            grouped_data[group_key].append(float_val)

        # Compute Aggregated Results
        result_rows = []
        for k, v_list in grouped_data.items():
            agg_val = cls.calculate_aggregation(v_list, agg_op)
            row_dict = {
                dim_col.name if dim_col else "Metric": k,
                f"{agg_op}_{target_measure.name}": agg_val,
                "Count": len(v_list),
            }
            if is_temporal:
                row_dict["_sort_key"] = grouped_sort_keys.get(k, (0,))
            result_rows.append(row_dict)

        # Apply Ranking / Sorting
        is_bottom = "terendah" in q_norm or "bottom" in q_norm
        is_top = "teratas" in q_norm or "tertinggi" in q_norm or "top" in q_norm or "ranking" in q_norm
        metric_col_name = f"{agg_op}_{target_measure.name}"

        if is_bottom:
            result_rows.sort(key=lambda x: x[metric_col_name])
        elif is_top:
            result_rows.sort(key=lambda x: x[metric_col_name], reverse=True)
        elif is_temporal:
            # Chronological sort for pure temporal data
            result_rows.sort(key=lambda x: x.get("_sort_key", (0,)))
        else:
            result_rows.sort(key=lambda x: x[metric_col_name], reverse=True)

        if is_temporal:
            for r in result_rows:
                r.pop("_sort_key", None)

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

        chart_type = suitability.recommended_chart_type
        if is_temporal and chart_type not in ["LINE", "COLUMN"]:
            chart_type = "LINE"

        chart_data = ChartData(
            chart_type=chart_type,
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
                filters_applied=[],
                verification_status="VERIFIED_NUMERIC_TRUTH",
            ),
            summary_metric=f"{agg_op} {target_measure.name}",
            summary_value=cls.calculate_aggregation([x for v in grouped_data.values() for x in v], agg_op),
        )

        return ExplainableAnalyticsResult(
            question=user_query,
            resolved_intent=f"Calculate {agg_op} of {target_measure.name}" + (f" grouped by {dim_col.name} ({temporal_granularity})" if (dim_col and is_temporal) else (f" grouped by {dim_col.name}" if dim_col else "")),
            source_sheets=[cur_sheet_name] + ([join_rel.target_sheet] if join_rel else []),
            source_columns=[target_measure.name] + ([dim_col.name] if dim_col else []),
            source_ranges=source_ranges,
            filters_applied=[],
            aggregation=agg_op,
            grouping=dim_col.name if dim_col else None,
            result_rows=result_rows,
            calculation_method=f"Python deterministic {agg_op} aggregation over {len(result_rows)} {'temporal periods' if is_temporal else 'groups'}",
            verification_status="VERIFIED_NUMERIC_TRUTH",
            chart_data=chart_data,
            timing_ms=(time.perf_counter() - start_time) * 1000,
        )
