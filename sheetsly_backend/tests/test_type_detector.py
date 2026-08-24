"""Tests for deterministic data type detection and semantic profiling."""

from datetime import date
from app.engine.profiler.type_detector import TypeDetector
from app.models.schemas import DataTypeEnum, SemanticTypeEnum


def test_detect_individual_types():
    assert TypeDetector.detect_value_type(None)[0] == DataTypeEnum.NULL
    assert TypeDetector.detect_value_type("")[0] == DataTypeEnum.NULL
    assert TypeDetector.detect_value_type(100)[0] == DataTypeEnum.INTEGER
    assert TypeDetector.detect_value_type("250")[0] == DataTypeEnum.INTEGER
    assert TypeDetector.detect_value_type(99.5)[0] == DataTypeEnum.FLOAT
    assert TypeDetector.detect_value_type("1,250.75")[0] == DataTypeEnum.FLOAT
    assert TypeDetector.detect_value_type("$1,500.00")[0] == DataTypeEnum.CURRENCY
    assert TypeDetector.detect_value_type("Rp 500.000")[0] == DataTypeEnum.CURRENCY
    assert TypeDetector.detect_value_type("15.5%")[0] == DataTypeEnum.PERCENTAGE
    assert TypeDetector.detect_value_type("TRUE")[0] == DataTypeEnum.BOOLEAN
    assert TypeDetector.detect_value_type(True)[0] == DataTypeEnum.BOOLEAN
    assert TypeDetector.detect_value_type("2026-01-15")[0] == DataTypeEnum.DATE
    assert TypeDetector.detect_value_type(date(2026, 1, 15))[0] == DataTypeEnum.DATE
    assert TypeDetector.detect_value_type("Acme Corporation")[0] == DataTypeEnum.STRING


def test_profile_identifier_column():
    ids = ["CUST-001", "CUST-002", "CUST-003", "CUST-004", "CUST-005"]
    best_type, semantic, conf, nulls, uniq, samples = TypeDetector.profile_column_vector(ids, "Customer_ID")
    assert best_type == DataTypeEnum.STRING
    assert semantic == SemanticTypeEnum.IDENTIFIER
    assert nulls == 0
    assert uniq == 5


def test_profile_measure_column():
    revenues = ["$100.00", "$250.00", "$500.00", "$320.00"]
    best_type, semantic, conf, nulls, uniq, samples = TypeDetector.profile_column_vector(revenues, "Revenue")
    assert best_type == DataTypeEnum.CURRENCY
    assert semantic == SemanticTypeEnum.NUMERIC_MEASURE
    assert nulls == 0


def test_profile_temporal_column():
    dates = ["2026-01-01", "2026-01-02", "2026-01-03"]
    best_type, semantic, conf, nulls, uniq, samples = TypeDetector.profile_column_vector(dates, "Order_Date")
    assert best_type == DataTypeEnum.DATE
    assert semantic == SemanticTypeEnum.TEMPORAL
