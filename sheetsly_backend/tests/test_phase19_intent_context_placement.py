"""
Comprehensive Test Suite for Phase 19:
Spreadsheet Agent Intent, Context & Placement Correction:
1. Natural Language Undo / Redo / Cancel priority routing
2. Selected Cell / "Cells Ini" / "Di Sini" destination resolution
3. Strict separation of source ranges vs destination anchors
4. Multi-visualization intent with atomic transactions and clean grid placement
5. Context-aware analytical queries and regression safety
"""

import pytest
from app.engine.agent.action_model import ActionTypeEnum
from app.engine.agent.agent_orchestrator import AgentOrchestrator
from app.engine.agent.agent_planner import SpreadsheetAgentPlanner
from app.engine.agent.transaction_model import AgentResponseStatusEnum
from app.engine.parser.sheet_reader import RawSheetGrid
from app.engine.profiler.workbook_index import (
    ColumnIndexEntry,
    SheetIndexEntry,
    TableIndexEntry,
    WorkbookMetadataIndex,
)
from app.models.schemas import CellCoordinate, CellData, DataTypeEnum, SemanticTypeEnum


@pytest.fixture
def superstore_sample():
    cells = {}
    headers = ["Order ID", "Region", "Category", "Sales", "Profit", "Order Date"]
    types = [
        DataTypeEnum.STRING,
        DataTypeEnum.STRING,
        DataTypeEnum.STRING,
        DataTypeEnum.FLOAT,
        DataTypeEnum.FLOAT,
        DataTypeEnum.DATE,
    ]
    for c_idx, (h, dt) in enumerate(zip(headers, types), start=1):
        col_letter = chr(64 + c_idx)
        cells[(1, c_idx)] = CellData(
            coordinate=CellCoordinate(row=1, column=c_idx, cell_ref=f"{col_letter}1", col_letter=col_letter),
            original_value=h,
            parsed_value=h,
            data_type=dt,
            is_empty=False,
        )

    rows_data = [
        ("CA-101", "West", "Technology", 100.0, 20.0, "2024-01-15"),
        ("CA-102", "West", "Furniture", 50.0, 5.0, "2024-02-10"),
        ("CA-103", "East", "Furniture", 200.0, 30.0, "2024-01-20"),
        ("CA-104", "East", "Technology", 80.0, 15.0, "2024-03-05"),
        ("CA-105", "South", "Office Supplies", 30.0, 2.0, "2024-02-28"),
        ("CA-106", "Central", "Office Supplies", 5.0, 1.0, "2024-03-12"),
    ]

    for r_idx, row in enumerate(rows_data, start=2):
        for c_idx, val in enumerate(row, start=1):
            col_letter = chr(64 + c_idx)
            dt = types[c_idx - 1]
            cells[(r_idx, c_idx)] = CellData(
                coordinate=CellCoordinate(row=r_idx, column=c_idx, cell_ref=f"{col_letter}{r_idx}", col_letter=col_letter),
                original_value=str(val),
                parsed_value=val,
                data_type=dt,
                is_empty=False,
            )

    grid = RawSheetGrid(
        sheet_name="Orders",
        min_row=1,
        max_row=7,
        min_col=1,
        max_col=6,
        cells=cells,
    )

    columns = [
        ColumnIndexEntry(index=0, name="Order ID", normalized_name="order id", source_column_letter="A", semantic_type=SemanticTypeEnum.IDENTIFIER, data_type=DataTypeEnum.STRING),
        ColumnIndexEntry(index=1, name="Region", normalized_name="region", source_column_letter="B", semantic_type=SemanticTypeEnum.CATEGORICAL, data_type=DataTypeEnum.STRING),
        ColumnIndexEntry(index=2, name="Category", normalized_name="category", source_column_letter="C", semantic_type=SemanticTypeEnum.CATEGORICAL, data_type=DataTypeEnum.STRING),
        ColumnIndexEntry(index=3, name="Sales", normalized_name="sales", source_column_letter="D", semantic_type=SemanticTypeEnum.NUMERIC_MEASURE, data_type=DataTypeEnum.FLOAT),
        ColumnIndexEntry(index=4, name="Profit", normalized_name="profit", source_column_letter="E", semantic_type=SemanticTypeEnum.NUMERIC_MEASURE, data_type=DataTypeEnum.FLOAT),
        ColumnIndexEntry(index=5, name="Order Date", normalized_name="order date", source_column_letter="F", semantic_type=SemanticTypeEnum.TEMPORAL, data_type=DataTypeEnum.DATE),
    ]

    table_entry = TableIndexEntry(
        table_id="tbl_orders",
        sheet_name="Orders",
        name="Orders_Table",
        range_address="A1:F7",
        header_range="A1:F1",
        data_range="A2:F7",
        header_row_index=1,
        row_count=6,
        column_count=6,
        columns=columns,
    )

    sheet_entry = SheetIndexEntry(
        name="Orders",
        index=0,
        total_rows=7,
        total_columns=6,
        used_range="A1:F7",
        tables=[table_entry],
    )

    wb_index = WorkbookMetadataIndex(
        dataset_id="ds_p19_superstore",
        filename="Superstore_P19.xlsx",
        sheet_count=1,
        sheet_names=["Orders"],
        active_sheet_name="Orders",
        sheets={"Orders": sheet_entry},
    )

    return wb_index, grid


