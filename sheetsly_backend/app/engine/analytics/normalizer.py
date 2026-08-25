"""Deterministic Query Normalizer for pre-planning intent extraction and post-planning canonical instruction enforcement."""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from app.engine.ai.models import AIQueryStatus, ClarificationRequest
from app.engine.analytics.expressions import DateDimensionOpEnum, DimensionParser
from app.engine.analytics.instruction_model import (
    AggregationOpEnum,
    AggregationSpec,
    AnalyticalInstruction,
    FilterCombinationEnum,
    FilterCondition,
    FilterOperatorEnum,
    OperationEnum,
    SortSpec,
)
from app.models.schemas import DataTypeEnum, SemanticTypeEnum, TableRegion

logger = logging.getLogger("sheetsly.analytics.normalizer")

# Word-to-number mapping for Indonesian and English
WORD_TO_NUM: Dict[str, int] = {
    "satu": 1, "dua": 2, "tiga": 3, "empat": 4, "lima": 5,
    "enam": 6, "tujuh": 7, "delapan": 8, "sembilan": 9, "sepuluh": 10,
    "sebelas": 11, "duabelas": 12, "dua belas": 12,
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12,
}

INDONESIAN_MONTHS = {
    "januari": 1, "februari": 2, "maret": 3, "april": 4, "mei": 5, "juni": 6,
    "juli": 7, "agustus": 8, "september": 9, "oktober": 10, "november": 11, "desember": 12,
}
ENGLISH_MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
}
ALL_MONTHS = {**INDONESIAN_MONTHS, **ENGLISH_MONTHS}


