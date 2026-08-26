"""Generalized Ambiguity Framework across 11 distinct spreadsheet domains."""

import re
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field

from app.engine.ai.models import ClarificationRequest
from app.engine.profiler.workbook_index import (
    ColumnIndexEntry,
    SheetIndexEntry,
    TableIndexEntry,
    WorkbookMetadataIndex,
)
from app.models.schemas import DataTypeEnum, SemanticTypeEnum


class AmbiguityDomainEnum(str, Enum):
    """Authoritative 11 ambiguity domains."""

    COLUMN = "COLUMN"
    SHEET = "SHEET"
    TABLE = "TABLE"
    RANGE = "RANGE"
    DATE_TEMPORAL = "DATE_TEMPORAL"
    METRIC = "METRIC"
    AGGREGATION = "AGGREGATION"
    COMPARISON = "COMPARISON"
    FORMATTING = "FORMATTING"
    MUTATION_DESTINATION = "MUTATION_DESTINATION"
    CHART = "CHART"


class CandidateResolutionResult(BaseModel):
    """Result of ambiguity evaluation within a specific domain."""

    domain: AmbiguityDomainEnum
    is_ambiguous: bool = False
    is_unsupported: bool = False
    resolved_candidate: Optional[Any] = None
    candidates: List[Any] = Field(default_factory=list)
    confidence: float = 1.0
    clarification_needed: bool = False
    clarification_request: Optional[ClarificationRequest] = None
    reason: str = ""