class TestPhase19NaturalLanguageUndoRedo:
    """1. Natural Language Undo, Redo, and Cancel intent handling."""

    def test_undo_langkah_tersebut(self, superstore_sample):
        wb_index, grid = superstore_sample
        orchestrator = AgentOrchestrator()

        # Step 1: Create chart at B12
        res1 = orchestrator.process_request(
            "buatkan pie chart di B12 untuk Region berdasarkan Sales",
            wb_index,
            grid,
        )
        assert res1.status == AgentResponseStatusEnum.SUCCESS
        assert len(grid.charts) == 1

        # Step 2: "undo langkah tersebut"
        res2 = orchestrator.process_request(
            "undo langkah tersebut",
            wb_index,
            grid,
        )
        assert res2.status == AgentResponseStatusEnum.ROLLBACK_SUCCESS
        assert len(grid.charts) == 0

    def test_undo_perubahan_tadi(self, superstore_sample):
        wb_index, grid = superstore_sample
        orchestrator = AgentOrchestrator()

        orchestrator.process_request("buat total sales di D10", wb_index, grid)
        assert (10, 4) in grid.cells and grid.cells[(10, 4)].formula is not None

        res_undo = orchestrator.process_request("undo perubahan tadi", wb_index, grid)
        assert res_undo.status == AgentResponseStatusEnum.ROLLBACK_SUCCESS
        assert (10, 4) not in grid.cells or grid.cells[(10, 4)].formula is None

    def test_batalkan_langkah_tadi(self, superstore_sample):
        wb_index, grid = superstore_sample
        orchestrator = AgentOrchestrator()

        orchestrator.process_request("buat total sales di D10", wb_index, grid)
        res_undo = orchestrator.process_request("batalkan langkah tadi", wb_index, grid)
        assert res_undo.status == AgentResponseStatusEnum.ROLLBACK_SUCCESS

    def test_kembalikan_seperti_sebelumnya(self, superstore_sample):
        wb_index, grid = superstore_sample
        orchestrator = AgentOrchestrator()

        orchestrator.process_request("buat total sales di D10", wb_index, grid)
        res_undo = orchestrator.process_request("kembalikan seperti sebelumnya", wb_index, grid)
        assert res_undo.status == AgentResponseStatusEnum.ROLLBACK_SUCCESS

    def test_redo_langkah_tersebut(self, superstore_sample):
        wb_index, grid = superstore_sample
        orchestrator = AgentOrchestrator()

        orchestrator.process_request("buat total sales di D10", wb_index, grid)
        orchestrator.process_request("undo", wb_index, grid)
        res_redo = orchestrator.process_request("redo langkah tersebut", wb_index, grid)
        assert res_redo.status == AgentResponseStatusEnum.SUCCESS
        assert (10, 4) in grid.cells and grid.cells[(10, 4)].formula is not None

    def test_cancel_operation_no_mutation(self, superstore_sample):
        wb_index, grid = superstore_sample
        orchestrator = AgentOrchestrator()

        res_cancel = orchestrator.process_request("batalkan operasi ini", wb_index, grid)
        assert res_cancel.status == AgentResponseStatusEnum.SUCCESS
        assert "dibatalkan" in res_cancel.message.lower() or "cancelled" in res_cancel.message.lower()


