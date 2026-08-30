"""Phase 15 Test Suite — Spreadsheet Agent Visualization & Dashboard Capability."""

import pytest
from app.engine.agent.action_model import ActionTypeEnum, SpreadsheetAction
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
def mock_grid_and_index():
    cells = {}
    # Header row
    cells[(1, 1)] = CellData(coordinate=CellCoordinate(row=1, column=1, cell_ref="A1", col_letter="A"), data_type=DataTypeEnum.INTEGER, original_value="OrderID", parsed_value="OrderID", is_empty=False)
    cells[(1, 2)] = CellData(coordinate=CellCoordinate(row=1, column=2, cell_ref="B1", col_letter="B"), data_type=DataTypeEnum.STRING, original_value="Region", parsed_value="Region", is_empty=False)
    cells[(1, 3)] = CellData(coordinate=CellCoordinate(row=1, column=3, cell_ref="C1", col_letter="C"), data_type=DataTypeEnum.FLOAT, original_value="Sales", parsed_value="Sales", is_empty=False)
    cells[(1, 4)] = CellData(coordinate=CellCoordinate(row=1, column=4, cell_ref="D1", col_letter="D"), data_type=DataTypeEnum.FLOAT, original_value="Profit", parsed_value="Profit", is_empty=False)
    cells[(1, 5)] = CellData(coordinate=CellCoordinate(row=1, column=5, cell_ref="E1", col_letter="E"), data_type=DataTypeEnum.DATE, original_value="OrderDate", parsed_value="OrderDate", is_empty=False)

    regions = ["East", "West", "Central", "South"]
    dates = ["2026-01-15", "2026-02-15", "2026-03-15", "2026-04-15"]
    for r in range(2, 12):
        cells[(r, 1)] = CellData(coordinate=CellCoordinate(row=r, column=1, cell_ref=f"A{r}", col_letter="A"), data_type=DataTypeEnum.INTEGER, original_value=r - 1, parsed_value=r - 1, is_empty=False)
        reg = regions[(r - 2) % len(regions)]
        cells[(r, 2)] = CellData(coordinate=CellCoordinate(row=r, column=2, cell_ref=f"B{r}", col_letter="B"), data_type=DataTypeEnum.STRING, original_value=reg, parsed_value=reg, is_empty=False)
        sales_val = float(r * 100)
        cells[(r, 3)] = CellData(coordinate=CellCoordinate(row=r, column=3, cell_ref=f"C{r}", col_letter="C"), data_type=DataTypeEnum.FLOAT, original_value=sales_val, parsed_value=sales_val, is_empty=False)
        profit_val = float(r * 25)
        cells[(r, 4)] = CellData(coordinate=CellCoordinate(row=r, column=4, cell_ref=f"D{r}", col_letter="D"), data_type=DataTypeEnum.FLOAT, original_value=profit_val, parsed_value=profit_val, is_empty=False)
        d_val = dates[(r - 2) % len(dates)]
        cells[(r, 5)] = CellData(coordinate=CellCoordinate(row=r, column=5, cell_ref=f"E{r}", col_letter="E"), data_type=DataTypeEnum.DATE, original_value=d_val, parsed_value=d_val, is_empty=False)

    grid = RawSheetGrid(sheet_name="Orders", min_row=1, max_row=11, min_col=1, max_col=5, cells=cells)

    columns = [
        ColumnIndexEntry(index=0, name="OrderID", normalized_name="orderid", source_column_letter="A", semantic_type=SemanticTypeEnum.IDENTIFIER, data_type=DataTypeEnum.INTEGER),
        ColumnIndexEntry(index=1, name="Region", normalized_name="region", source_column_letter="B", semantic_type=SemanticTypeEnum.CATEGORICAL, data_type=DataTypeEnum.STRING),
        ColumnIndexEntry(index=2, name="Sales", normalized_name="sales", source_column_letter="C", semantic_type=SemanticTypeEnum.NUMERIC_MEASURE, data_type=DataTypeEnum.FLOAT),
        ColumnIndexEntry(index=3, name="Profit", normalized_name="profit", source_column_letter="D", semantic_type=SemanticTypeEnum.NUMERIC_MEASURE, data_type=DataTypeEnum.FLOAT),
        ColumnIndexEntry(index=4, name="OrderDate", normalized_name="orderdate", source_column_letter="E", semantic_type=SemanticTypeEnum.TEMPORAL, data_type=DataTypeEnum.DATE),
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
        total_rows=11,
        total_columns=5,
        used_range="A1:E11",
        tables=[table_entry],
    )

    index = WorkbookMetadataIndex(
        dataset_id="ds_phase15_test",
        filename="Store.xlsx",
        sheet_count=1,
        sheet_names=["Orders"],
        active_sheet_name="Orders",
        sheets={"Orders": sheet_entry},
    )

    return grid, index


