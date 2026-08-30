"""Phase 14 Test Suite — Spreadsheet Workspace UX, Agent Interaction & Grid Capability Enhancement."""

import pytest
from app.engine.agent.action_model import ActionTypeEnum, FormattingStyle, SpreadsheetAction
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
def mock_grid_and_index():
    cells = {}
    # Header row
    cells[(1, 1)] = CellData(coordinate=CellCoordinate(row=1, column=1, cell_ref="A1", col_letter="A"), data_type=DataTypeEnum.STRING, original_value="OrderID", parsed_value="OrderID", is_empty=False)
    cells[(1, 2)] = CellData(coordinate=CellCoordinate(row=1, column=2, cell_ref="B1", col_letter="B"), data_type=DataTypeEnum.STRING, original_value="Region", parsed_value="Region", is_empty=False)
    cells[(1, 3)] = CellData(coordinate=CellCoordinate(row=1, column=3, cell_ref="C1", col_letter="C"), data_type=DataTypeEnum.STRING, original_value="Sales", parsed_value="Sales", is_empty=False)
    cells[(1, 4)] = CellData(coordinate=CellCoordinate(row=1, column=4, cell_ref="D1", col_letter="D"), data_type=DataTypeEnum.STRING, original_value="Profit", parsed_value="Profit", is_empty=False)
    cells[(1, 5)] = CellData(coordinate=CellCoordinate(row=1, column=5, cell_ref="E1", col_letter="E"), data_type=DataTypeEnum.STRING, original_value="Margin", parsed_value="Margin", is_empty=False)

    # Data rows 2..11
    for r in range(2, 12):
        cells[(r, 1)] = CellData(coordinate=CellCoordinate(row=r, column=1, cell_ref=f"A{r}", col_letter="A"), data_type=DataTypeEnum.INTEGER, original_value=r - 1, parsed_value=r - 1, is_empty=False)
        cells[(r, 2)] = CellData(coordinate=CellCoordinate(row=r, column=2, cell_ref=f"B{r}", col_letter="B"), data_type=DataTypeEnum.STRING, original_value="East" if r % 2 == 0 else "West", parsed_value="East" if r % 2 == 0 else "West", is_empty=False)
        cells[(r, 3)] = CellData(coordinate=CellCoordinate(row=r, column=3, cell_ref=f"C{r}", col_letter="C"), data_type=DataTypeEnum.FLOAT, original_value=float(r * 100), parsed_value=float(r * 100), is_empty=False)
        cells[(r, 4)] = CellData(coordinate=CellCoordinate(row=r, column=4, cell_ref=f"D{r}", col_letter="D"), data_type=DataTypeEnum.FLOAT, original_value=float(r * 20), parsed_value=float(r * 20), is_empty=False)
        cells[(r, 5)] = CellData(coordinate=CellCoordinate(row=r, column=5, cell_ref=f"E{r}", col_letter="E"), data_type=DataTypeEnum.FLOAT, original_value=0.2, parsed_value=0.2, is_empty=False)

    grid = RawSheetGrid(sheet_name="Orders", min_row=1, max_row=15, min_col=1, max_col=5, cells=cells)

    columns = [
        ColumnIndexEntry(index=0, name="OrderID", normalized_name="orderid", source_column_letter="A", semantic_type=SemanticTypeEnum.IDENTIFIER, data_type=DataTypeEnum.INTEGER),
        ColumnIndexEntry(index=1, name="Region", normalized_name="region", source_column_letter="B", semantic_type=SemanticTypeEnum.CATEGORICAL, data_type=DataTypeEnum.STRING),
        ColumnIndexEntry(index=2, name="Sales", normalized_name="sales", source_column_letter="C", semantic_type=SemanticTypeEnum.NUMERIC_MEASURE, data_type=DataTypeEnum.FLOAT),
        ColumnIndexEntry(index=3, name="Profit", normalized_name="profit", source_column_letter="D", semantic_type=SemanticTypeEnum.NUMERIC_MEASURE, data_type=DataTypeEnum.FLOAT),
        ColumnIndexEntry(index=4, name="Margin", normalized_name="margin", source_column_letter="E", semantic_type=SemanticTypeEnum.NUMERIC_MEASURE, data_type=DataTypeEnum.FLOAT),
    ]

    table_entry = TableIndexEntry(
        table_id="tbl_orders_1",
        sheet_name="Orders",
        name="Orders_Table",
        range_address="A1:E11",
        header_range="A1:E1",
        data_range="A2:E11",
        header_row_index=1,
        row_count=10,
        column_count=5,
        columns=columns,
    )

    sheet_entry = SheetIndexEntry(
        name="Orders",
        index=0,
        total_rows=15,
        total_columns=5,
        used_range="A1:E11",
        tables=[table_entry],
    )

    index = WorkbookMetadataIndex(
        dataset_id="ds_phase14_test",
        filename="Store.xlsx",
        sheet_count=1,
        sheet_names=["Orders"],
        active_sheet_name="Orders",
        sheets={"Orders": sheet_entry},
    )

    return grid, index


