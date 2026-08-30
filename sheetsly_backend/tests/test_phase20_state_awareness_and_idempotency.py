"""
Comprehensive Test Suite for Phase 20:
Spreadsheet Agent State Awareness, Idempotency & Collision-Safe Placement
1. Partial multi-intent mutation (already satisfied formula preserved, missing label written)
2. Idempotent formula write (0 mutations when formula already exists)
3. Formula conflict protection (clarification on conflicting formula/value)
4. Duplicate chart rejection (0 new charts when identical chart exists)
5. Chart bounding-box spatial collision detection (explicit overlapping target rejected)
6. Free chart placement (auto-placed chart chooses non-overlapping anchor)
7. Selected-cell context retention (B40 + 'di cells ini')
8. Multi-visualization deduplication (skips already existing charts)
9. Multi-visualization spatial safety (all generated charts have disjoint bounding boxes)
10. Natural language undo and redo lifecycle
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
from app.engine.visualization.chart_model import ChartTypeEnum
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
        dataset_id="ds_p20_superstore",
        filename="superstore.xlsx",
        sheets={"Orders": sheet_entry},
        default_sheet="Orders",
    )

    return wb_index, grid


class TestPhase20MultiIntentAndIdempotency:
    """Test Suite for Phase 20 state-awareness, multi-intent decomposition, and idempotency."""

    def test_partial_multi_intent_mutation(self, superstore_sample):
        """Test 1: When D10 already has =SUM(D2:D7), only mutate C10 with WRITE_VALUE."""
        wb_index, grid = superstore_sample

        # Pre-populate D10 with the exact formula
        grid.cells[(10, 4)] = CellData(
            coordinate=CellCoordinate(row=10, column=4, cell_ref="D10", col_letter="D"),
            data_type=DataTypeEnum.FLOAT,
            original_value="465.0",
            parsed_value=465.0,
            formula="=SUM(D2:D7)",
            is_empty=False,
        )

        orchestrator = AgentOrchestrator()
        result = orchestrator.process_request(
            user_request="total sales di D10 dan berikan label TOTAL di C10",
            workbook_index=wb_index,
            grid=grid,
            active_sheet_name="Orders",
        )

        assert result.status == AgentResponseStatusEnum.SUCCESS
        assert result.transaction is not None
        assert len(result.transaction.actions) == 1
        assert result.transaction.actions[0].action_type == ActionTypeEnum.WRITE_VALUE
        assert result.transaction.actions[0].target_cell == "C10"
        assert result.transaction.actions[0].value == "TOTAL"
        assert (10, 3) in grid.cells and grid.cells[(10, 3)].parsed_value == "TOTAL"
        assert (10, 4) in grid.cells and grid.cells[(10, 4)].formula == "=SUM(D2:D7)"
        assert "D10 sudah benar" in result.message or "sudah sesuai" in result.message or "Label 'TOTAL' ditambahkan" in result.message or "is already correct" in result.message

    def test_idempotent_formula_zero_mutations(self, superstore_sample):
        """Test 2: When D10 already contains =SUM(D2:D7), asking for total sales produces 0 mutations."""
        wb_index, grid = superstore_sample

        grid.cells[(10, 4)] = CellData(
            coordinate=CellCoordinate(row=10, column=4, cell_ref="D10", col_letter="D"),
            data_type=DataTypeEnum.FLOAT,
            original_value="465.0",
            parsed_value=465.0,
            formula="=SUM(D2:D7)",
            is_empty=False,
        )

        orchestrator = AgentOrchestrator()
        result = orchestrator.process_request(
            user_request="total sales di D10",
            workbook_index=wb_index,
            grid=grid,
            active_sheet_name="Orders",
        )

        assert result.status == AgentResponseStatusEnum.SUCCESS
        assert result.transaction is None
        assert "sudah tersedia di D10" in result.message or "tidak ada perubahan" in result.message or "already calculated" in result.message

    def test_formula_conflict_protection(self, superstore_sample):
        """Test 3: When D10 contains =AVERAGE(D2:D7), requesting total sales in D10 triggers clarification without overwriting."""
        wb_index, grid = superstore_sample

        grid.cells[(10, 4)] = CellData(
            coordinate=CellCoordinate(row=10, column=4, cell_ref="D10", col_letter="D"),
            data_type=DataTypeEnum.FLOAT,
            original_value="77.5",
            parsed_value=77.5,
            formula="=AVERAGE(D2:D7)",
            is_empty=False,
        )

        orchestrator = AgentOrchestrator()
        result = orchestrator.process_request(
            user_request="total sales di D10",
            workbook_index=wb_index,
            grid=grid,
            active_sheet_name="Orders",
        )

        assert result.status == AgentResponseStatusEnum.CLARIFICATION
        assert result.transaction is None
        assert "D10" in result.message
        assert "sudah berisi formula" in result.message or "sudah terisi data" in result.message or "already contains" in result.message

    def test_duplicate_chart_rejection(self, superstore_sample):
        """Test 4: When Sales by Region PIE chart exists, repeating request produces 0 new charts."""
        wb_index, grid = superstore_sample

        # Pre-populate existing chart in grid.charts
        grid.charts["chart_1"] = {
            "chart_id": "chart_1",
            "title": "Sales by Region",
            "chart_type": "PIE",
            "dimension_column": "Region",
            "measure_column": "Sales",
            "aggregation": "SUM",
            "destination_cell": "B12",
            "width_cols": 7,
            "height_rows": 14,
        }

        orchestrator = AgentOrchestrator()
        result = orchestrator.process_request(
            user_request="buatkan pie chart sales by region",
            workbook_index=wb_index,
            grid=grid,
            active_sheet_name="Orders",
        )

        assert result.status == AgentResponseStatusEnum.SUCCESS
        assert result.transaction is None
        assert "sudah tersedia di B12" in result.message or "tidak membuat duplikat" in result.message or "already exists" in result.message

    def test_chart_bounding_box_collision(self, superstore_sample):
        """Test 5: Explicit chart placement at D15 is rejected because it overlaps existing B12:I25 chart."""
        wb_index, grid = superstore_sample

        grid.charts["chart_1"] = {
            "chart_id": "chart_1",
            "title": "Sales by Region",
            "chart_type": "PIE",
            "dimension_column": "Region",
            "measure_column": "Sales",
            "aggregation": "SUM",
            "destination_cell": "B12",
            "width_cols": 7,
            "height_rows": 14,
        }

        orchestrator = AgentOrchestrator()
        result = orchestrator.process_request(
            user_request="buatkan bar chart sales by category di D15",
            workbook_index=wb_index,
            grid=grid,
            active_sheet_name="Orders",
        )

        assert result.status == AgentResponseStatusEnum.CLARIFICATION
        assert result.transaction is None
        assert "tumpang tindih" in result.message or "overlaps" in result.message

    def test_free_chart_placement_avoids_existing_chart(self, superstore_sample):
        """Test 6: When B12:I25 is occupied by a chart, auto-placed new chart chooses a disjoint anchor below."""
        wb_index, grid = superstore_sample

        grid.charts["chart_1"] = {
            "chart_id": "chart_1",
            "title": "Sales by Region",
            "chart_type": "PIE",
            "dimension_column": "Region",
            "measure_column": "Sales",
            "aggregation": "SUM",
            "destination_cell": "B12",
            "width_cols": 7,
            "height_rows": 14,
        }

        orchestrator = AgentOrchestrator()
        result = orchestrator.process_request(
            user_request="buatkan chart sales by category",
            workbook_index=wb_index,
            grid=grid,
            active_sheet_name="Orders",
        )

        assert result.status == AgentResponseStatusEnum.SUCCESS
        assert result.transaction is not None
        assert len(result.transaction.actions) == 1
        new_dest = result.transaction.actions[0].target_cell
        assert new_dest is not None
        # Must be at or below row 27 (12 + 14 + 1)
        row_num = int(new_dest[1:])
        assert row_num >= 27

    def test_selected_cell_context_authoritative(self, superstore_sample):
        """Test 7: Selected cell B40 with 'di cells ini' resolves to anchor B40."""
        wb_index, grid = superstore_sample

        orchestrator = AgentOrchestrator()
        result = orchestrator.process_request(
            user_request="buatkan visualisasi sales by region di cells ini",
            workbook_index=wb_index,
            grid=grid,
            active_sheet_name="Orders",
            selected_range="B40",
        )

        assert result.status == AgentResponseStatusEnum.SUCCESS
        assert result.transaction is not None
        assert len(result.transaction.actions) == 1
        assert result.transaction.actions[0].target_cell == "B40"
        assert result.transaction.actions[0].chart_spec.destination_cell == "B40"

    def test_multi_visualization_deduplication(self, superstore_sample):
        """Test 8: Multi-vis query skips existing Sales by Region chart and generates only remaining missing charts."""
        wb_index, grid = superstore_sample

        grid.charts["chart_1"] = {
            "chart_id": "chart_1",
            "title": "Sales by Region",
            "chart_type": "PIE",
            "dimension_column": "Region",
            "measure_column": "Sales",
            "aggregation": "SUM",
            "destination_cell": "B12",
            "width_cols": 7,
            "height_rows": 14,
        }

        orchestrator = AgentOrchestrator()
        result = orchestrator.process_request(
            user_request="visualisasikan semua kemungkinan yang relevan",
            workbook_index=wb_index,
            grid=grid,
            active_sheet_name="Orders",
        )

        assert result.status == AgentResponseStatusEnum.SUCCESS
        assert result.transaction is not None
        # Generated charts must not include PIE of Region
        for act in result.transaction.actions:
            spec = act.chart_spec
            assert not (spec.dimension_column == "Region" and spec.chart_type == ChartTypeEnum.PIE)

    def test_multi_visualization_spatial_safety(self, superstore_sample):
        """Test 9: All generated charts in multi-vis layout have non-overlapping bounding boxes."""
        wb_index, grid = superstore_sample

        orchestrator = AgentOrchestrator()
        result = orchestrator.process_request(
            user_request="buat semua visualisasi yang relevan mulai dari B40",
            workbook_index=wb_index,
            grid=grid,
            active_sheet_name="Orders",
        )

        assert result.status == AgentResponseStatusEnum.SUCCESS
        assert result.transaction is not None
        assert len(result.transaction.actions) >= 2

        # Check all bounding boxes for disjointness
        from openpyxl.utils.cell import column_index_from_string, coordinate_from_string

        boxes = []
        for act in result.transaction.actions:
            dest = act.target_cell
            c_str, r_int = coordinate_from_string(dest)
            c_int = column_index_from_string(c_str)
            w = act.chart_spec.width_cols
            h = act.chart_spec.height_rows
            b = (c_int, r_int, c_int + w - 1, r_int + h - 1)
            for prev_b in boxes:
                is_disjoint = (
                    b[2] < prev_b[0]
                    or b[0] > prev_b[2]
                    or b[3] < prev_b[1]
                    or b[1] > prev_b[3]
                )
                assert is_disjoint, f"Box {b} overlaps with {prev_b}"
            boxes.append(b)

    def test_natural_language_undo_and_redo_lifecycle(self, superstore_sample):
        """Test 11 & 12: Natural language undo and redo on chart mutation."""
        wb_index, grid = superstore_sample

        orchestrator = AgentOrchestrator()
        # 1. Create Chart
        res1 = orchestrator.process_request(
            user_request="buatkan pie chart sales by region di B12",
            workbook_index=wb_index,
            grid=grid,
            active_sheet_name="Orders",
        )
        assert res1.status == AgentResponseStatusEnum.SUCCESS
        assert "chart_1" in grid.charts or len(grid.charts) == 1

        # 2. Undo via natural language
        res2 = orchestrator.process_request(
            user_request="undo langkah tersebut",
            workbook_index=wb_index,
            grid=grid,
            active_sheet_name="Orders",
        )
        assert res2.status in {AgentResponseStatusEnum.SUCCESS, AgentResponseStatusEnum.ROLLBACK_SUCCESS}
        assert len(grid.charts) == 0

        # 3. Redo via natural language
        res3 = orchestrator.process_request(
            user_request="redo langkah tersebut",
            workbook_index=wb_index,
            grid=grid,
            active_sheet_name="Orders",
        )
        assert res3.status in {AgentResponseStatusEnum.SUCCESS, AgentResponseStatusEnum.ROLLBACK_SUCCESS}
        assert len(grid.charts) == 1
