"""Comprehensive unit and matrix test suite for Phase 3:
Relationship Graph and Generalized Ambiguity Resolver across 11 domains.
"""

import pytest

from app.engine.analytics.ambiguity_resolver import (
    AmbiguityDomainEnum,
    GeneralizedAmbiguityResolver,
)
from app.engine.profiler.relationship_detector import (
    RelationshipDetector,
    RelationshipDirectionEnum,
    RelationshipStatusEnum,
)
from app.engine.profiler.workbook_index import (
    ColumnIndexEntry,
    SheetIndexEntry,
    TableIndexEntry,
    WorkbookMetadataIndex,
)
from app.models.schemas import DataTypeEnum, SemanticTypeEnum


def _make_col(name: str, dt: DataTypeEnum, sem: SemanticTypeEnum, uniq: int = 50, tot: int = 100, samples=None) -> ColumnIndexEntry:
    return ColumnIndexEntry(
        index=0,
        name=name,
        normalized_name=name.strip().lower().replace("_", " "),
        source_column_letter="A",
        data_type=dt,
        semantic_type=sem,
        type_confidence=1.0,
        total_count=tot,
        null_count=0,
        null_ratio=0.0,
        unique_count=uniq,
        cardinality_ratio=uniq / max(1, tot),
        sample_values=samples or ["CUST-001", "CUST-002", "CUST-003"],
        is_key_candidate=(uniq == tot or sem == SemanticTypeEnum.IDENTIFIER),
    )


# ============================================================================
# 1. RELATIONSHIP GRAPH TESTS
# ============================================================================

def test_relationship_detection_true_positive():
    """Verify true positive relationship detection between Orders and Customers on CustomerID."""
    orders_col = _make_col("CustomerID", DataTypeEnum.STRING, SemanticTypeEnum.IDENTIFIER, uniq=50, tot=500, samples=["C01", "C02", "C03"])
    cust_col = _make_col("CustomerID", DataTypeEnum.STRING, SemanticTypeEnum.IDENTIFIER, uniq=50, tot=50, samples=["C01", "C02", "C03"])

    tbl_orders = TableIndexEntry(table_id="tbl_orders", name="Orders Data", sheet_name="Orders", range_address="A1:E500", columns=[orders_col])
    tbl_cust = TableIndexEntry(table_id="tbl_cust", name="Customers Data", sheet_name="Customers", range_address="A1:C50", columns=[cust_col])

    sheet_orders = SheetIndexEntry(name="Orders", index=0, tables=[tbl_orders])
    sheet_cust = SheetIndexEntry(name="Customers", index=1, tables=[tbl_cust])

    index = WorkbookMetadataIndex(
        dataset_id="ds_rel",
        filename="Store.xlsx",
        sheet_count=2,
        sheet_names=["Orders", "Customers"],
        active_sheet_name="Orders",
        sheets={"Orders": sheet_orders, "Customers": sheet_cust},
    )

    graph = RelationshipDetector.detect_relationships(index)
    verified = graph.get_verified_relationships()

    assert len(verified) == 1
    rel = verified[0]
    assert rel.status == RelationshipStatusEnum.VERIFIED
    assert rel.confidence_score >= 0.85
    assert rel.directionality == RelationshipDirectionEnum.MANY_TO_ONE  # Orders is Many, Cust is One


