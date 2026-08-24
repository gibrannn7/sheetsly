"""Integration tests for FastAPI endpoints: upload, inspection, sheet metadata, and data grid viewer."""

from pathlib import Path
from fastapi.testclient import TestClient


def test_upload_and_inspect_api(client: TestClient, vertical_table_file: Path):
    with open(vertical_table_file, "rb") as f:
        response = client.post(
            "/api/v1/datasets/upload",
            files={"file": (vertical_table_file.name, f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )

    assert response.status_code == 201
    data = response.json()
    assert "dataset_id" in data
    dataset_id = data["dataset_id"]
    assert data["sheet_count"] == 1
    assert data["filename"] == vertical_table_file.name

    sheet = data["sheets"][0]
    assert sheet["name"] == "Sales"
    assert sheet["total_rows"] == 6
    assert len(sheet["tables"]) == 1

    tbl = sheet["tables"][0]
    assert tbl["orientation"] == "VERTICAL"
    assert tbl["column_count"] == 6

    # Test GET dataset overview
    overview_resp = client.get(f"/api/v1/datasets/{dataset_id}")
    assert overview_resp.status_code == 200
    assert overview_resp.json()["dataset_id"] == dataset_id

    # Test GET sheet metadata
    sheet_resp = client.get(f"/api/v1/datasets/{dataset_id}/sheets/Sales")
    assert sheet_resp.status_code == 200
    assert sheet_resp.json()["name"] == "Sales"

    # Test GET sheet data grid
    grid_resp = client.get(f"/api/v1/datasets/{dataset_id}/sheets/Sales/data?page=1&page_size=10")
    assert grid_resp.status_code == 200
    grid_data = grid_resp.json()
    assert grid_data["total_rows"] == 6
    assert len(grid_data["rows"]) == 6

    # Verify cell coordinate preservation in row 0, col 0
    first_cell = grid_data["rows"][0][0]
    assert first_cell["coordinate"]["cell_ref"] == "A1"
    assert first_cell["original_value"] == "Transaction_ID"


def test_upload_invalid_file_extension(client: TestClient, tmp_path: Path):
    bad_file = tmp_path / "test.exe"
    bad_file.write_text("not an excel file")

    with open(bad_file, "rb") as f:
        response = client.post(
            "/api/v1/datasets/upload",
            files={"file": ("test.exe", f, "application/octet-stream")},
        )

    assert response.status_code == 400
    err = response.json()
    assert err["error"]["code"] == "FILE_VALIDATION_ERROR"


def test_nonexistent_dataset_returns_404(client: TestClient):
    response = client.get("/api/v1/datasets/nonexistent-uuid-12345")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "DATASET_NOT_FOUND"


def test_nonexistent_sheet_returns_404(client: TestClient, vertical_table_file: Path):
    with open(vertical_table_file, "rb") as f:
        res = client.post(
            "/api/v1/datasets/upload",
            files={"file": (vertical_table_file.name, f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
    dataset_id = res.json()["dataset_id"]

    response = client.get(f"/api/v1/datasets/{dataset_id}/sheets/NonExistentSheet")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "SHEET_NOT_FOUND"
