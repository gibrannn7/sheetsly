"""Integration tests for Analytics API endpoints."""

from pathlib import Path
from fastapi.testclient import TestClient


def test_analyze_endpoint_and_catalog(client: TestClient, vertical_table_file: Path):
    # 1. Test Operations Catalog endpoint
    cat_resp = client.get("/api/v1/operations/catalog")
    assert cat_resp.status_code == 200
    cat_data = cat_resp.json()
    assert "SUM" in cat_data["operations"]
    assert "GROUP_BY" in cat_data["operations"]
    assert "COUNT_ROWS" in cat_data["count_semantics"]

    # 2. Upload file
    with open(vertical_table_file, "rb") as f:
        up_resp = client.post(
            "/api/v1/datasets/upload",
            files={"file": (vertical_table_file.name, f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
    dataset_id = up_resp.json()["dataset_id"]

    # 3. Test POST /datasets/{dataset_id}/analyze for SUM
    payload_sum = {
        "operation": "SUM",
        "dataset_id": dataset_id,
        "sheet_name": "Sales",
        "target_column": "Revenue",
    }
    analyze_resp = client.post(f"/api/v1/datasets/{dataset_id}/analyze", json=payload_sum)
    assert analyze_resp.status_code == 200
    res = analyze_resp.json()
    assert res["result_type"] == "SCALAR"
    assert res["scalar_value"] == 3635.0
    assert res["lineage"]["total_table_rows"] == 5

    # 4. Test POST /datasets/{dataset_id}/analyze for GROUP_BY
    payload_group = {
        "operation": "GROUP_BY",
        "dataset_id": dataset_id,
        "sheet_name": "Sales",
        "group_by_columns": ["Status"],
        "aggregations": [
            {"column": "Revenue", "operation": "SUM", "alias": "Total_Rev"},
            {"column": "Quantity", "operation": "AVERAGE", "alias": "Avg_Qty"},
        ],
        "sort": {"column": "Total_Rev", "ascending": False},
    }
    group_resp = client.post(f"/api/v1/datasets/{dataset_id}/analyze", json=payload_group)
    assert group_resp.status_code == 200
    res_group = group_resp.json()
    assert res_group["result_type"] == "TABLE"
    assert res_group["table_data"]["total_rows"] == 2
    assert res_group["table_data"]["rows"][0]["Status"] == "Completed"
    assert res_group["table_data"]["rows"][0]["Total_Rev"] == 3460.0

    # 5. Test validation error returns 422
    payload_invalid = {
        "operation": "SUM",
        "dataset_id": dataset_id,
        "sheet_name": "Sales",
        "target_column": "Product",  # string column
    }
    err_resp = client.post(f"/api/v1/datasets/{dataset_id}/analyze", json=payload_invalid)
    assert err_resp.status_code == 422
    err_data = err_resp.json()
    assert err_data["error"]["code"] == "ANALYTICAL_VALIDATION_ERROR"