class TestPhase19SelectedCellDestination:
    """2. Selected cell / 'cells ini' / 'di sini' destination resolution."""

    def test_selected_b40_di_cells_ini_formula(self, superstore_sample):
        wb_index, grid = superstore_sample
        orchestrator = AgentOrchestrator()

        res = orchestrator.process_request(
            "buatkan total sales di cells ini",
            wb_index,
            grid,
            selected_range="B40",
        )
        assert res.status == AgentResponseStatusEnum.SUCCESS
        assert (40, 2) in grid.cells
        assert grid.cells[(40, 2)].formula == "=SUM(D2:D7)"

    def test_selected_b40_di_cells_ini_visualization(self, superstore_sample):
        wb_index, grid = superstore_sample
        orchestrator = AgentOrchestrator()

        res = orchestrator.process_request(
            "buatkan visualisasi sales by region di cells ini",
            wb_index,
            grid,
            selected_range="B40",
        )
        assert res.status == AgentResponseStatusEnum.SUCCESS
        assert len(grid.charts) == 1
        chart = next(iter(grid.charts.values()))
        assert chart["destination_cell"] == "B40"

    def test_explicit_destination_overrides_selection(self, superstore_sample):
        wb_index, grid = superstore_sample
        orchestrator = AgentOrchestrator()

        res = orchestrator.process_request(
            "buatkan pie chart di B12 untuk Region berdasarkan Sales",
            wb_index,
            grid,
            selected_range="B40",
        )
        assert res.status == AgentResponseStatusEnum.SUCCESS
        assert len(grid.charts) == 1
        chart = next(iter(grid.charts.values()))
        assert chart["destination_cell"] == "B12"

    def test_selected_b40_implicit_formula(self, superstore_sample):
        wb_index, grid = superstore_sample
        orchestrator = AgentOrchestrator()

        res = orchestrator.process_request(
            "buatkan total sales",
            wb_index,
            grid,
            selected_range="B40",
        )
        assert res.status == AgentResponseStatusEnum.SUCCESS
        assert (40, 2) in grid.cells
        assert grid.cells[(40, 2)].formula == "=SUM(D2:D7)"

    def test_selected_b40_implicit_chart(self, superstore_sample):
        wb_index, grid = superstore_sample
        orchestrator = AgentOrchestrator()

        res = orchestrator.process_request(
            "buatkan chart sales by region",
            wb_index,
            grid,
            selected_range="B40",
        )
        assert res.status == AgentResponseStatusEnum.SUCCESS
        assert len(grid.charts) == 1
        chart = next(iter(grid.charts.values()))
        assert chart["destination_cell"] == "B40"


class TestPhase19SourceVsDestination:
    """3. Separation of source data ranges vs destination targets."""

    def test_source_range_with_explicit_destination(self, superstore_sample):
        wb_index, grid = superstore_sample
        orchestrator = AgentOrchestrator()

        res = orchestrator.process_request(
            "buatkan total dari data yang dipilih di D10",
            wb_index,
            grid,
            selected_range="D2:D5",
        )
        assert res.status == AgentResponseStatusEnum.SUCCESS
        assert (10, 4) in grid.cells
        assert grid.cells[(10, 4)].formula == "=SUM(D2:D5)"


class TestPhase19MultiVisualization:
    """4. Multi-visualization intent, atomic execution, and atomic rollback."""

    def test_visualisasikan_semua_kemungkinan(self, superstore_sample):
        wb_index, grid = superstore_sample
        orchestrator = AgentOrchestrator()

        res = orchestrator.process_request(
            "visualisasikan semua kemungkinan",
            wb_index,
            grid,
            selected_range="B40",
        )
        assert res.status == AgentResponseStatusEnum.SUCCESS
        # Should generate multiple relevant charts (e.g. 4)
        assert len(grid.charts) >= 3
        chart_destinations = [c["destination_cell"] for c in grid.charts.values()]
        # Starts at B40
        assert "B40" in chart_destinations
        assert "J40" in chart_destinations

        # Atomic Undo
        res_undo = orchestrator.process_request("undo langkah tersebut", wb_index, grid)
        assert res_undo.status == AgentResponseStatusEnum.ROLLBACK_SUCCESS
        assert len(grid.charts) == 0

    def test_berikan_semuanya_multi_vis(self, superstore_sample):
        wb_index, grid = superstore_sample
        orchestrator = AgentOrchestrator()

        res = orchestrator.process_request(
            "berikan semuanya, seperti sales by region, dan lainnya, jangan hanya itu saja",
            wb_index,
            grid,
        )
        assert res.status == AgentResponseStatusEnum.SUCCESS
        assert len(grid.charts) >= 3

    def test_multi_vis_explicit_start_anchor(self, superstore_sample):
        wb_index, grid = superstore_sample
        orchestrator = AgentOrchestrator()

        res = orchestrator.process_request(
            "buat semua visualisasi mulai dari B50",
            wb_index,
            grid,
            selected_range="B12",
        )
        assert res.status == AgentResponseStatusEnum.SUCCESS
        chart_destinations = [c["destination_cell"] for c in grid.charts.values()]
        assert "B50" in chart_destinations
        assert "J50" in chart_destinations