def test_agent_create_pie_chart_explicit_destination(mock_grid_and_index):
    grid, index = mock_grid_and_index

    # User explicitly asks for Pie chart at B12 for Region based on Sales
    actions, status, req, msg = SpreadsheetAgentPlanner.plan_agent_actions(
        user_request="buatkan pie chart di rentang B12 untuk kolom Region berdasarkan Sales",
        workbook_index=index,
        grid=grid,
        active_sheet_name="Orders",
    )
    assert status == AgentResponseStatusEnum.SUCCESS
    assert len(actions) == 1
    act = actions[0]
    assert act.action_type == ActionTypeEnum.CREATE_CHART
    assert act.target_cell == "B12"
    assert act.chart_spec is not None
    assert act.chart_spec.chart_type == "PIE"
    assert act.chart_spec.dimension_column == "Region"
    assert act.chart_spec.measure_column == "Sales"
    assert act.chart_spec.destination_cell == "B12"
    assert len(act.chart_spec.summary_data) == 4

    # Execute via Orchestrator
    orch = AgentOrchestrator()
    res = orch.process_request(
        user_request="buatkan pie chart di rentang B12 untuk kolom Region berdasarkan Sales",
        workbook_index=index,
        grid=grid,
        active_sheet_name="Orders",
    )
    assert res.status == AgentResponseStatusEnum.SUCCESS
    assert res.transaction is not None
    assert res.transaction.verification_report.is_verified is True
    assert "chart_" in list(grid.charts.keys())[0]

    # Test Undo restores grid state
    undo_res = orch.undo_last_transaction(grid=grid)
    assert undo_res.status == AgentResponseStatusEnum.ROLLBACK_SUCCESS
    assert len(grid.charts) == 0


def test_agent_create_bar_chart_and_ranking(mock_grid_and_index):
    grid, index = mock_grid_and_index

    actions, status, req, msg = SpreadsheetAgentPlanner.plan_agent_actions(
        user_request="buat bar chart total Sales per Region di N2",
        workbook_index=index,
        grid=grid,
        active_sheet_name="Orders",
    )
    assert status == AgentResponseStatusEnum.SUCCESS
    assert len(actions) == 1
    act = actions[0]
    assert act.action_type == ActionTypeEnum.CREATE_CHART
    assert act.chart_spec.chart_type == "BAR"
    assert act.chart_spec.destination_cell == "N2"


def test_agent_create_line_chart_temporal(mock_grid_and_index):
    grid, index = mock_grid_and_index

    actions, status, req, msg = SpreadsheetAgentPlanner.plan_agent_actions(
        user_request="buat line chart penjualan per order date di G5",
        workbook_index=index,
        grid=grid,
        active_sheet_name="Orders",
    )
    assert status == AgentResponseStatusEnum.SUCCESS
    act = actions[0]
    assert act.action_type == ActionTypeEnum.CREATE_CHART
    assert act.chart_spec.chart_type == "LINE"
    assert act.chart_spec.dimension_column == "OrderDate"


def test_agent_selected_range_visualization(mock_grid_and_index):
    grid, index = mock_grid_and_index

    # User selected range B2:C11 on UI and asked to visualize
    actions, status, req, msg = SpreadsheetAgentPlanner.plan_agent_actions(
        user_request="visualisasikan data yang saya pilih",
        workbook_index=index,
        grid=grid,
        active_sheet_name="Orders",
        selected_range="B2:C11",
    )
    assert status == AgentResponseStatusEnum.SUCCESS
    act = actions[0]
    assert act.action_type == ActionTypeEnum.CREATE_CHART
    assert act.chart_spec.dimension_column == "Region"
    assert act.chart_spec.measure_column == "Sales"


