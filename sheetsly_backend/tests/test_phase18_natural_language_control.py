"""
Comprehensive Test Suite for Phase 18:
Natural-Language Transaction Control, Multi-Intent Command Parsing, Context-Aware Analytical Inquiries & Controlled Workbook Completion.
"""

import copy
import pytest
from app.engine.agent.action_model import ActionTypeEnum
from app.engine.agent.agent_orchestrator import AgentOrchestrator
from app.engine.agent.agent_planner import SpreadsheetAgentPlanner
from app.engine.agent.memory_manager import MemoryManager
from app.engine.agent.transaction_manager import TransactionManager
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
def superstore_sample_workbook():
    cells = {}
    headers = ["Order ID", "Region", "Category", "Sales", "Profit"]
    types = [DataTypeEnum.STRING, DataTypeEnum.STRING, DataTypeEnum.STRING, DataTypeEnum.FLOAT, DataTypeEnum.FLOAT]
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
        ("CA-101", "West", "Technology", 100.0, 20.0),
        ("CA-102", "West", "Furniture", 50.0, 5.0),
        ("CA-103", "East", "Furniture", 200.0, 30.0),
        ("CA-104", "East", "Technology", 80.0, 15.0),
        ("CA-105", "South", "Office Supplies", 30.0, 2.0),
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
        max_row=6,
        min_col=1,
        max_col=5,
        cells=cells,
    )

    columns = [
        ColumnIndexEntry(index=0, name="Order ID", normalized_name="order id", source_column_letter="A", semantic_type=SemanticTypeEnum.IDENTIFIER, data_type=DataTypeEnum.STRING),
        ColumnIndexEntry(index=1, name="Region", normalized_name="region", source_column_letter="B", semantic_type=SemanticTypeEnum.CATEGORICAL, data_type=DataTypeEnum.STRING),
        ColumnIndexEntry(index=2, name="Category", normalized_name="category", source_column_letter="C", semantic_type=SemanticTypeEnum.CATEGORICAL, data_type=DataTypeEnum.STRING),
        ColumnIndexEntry(index=3, name="Sales", normalized_name="sales", source_column_letter="D", semantic_type=SemanticTypeEnum.NUMERIC_MEASURE, data_type=DataTypeEnum.FLOAT),
        ColumnIndexEntry(index=4, name="Profit", normalized_name="profit", source_column_letter="E", semantic_type=SemanticTypeEnum.NUMERIC_MEASURE, data_type=DataTypeEnum.FLOAT),
    ]

    table_entry = TableIndexEntry(
        table_id="tbl_orders",
        sheet_name="Orders",
        name="Orders_Table",
        range_address="A1:E6",
        header_range="A1:E1",
        data_range="A2:E6",
        header_row_index=1,
        row_count=5,
        column_count=5,
        columns=columns,
    )

    sheet_entry = SheetIndexEntry(
        name="Orders",
        index=0,
        total_rows=6,
        total_columns=5,
        used_range="A1:E6",
        tables=[table_entry],
    )

    wb_index = WorkbookMetadataIndex(
        dataset_id="ds_test_p18_superstore",
        filename="Superstore_P18.xlsx",
        sheet_count=1,
        sheet_names=["Orders"],
        active_sheet_name="Orders",
        sheets={"Orders": sheet_entry},
    )

    return wb_index, grid


