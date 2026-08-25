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


def test_sheet_data_grid_search_functionality(client: TestClient, vertical_table_file: Path):
    with open(vertical_table_file, "rb") as f:
        res = client.post(
            "/api/v1/datasets/upload",
            files={"file": (vertical_table_file.name, f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
    dataset_id = res.json()["dataset_id"]

    # 1. Search partial text case-insensitive with whitespace
    search_resp = client.get(f"/api/v1/datasets/{dataset_id}/sheets/Sales/data?page=1&page_size=10&q=%20%20laptop%20%20")
    assert search_resp.status_code == 200
    search_data = search_resp.json()
    assert search_data["total_rows"] == 1
    assert len(search_data["rows"]) == 1
    assert search_data["rows"][0][1]["original_value"] == "Laptop Pro"

    # 2. Search numeric / ID value
    id_resp = client.get(f"/api/v1/datasets/{dataset_id}/sheets/Sales/data?page=1&page_size=10&q=TXN-003")
    assert id_resp.status_code == 200
    id_data = id_resp.json()
    assert id_data["total_rows"] == 1
    assert id_data["rows"][0][0]["original_value"] == "TXN-003"
    assert id_data["rows"][0][1]["original_value"] == "USB-C Hub"

    # 3. Search status category
    status_resp = client.get(f"/api/v1/datasets/{dataset_id}/sheets/Sales/data?page=1&page_size=10&q=completed")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["total_rows"] == 4
    assert len(status_data["rows"]) == 4

    # 4. Search with pagination on search results (page_size=2)
    p1_resp = client.get(f"/api/v1/datasets/{dataset_id}/sheets/Sales/data?page=1&page_size=2&q=completed")
    assert p1_resp.status_code == 200
    p1_data = p1_resp.json()
    assert p1_data["total_rows"] == 4
    assert len(p1_data["rows"]) == 2

    p2_resp = client.get(f"/api/v1/datasets/{dataset_id}/sheets/Sales/data?page=2&page_size=2&q=completed")
    assert p2_resp.status_code == 200
    p2_data = p2_resp.json()
    assert p2_data["total_rows"] == 4
    assert len(p2_data["rows"]) == 2

    # 5. Search with zero matches
    empty_resp = client.get(f"/api/v1/datasets/{dataset_id}/sheets/Sales/data?page=1&page_size=10&q=NonExistentMatch12345")
    assert empty_resp.status_code == 200
    empty_data = empty_resp.json()
    assert empty_data["total_rows"] == 0
    assert len(empty_data["rows"]) == 0