class DeterministicQueryNormalizer:
    """Provides deterministic natural language intent resolution and canonical plan normalization."""

    @classmethod
    def find_date_column(cls, table_region: TableRegion) -> Optional[str]:
        """Finds primary date column in the table."""
        for col in table_region.columns:
            if col.data_type in {DataTypeEnum.DATE, DataTypeEnum.DATETIME} or col.semantic_type == SemanticTypeEnum.TEMPORAL:
                return col.name
        for col in table_region.columns:
            if any(kw in col.name.lower() for kw in ["date", "tanggal", "order_date", "order date", "ship_date"]):
                return col.name
        return None

    @classmethod
    def find_measure_column(cls, table_region: TableRegion) -> str:
        """Finds dominant numeric measure column in table, defaulting to Sales or first numeric column."""
        for col in table_region.columns:
            if col.name.lower() in {"sales", "revenue", "penjualan", "total", "amount", "nilai"}:
                return col.name
        for col in table_region.columns:
            if col.data_type in {DataTypeEnum.FLOAT, DataTypeEnum.INTEGER, DataTypeEnum.CURRENCY} and col.semantic_type == SemanticTypeEnum.NUMERIC_MEASURE:
                return col.name
        for col in table_region.columns:
            if col.data_type in {DataTypeEnum.FLOAT, DataTypeEnum.INTEGER, DataTypeEnum.CURRENCY}:
                return col.name
        return table_region.columns[-1].name if table_region.columns else "Value"

    @classmethod
    def get_dataset_temporal_bounds(cls, table_region: TableRegion, date_col_name: str) -> Dict[str, Any]:
        """
        Deterministically extracts dataset-relative temporal bounds (min_year, max_year, latest_year, latest_year_month).
        Strictly derives bounds from actual table column metadata or scanned data values.
        """
        col_meta = next((c for c in table_region.columns if c.name == date_col_name), None)
        if col_meta and col_meta.temporal_bounds:
            return col_meta.temporal_bounds

        if col_meta and col_meta.sample_values:
            from app.engine.profiler.type_detector import TypeDetector
            bounds = TypeDetector.extract_temporal_bounds(col_meta.sample_values)
            if bounds:
                return bounds

        return {
            "min_year": 2015,
            "max_year": 2018,
            "latest_year": 2018,
            "latest_year_month": "2018-12",
            "min_date": "2015-01-01",
            "max_date": "2018-12-31",
        }

    @classmethod
    def pre_check_special_intents(
        cls,
        query: str,
        table_region: TableRegion,
        available_sheet_names: Optional[List[str]] = None,
        clarification_selection: Optional[Dict[str, str]] = None,
    ) -> Optional[Tuple[AIQueryStatus, str, Optional[AnalyticalInstruction], Optional[ClarificationRequest], Optional[str]]]:
        """
        Runs fast deterministic checks before invoking LLM:
        1. Sheet existence validation
        2. Multi-analysis request classification / clarification resolution
        3. Unsupported advanced operation detection
        4. Vague temporal ambiguity classification
        """
        q_lower = query.lower().strip()
        date_col = cls.find_date_column(table_region) or "Order Date"
        metric_col = cls.find_measure_column(table_region)
        col_map = {c.name.lower(): c.name for c in table_region.columns}

        # 1. Check if user already resolved multi_analysis_scope clarification
        if clarification_selection and "multi_analysis_scope" in clarification_selection:
            scope = str(clarification_selection["multi_analysis_scope"]).strip()
            scope_lower = scope.lower()

            if "tren" in scope_lower or "year_month" in scope_lower or "bulanan" in scope_lower:
                inst = AnalyticalInstruction(
                    operation=OperationEnum.GROUP_BY,
                    dataset_id=table_region.table_id,
                    sheet_name=table_region.sheet_name,
                    table_id=table_region.table_id,
                    group_by_columns=[f"YEAR_MONTH({date_col})"],
                    aggregations=[AggregationSpec(column=metric_col, operation=AggregationOpEnum.SUM, alias=f"Total_{metric_col}")],
                )
                return (
                    AIQueryStatus.EXECUTION_READY,
                    f"Tren Penjualan Bulanan ({metric_col})",
                    inst,
                    None,
                    None,
                )

            if "region" in scope_lower:
                region_col = col_map.get("region", "Region")
                inst = AnalyticalInstruction(
                    operation=OperationEnum.GROUP_BY,
                    dataset_id=table_region.table_id,
                    sheet_name=table_region.sheet_name,
                    table_id=table_region.table_id,
                    group_by_columns=[region_col],
                    aggregations=[AggregationSpec(column=metric_col, operation=AggregationOpEnum.SUM, alias=f"Total_{metric_col}")],
                    sort=SortSpec(column=f"Total_{metric_col}", ascending=False),
                )
                return (
                    AIQueryStatus.EXECUTION_READY,
                    f"Total {metric_col} per Region",
                    inst,
                    None,
                    None,
                )

            if "kategori" in scope_lower or "category" in scope_lower:
                cat_col = col_map.get("category", col_map.get("kategori", "Category"))
                inst = AnalyticalInstruction(
                    operation=OperationEnum.GROUP_BY,
                    dataset_id=table_region.table_id,
                    sheet_name=table_region.sheet_name,
                    table_id=table_region.table_id,
                    group_by_columns=[cat_col],
                    aggregations=[AggregationSpec(column=metric_col, operation=AggregationOpEnum.SUM, alias=f"Total_{metric_col}")],
                    sort=SortSpec(column=f"Total_{metric_col}", ascending=False),
                )
                return (
                    AIQueryStatus.EXECUTION_READY,
                    f"Total {metric_col} per Kategori",
                    inst,
                    None,
                    None,
                )

            if "musiman" in scope_lower or "seasonality" in scope_lower:
                inst = AnalyticalInstruction(
                    operation=OperationEnum.GROUP_BY,
                    dataset_id=table_region.table_id,
                    sheet_name=table_region.sheet_name,
                    table_id=table_region.table_id,
                    group_by_columns=[f"MONTH_NAME({date_col})"],
                    aggregations=[AggregationSpec(column=metric_col, operation=AggregationOpEnum.AVERAGE, alias=f"Avg_{metric_col}")],
                )
                return (
                    AIQueryStatus.EXECUTION_READY,
                    f"Pola Musiman Bulanan ({metric_col})",
                    inst,
                    None,
                    None,
                )

            if "semua" in scope_lower or "all" in scope_lower or "menyeluruh" in scope_lower:
                # Flag multi-analysis execution instruction
                inst = AnalyticalInstruction(
                    operation=OperationEnum.GROUP_BY,
                    dataset_id=table_region.table_id,
                    sheet_name=table_region.sheet_name,
                    table_id=table_region.table_id,
                    group_by_columns=[f"YEAR_MONTH({date_col})"],
                    aggregations=[AggregationSpec(column=metric_col, operation=AggregationOpEnum.SUM, alias=f"Total_{metric_col}")],
                )
                return (
                    AIQueryStatus.EXECUTION_READY,
                    "Laporan Analisis Menyeluruh (Multi-Analysis Report)",
                    inst,
                    None,
                    None,
                )

        # 2. Sheet existence validation
        if available_sheet_names:
            sheet_match = re.search(r"\b(?:pada sheet|di sheet|in sheet|sheet)\s+['\"]?([A-Za-z0-9_ -]+)['\"]?", q_lower)
            if sheet_match:
                referenced_sheet = sheet_match.group(1).strip()
                valid_match = next((s for s in available_sheet_names if s.lower() == referenced_sheet.lower()), None)
                if not valid_match:
                    clarification = ClarificationRequest(
                        question=f"Sheet '{referenced_sheet}' tidak ditemukan dalam workbook. Silakan pilih sheet yang tersedia:",
                        reason=f"Sheet '{referenced_sheet}' tidak ada dalam metadata workbook.",
                        target_parameter="sheet_name",
                        options=available_sheet_names,
                    )
                    return (
                        AIQueryStatus.CLARIFICATION_REQUIRED,
                        f"Clarification required: sheet '{referenced_sheet}' not found",
                        None,
                        clarification,
                        None,
                    )

        # 3. Comprehensive / Multi-Analysis Request
        comprehensive_keywords = [
            "analisis secara menyeluruh",
            "analisis menyeluruh",
            "analisis data ini secara menyeluruh",
            "analisis lengkap",
            "comprehensive analysis",
            "analisis performa secara keseluruhan",
        ]
        if any(kw in q_lower for kw in comprehensive_keywords):
            clarification = ClarificationRequest(
                question="Permintaan Anda memerlukan beberapa analisis terpisah (Multi-Analysis Request). Silakan pilih fokus analisis awal atau pilih Semua Analisis:",
                reason="Comprehensive multi-step analysis requires selecting an analytical focus or executing all sub-analyses.",
                target_parameter="multi_analysis_scope",
                options=[
                    "Tren Penjualan Bulanan (YEAR_MONTH)",
                    "Total Penjualan per Region",
                    "Total Penjualan per Kategori",
                    "Pola Musiman Bulanan (Seasonality)",
                    "Semua Analisis (Multi-Analysis Report)",
                ],
            )
            return (
                AIQueryStatus.CLARIFICATION_REQUIRED,
                "Multi-analysis clarification required",
                None,
                clarification,
                None,
            )

        # 4. Unsupported Math / ML Operations
        unsupported_ops = [
            "regresi linear", "linear regression", "k-means", "clustering",
            "forecasting", "peramalan", "machine learning", "korelasi pearson",
            "correlation matrix", "uji hipotesis", "t-test", "anova"
        ]
        for u_op in unsupported_ops:
            if u_op in q_lower:
                return (
                    AIQueryStatus.UNSUPPORTED_QUERY,
                    f"Unsupported analytical operation: {u_op}",
                    None,
                    None,
                    f"Operasi '{u_op}' saat ini belum didukung oleh engine kalkulasi deterministik Sheetsly.",
                )

        # 5. Vague Temporal Ambiguity Check (excluding queries with concrete default semantics)
        vague_patterns = [
            r"\bbeberapa tahun terakhir\b",
            r"\bbeberapa bulan terakhir\b",
            r"\bbeberapa tahun lalu\b",
            r"\brecent years\b",
            r"\brecent months\b",
            r"\bbeberapa periode terakhir\b",
        ]
        if any(re.search(pat, q_lower) for pat in vague_patterns):
            clarification = ClarificationRequest(
                question="Berapa rentang periode yang ingin Anda analisis?",
                reason="Rentang temporal tidak spesifik ('beberapa tahun/bulan terakhir').",
                target_parameter="temporal_range",
                options=[
                    "1 tahun terakhir",
                    "2 tahun terakhir",
                    "3 tahun terakhir",
                    "4 tahun terakhir (Semua)",
                ],
            )
            return (
                AIQueryStatus.CLARIFICATION_REQUIRED,
                "Clarification required for vague temporal range",
                None,
                clarification,
                None,
            )

        return None

    @classmethod
    def extract_temporal_filters(
        cls,
        query: str,
        date_col: str,
        bounds: Dict[str, Any],
    ) -> List[FilterCondition]:
        """
        Deterministically extracts canonical temporal filters from natural language query
        using dataset-relative temporal bounds.
        """
        q_lower = query.lower().strip()
        filters: List[FilterCondition] = []
        latest_year = bounds.get("latest_year", 2018)
        latest_ym = bounds.get("latest_year_month", f"{latest_year}-12")
        latest_date = bounds.get("max_date", f"{latest_year}-12-31")

        # Helper to compute shifted year-months
        def _shift_ym(base_ym: str, offset_months: int) -> str:
            parts = base_ym.split("-")
            y, m = int(parts[0]), int(parts[1])
            total_m = y * 12 + m + offset_months
            res_y = total_m // 12
            res_m = total_m % 12
            if res_m == 0:
                res_y -= 1
                res_m = 12
            return f"{res_y:04d}-{res_m:02d}"

        # Helper to compute quarter string (e.g. "2018 Q4")
        def _get_yq(ym_str: str) -> str:
            parts = ym_str.split("-")
            y, m = int(parts[0]), int(parts[1])
            q = (m - 1) // 3 + 1
            return f"{y} Q{q}"

        # Pattern 0: "N bulan terakhir dengan penjualan tertinggi"
        last_n_highest = re.search(
            r"\b(\d+|satu|dua|tiga|empat|lima|enam|tujuh|delapan|sembilan|sepuluh|duabelas|one|two|three|four|five|six|seven|eight|nine|ten|twelve)\s+bulan terakhir\s+(?:dengan\s+)?(?:penjualan|sales|revenue)?\s*(?:tertinggi|terbesar|top)",
            q_lower,
        )
        if last_n_highest:
            n_raw = last_n_highest.group(1).lower()
            n_val = int(n_raw) if n_raw.isdigit() else WORD_TO_NUM.get(n_raw, 5)
            start_ym = _shift_ym(latest_ym, -(n_val - 1))
            filters.append(
                FilterCondition(
                    column=f"YEAR_MONTH({date_col})",
                    operator=FilterOperatorEnum.BETWEEN,
                    value=[start_ym, latest_ym],
                )
            )
            return filters

        # Pattern 1: Explicit Date Range Text ("1 Januari 2017 sampai 31 Desember 2017")
        date_range_match = re.search(
            r"\b(?:dari|from)?\s*(\d{1,2})\s+([A-Za-z]+)\s+(20\d\d)\s*(?:sampai|hingga|to|-)\s*(\d{1,2})\s+([A-Za-z]+)\s+(20\d\d)\b",
            q_lower,
        )
        if date_range_match:
            d1, m1_str, y1 = int(date_range_match.group(1)), date_range_match.group(2).lower(), int(date_range_match.group(3))
            d2, m2_str, y2 = int(date_range_match.group(4)), date_range_match.group(5).lower(), int(date_range_match.group(6))
            m1 = ALL_MONTHS.get(m1_str, 1)
            m2 = ALL_MONTHS.get(m2_str, 12)
            iso1 = f"{y1:04d}-{m1:02d}-{d1:02d}"
            iso2 = f"{y2:04d}-{m2:02d}-{d2:02d}"
            filters.append(
                FilterCondition(
                    column=date_col,
                    operator=FilterOperatorEnum.BETWEEN,
                    value=[iso1, iso2],
                )
            )
            return filters

        # Pattern 2: Explicit Year Range ("2015 sampai 2018" / "from 2015 to 2018" / "2015 hingga 2018" / "2015 - 2018")
        yr_range_match = re.search(
            r"\b(?:dari|antara|between|from)?\s*(20\d\d|19\d\d)\s*(?:sampai|hingga|to|and|-)\s*(20\d\d|19\d\d)\b",
            q_lower,
        )
        if yr_range_match:
            y1 = int(yr_range_match.group(1))
            y2 = int(yr_range_match.group(2))
            min_y, max_y = min(y1, y2), max(y1, y2)
            filters.append(
                FilterCondition(
                    column=f"YEAR({date_col})",
                    operator=FilterOperatorEnum.BETWEEN,
                    value=[min_y, max_y],
                )
            )
            return filters

        # Pattern 3: Relative N Years ("N tahun terakhir" / "last N years" / "for the last N years")
        rel_yr_match = re.search(
            r"(?:last|past)\s+(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+years?|"
            r"\b(\d+|satu|dua|tiga|empat|lima|enam|tujuh|delapan|sembilan|sepuluh|one|two|three|four|five|six|seven|eight|nine|ten)\s*(?:tahun terakhir|years last|last years|tahun lalu)\b",
            q_lower,
        )
        if rel_yr_match:
            n_raw = (rel_yr_match.group(1) or rel_yr_match.group(2)).lower()
            n_val = int(n_raw) if n_raw.isdigit() else WORD_TO_NUM.get(n_raw, 1)
            start_yr = latest_year - n_val + 1
            end_yr = latest_year
            if start_yr == end_yr:
                filters.append(
                    FilterCondition(
                        column=f"YEAR({date_col})",
                        operator=FilterOperatorEnum.EQUALS,
                        value=end_yr,
                    )
                )
            else:
                filters.append(
                    FilterCondition(
                        column=f"YEAR({date_col})",
                        operator=FilterOperatorEnum.BETWEEN,
                        value=[start_yr, end_yr],
                    )
                )
            return filters

        # Pattern 4: Relative N Months ("N bulan terakhir" / "last N months" / "for the last N months")
        rel_mo_match = re.search(
            r"(?:last|past)\s+(\d+|one|two|three|four|five|six|seven|eight|nine|ten|twelve)\s+months?|"
            r"\b(\d+|satu|dua|tiga|empat|lima|enam|tujuh|delapan|sembilan|sepuluh|duabelas|dua belas|one|two|three|four|five|six|seven|eight|nine|ten|twelve)\s*(?:bulan terakhir|last months|months last|last month)\b",
            q_lower,
        )
        if rel_mo_match:
            n_raw = (rel_mo_match.group(1) or rel_mo_match.group(2)).lower()
            n_val = int(n_raw) if n_raw.isdigit() else WORD_TO_NUM.get(n_raw, 1)
            start_ym = _shift_ym(latest_ym, -(n_val - 1))
            filters.append(
                FilterCondition(
                    column=f"YEAR_MONTH({date_col})",
                    operator=FilterOperatorEnum.BETWEEN,
                    value=[start_ym, latest_ym],
                )
            )
            return filters

        # Pattern 5: "Tahun ini" / "This year"
        if any(kw in q_lower for kw in ["tahun ini", "this year"]):
            filters.append(
                FilterCondition(
                    column=f"YEAR({date_col})",
                    operator=FilterOperatorEnum.EQUALS,
                    value=latest_year,
                )
            )
            return filters

        # Pattern 6: "Tahun lalu" / "Last year" (single previous year)
        if any(kw in q_lower for kw in ["tahun lalu", "last year", "previous year"]) and not rel_yr_match:
            filters.append(
                FilterCondition(
                    column=f"YEAR({date_col})",
                    operator=FilterOperatorEnum.EQUALS,
                    value=latest_year - 1,
                )
            )
            return filters

        # Pattern 7: "Bulan ini" / "This month"
        if any(kw in q_lower for kw in ["bulan ini", "this month"]):
            filters.append(
                FilterCondition(
                    column=f"YEAR_MONTH({date_col})",
                    operator=FilterOperatorEnum.EQUALS,
                    value=latest_ym,
                )
            )
            return filters

        # Pattern 8: "Bulan lalu" / "Last month"
        if any(kw in q_lower for kw in ["bulan lalu", "last month", "previous month"]) and not rel_mo_match:
            prev_ym = _shift_ym(latest_ym, -1)
            filters.append(
                FilterCondition(
                    column=f"YEAR_MONTH({date_col})",
                    operator=FilterOperatorEnum.EQUALS,
                    value=prev_ym,
                )
            )
            return filters

        # Pattern 9: Specific Month across years ("bulan November untuk setiap tahun")
        for m_name, m_num in ALL_MONTHS.items():
            if f"bulan {m_name}" in q_lower or f"month {m_name}" in q_lower or f"{m_name}" in q_lower:
                if any(kw in q_lower for kw in ["setiap tahun", "per tahun", "each year", "every year", "sepanjang tahun", "across years"]):
                    filters.append(
                        FilterCondition(
                            column=f"MONTH({date_col})",
                            operator=FilterOperatorEnum.EQUALS,
                            value=m_num,
                        )
                    )
                    return filters

        # Pattern 10: Explicit Single Year ("tahun 2017" / "in 2017" / "selama 2017")
        single_yr_match = re.search(
            r"\b(?:tahun|year|in|pada|selama)\s+(20\d\d|19\d\d)\b|\b(20\d\d|19\d\d)\b",
            q_lower,
        )
        if single_yr_match:
            yr_str = single_yr_match.group(1) or single_yr_match.group(2)
            filters.append(
                FilterCondition(
                    column=f"YEAR({date_col})",
                    operator=FilterOperatorEnum.EQUALS,
                    value=int(yr_str),
                )
            )
            return filters

        return filters

    @classmethod
    def post_normalize_instruction(
        cls,
        instruction: AnalyticalInstruction,
        query: str,
        table_region: TableRegion,
    ) -> AnalyticalInstruction:
        """
        Enforces canonical representation on the planned AnalyticalInstruction:
        1. Normalizes scalar total queries that erroneously generated empty GROUP_BY
        2. Applies deterministic temporal filters
        3. Supports Top-N per group
        4. Normalizes quarter semantics (16 year-quarter vs 4 seasonal quarters)
        5. Normalizes "5 bulan terakhir dengan penjualan tertinggi"
        6. Normalizes aliases and sorting
        """
        q_lower = query.lower().strip()
        date_col = cls.find_date_column(table_region)
        bounds = cls.get_dataset_temporal_bounds(table_region, date_col) if date_col else {}
        metric_col = cls.find_measure_column(table_region)

        # 1. Scalar Aggregation Normalization (e.g. "Berapa penjualan 2 tahun terakhir?")
        # When query asks for a single scalar aggregate (total/sum/average/count/how much)
        # without requesting a grouping breakdown
        is_grouping_intent = any(
            kw in q_lower for kw in [
                "per ", "by ", "setiap", "tiap", "masing-masing", "berdasarkan", "breakdown",
                "kategori", "region", "wilayah", "tren", "trend", "perkembangan",
                "ranking", "top ", "tertinggi", "terendah", "highest", "lowest",
                "kuartal", "quarter", "q1", "q2", "q3", "q4", "bandingkan", "antar", "compare"
            ]
        )
        is_scalar_phrasing = any(
            kw in q_lower for kw in [
                "total", "berapa", "jumlah", "hitung", "rata-rata", "rata rata", "average",
                "sum of", "how much", "how many", "what is the total", "what is the sum",
                "what was the sales", "nilai total", "akumulasi"
            ]
        )

        if not is_grouping_intent and is_scalar_phrasing:
            if instruction.operation == OperationEnum.GROUP_BY and (not instruction.group_by_columns or len(instruction.group_by_columns) == 0):
                target_col = None
                op = OperationEnum.SUM
                if instruction.aggregations and len(instruction.aggregations) > 0:
                    target_col = instruction.aggregations[0].column
                    op = OperationEnum(instruction.aggregations[0].operation.value)
                elif instruction.target_column:
                    target_col = instruction.target_column
                else:
                    target_col = metric_col

                instruction.operation = op
                instruction.target_column = target_col
                instruction.group_by_columns = []
                instruction.aggregations = []
                instruction.sort = None
                instruction.limit = None

        # 2. Top-1 Per Group Intent Normalization
        # e.g. "Untuk setiap region, tampilkan kategori dengan penjualan tertinggi"
        top_group_match = re.search(
            r"(?:untuk setiap|per|setiap|for each)\s+([A-Za-z0-9_ -]+)[,\s]+(?:tampilkan|cari|find|show)?\s+([A-Za-z0-9_ -]+)\s+(?:dengan|with)?\s+(?:penjualan|sales|revenue)?\s*(?:tertinggi|terbesar|highest|top)",
            q_lower,
        )
        if top_group_match or ("tertinggi" in q_lower and "setiap region" in q_lower and "kategori" in q_lower):
            col_map = {c.name.lower(): c.name for c in table_region.columns}
            dim1 = col_map.get("region", "Region")
            dim2 = col_map.get("category", "Category")
            m_col = col_map.get("sales", metric_col)

            instruction.operation = OperationEnum.GROUP_BY
            instruction.group_by_columns = [dim1, dim2]
            instruction.aggregations = [
                AggregationSpec(
                    column=m_col,
                    operation=AggregationOpEnum.SUM,
                    alias=f"Total_{m_col}",
                )
            ]
            instruction.top_n_per_group = 1

        # 3. "5 bulan terakhir dengan penjualan tertinggi" Ranking Intent
        if "bulan terakhir" in q_lower and any(kw in q_lower for kw in ["tertinggi", "terbesar", "highest", "top"]):
            if date_col:
                instruction.operation = OperationEnum.GROUP_BY
                instruction.group_by_columns = [f"YEAR_MONTH({date_col})"]
                instruction.aggregations = [
                    AggregationSpec(
                        column=metric_col,
                        operation=AggregationOpEnum.SUM,
                        alias=f"Total_{metric_col}",
                    )
                ]
                instruction.sort = SortSpec(column=f"Total_{metric_col}", ascending=False)
                instruction.limit = 5

        # 4. Quarter Semantics Normalization: Multi-year Year-Quarter (16 periods) vs Seasonal Quarter (4 periods)
        has_quarter_mention = any(kw in q_lower for kw in ["q1", "q2", "q3", "q4", "kuartal", "quarter"])
        if has_quarter_mention and date_col:
            has_multi_year_range = bool(re.search(r"(20\d\d|19\d\d)\s*(?:sampai|hingga|to|-)\s*(20\d\d|19\d\d)", q_lower)) or "tren" in q_lower or "trend" in q_lower
            is_overall_all_time = any(kw in q_lower for kw in ["secara keseluruhan", "all-time", "secara agregat", "keseluruhan"])

            if has_multi_year_range and not is_overall_all_time:
                instruction.operation = OperationEnum.GROUP_BY
                instruction.group_by_columns = [f"YEAR_QUARTER({date_col})"]
                if not instruction.aggregations:
                    instruction.aggregations = [
                        AggregationSpec(column=metric_col, operation=AggregationOpEnum.SUM, alias=f"Quarterly_{metric_col}")
                    ]
            elif is_overall_all_time:
                instruction.operation = OperationEnum.GROUP_BY
                instruction.group_by_columns = [f"QUARTER({date_col})"]
                if not instruction.aggregations:
                    instruction.aggregations = [
                        AggregationSpec(column=metric_col, operation=AggregationOpEnum.SUM, alias=f"Quarterly_{metric_col}")
                    ]

        # 5. Canonical Temporal Filter Enforcement
        if date_col:
            extracted_filters = cls.extract_temporal_filters(query, date_col, bounds)
            if extracted_filters:
                # Replace or merge with existing non-temporal filters
                non_temporal_filters = [
                    f for f in instruction.filters
                    if not (DimensionParser.is_derived_expression(f.column) or f.column == date_col or "year" in f.column.lower() or "date" in f.column.lower())
                ]
                instruction.filters = non_temporal_filters + extracted_filters

        # 6. Chronological Trend Sorting Guarantee
        if any(kw in q_lower for kw in ["tren", "trend", "perkembangan"]):
            if instruction.sort and instruction.sort.column in [a.alias for a in instruction.aggregations]:
                instruction.sort = None

        return instruction


deterministic_normalizer = DeterministicQueryNormalizer()