class TestPhase18NaturalLanguageTransactionControl:
    """Tests 1-7: Natural Language UNDO, REDO, CANCEL, NO-OP, and INSPECTION."""

    def test_undo_command_english(self, superstore_sample_workbook):
        wb_index, grid = superstore_sample_workbook
        orchestrator = AgentOrchestrator()
        # Step 1: Execute mutation
        res1 = orchestrator.process_request("total sales in D8", wb_index, grid)
        assert res1.status == AgentResponseStatusEnum.SUCCESS
        assert grid.get_cell(8, 4).formula == "=SUM(D2:D6)"

        # Step 2: Natural language undo
        res_undo = orchestrator.process_request("please undo", wb_index, grid)
        assert res_undo.status == AgentResponseStatusEnum.ROLLBACK_SUCCESS
        assert grid.get_cell(8, 4).is_empty
        assert "Undone" in res_undo.message or "reverted" in res_undo.message

    def test_indonesian_undo(self, superstore_sample_workbook):
        wb_index, grid = superstore_sample_workbook
        orchestrator = AgentOrchestrator()
        res1 = orchestrator.process_request("total profit di E8", wb_index, grid)
        assert res1.status == AgentResponseStatusEnum.SUCCESS
        assert grid.get_cell(8, 5).formula == "=SUM(E2:E6)"

        res_undo = orchestrator.process_request("batalkan perubahan terakhir", wb_index, grid)
        assert res_undo.status == AgentResponseStatusEnum.ROLLBACK_SUCCESS
        assert grid.get_cell(8, 5).is_empty
        assert "dibatalkan" in res_undo.message

    def test_redo_command_english_and_indonesian(self, superstore_sample_workbook):
        wb_index, grid = superstore_sample_workbook
        orchestrator = AgentOrchestrator()
        # Execute -> Undo -> Redo
        orchestrator.process_request("total sales di D8", wb_index, grid)
        orchestrator.process_request("undo", wb_index, grid)
        assert grid.get_cell(8, 4).is_empty

        res_redo = orchestrator.process_request("redo", wb_index, grid)
        assert res_redo.status == AgentResponseStatusEnum.SUCCESS
        assert grid.get_cell(8, 4).formula == "=SUM(D2:D6)"
        assert "Redone" in res_redo.message or "reapplied" in res_redo.message

    def test_cancel_command(self, superstore_sample_workbook):
        wb_index, grid = superstore_sample_workbook
        orchestrator = AgentOrchestrator()
        res = orchestrator.process_request("cancel operation", wb_index, grid)
        assert res.status == AgentResponseStatusEnum.SUCCESS
        assert "cancelled" in res.message.lower() or "dibatalkan" in res.message.lower()

    def test_no_op_undo_and_redo(self, superstore_sample_workbook):
        wb_index, grid = superstore_sample_workbook
        orchestrator = AgentOrchestrator()
        res_undo = orchestrator.process_request("undo", wb_index, grid)
        assert res_undo.status == AgentResponseStatusEnum.ROLLBACK_FAILURE
        assert "nothing to undo" in res_undo.message.lower() or "tidak ada" in res_undo.message.lower()

        res_redo = orchestrator.process_request("redo", wb_index, grid)
        assert res_redo.status == AgentResponseStatusEnum.SUCCESS
        assert "nothing to redo" in res_redo.message.lower() or "tidak ada" in res_redo.message.lower()

    def test_inspection_command_what_did_you_change(self, superstore_sample_workbook):
        wb_index, grid = superstore_sample_workbook
        orchestrator = AgentOrchestrator()
        orchestrator.process_request("total sales di D8", wb_index, grid)

        res_inspect = orchestrator.process_request("what did you change?", wb_index, grid)
        assert res_inspect.status == AgentResponseStatusEnum.SUCCESS
        assert "D8" in res_inspect.message
        assert "=SUM(D2:D6)" in res_inspect.message


class TestPhase18MultiIntentAndTargeting:
    """Tests 8-12: Multi-Intent composition, explicit destination priority, minimal mutation."""

    def test_multi_intent_label_and_formula(self, superstore_sample_workbook):
        wb_index, grid = superstore_sample_workbook
        orchestrator = AgentOrchestrator()
        # "total sales di D8 dengan label TOTAL di C8"
        res = orchestrator.process_request(
            "total sales di D8 dengan label TOTAL di C8",
            wb_index,
            grid,
        )
        assert res.status == AgentResponseStatusEnum.SUCCESS
        assert grid.get_cell(8, 3).parsed_value == "TOTAL"
        assert grid.get_cell(8, 4).formula == "=SUM(D2:D6)"

        # Verify atomic undo reverts BOTH label and formula in one single step
        res_undo = orchestrator.process_request("undo", wb_index, grid)
        assert res_undo.status == AgentResponseStatusEnum.ROLLBACK_SUCCESS
        assert grid.get_cell(8, 3).is_empty
        assert grid.get_cell(8, 4).is_empty

    def test_multi_intent_formula_label_and_currency_format(self, superstore_sample_workbook):
        wb_index, grid = superstore_sample_workbook
        actions, status, _, msg = SpreadsheetAgentPlanner.plan_agent_actions(
            "total profit in N20, label it Total Profit in M20, and format N20 as currency",
            wb_index,
            grid,
        )
        assert status == AgentResponseStatusEnum.SUCCESS
        assert len(actions) == 3
        assert actions[0].action_type == ActionTypeEnum.WRITE_VALUE
        assert actions[0].target_cell == "M20"
        assert actions[0].value == "Total Profit"
        assert actions[1].action_type == ActionTypeEnum.WRITE_FORMULA
        assert actions[1].target_cell == "N20"
        assert actions[1].formula == "=SUM(E2:E6)"
        assert actions[2].action_type == ActionTypeEnum.SET_NUMBER_FORMAT
        assert actions[2].target_cell == "N20"

    def test_explicit_destination_overrides_selected_cell(self, superstore_sample_workbook):
        wb_index, grid = superstore_sample_workbook
        actions, status, _, _ = SpreadsheetAgentPlanner.plan_agent_actions(
            "total sales in N20",
            wb_index,
            grid,
            selected_range="D8",
        )
        assert status == AgentResponseStatusEnum.SUCCESS
        assert len(actions) == 1
        assert actions[0].target_cell == "N20"

    def test_selected_cell_destination_when_no_explicit_coord(self, superstore_sample_workbook):
        wb_index, grid = superstore_sample_workbook
        actions, status, _, _ = SpreadsheetAgentPlanner.plan_agent_actions(
            "calculate total sales",
            wb_index,
            grid,
            selected_range="D10",
        )
        assert status == AgentResponseStatusEnum.SUCCESS
        assert len(actions) == 1
        assert actions[0].target_cell == "D10"

    def test_minimal_mutation_single_formula_write(self, superstore_sample_workbook):
        wb_index, grid = superstore_sample_workbook
        actions, status, _, _ = SpreadsheetAgentPlanner.plan_agent_actions(
            "calculate total sales in D10",
            wb_index,
            grid,
        )
        assert status == AgentResponseStatusEnum.SUCCESS
        assert len(actions) == 1
        assert actions[0].action_type == ActionTypeEnum.WRITE_FORMULA
        assert actions[0].target_cell == "D10"