def test_relationship_detection_false_positive_rejected():
    """Verify that same column name with numeric measure or mismatched semantics is rejected."""
    orders_sales = _make_col("Sales", DataTypeEnum.FLOAT, SemanticTypeEnum.NUMERIC_MEASURE, uniq=500, tot=500)
    targets_sales = _make_col("Sales", DataTypeEnum.FLOAT, SemanticTypeEnum.NUMERIC_MEASURE, uniq=12, tot=12)

    tbl_orders = TableIndexEntry(table_id="tbl_orders", name="Orders", sheet_name="Orders", range_address="A1:D500", columns=[orders_sales])
    tbl_targets = TableIndexEntry(table_id="tbl_targets", name="Targets", sheet_name="Targets", range_address="A1:B12", columns=[targets_sales])

    sheet_orders = SheetIndexEntry(name="Orders", index=0, tables=[tbl_orders])
    sheet_targets = SheetIndexEntry(name="Targets", index=1, tables=[tbl_targets])

    index = WorkbookMetadataIndex(
        dataset_id="ds_rej",
        filename="Data.xlsx",
        sheet_count=2,
        sheet_names=["Orders", "Targets"],
        active_sheet_name="Orders",
        sheets={"Orders": sheet_orders, "Targets": sheet_targets},
    )

    graph = RelationshipDetector.detect_relationships(index)
    verified = graph.get_verified_relationships()
    assert len(verified) == 0  # Rejects numeric measure links cleanly


# ============================================================================
# 2. GENERALIZED AMBIGUITY FRAMEWORK (11 DOMAINS)
# ============================================================================

def test_column_ambiguity_single_match_resolves():
    cols = [_make_col("Sales", DataTypeEnum.FLOAT, SemanticTypeEnum.NUMERIC_MEASURE)]
    res = GeneralizedAmbiguityResolver.resolve_column_ambiguity("total penjualan sales", cols)
    assert res.domain == AmbiguityDomainEnum.COLUMN
    assert res.is_ambiguous is False
    assert res.resolved_candidate.name == "Sales"


def test_column_ambiguity_multiple_matches_triggers_clarification():
    cols = [
        _make_col("Sales", DataTypeEnum.FLOAT, SemanticTypeEnum.NUMERIC_MEASURE),
        _make_col("Net Sales", DataTypeEnum.FLOAT, SemanticTypeEnum.NUMERIC_MEASURE),
        _make_col("Gross Sales", DataTypeEnum.FLOAT, SemanticTypeEnum.NUMERIC_MEASURE),
    ]
    res = GeneralizedAmbiguityResolver.resolve_column_ambiguity("sales", cols)
    assert res.is_ambiguous is True
    assert res.clarification_needed is True
    assert len(res.candidates) >= 2


def test_sheet_ambiguity_resolution_and_clarification():
    index = WorkbookMetadataIndex(
        dataset_id="ds_s",
        filename="Multi.xlsx",
        sheet_count=2,
        sheet_names=["Sales 2023", "Sales 2024"],
        active_sheet_name="Sales 2023",
        sheets={},
    )
    # Generic "sales" query matches both sheets -> clarification
    res = GeneralizedAmbiguityResolver.resolve_sheet_ambiguity("tampilkan data sales", index)
    assert res.is_ambiguous is True
    assert res.clarification_needed is True


def test_table_ambiguity_resolution():
    tbl1 = TableIndexEntry(table_id="tbl_1", name="Summary Table", sheet_name="S1", range_address="A1:D10")
    tbl2 = TableIndexEntry(table_id="tbl_2", name="Detail Table", sheet_name="S1", range_address="A15:D50")
    sheet = SheetIndexEntry(name="S1", index=0, tables=[tbl1, tbl2])

    res = GeneralizedAmbiguityResolver.resolve_table_ambiguity("tampilkan data", sheet)
    assert res.is_ambiguous is True
    assert res.clarification_needed is True


def test_range_ambiguity_resolution():
    res_explicit = GeneralizedAmbiguityResolver.resolve_range_ambiguity("total data A1:B20", "A1:E100")
    assert res_explicit.resolved_candidate == "A1:B20"

    res_default = GeneralizedAmbiguityResolver.resolve_range_ambiguity("total data", "A1:E100")
    assert res_default.resolved_candidate == "A1:E100"


