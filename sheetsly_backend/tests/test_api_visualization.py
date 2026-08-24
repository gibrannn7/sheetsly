"""Integration tests for Visualization API endpoints."""

from pathlib import Path
from fastapi.testclient import TestClient


def test_visualization_api_workflow(client: TestClient, vertical_table_file: Path):
    # 1. Upload dataset
    with open(vertical_table_file, "rb") as f:
        up_resp = client.post(
            "/api/v1/datasets/upload",
            files={"file": (vertical_table_file.name, f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
    dataset_id = up_resp.json()["dataset_id"]

    # 2. Execute analysis (GROUP_BY Status -> SUM(Revenue))
    payload_group = {
        "operation": "GROUP_BY",
        "dataset_id": dataset_id,
        "sheet_name": "Sales",
        "group_by_columns": ["Status"],
        "aggregations": [
            {"column": "Revenue", "operation": "SUM", "alias": "Total_Rev"},
        ],
    }
    analyze_resp = client.post(f"/api/v1/datasets/{dataset_id}/analyze", json=payload_group)
    assert analyze_resp.status_code == 200
    analytical_result = analyze_resp.json()

    # 3. Test POST /visualization/recommend
    rec_resp = client.post("/api/v1/visualization/recommend", json=analytical_result)
    assert rec_resp.status_code == 200
    rec_data = rec_resp.json()
    assert rec_data["preferred_type"] == "BAR"
    assert "PIE" in rec_data["compatible_types"]

    # 4. Test POST /datasets/{dataset_id}/visualize (from AnalyticalResult)
    viz_payload = {
        "dataset_id": dataset_id,
        "analytical_result": analytical_result,
        "chart_type": "BAR",
        "title": "Revenue by Status",
    }
    viz_resp = client.post(f"/api/v1/datasets/{dataset_id}/visualize", json=viz_payload)
    assert viz_resp.status_code == 200
    viz_data = viz_resp.json()
    chart_id = viz_data["chart_metadata"]["chart_id"]
    assert viz_data["chart_metadata"]["chart_type"] == "BAR"
    assert viz_data["chart_metadata"]["title"] == "Revenue by Status"
    assert viz_data["chart_metadata"]["dataset_id"] == dataset_id
    assert viz_data["chart_metadata"]["sheet_name"] == "Sales"
    assert "image_url" in viz_data

    # 5. Test GET /datasets/{dataset_id}/charts/{chart_id}/image
    img_resp = client.get(f"/api/v1/datasets/{dataset_id}/charts/{chart_id}/image")
    assert img_resp.status_code == 200
    assert img_resp.headers["content-type"] == "image/png"
    assert len(img_resp.content) > 1000

    # 6. Test POST /datasets/{dataset_id}/visualize/from-instruction (shortcut)
    shortcut_payload = {
        "instruction": payload_group,
        "chart_type": "PIE",
        "title": "Status Distribution",
    }
    short_resp = client.post(f"/api/v1/datasets/{dataset_id}/visualize/from-instruction", json=shortcut_payload)
    assert short_resp.status_code == 200
    short_data = short_resp.json()
    assert short_data["chart_metadata"]["chart_type"] == "PIE"

    # 7. Test Incompatible Chart Rejection (SCATTER on 1 categorical + 1 numeric)
    invalid_viz_payload = {
        "dataset_id": dataset_id,
        "analytical_result": analytical_result,
        "chart_type": "SCATTER",
    }
    err_resp = client.post(f"/api/v1/datasets/{dataset_id}/visualize", json=invalid_viz_payload)
    assert err_resp.status_code == 422
    err_json = err_resp.json()
    assert err_json["error"]["code"] == "INCOMPATIBLE_CHART_TYPE"