def test_agent_explicit_range_targeting(mock_grid_and_index):
    grid, index = mock_grid_and_index

    # User passes explicit range in prompt
    actions, status, req, msg = SpreadsheetAgentPlanner.plan_agent_actions(
        user_request="buatkan total dari C2:C11",
        workbook_index=index,
        grid=grid,
        active_sheet_name="Orders",
    )
    assert status == AgentResponseStatusEnum.SUCCESS
    assert len(actions) >= 1
    formula_act = next(a for a in actions if a.action_type == ActionTypeEnum.WRITE_FORMULA)
    assert formula_act.formula == "=SUM(C2:C11)"
    # Sum of 200 + 300 + ... + 1100 = 6500.0
    assert formula_act.expected_result == 6500.0


def test_agent_selected_range_propagation(mock_grid_and_index):
    grid, index = mock_grid_and_index

    # User selected range C2:C11 on UI
    actions, status, req, msg = SpreadsheetAgentPlanner.plan_agent_actions(
        user_request="hitung rata-rata",
        workbook_index=index,
        grid=grid,
        active_sheet_name="Orders",
        selected_range="C2:C11",
    )
    assert status == AgentResponseStatusEnum.SUCCESS
    formula_act = next(a for a in actions if a.action_type == ActionTypeEnum.WRITE_FORMULA)
    assert formula_act.formula == "=AVERAGE(C2:C11)"
    assert formula_act.expected_result == 650.0


def test_agent_formatting_bold_header(mock_grid_and_index):
    grid, index = mock_grid_and_index

    actions, status, req, msg = SpreadsheetAgentPlanner.plan_agent_actions(
        user_request="tebalkan header tabel ini",
        workbook_index=index,
        grid=grid,
        active_sheet_name="Orders",
    )
    assert status == AgentResponseStatusEnum.SUCCESS
    format_act = next(a for a in actions if a.action_type == ActionTypeEnum.FORMAT_RANGE)
    assert format_act.target_range == "A1:E1"
    assert format_act.style.bold is True

    # Execute via Orchestrator and test undo
    orch = AgentOrchestrator()
    res = orch.process_request(
        user_request="tebalkan header tabel ini",
        workbook_index=index,
        grid=grid,
        active_sheet_name="Orders",
    )
    assert res.status == AgentResponseStatusEnum.SUCCESS
    assert res.transaction is not None
    assert res.transaction.verification_report is not None
    assert res.transaction.verification_report.is_verified is True


def test_agent_formatting_currency(mock_grid_and_index):
    grid, index = mock_grid_and_index

    actions, status, req, msg = SpreadsheetAgentPlanner.plan_agent_actions(
        user_request="format kolom sales sebagai currency",
        workbook_index=index,
        grid=grid,
        active_sheet_name="Orders",
    )
    assert status == AgentResponseStatusEnum.SUCCESS
    num_fmt_act = next(a for a in actions if a.action_type == ActionTypeEnum.SET_NUMBER_FORMAT)
    assert num_fmt_act.target_range == "C2:C11"
    assert num_fmt_act.number_format in ["$#,##0.00", "Rp#,##0"]