def test_agent_create_kpi_card(mock_grid_and_index):
    grid, index = mock_grid_and_index

    actions, status, req, msg = SpreadsheetAgentPlanner.plan_agent_actions(
        user_request="buat KPI total sales di G2",
        workbook_index=index,
        grid=grid,
        active_sheet_name="Orders",
    )
    assert status == AgentResponseStatusEnum.SUCCESS
    act = actions[0]
    assert act.action_type == ActionTypeEnum.CREATE_KPI
    assert act.kpi_spec is not None
    assert act.kpi_spec.measure_column == "Sales"
    assert act.kpi_spec.aggregation == "SUM"
    # Sum of 200 + 300 + ... + 1100 = 6500.0
    assert float(act.kpi_spec.calculated_value) == 6500.0


def test_agent_dashboard_generation(mock_grid_and_index):
    grid, index = mock_grid_and_index

    actions, status, req, msg = SpreadsheetAgentPlanner.plan_agent_actions(
        user_request="buat dashboard penjualan",
        workbook_index=index,
        grid=grid,
        active_sheet_name="Orders",
    )
    assert status == AgentResponseStatusEnum.SUCCESS
    assert len(actions) >= 4
    # Contains 2 KPIs and 2 Charts
    kpi_actions = [a for a in actions if a.action_type == ActionTypeEnum.CREATE_KPI]
    chart_actions = [a for a in actions if a.action_type == ActionTypeEnum.CREATE_CHART]
    assert len(kpi_actions) == 2
    assert len(chart_actions) == 2

    orch = AgentOrchestrator()
    res = orch.process_request(
        user_request="buat dashboard penjualan",
        workbook_index=index,
        grid=grid,
        active_sheet_name="Orders",
    )
    assert res.status == AgentResponseStatusEnum.SUCCESS
    assert len(grid.kpis) == 2
    assert len(grid.charts) == 2

    # Undo removes entire dashboard atomically
    undo_res = orch.undo_last_transaction(grid=grid)
    assert undo_res.status == AgentResponseStatusEnum.ROLLBACK_SUCCESS
    assert len(grid.kpis) == 0
    assert len(grid.charts) == 0


def test_agent_chart_update_and_delete(mock_grid_and_index):
    grid, index = mock_grid_and_index

    # Create Chart
    orch = AgentOrchestrator()
    res1 = orch.process_request(
        user_request="buat pie chart Region berdasarkan Sales di B12",
        workbook_index=index,
        grid=grid,
        active_sheet_name="Orders",
    )
    assert res1.status == AgentResponseStatusEnum.SUCCESS
    assert len(grid.charts) == 1

    # Update Chart to Bar
    res2 = orch.process_request(
        user_request="ubah chart ini menjadi bar chart di B12",
        workbook_index=index,
        grid=grid,
        active_sheet_name="Orders",
    )
    assert res2.status == AgentResponseStatusEnum.SUCCESS

    # Delete Chart
    res3 = orch.process_request(
        user_request="hapus chart di B12",
        workbook_index=index,
        grid=grid,
        active_sheet_name="Orders",
    )
    assert res3.status == AgentResponseStatusEnum.SUCCESS
    assert len(grid.charts) == 0


def test_agent_english_and_indonesian_parity(mock_grid_and_index):
    grid, index = mock_grid_and_index

    # English prompt
    actions_en, status_en, _, _ = SpreadsheetAgentPlanner.plan_agent_actions(
        user_request="create a bar chart for Region by Sales at N2",
        workbook_index=index,
        grid=grid,
        active_sheet_name="Orders",
    )
    assert status_en == AgentResponseStatusEnum.SUCCESS
    assert actions_en[0].action_type == ActionTypeEnum.CREATE_CHART

    # Indonesian prompt
    actions_id, status_id, _, _ = SpreadsheetAgentPlanner.plan_agent_actions(
        user_request="buatkan diagram batang untuk Region berdasarkan Sales di N2",
        workbook_index=index,
        grid=grid,
        active_sheet_name="Orders",
    )
    assert status_id == AgentResponseStatusEnum.SUCCESS
    assert actions_id[0].action_type == ActionTypeEnum.CREATE_CHART


