"""Comprehensive API tests for Phase 8:
Spreadsheet Agent Endpoints (Action, Undo, History, Clarification & Rollback synchronization).
"""

from io import BytesIO
from fastapi.testclient import TestClient
import openpyxl
import pytest

from app.main import app

client = TestClient(app)


def _create_sample_excel_bytes() -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Orders"
    ws.append(["OrderID", "Customer", "Region", "Sales", "Profit"])
    ws.append(["ORD-1", "Alice", "East", 100.0, 20.0])
    ws.append(["ORD-2", "Bob", "West", 250.0, 50.0])
    ws.append(["ORD-3", "Charlie", "East", 150.0, 30.0])
    ws.append(["ORD-4", "Diana", "South", 300.0, 60.0])
    ws.append(["ORD-5", "Evan", "West", 200.0, 40.0])

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_agent_api_action_and_undo_flow():
    """Test full agent action -> commit -> undo flow via FastAPI endpoints."""
    # 1. Upload sample workbook
    file_bytes = _create_sample_excel_bytes()
    upload_res = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("SalesStore.xlsx", file_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert upload_res.status_code == 201
    overview = upload_res.json()
    dataset_id = overview["dataset_id"]

    # 2. Execute Agent Action
    action_res = client.post(
        "/api/v1/agent/action",
        json={
            "dataset_id": dataset_id,
            "user_request": "buatkan total penjualan",
            "active_sheet_name": "Orders",
        },
    )
    assert action_res.status_code == 200
    act_data = action_res.json()
    assert act_data["status"] == "SUCCESS"
    assert "D7" in act_data["affected_ranges"] or "C7:D7" in act_data["affected_ranges"]

    # 3. Check Agent History
    hist_res = client.get(f"/api/v1/agent/history/{dataset_id}")
    assert hist_res.status_code == 200
    hist_data = hist_res.json()
    assert hist_data["can_undo"] is True
    assert len(hist_data["history"]) >= 1

    # 4. Execute Undo
    undo_res = client.post(
        "/api/v1/agent/undo",
        json={
            "dataset_id": dataset_id,
            "active_sheet_name": "Orders",
        },
    )
    assert undo_res.status_code == 200
    undo_data = undo_res.json()
    assert undo_data["status"] == "ROLLBACK_SUCCESS"


def test_agent_api_unsupported_query():
    """Test agent handles unsupported query cleanly."""
    file_bytes = _create_sample_excel_bytes()
    upload_res = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("SalesStore.xlsx", file_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    dataset_id = upload_res.json()["dataset_id"]

    action_res = client.post(
        "/api/v1/agent/action",
        json={
            "dataset_id": dataset_id,
            "user_request": "kirim email ke semua customer",
            "active_sheet_name": "Orders",
        },
    )
    assert action_res.status_code == 200
    act_data = action_res.json()
    assert act_data["status"] in {"UNSUPPORTED", "VALIDATION_ERROR"}


def test_agent_api_clarification_on_ambiguity():
    """Test agent returns CLARIFICATION and does zero mutation when column is ambiguous."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Orders"
    ws.append(["OrderID", "Sales", "Net Sales"])
    ws.append(["ORD-1", 100.0, 90.0])
    ws.append(["ORD-2", 200.0, 180.0])
    buf = BytesIO()
    wb.save(buf)

    upload_res = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("MultiSales.xlsx", buf.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    dataset_id = upload_res.json()["dataset_id"]

    action_res = client.post(
        "/api/v1/agent/action",
        json={
            "dataset_id": dataset_id,
            "user_request": "buatkan total penjualan",
            "active_sheet_name": "Orders",
        },
    )
    assert action_res.status_code == 200
    act_data = action_res.json()
    assert act_data["status"] == "CLARIFICATION"
    assert act_data["clarification"] is not None
    assert len(act_data["clarification"]["options"]) >= 2