def test_temporal_ambiguity_multi_date_clarification():
    date1 = _make_col("Order Date", DataTypeEnum.DATE, SemanticTypeEnum.TEMPORAL)
    date2 = _make_col("Ship Date", DataTypeEnum.DATE, SemanticTypeEnum.TEMPORAL)
    res = GeneralizedAmbiguityResolver.resolve_temporal_ambiguity("penjualan tahun 2018", [date1, date2])
    assert res.is_ambiguous is True
    assert res.clarification_needed is True


def test_metric_ambiguity_superlative_clarification():
    m1 = _make_col("Sales", DataTypeEnum.FLOAT, SemanticTypeEnum.NUMERIC_MEASURE)
    m2 = _make_col("Profit", DataTypeEnum.FLOAT, SemanticTypeEnum.NUMERIC_MEASURE)
    m3 = _make_col("Quantity", DataTypeEnum.INTEGER, SemanticTypeEnum.NUMERIC_MEASURE)

    # Superlative without measure -> Clarification
    res = GeneralizedAmbiguityResolver.resolve_metric_ambiguity("tampilkan top 5 produk terbaik", [m1, m2, m3])
    assert res.is_ambiguous is True
    assert res.clarification_needed is True


def test_aggregation_ambiguity():
    res_sum = GeneralizedAmbiguityResolver.resolve_aggregation_ambiguity("berapa total penjualan")
    assert res_sum.resolved_candidate == "SUM"

    res_avg = GeneralizedAmbiguityResolver.resolve_aggregation_ambiguity("rata-rata harga")
    assert res_avg.resolved_candidate == "AVERAGE"

    res_cnt = GeneralizedAmbiguityResolver.resolve_aggregation_ambiguity("banyaknya transaksi")
    assert res_cnt.resolved_candidate == "COUNT_ROWS"


def test_comparison_ambiguity_missing_baseline_clarification():
    res_no_base = GeneralizedAmbiguityResolver.resolve_comparison_ambiguity("apakah penjualan meningkat?", has_baseline=False, has_metric=True)
    assert res_no_base.is_ambiguous is True
    assert res_no_base.clarification_needed is True

    res_valid = GeneralizedAmbiguityResolver.resolve_comparison_ambiguity("apakah penjualan lebih baik vs 2023?", has_baseline=True, has_metric=True)
    assert res_valid.is_ambiguous is False
    assert res_valid.resolved_candidate == "VALID_COMPARISON"


def test_formatting_ambiguity_missing_target():
    res_vague = GeneralizedAmbiguityResolver.resolve_formatting_ambiguity("warnai hasilnya", target_specified=False)
    assert res_vague.is_ambiguous is True
    assert res_vague.clarification_needed is True

    res_spec = GeneralizedAmbiguityResolver.resolve_formatting_ambiguity("tebalkan sel D102", target_specified=True)
    assert res_spec.is_ambiguous is False


def test_mutation_destination_ambiguity():
    tbl = TableIndexEntry(table_id="tbl_1", name="Data", sheet_name="S1", range_address="A1:D100")
    res_explicit = GeneralizedAmbiguityResolver.resolve_mutation_destination_ambiguity("buat total di cell D102", tbl)
    assert res_explicit.resolved_candidate == "D102"

    res_auto = GeneralizedAmbiguityResolver.resolve_mutation_destination_ambiguity("buatkan total penjualan", tbl)
    assert res_auto.resolved_candidate == "SAFE_SUMMARY_ROW_BELOW_DATA"


def test_chart_ambiguity_suitability():
    res_valid = GeneralizedAmbiguityResolver.resolve_chart_ambiguity("buat chart", dimension_count=1, measure_count=1)
    assert res_valid.is_unsupported is False
    assert res_valid.resolved_candidate == "VALID_CHART_CANDIDATE"

    res_no_measure = GeneralizedAmbiguityResolver.resolve_chart_ambiguity("buat chart", dimension_count=1, measure_count=0)
    assert res_no_measure.is_unsupported is True