def test_agent_explicit_destination_placement(mock_grid_and_index):
    grid, index = mock_grid_and_index

    actions, status, req, msg = SpreadsheetAgentPlanner.plan_agent_actions(
        user_request="buatkan total sales di N2",
        workbook_index=index,
        grid=grid,
        active_sheet_name="Orders",
    )
    assert status == AgentResponseStatusEnum.SUCCESS
    formula_act = next(a for a in actions if a.action_type == ActionTypeEnum.WRITE_FORMULA)
    assert formula_act.target_cell == "N2"
    assert formula_act.formula == "=SUM(C2:C11)"
    assert formula_act.expected_result == 6500.0


def test_agent_destination_collision_guard(mock_grid_and_index):
    grid, index = mock_grid_and_index

    # C5 is occupied by existing sales data (500.0)
    actions, status, req, msg = SpreadsheetAgentPlanner.plan_agent_actions(
        user_request="buatkan total sales di C5",
        workbook_index=index,
        grid=grid,
        active_sheet_name="Orders",
    )
    assert status == AgentResponseStatusEnum.CLARIFICATION
    assert req is not None
    assert "C5" in req.question


def test_agent_direct_formula_write_and_undo_on_empty_cell(mock_grid_and_index):
    grid, index = mock_grid_and_index

    # Formula bar write to virtual empty cell N2
    actions, status, req, msg = SpreadsheetAgentPlanner.plan_agent_actions(
        user_request="Tulis rumus =SUM(C2:C11) di N2",
        workbook_index=index,
        grid=grid,
        active_sheet_name="Orders",
    )
    assert status == AgentResponseStatusEnum.SUCCESS
    assert len(actions) == 1
    assert actions[0].action_type == ActionTypeEnum.WRITE_FORMULA
    assert actions[0].target_cell == "N2"
    assert actions[0].expected_result == 6500.0

    orch = AgentOrchestrator()
    res = orch.process_request(
        user_request="Tulis rumus =SUM(C2:C11) di N2",
        workbook_index=index,
        grid=grid,
        active_sheet_name="Orders",
    )
    assert res.status == AgentResponseStatusEnum.SUCCESS
    assert res.transaction is not None
    assert res.transaction.verification_report.is_verified is True

    # Cell N2 (row 2, col 14) is now populated
    cell_n2 = grid.get_cell(2, 14)
    assert cell_n2.parsed_value == 6500.0
    assert cell_n2.formula == "=SUM(C2:C11)"

    # Undo
    undo_res = orch.undo_last_transaction(grid=grid)
    assert undo_res.status == AgentResponseStatusEnum.ROLLBACK_SUCCESS
    # N2 is restored to empty
    cell_n2_restored = grid.get_cell(2, 14)
    assert cell_n2_restored.is_empty is True


def test_agent_direct_value_write_to_empty_cell(mock_grid_and_index):
    grid, index = mock_grid_and_index

    actions, status, req, msg = SpreadsheetAgentPlanner.plan_agent_actions(
        user_request="Tulis nilai 'Target Summary' di N1",
        workbook_index=index,
        grid=grid,
        active_sheet_name="Orders",
    )
    assert status == AgentResponseStatusEnum.SUCCESS
    assert len(actions) == 1
    assert actions[0].action_type == ActionTypeEnum.WRITE_VALUE
    assert actions[0].target_cell == "N1"
    assert actions[0].value == "Target Summary"

    orch = AgentOrchestrator()
    res = orch.process_request(
        user_request="Tulis nilai 'Target Summary' di N1",
        workbook_index=index,
        grid=grid,
        active_sheet_name="Orders",
    )
    assert res.status == AgentResponseStatusEnum.SUCCESS
    assert res.transaction.verification_report.is_verified is True
    cell_n1 = grid.get_cell(1, 14)
    assert cell_n1.parsed_value == "Target Summary"