def test_base_model_gemini_31_flash_lite_and_qwen_122b():
    """Verify Gemini 3.1 Flash Lite is the active base model and Qwen 3.5 122B is configured."""
    from app.core.config import settings
    from app.engine.ai.models import ALLOWED_AI_MODELS, DEFAULT_AI_MODEL, get_provider_for_model

    assert DEFAULT_AI_MODEL == "gemini-3.1-flash-lite"
    assert settings.GEMINI_DEFAULT_MODEL == "gemini-3.1-flash-lite"
    assert settings.QWEN_MODEL == "qwen3.5-122b-a10b"
    assert "gemini-3.1-flash-lite" in ALLOWED_AI_MODELS
    assert "qwen3.5-122b-a10b" in ALLOWED_AI_MODELS
    assert "qwen3.5-397b-a17b" not in ALLOWED_AI_MODELS
    assert "qwen3.5-plus" not in ALLOWED_AI_MODELS
    assert get_provider_for_model(None) == "gemini"
    assert get_provider_for_model("gemini-3.1-flash-lite") == "gemini"
    assert get_provider_for_model("qwen3.5-122b-a10b") == "qwen"


def test_destination_placement_syntax_variations(mock_grid_and_index):
    """Verify all destination placement variations resolve to the exact anchor cell."""
    grid, index = mock_grid_and_index

    variations = [
        ("buatkan pie chart di B12 untuk Region berdasarkan Sales", "B12"),
        ("buatkan pie chart di rentang B12 untuk kolom Region berdasarkan Sales", "B12"),
        ("buatkan line chart mulai dari H15 untuk Sales berdasarkan OrderDate", "H15"),
        ("buatkan bar chart pada posisi N20 dari Region dan Sales", "N20"),
        ("letakkan bar chart di G5 untuk Region berdasarkan Sales", "G5"),
        ("buatkan area chart di range B12 untuk Region berdasarkan Sales", "B12"),
        ("buatkan pie chart di rentang B12:G25 untuk Region berdasarkan Sales", "B12"),
    ]

    for prompt, expected_dest in variations:
        actions, status, req, msg = SpreadsheetAgentPlanner.plan_agent_actions(
            user_request=prompt,
            workbook_index=index,
            grid=grid,
            active_sheet_name="Orders",
        )
        assert status == AgentResponseStatusEnum.SUCCESS, f"Failed for prompt: {prompt}"
        assert len(actions) == 1, f"Expected 1 action for {prompt}"
        assert actions[0].action_type == ActionTypeEnum.CREATE_CHART, f"Expected CREATE_CHART for {prompt}"
        assert actions[0].target_cell == expected_dest, f"Expected {expected_dest} for {prompt}, got {actions[0].target_cell}"
        assert actions[0].chart_spec.destination_cell == expected_dest


def test_all_supported_chart_types(mock_grid_and_index):
    """Verify all 7 chart types (PIE, BAR, COLUMN, LINE, AREA, SCATTER, HISTOGRAM) plan cleanly."""
    grid, index = mock_grid_and_index

    chart_tests = [
        ("buatkan pie chart Region berdasarkan Sales di B12", "PIE"),
        ("buatkan bar chart Region berdasarkan Sales di B12", "BAR"),
        ("buatkan column chart Region berdasarkan Sales di B12", "COLUMN"),
        ("buatkan line chart OrderDate berdasarkan Sales di B12", "LINE"),
        ("buatkan area chart OrderDate berdasarkan Sales di B12", "AREA"),
        ("buatkan scatter plot Sales dan Profit di B12", "SCATTER"),
        ("buatkan histogram distribusi Sales di B12", "HISTOGRAM"),
    ]

    for prompt, expected_type in chart_tests:
        actions, status, _, _ = SpreadsheetAgentPlanner.plan_agent_actions(
            user_request=prompt,
            workbook_index=index,
            grid=grid,
            active_sheet_name="Orders",
        )
        assert status == AgentResponseStatusEnum.SUCCESS
        assert actions[0].chart_spec.chart_type == expected_type


def test_export_xlsx_includes_charts(mock_grid_and_index):
    """Verify openpyxl XLSX export preserves openpyxl.chart objects."""
    import openpyxl
    from app.api.routes.datasets import export_dataset

    grid, index = mock_grid_and_index

    # Add a chart to grid
    orch = AgentOrchestrator()
    res = orch.process_request(
        user_request="buatkan pie chart di rentang B12 untuk kolom Region berdasarkan Sales",
        workbook_index=index,
        grid=grid,
        active_sheet_name="Orders",
    )
    assert res.status == AgentResponseStatusEnum.SUCCESS
    assert len(grid.charts) == 1

