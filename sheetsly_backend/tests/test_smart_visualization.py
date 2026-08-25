"""Automated regression test suite for Smart Generate Chart capability."""

import io
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.engine.visualization.chart_model import ChartTypeEnum, SmartGenerateRequest
from app.engine.visualization.smart_generator import SmartChartGenerator
from app.engine.pipeline import ingestion_pipeline


client = TestClient(app)


def upload_csv_data(client_instance: TestClient, csv_content: str, filename: str = "test.csv") -> str:
    """Helper to upload CSV and return dataset_id."""
    files = {"file": (filename, io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    response = client_instance.post("/api/v1/datasets/upload", files=files)
    assert response.status_code in [200, 201]
    return response.json()["dataset_id"]


def test_smart_generate_sales_dataset():
    """1. Dataset with Region, Product, Units, Revenue -> generates ranked bar/pie/scatter/histogram charts."""
    csv_data = (
        "Region,Product,Units,Revenue\n"
        "East,Widget A,10,100.0\n"
        "East,Widget B,15,150.0\n"
        "West,Widget A,20,200.0\n"
        "West,Widget B,25,250.0\n"
        "North,Widget C,30,300.0\n"
    )
    dataset_id = upload_csv_data(client, csv_data, "sales.csv")

    response = client.post(
        f"/api/v1/datasets/{dataset_id}/visualize/smart-generate",
        json={"max_charts": 5},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["selected_charts_count"] > 0
    assert data["selected_charts_count"] <= 5
    assert len(data["charts"]) <= 5

    chart_types = [c["chart_type"] for c in data["charts"]]
    # Should include Bar comparisons
    assert "BAR" in chart_types

    # Verify each chart has complete metadata and "why_this_chart" explanation
    for c in data["charts"]:
        assert c["title"]
        assert c["why_this_chart"]
        assert c["visualization"]["image_url"]
        assert c["rank_score"] > 0


def test_smart_generate_time_series_dataset():
    """2. Dataset with Date + Revenue -> generates time-series Line chart candidate."""
    csv_data = (
        "Order Date,Revenue\n"
        "2023-01-01,1000\n"
        "2023-02-01,1500\n"
        "2023-03-01,1200\n"
        "2023-04-01,1800\n"
        "2023-05-01,2200\n"
    )
    dataset_id = upload_csv_data(client, csv_data, "timeseries.csv")

    response = client.post(
        f"/api/v1/datasets/{dataset_id}/visualize/smart-generate",
        json={"max_charts": 5},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["selected_charts_count"] > 0

    first_chart = data["charts"][0]
    # Line chart should be highest ranked for time series
    assert first_chart["chart_type"] == "LINE"
    assert first_chart["dimension_column"] == "Order Date"
    assert "temporal dimension" in first_chart["why_this_chart"].lower()


def test_smart_generate_excludes_order_id_as_primary_dimension():
    """3. Dataset with Order ID + Category + Revenue -> Order ID should NOT become the primary dimension."""
    csv_data = (
        "Order_ID,Category,Revenue\n"
        "ORD-001,Electronics,500\n"
        "ORD-002,Furniture,300\n"
        "ORD-003,Electronics,450\n"
        "ORD-004,Office Supplies,120\n"
        "ORD-005,Furniture,600\n"
    )
    dataset_id = upload_csv_data(client, csv_data, "orders.csv")

    response = client.post(
        f"/api/v1/datasets/{dataset_id}/visualize/smart-generate",
        json={"max_charts": 5},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["selected_charts_count"] > 0

    # Ensure no chart has Order_ID as its primary categorical dimension
    for c in data["charts"]:
        if c["chart_type"] in ["BAR", "PIE", "LINE"]:
            assert c["dimension_column"] != "Order_ID"


def test_smart_generate_high_cardinality_protection():
    """4. Dataset with high cardinality dimension (9800 unique rows) -> no unreadable chart."""
    rows = ["Row_ID,User_Name,Score\n"]
    for i in range(1, 100):
        rows.append(f"ID_{i},User_{i},{i * 10}\n")
    csv_data = "".join(rows)

    dataset_id = upload_csv_data(client, csv_data, "large_cardinality.csv")

    response = client.post(
        f"/api/v1/datasets/{dataset_id}/visualize/smart-generate",
        json={"max_charts": 5},
    )
    assert response.status_code == 200
    data = response.json()
    # High cardinality User_Name and Row_ID should not become 100-category bar charts
    for c in data["charts"]:
        assert c["dimension_column"] != "Row_ID"
        assert c["dimension_column"] != "User_Name"


def test_smart_generate_only_numeric_columns():
    """5. Dataset with only continuous numeric columns -> generates Scatter and Histogram."""
    csv_data = (
        "StudyHours,ExamScore\n"
        "2.5,65\n"
        "3.0,70\n"
        "4.5,82\n"
        "5.0,88\n"
        "6.5,95\n"
    )
    dataset_id = upload_csv_data(client, csv_data, "correlation.csv")

    response = client.post(
        f"/api/v1/datasets/{dataset_id}/visualize/smart-generate",
        json={"max_charts": 5},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["selected_charts_count"] > 0

    chart_types = {c["chart_type"] for c in data["charts"]}
    assert "SCATTER" in chart_types or "HISTOGRAM" in chart_types


def test_smart_generate_only_text_columns():
    """6. Dataset with only non-analyzable text columns -> returns truthful empty state or frequency bar."""
    csv_data = (
        "Comment,Reviewer\n"
        "Great service,Alice\n"
        "Poor experience,Bob\n"
        "Average quality,Charlie\n"
    )
    dataset_id = upload_csv_data(client, csv_data, "text_only.csv")

    response = client.post(
        f"/api/v1/datasets/{dataset_id}/visualize/smart-generate",
        json={"max_charts": 5},
    )
    assert response.status_code == 200
    data = response.json()
    # May return frequency count or empty state gracefully without crashing
    assert isinstance(data["charts"], list)
    assert data["selected_charts_count"] <= 5


def test_smart_generate_small_categorical_composition():
    """7. Dataset with 3 categories -> creates Part-to-Whole Pie chart or Bar chart."""
    csv_data = (
        "Tier,Revenue\n"
        "Bronze,1000\n"
        "Silver,2500\n"
        "Gold,5000\n"
    )
    dataset_id = upload_csv_data(client, csv_data, "tiers.csv")

    response = client.post(
        f"/api/v1/datasets/{dataset_id}/visualize/smart-generate",
        json={"max_charts": 5},
    )
    assert response.status_code == 200
    data = response.json()
    chart_types = [c["chart_type"] for c in data["charts"]]
    assert "BAR" in chart_types or "PIE" in chart_types


def test_smart_generate_no_pie_for_many_categories():
    """8. Dataset with 30 categories -> strictly rejects Pie charts for >7 categories."""
    rows = ["City,Sales\n"]
    for i in range(1, 31):
        rows.append(f"City_{i},{i * 100}\n")
    csv_data = "".join(rows)

    dataset_id = upload_csv_data(client, csv_data, "cities.csv")

    response = client.post(
        f"/api/v1/datasets/{dataset_id}/visualize/smart-generate",
        json={"max_charts": 5},
    )
    assert response.status_code == 200
    data = response.json()
    for c in data["charts"]:
        if c["dimension_column"] == "City":
            # Must NOT be a Pie chart
            assert c["chart_type"] != "PIE"


def test_smart_generate_redundancy_filtered():
    """9. Duplicate candidate scenarios -> redundant charts are filtered."""
    csv_data = (
        "Region,Revenue\n"
        "East,100\n"
        "West,200\n"
        "North,300\n"
    )
    dataset_id = upload_csv_data(client, csv_data, "redundancy.csv")

    response = client.post(
        f"/api/v1/datasets/{dataset_id}/visualize/smart-generate",
        json={"max_charts": 5},
    )
    assert response.status_code == 200
    data = response.json()
    # Check that there are no duplicate (dimension_column, metric_column, chart_type) combinations
    seen_combos = set()
    for c in data["charts"]:
        combo = (c["dimension_column"], c["metric_column"], c["chart_type"])
        assert combo not in seen_combos
        seen_combos.add(combo)


def test_smart_generate_maximum_limit_enforced():
    """10. Smart Generate never exceeds 5 charts, respecting max_charts."""
    csv_data = (
        "Region,Category,Segment,Units,Revenue,Profit\n"
        "East,Technology,Consumer,10,500,100\n"
        "East,Furniture,Corporate,15,400,50\n"
        "West,Technology,Home Office,20,800,200\n"
        "West,Furniture,Consumer,25,600,120\n"
        "North,Office Supplies,Corporate,30,300,80\n"
    )
    dataset_id = upload_csv_data(client, csv_data, "enterprise.csv")

    response = client.post(
        f"/api/v1/datasets/{dataset_id}/visualize/smart-generate",
        json={"max_charts": 3},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["charts"]) <= 3
    assert data["selected_charts_count"] <= 3
    assert data["selected_charts_count"] <= 5