class TestPhase18MetricResolutionAndInspection:
    """Tests 13-16: Missing metric handling, semantic aliases, dataset explanation, cell inspection."""

    def test_missing_metric_rejection_no_silent_fallback(self, superstore_sample_workbook):
        wb_index, grid = superstore_sample_workbook
        actions, status, _, msg = SpreadsheetAgentPlanner.plan_agent_actions(
            "calculate total discount",
            wb_index,
            grid,
        )
        assert status == AgentResponseStatusEnum.UNSUPPORTED
        assert "discount" in msg.lower()
        assert "Sales" in msg and "Profit" in msg

    def test_metric_semantic_resolution_profit(self, superstore_sample_workbook):
        wb_index, grid = superstore_sample_workbook
        actions, status, _, msg = SpreadsheetAgentPlanner.plan_agent_actions(
            "hitung total keuntungan di E8",
            wb_index,
            grid,
        )
        assert status == AgentResponseStatusEnum.SUCCESS
        assert actions[0].formula == "=SUM(E2:E6)"
        assert "Profit" in msg or "keuntungan" in msg.lower()

    def test_dataset_explanation_factual_and_zero_mutations(self, superstore_sample_workbook):
        wb_index, grid = superstore_sample_workbook
        actions, status, _, msg = SpreadsheetAgentPlanner.plan_agent_actions(
            "ini sebenarnya data apa sih?",
            wb_index,
            grid,
        )
        assert status == AgentResponseStatusEnum.SUCCESS
        assert len(actions) == 0
        assert "5 baris" in msg or "5" in msg
        assert "Sales" in msg and "Profit" in msg

    def test_cell_inspection_returns_value_and_formula(self, superstore_sample_workbook):
        wb_index, grid = superstore_sample_workbook
        actions, status, _, msg = SpreadsheetAgentPlanner.plan_agent_actions(
            "apa yang ada di D2?",
            wb_index,
            grid,
        )
        assert status == AgentResponseStatusEnum.SUCCESS
        assert len(actions) == 0
        assert "100" in msg