class GeneralizedAmbiguityResolver:
    """Evaluates and resolves candidate ambiguity across all 11 domains deterministically."""

    SEMANTIC_ALIASES: Dict[str, List[str]] = {
        "penjualan": ["sales", "revenue", "omset", "omzet"],
        "omset": ["sales", "revenue", "penjualan"],
        "omzet": ["sales", "revenue", "penjualan"],
        "revenue": ["sales", "penjualan", "omset"],
        "sales": ["penjualan", "revenue", "omset"],
        "keuntungan": ["profit", "laba", "untung"],
        "laba": ["profit", "keuntungan", "untung"],
        "profit": ["laba", "keuntungan", "untung"],
        "diskon": ["discount", "potongan"],
        "discount": ["diskon", "potongan"],
        "biaya": ["cost", "expense"],
        "cost": ["biaya", "expense"],
        "kuantitas": ["quantity", "qty", "jumlah"],
        "quantity": ["kuantitas", "qty", "jumlah"],
        "pelanggan": ["customer", "client"],
        "customer": ["pelanggan", "client"],
        "produk": ["product", "item"],
        "product": ["produk", "item"],
        "pesanan": ["order"],
        "order": ["pesanan"],
        "tanggal": ["date", "time"],
        "date": ["tanggal", "time"],
    }

    # ------------------------------------------------------------------------
    # 1. COLUMN AMBIGUITY
    # ------------------------------------------------------------------------
    @classmethod
    def resolve_column_ambiguity(
        cls,
        query: str,
        columns: List[ColumnIndexEntry],
        target_role: Optional[SemanticTypeEnum] = None,
    ) -> CandidateResolutionResult:
        """
        Resolves target column against table columns.
        If multiple columns match (e.g. 'Sales' vs 'Net Sales') -> Clarification.
        """
        q_norm = query.strip().lower()
        
        # Filter by role if specified
        candidate_cols = [c for c in columns if target_role is None or c.semantic_type == target_role]
        if not candidate_cols:
            candidate_cols = columns

        exact_matches = [c for c in candidate_cols if c.normalized_name in q_norm or q_norm in c.normalized_name]
        
        # Substring keyword matches & semantic alias matches
        tokens = [t for t in re.split(r"\W+", q_norm) if len(t) > 2]
        expanded_tokens = set(tokens)
        for t in tokens:
            if t in cls.SEMANTIC_ALIASES:
                expanded_tokens.update(cls.SEMANTIC_ALIASES[t])

        token_matches = []
        for c in candidate_cols:
            c_tokens = set(re.split(r"\W+", c.normalized_name))
            if any(t in c_tokens for t in expanded_tokens):
                token_matches.append(c)

        pool = exact_matches if exact_matches else token_matches

        # Deduplicate
        seen_names = set()
        dedup_pool = []
        for c in pool:
            if c.name not in seen_names:
                seen_names.add(c.name)
                dedup_pool.append(c)

        if len(dedup_pool) == 1:
            return CandidateResolutionResult(
                domain=AmbiguityDomainEnum.COLUMN,
                is_ambiguous=False,
                resolved_candidate=dedup_pool[0],
                candidates=[dedup_pool[0].name],
                confidence=1.0,
                reason=f"Unambiguous column match: '{dedup_pool[0].name}'",
            )
        elif len(dedup_pool) > 1:
            req = ClarificationRequest(
                question=f"Terdapat beberapa kolom yang cocok: {', '.join([c.name for c in dedup_pool])}. Kolom mana yang ingin digunakan?",
                reason="Multiple candidate columns matched the query equally.",
                target_parameter="target_column",
                options=[c.name for c in dedup_pool],
            )
            return CandidateResolutionResult(
                domain=AmbiguityDomainEnum.COLUMN,
                is_ambiguous=True,
                candidates=[c.name for c in dedup_pool],
                confidence=0.5,
                clarification_needed=True,
                clarification_request=req,
                reason="Multiple equally plausible columns matched.",
            )
        else:
            return CandidateResolutionResult(
                domain=AmbiguityDomainEnum.COLUMN,
                is_unsupported=True,
                confidence=0.0,
                reason=f"Tidak ditemukan kolom yang cocok untuk query '{query}'.",
            )

    # ------------------------------------------------------------------------
    # 2. SHEET AMBIGUITY
    # ------------------------------------------------------------------------
    @classmethod
    def resolve_sheet_ambiguity(
        cls,
        query: str,
        index: WorkbookMetadataIndex,
        active_sheet: Optional[str] = None,
    ) -> CandidateResolutionResult:
        """Resolves target sheet. If multiple sheets match query tokens -> Clarification."""
        q_norm = query.strip().lower()
        q_tokens = set(re.split(r"\W+", q_norm))

        matched_sheets = []
        for s in index.sheet_names:
            s_tokens = set(re.split(r"\W+", s.lower()))
            if s.lower() in q_norm or (s_tokens.intersection(q_tokens) and len(s_tokens.intersection(q_tokens)) >= 1 and any(len(t) > 3 for t in s_tokens.intersection(q_tokens))):
                matched_sheets.append(s)

        if len(matched_sheets) == 1:
            return CandidateResolutionResult(
                domain=AmbiguityDomainEnum.SHEET,
                resolved_candidate=matched_sheets[0],
                candidates=matched_sheets,
                confidence=1.0,
            )
        elif len(matched_sheets) > 1:
            req = ClarificationRequest(
                question=f"Terdapat beberapa sheet yang cocok ({', '.join(matched_sheets)}). Sheet mana yang dimaksud?",
                reason="Query matches multiple sheet names in workbook.",
                target_parameter="sheet_name",
                options=matched_sheets,
            )
            return CandidateResolutionResult(
                domain=AmbiguityDomainEnum.SHEET,
                is_ambiguous=True,
                candidates=matched_sheets,
                clarification_needed=True,
                clarification_request=req,
            )
        else:
            cur = active_sheet or index.active_sheet_name
            return CandidateResolutionResult(
                domain=AmbiguityDomainEnum.SHEET,
                resolved_candidate=cur,
                candidates=[cur],
                confidence=0.9,
                reason=f"Defaulted to active sheet '{cur}'.",
            )

    # ------------------------------------------------------------------------
    # 3. TABLE AMBIGUITY
    # ------------------------------------------------------------------------
    @classmethod
    def resolve_table_ambiguity(
        cls,
        query: str,
        sheet_entry: SheetIndexEntry,
    ) -> CandidateResolutionResult:
        """Resolves target table in sheet."""
        if not sheet_entry.tables:
            return CandidateResolutionResult(
                domain=AmbiguityDomainEnum.TABLE,
                is_unsupported=True,
                reason=f"Sheet '{sheet_entry.name}' tidak memiliki tabel terstruktur.",
            )
        if len(sheet_entry.tables) == 1:
            return CandidateResolutionResult(
                domain=AmbiguityDomainEnum.TABLE,
                resolved_candidate=sheet_entry.tables[0],
                candidates=[sheet_entry.tables[0].name],
                confidence=1.0,
            )

        q_norm = query.strip().lower()
        matched_tables = [t for t in sheet_entry.tables if t.name.lower() in q_norm or t.table_id.lower() in q_norm]
        if len(matched_tables) == 1:
            return CandidateResolutionResult(
                domain=AmbiguityDomainEnum.TABLE,
                resolved_candidate=matched_tables[0],
                candidates=[matched_tables[0].name],
                confidence=1.0,
            )

        req = ClarificationRequest(
            question=f"Terdapat {len(sheet_entry.tables)} tabel di sheet '{sheet_entry.name}'. Tabel mana yang ingin dianalisis?",
            reason="Multiple structured tables exist in sheet with no unambiguous selection.",
            target_parameter="table_id",
            options=[t.name for t in sheet_entry.tables],
        )
        return CandidateResolutionResult(
            domain=AmbiguityDomainEnum.TABLE,
            is_ambiguous=True,
            candidates=[t.name for t in sheet_entry.tables],
            clarification_needed=True,
            clarification_request=req,
        )

    # ------------------------------------------------------------------------
    # 4. RANGE AMBIGUITY
    # ------------------------------------------------------------------------
    @classmethod
    def resolve_range_ambiguity(
        cls,
        query: str,
        default_data_range: Optional[str] = None,
    ) -> CandidateResolutionResult:
        """Resolves target cell range."""
        range_match = re.search(r"\b[A-Z]{1,3}\d+:[A-Z]{1,3}\d+\b", query.upper())
        if range_match:
            return CandidateResolutionResult(
                domain=AmbiguityDomainEnum.RANGE,
                resolved_candidate=range_match.group(0),
                candidates=[range_match.group(0)],
                confidence=1.0,
            )
        if default_data_range:
            return CandidateResolutionResult(
                domain=AmbiguityDomainEnum.RANGE,
                resolved_candidate=default_data_range,
                candidates=[default_data_range],
                confidence=0.9,
                reason=f"Resolved to detected table data range {default_data_range}.",
            )
        req = ClarificationRequest(
            question="Rentang sel data tidak spesifik. Mohon sebutkan rentang sel (misal: A1:D50).",
            reason="Ambiguous cell range referenced without active selection.",
            target_parameter="range_address",
            options=[],
        )
        return CandidateResolutionResult(
            domain=AmbiguityDomainEnum.RANGE,
            is_ambiguous=True,
            clarification_needed=True,
            clarification_request=req,
        )

    # ------------------------------------------------------------------------
    # 5. DATE / TEMPORAL AMBIGUITY
    # ------------------------------------------------------------------------
    @classmethod
    def resolve_temporal_ambiguity(
        cls,
        query: str,
        date_columns: List[ColumnIndexEntry],
    ) -> CandidateResolutionResult:
        """Resolves temporal date column against temporal intent."""
        if not date_columns:
            return CandidateResolutionResult(
                domain=AmbiguityDomainEnum.DATE_TEMPORAL,
                is_unsupported=True,
                reason="Tidak ada kolom tanggal/waktu pada dataset ini.",
            )
        if len(date_columns) == 1:
            return CandidateResolutionResult(
                domain=AmbiguityDomainEnum.DATE_TEMPORAL,
                resolved_candidate=date_columns[0],
                candidates=[date_columns[0].name],
                confidence=1.0,
            )

        q_norm = query.strip().lower()
        matched = [c for c in date_columns if c.normalized_name in q_norm]
        if len(matched) == 1:
            return CandidateResolutionResult(
                domain=AmbiguityDomainEnum.DATE_TEMPORAL,
                resolved_candidate=matched[0],
                candidates=[matched[0].name],
                confidence=1.0,
            )

        req = ClarificationRequest(
            question=f"Terdapat beberapa kolom tanggal ({', '.join([c.name for c in date_columns])}). Tanggal mana yang ingin dijadikan acuan?",
            reason="Multiple temporal columns available in table.",
            target_parameter="target_date_column",
            options=[c.name for c in date_columns],
        )
        return CandidateResolutionResult(
            domain=AmbiguityDomainEnum.DATE_TEMPORAL,
            is_ambiguous=True,
            candidates=[c.name for c in date_columns],
            clarification_needed=True,
            clarification_request=req,
        )

    # ------------------------------------------------------------------------
    # 6. METRIC AMBIGUITY
    # ------------------------------------------------------------------------
    @classmethod
    def resolve_metric_ambiguity(
        cls,
        query: str,
        measure_columns: List[ColumnIndexEntry],
    ) -> CandidateResolutionResult:
        """Resolves target numeric measure column."""
        if not measure_columns:
            return CandidateResolutionResult(
                domain=AmbiguityDomainEnum.METRIC,
                is_unsupported=True,
                reason="Tidak ditemukan kolom angka/metrik numerik.",
            )
        q_norm = query.strip().lower()
        matched = [c for c in measure_columns if c.normalized_name in q_norm]
        if len(matched) == 1:
            return CandidateResolutionResult(
                domain=AmbiguityDomainEnum.METRIC,
                resolved_candidate=matched[0],
                candidates=[matched[0].name],
                confidence=1.0,
            )
        if len(measure_columns) == 1:
            return CandidateResolutionResult(
                domain=AmbiguityDomainEnum.METRIC,
                resolved_candidate=measure_columns[0],
                candidates=[measure_columns[0].name],
                confidence=0.9,
            )

        superlatives = ["terbaik", "top", "tertinggi", "terbesar", "terbanyak", "ranking"]
        if any(s in q_norm for s in superlatives) and not matched:
            req = ClarificationRequest(
                question=f"Ingin melihat peringkat berdasarkan metrik apa? ({', '.join([c.name for c in measure_columns])})",
                reason="Superlative ranking query requested without explicit measure.",
                target_parameter="target_measure_column",
                options=[c.name for c in measure_columns],
            )
            return CandidateResolutionResult(
                domain=AmbiguityDomainEnum.METRIC,
                is_ambiguous=True,
                candidates=[c.name for c in measure_columns],
                clarification_needed=True,
                clarification_request=req,
            )

        return CandidateResolutionResult(
            domain=AmbiguityDomainEnum.METRIC,
            resolved_candidate=measure_columns[0],
            candidates=[c.name for c in measure_columns],
            confidence=0.75,
            reason=f"Defaulted to primary measure '{measure_columns[0].name}'.",
        )

    # ------------------------------------------------------------------------
    # 7. AGGREGATION AMBIGUITY
    # ------------------------------------------------------------------------
    @classmethod
    def resolve_aggregation_ambiguity(
        cls,
        query: str,
    ) -> CandidateResolutionResult:
        """Distinguishes between SUM, AVERAGE, COUNT, MIN, MAX, MEDIAN."""
        q_norm = query.strip().lower()
        if any(w in q_norm for w in ["rata-rata", "average", "mean"]):
            return CandidateResolutionResult(domain=AmbiguityDomainEnum.AGGREGATION, resolved_candidate="AVERAGE", confidence=1.0)
        if any(w in q_norm for w in ["jumlah transaksi", "banyaknya", "count", "berapa kali", "berapa transaksi"]):
            return CandidateResolutionResult(domain=AmbiguityDomainEnum.AGGREGATION, resolved_candidate="COUNT_ROWS", confidence=1.0)
        if any(w in q_norm for w in ["minimum", "terkecil", "terendah", "paling sedikit"]):
            return CandidateResolutionResult(domain=AmbiguityDomainEnum.AGGREGATION, resolved_candidate="MIN", confidence=1.0)
        if any(w in q_norm for w in ["maximum", "terbesar", "tertinggi", "paling banyak"]):
            return CandidateResolutionResult(domain=AmbiguityDomainEnum.AGGREGATION, resolved_candidate="MAX", confidence=1.0)
        if any(w in q_norm for w in ["median", "nilai tengah"]):
            return CandidateResolutionResult(domain=AmbiguityDomainEnum.AGGREGATION, resolved_candidate="MEDIAN", confidence=1.0)
        if any(w in q_norm for w in ["total", "jumlah", "omset", "penjualan", "revenue", "sum"]):
            return CandidateResolutionResult(domain=AmbiguityDomainEnum.AGGREGATION, resolved_candidate="SUM", confidence=1.0)

        return CandidateResolutionResult(domain=AmbiguityDomainEnum.AGGREGATION, resolved_candidate="SUM", confidence=0.85)

    # ------------------------------------------------------------------------
    # 8. COMPARISON AMBIGUITY
    # ------------------------------------------------------------------------
    @classmethod
    def resolve_comparison_ambiguity(
        cls,
        query: str,
        has_baseline: bool,
        has_metric: bool,
    ) -> CandidateResolutionResult:
        """Validates comparison criteria."""
        q_norm = query.strip().lower()
        is_comp = any(w in q_norm for w in ["lebih baik", "lebih tinggi", "dibandingkan", "vs", "compare", "meningkat", "turun"])
        if not is_comp:
            return CandidateResolutionResult(domain=AmbiguityDomainEnum.COMPARISON, resolved_candidate="NONE", confidence=1.0)

        if not has_baseline:
            req = ClarificationRequest(
                question="Perbandingan memerlukan periode atau pembanding baseline (misal: vs bulan lalu, vs 2023).",
                reason="Comparison operation requested without baseline reference.",
                target_parameter="comparison_baseline",
                options=[],
            )
            return CandidateResolutionResult(
                domain=AmbiguityDomainEnum.COMPARISON,
                is_ambiguous=True,
                clarification_needed=True,
                clarification_request=req,
            )
        return CandidateResolutionResult(domain=AmbiguityDomainEnum.COMPARISON, resolved_candidate="VALID_COMPARISON", confidence=1.0)

    # ------------------------------------------------------------------------
    # 9. FORMATTING AMBIGUITY
    # ------------------------------------------------------------------------
    @classmethod
    def resolve_formatting_ambiguity(
        cls,
        query: str,
        target_specified: bool,
    ) -> CandidateResolutionResult:
        """Ensures formatting request specifies a valid target range or cell."""
        q_norm = query.strip().lower()
        is_fmt = any(w in q_norm for w in ["warnai", "tebalkan", "bold", "rapihkan", "highlight", "format"])
        if not is_fmt:
            return CandidateResolutionResult(domain=AmbiguityDomainEnum.FORMATTING, resolved_candidate="NONE")

        if not target_specified:
            req = ClarificationRequest(
                question="Mohon sebutkan sel atau rentang yang ingin diformat (misal: sel D102 atau range A1:E1).",
                reason="Formatting instruction does not specify target cell or range.",
                target_parameter="target_cell_range",
                options=[],
            )
            return CandidateResolutionResult(
                domain=AmbiguityDomainEnum.FORMATTING,
                is_ambiguous=True,
                clarification_needed=True,
                clarification_request=req,
            )
        return CandidateResolutionResult(domain=AmbiguityDomainEnum.FORMATTING, resolved_candidate="VALID_FORMATTING", confidence=1.0)

    # ------------------------------------------------------------------------
    # 10. MUTATION / DESTINATION AMBIGUITY
    # ------------------------------------------------------------------------
    @classmethod
    def resolve_mutation_destination_ambiguity(
        cls,
        query: str,
        table_entry: Optional[TableIndexEntry],
    ) -> CandidateResolutionResult:
        """Determines target placement for summary or total formulas."""
        if not table_entry:
            return CandidateResolutionResult(
                domain=AmbiguityDomainEnum.MUTATION_DESTINATION,
                is_unsupported=True,
                reason="Tabel target tidak ditemukan untuk penempatan formula.",
            )
        explicit_cell = re.search(r"\b[A-Z]{1,3}\d+\b", query.upper())
        if explicit_cell:
            return CandidateResolutionResult(
                domain=AmbiguityDomainEnum.MUTATION_DESTINATION,
                resolved_candidate=explicit_cell.group(0),
                confidence=1.0,
            )
        return CandidateResolutionResult(
            domain=AmbiguityDomainEnum.MUTATION_DESTINATION,
            resolved_candidate="SAFE_SUMMARY_ROW_BELOW_DATA",
            confidence=0.95,
            reason="Deterministic placement: Safe summary row immediately below table data range.",
        )

    # ------------------------------------------------------------------------
    # 11. CHART AMBIGUITY
    # ------------------------------------------------------------------------
    @classmethod
    def resolve_chart_ambiguity(
        cls,
        query: str,
        dimension_count: int,
        measure_count: int,
    ) -> CandidateResolutionResult:
        """Validates suitability of visualization request."""
        if measure_count == 0:
            return CandidateResolutionResult(
                domain=AmbiguityDomainEnum.CHART,
                is_unsupported=True,
                reason="Visualisasi chart memerlukan minimal 1 kolom ukuran numerik.",
            )
        if dimension_count == 0:
            return CandidateResolutionResult(
                domain=AmbiguityDomainEnum.CHART,
                is_unsupported=True,
                reason="Visualisasi chart memerlukan minimal 1 kolom dimensi kategorikal atau tanggal.",
            )
        return CandidateResolutionResult(
            domain=AmbiguityDomainEnum.CHART,
            resolved_candidate="VALID_CHART_CANDIDATE",
            confidence=1.0,
        )

    # ------------------------------------------------------------------------
    # 12. JOIN KEY AMBIGUITY
    # ------------------------------------------------------------------------
    @classmethod
    def resolve_join_key_ambiguity(
        cls,
        query: str,
        candidate_columns: List[ColumnIndexEntry],
    ) -> CandidateResolutionResult:
        """Evaluates ambiguity when connecting multi-sheet data with multiple candidate keys."""
        if not candidate_columns:
            return CandidateResolutionResult(
                domain=AmbiguityDomainEnum.COLUMN,
                is_unsupported=True,
                reason="Tidak ditemukan kolom kunci relasi antar-sheet.",
            )
        if len(candidate_columns) == 1:
            return CandidateResolutionResult(
                domain=AmbiguityDomainEnum.COLUMN,
                resolved_candidate=candidate_columns[0].name,
                confidence=1.0,
            )
        return CandidateResolutionResult(
            domain=AmbiguityDomainEnum.COLUMN,
            is_ambiguous=True,
            candidates=[c.name for c in candidate_columns],
            confidence=0.5,
            clarification_needed=True,
            clarification_request=ClarificationRequest(
                question=f"Terdapat beberapa kolom kunci relasi ({', '.join([c.name for c in candidate_columns])}). Kunci mana yang ingin Anda gunakan untuk menghubungkan tabel?",
                reason="Multiple candidate join keys detected.",
                target_parameter="join_key_column",
                options=[c.name for c in candidate_columns],
            ),
        )