class TestPhase18AnalyticalInquiries:
    """Tests 17-20: Extremes, Superlatives, and Cross-Dimensional Partitioning."""

    def test_highest_sales_scalar_extreme(self, superstore_sample_workbook):
        wb_index, grid = superstore_sample_workbook
        # In grid: Sales are 100, 50, 200, 80, 30 -> max is 200.0
        actions, status, _, msg = SpreadsheetAgentPlanner.plan_agent_actions(
            "berapa sales terbesar?",
            wb_index,
            grid,
        )
        assert status == AgentResponseStatusEnum.SUCCESS
        assert len(actions) == 0
        assert "200.00" in msg

    def test_top_region_by_sales(self, superstore_sample_workbook):
        wb_index, grid = superstore_sample_workbook
        # East: 200 + 80 = 280; West: 100 + 50 = 150; South: 30 -> East is highest
        actions, status, _, msg = SpreadsheetAgentPlanner.plan_agent_actions(
            "region mana dengan sales tertinggi?",
            wb_index,
            grid,
        )
        assert status == AgentResponseStatusEnum.SUCCESS
        assert len(actions) == 0
        assert "East" in msg
        assert "280.00" in msg

    def test_bottom_region_by_sales(self, superstore_sample_workbook):
        wb_index, grid = superstore_sample_workbook
        # South: 30 -> lowest
        actions, status, _, msg = SpreadsheetAgentPlanner.plan_agent_actions(
            "region mana dengan sales terendah?",
            wb_index,
            grid,
        )
        assert status == AgentResponseStatusEnum.SUCCESS
        assert len(actions) == 0
        assert "South" in msg
        assert "30.00" in msg

    def test_highest_category_per_region_cross_dimensional(self, superstore_sample_workbook):
        wb_index, grid = superstore_sample_workbook
        # West: Tech=100, Furn=50 -> Tech
        # East: Furn=200, Tech=80 -> Furn
        # South: Office=30 -> Office
        actions, status, _, msg = SpreadsheetAgentPlanner.plan_agent_actions(
            "category dengan sales tertinggi di setiap region",
            wb_index,
            grid,
        )
        assert status == AgentResponseStatusEnum.SUCCESS
        assert len(actions) == 0
        assert "West: Technology" in msg
        assert "East: Furniture" in msg


class TestPhase18WorkbookCompletion:
    """Tests 21-24: Controlled completion, atomic rollback, collision protection, no fake charts."""

    def test_workbook_completion_planning(self, superstore_sample_workbook):
        wb_index, grid = superstore_sample_workbook
        actions, status, _, msg = SpreadsheetAgentPlanner.plan_agent_actions(
            "selesaikan data ini",
            wb_index,
            grid,
        )
        assert status == AgentResponseStatusEnum.SUCCESS
        assert len(actions) >= 5
        # Summary row starts at row 8 (data ends at row 6)
        assert actions[0].target_cell == "A8"
        assert actions[0].value == "Ringkasan Analisis"

    def test_workbook_completion_transaction_rollback(self, superstore_sample_workbook):
        wb_index, grid = superstore_sample_workbook
        orchestrator = AgentOrchestrator()
        res_exec = orchestrator.process_request("selesaikan data ini", wb_index, grid)
        assert res_exec.status == AgentResponseStatusEnum.SUCCESS
        assert not grid.get_cell(8, 1).is_empty

        res_undo = orchestrator.process_request("batalkan", wb_index, grid)
        assert res_undo.status == AgentResponseStatusEnum.ROLLBACK_SUCCESS
        assert grid.get_cell(8, 1).is_empty
        assert grid.get_cell(9, 2).is_empty

    def test_occupied_cell_collision_protection(self, superstore_sample_workbook):
        wb_index, grid = superstore_sample_workbook
        # Cell D2 is occupied (Sales = 100)
        actions, status, req, msg = SpreadsheetAgentPlanner.plan_agent_actions(
            "total sales di D2",
            wb_index,
            grid,
        )
        assert status == AgentResponseStatusEnum.CLARIFICATION
        assert req is not None
        assert "sudah terisi data" in msg

    def test_no_fake_chart_execution(self, superstore_sample_workbook):
        wb_index, grid = superstore_sample_workbook
        # A calculation or completion request must NEVER produce fake chart actions
        actions, status, _, _ = SpreadsheetAgentPlanner.plan_agent_actions(
            "calculate total sales in D8",
            wb_index,
            grid,
        )
        assert status == AgentResponseStatusEnum.SUCCESS
        for act in actions:
            assert act.action_type != ActionTypeEnum.CREATE_CHART

    def test_total_profit_when_available(self, superstore_sample_workbook):
        wb_index, grid = superstore_sample_workbook
        actions, status, _, msg = SpreadsheetAgentPlanner.plan_agent_actions(
            "calculate total profit in E8",
            wb_index,
            grid,
        )
        assert status == AgentResponseStatusEnum.SUCCESS
        assert len(actions) == 1
        assert actions[0].formula == "=SUM(E2:E6)"
        assert "Profit" in msg

    def test_language_parity_en_id(self, superstore_sample_workbook):
        wb_index, grid = superstore_sample_workbook
        # Indonesian
        _, _, _, msg_id = SpreadsheetAgentPlanner.plan_agent_actions("total sales di D8", wb_index, grid)
        assert "Selesai" in msg_id and "dihitung" in msg_id

        # English
        _, _, _, msg_en = SpreadsheetAgentPlanner.plan_agent_actions("calculate total sales in D8", wb_index, grid)
        assert "Done" in msg_en and "calculated" in msg_en
