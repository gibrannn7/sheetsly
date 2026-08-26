"""Comprehensive unit and integration test suite for Phase 5:
Deterministic Grid Placement, Formula Pipeline Execution, Data Preservation & End-to-End Agent Scenario.
"""

import pytest

from app.engine.agent import (
    ActionTypeEnum,
    AgentResponseStatusEnum,
    FormattingStyle,
    FormulaEvaluator,
    GridMutator,
    PlacementPolicy,
    SpreadsheetAction,
    SpreadsheetAgentPlanner,
)
from app.engine.parser.sheet_reader import RawSheetGrid
from app.engine.profiler.workbook_index import (
    ColumnIndexEntry,
    SheetIndexEntry,
    TableIndexEntry,
    WorkbookMetadataIndex,
)
from app.models.schemas import CellCoordinate, CellData, DataTypeEnum, SemanticTypeEnum


def _create_test_environment(row_count: int = 10):
    """Builds a realistic test workbook with Orders and Customers sheets and populated RawSheetGrids."""
    cells_orders = {}
    
    # Headers on Row 1
    headers = ["OrderID", "CustomerName", "Region", "Sales", "Profit"]
    col_types = [DataTypeEnum.STRING, DataTypeEnum.STRING, DataTypeEnum.STRING, DataTypeEnum.FLOAT, DataTypeEnum.FLOAT]
    col_roles = [SemanticTypeEnum.IDENTIFIER, SemanticTypeEnum.TEXT, SemanticTypeEnum.CATEGORICAL, SemanticTypeEnum.NUMERIC_MEASURE, SemanticTypeEnum.NUMERIC_MEASURE]

    for c_idx, h in enumerate(headers, start=1):
        col_let = chr(ord("A") + c_idx - 1)
        cells_orders[(1, c_idx)] = CellData(
            coordinate=CellCoordinate(row=1, column=c_idx, cell_ref=f"{col_let}1", col_letter=col_let),
            original_value=h,
            parsed_value=h,
            data_type=DataTypeEnum.STRING,
            is_empty=False,
        )

    # Data Rows 2 to row_count+1
    sales_values = [100.0, 250.0, 150.0, 300.0, 50.0, 200.0, 400.0, 120.0, 80.0, 350.0]
    profit_values = [20.0, 50.0, 30.0, 60.0, 10.0, 40.0, 80.0, 24.0, 16.0, 70.0]

    for r in range(2, row_count + 2):
        s_val = sales_values[(r - 2) % len(sales_values)]
        p_val = profit_values[(r - 2) % len(profit_values)]
        cells_orders[(r, 1)] = CellData(coordinate=CellCoordinate(row=r, column=1, cell_ref=f"A{r}", col_letter="A"), original_value=f"ORD-{r}", parsed_value=f"ORD-{r}", data_type=DataTypeEnum.STRING, is_empty=False)
        cells_orders[(r, 2)] = CellData(coordinate=CellCoordinate(row=r, column=2, cell_ref=f"B{r}", col_letter="B"), original_value=f"Cust-{r}", parsed_value=f"Cust-{r}", data_type=DataTypeEnum.STRING, is_empty=False)
        cells_orders[(r, 3)] = CellData(coordinate=CellCoordinate(row=r, column=3, cell_ref=f"C{r}", col_letter="C"), original_value="East", parsed_value="East", data_type=DataTypeEnum.STRING, is_empty=False)
        cells_orders[(r, 4)] = CellData(coordinate=CellCoordinate(row=r, column=4, cell_ref=f"D{r}", col_letter="D"), original_value=s_val, parsed_value=s_val, data_type=DataTypeEnum.FLOAT, is_empty=False)
        cells_orders[(r, 5)] = CellData(coordinate=CellCoordinate(row=r, column=5, cell_ref=f"E{r}", col_letter="E"), original_value=p_val, parsed_value=p_val, data_type=DataTypeEnum.FLOAT, is_empty=False)

    grid_orders = RawSheetGrid(
        sheet_name="Orders", min_row=1, max_row=row_count + 1, min_col=1, max_col=5,
        cells=cells_orders,
    )

    # Mock Customers Grid
    grid_cust = RawSheetGrid(
        sheet_name="Customers", min_row=1, max_row=5, min_col=1, max_col=2,
        cells={
            (1, 1): CellData(coordinate=CellCoordinate(row=1, column=1, cell_ref="A1", col_letter="A"), original_value="ID", parsed_value="ID", data_type=DataTypeEnum.STRING, is_empty=False),
            (1, 2): CellData(coordinate=CellCoordinate(row=1, column=2, cell_ref="B1", col_letter="B"), original_value="Name", parsed_value="Name", data_type=DataTypeEnum.STRING, is_empty=False),
        }
    )

    # Column Metadata
    cols_meta = []
    for c_idx, (h, dt, sem) in enumerate(zip(headers, col_types, col_roles)):
        cols_meta.append(
            ColumnIndexEntry(
                index=c_idx,
                name=h,
                normalized_name=h.lower(),
                source_column_letter=chr(ord("A") + c_idx),
                data_type=dt,
                semantic_type=sem,
                total_count=row_count,
                unique_count=row_count,
                sample_values=[100.0, 250.0],
            )
        )

    tbl = TableIndexEntry(
        table_id="tbl_orders",
        name="Orders Data",
        sheet_name="Orders",
        range_address=f"A1:E{row_count+1}",
        header_range="A1:E1",
        data_range=f"A2:E{row_count+1}",
        row_count=row_count,
        column_count=5,
        columns=cols_meta,
    )

    sheet_orders = SheetIndexEntry(
        name="Orders", index=0, total_rows=row_count+1, total_columns=5,
        used_range=f"A1:E{row_count+1}", tables=[tbl],
    )
    sheet_cust = SheetIndexEntry(
        name="Customers", index=1, total_rows=5, total_columns=2,
        used_range="A1:B5", tables=[],
    )

    index = WorkbookMetadataIndex(
        dataset_id="ds_exec_test",
        filename="SalesData.xlsx",
        sheet_count=2,
        sheet_names=["Orders", "Customers"],
        active_sheet_name="Orders",
        sheets={"Orders": sheet_orders, "Customers": sheet_cust},
    )

    return index, grid_orders, grid_cust


# ============================================================================
# 1. END-TO-END CONCRETE USER SCENARIO
# ============================================================================

def test_e2e_user_scenario_buatkan_total_penjualan():
    """
    Test the primary user scenario: 'buatkan total penjualan'.
    Verifies intent resolution, safe placement, formula creation, independent Python calculation,
    physical grid mutation, and zero unintended side-effects.
    """
    index, grid_orders, grid_cust = _create_test_environment(row_count=10)

    # 1. Plan Agent Actions
    actions, status, req, msg = SpreadsheetAgentPlanner.plan_agent_actions(
        user_request="buatkan total penjualan",
        workbook_index=index,
        grid=grid_orders,
    )

    assert status == AgentResponseStatusEnum.SUCCESS
    assert req is None
    assert len(actions) >= 3  # Label + Formula + Format/NumberFormat

    # 2. Verify planned actions
    act_label = actions[0]
    act_formula = actions[1]

    assert act_label.action_type == ActionTypeEnum.WRITE_VALUE
    assert act_label.target_cell == "C12"  # Row 12 (10 data rows + 1 header + 1)
    assert "Total" in str(act_label.value)

    assert act_formula.action_type == ActionTypeEnum.WRITE_FORMULA
    assert act_formula.target_cell == "D12"
    assert act_formula.formula == "=SUM(D2:D11)"
    assert act_formula.expected_result == 2000.0  # Sum of [100, 250, 150, 300, 50, 200, 400, 120, 80, 350]

    # 3. Execute Sequence on Grid
    diffs, report = GridMutator.execute_sequence(actions, grid_orders, index)

    assert report.is_verified is True
    assert report.verified_expected_value == 2000.0
    assert report.actual_evaluated_value == 2000.0

    # 4. Verify Physical Grid State
    cell_d12 = grid_orders.get_cell(12, 4)
    assert cell_d12.formula == "=SUM(D2:D11)"
    assert cell_d12.parsed_value == 2000.0

    cell_c12 = grid_orders.get_cell(12, 3)
    assert cell_c12.original_value == "Total Sales"

    # 5. DATA PRESERVATION: Verify source data rows remain 100% intact
    for r in range(2, 12):
        assert grid_orders.get_cell(r, 4).is_empty is False
        assert grid_orders.get_cell(r, 1).original_value == f"ORD-{r}"

    # 6. MULTI-SHEET ISOLATION: Verify Customers sheet was 100% untouched
    assert len(grid_cust.cells) == 2
    assert (12, 4) not in grid_cust.cells


# ============================================================================
# 2. FORMULA EVALUATOR TESTS ACROSS ARITHMETIC PRIMITIVES
# ============================================================================

def test_formula_evaluator_all_functions():
    """Verify independent Python evaluation of SUM, AVERAGE, COUNT, COUNTA, MIN, MAX, MEDIAN."""
    _, grid, _ = _create_test_environment(row_count=10)

    # SUM
    val_sum, _ = FormulaEvaluator.evaluate("=SUM(D2:D11)", grid)
    assert val_sum == 2000.0

    # AVERAGE
    val_avg, _ = FormulaEvaluator.evaluate("=AVERAGE(D2:D11)", grid)
    assert val_avg == 200.0

    # COUNT
    val_cnt, _ = FormulaEvaluator.evaluate("=COUNT(D2:D11)", grid)
    assert val_cnt == 10

    # COUNTA
    val_cnta, _ = FormulaEvaluator.evaluate("=COUNTA(A2:A11)", grid)
    assert val_cnta == 10

    # MIN & MAX
    val_min, _ = FormulaEvaluator.evaluate("=MIN(D2:D11)", grid)
    assert val_min == 50.0

    val_max, _ = FormulaEvaluator.evaluate("=MAX(D2:D11)", grid)
    assert val_max == 400.0

    # MEDIAN
    val_med, _ = FormulaEvaluator.evaluate("=MEDIAN(D2:D11)", grid)
    assert val_med == 175.0  # Median of sorted [50, 80, 100, 120, 150, 200, 250, 300, 350, 400] -> (150+200)/2


# ============================================================================
# 3. PHYSICAL ROW & COLUMN INSERTION TESTS
# ============================================================================

def test_grid_insert_row_execution():
    """Verify INSERT_ROW shifts cells down correctly and preserves data."""
    _, grid, _ = _create_test_environment(row_count=5)
    initial_d3_val = grid.get_cell(3, 4).parsed_value

    act_ins_row = SpreadsheetAction(
        action_id="act_ins_r",
        action_type=ActionTypeEnum.INSERT_ROW,
        sheet_name="Orders",
        row_index=3,
    )
    GridMutator.execute_action(act_ins_row, grid)

    # Cell originally at D3 is now shifted to D4
    assert grid.get_cell(4, 4).parsed_value == initial_d3_val
    assert grid.total_rows == 7  # Initial 6 + 1


def test_grid_insert_column_execution():
    """Verify INSERT_COLUMN shifts cells right correctly."""
    _, grid, _ = _create_test_environment(row_count=5)
    initial_d2_val = grid.get_cell(2, 4).parsed_value

    act_ins_col = SpreadsheetAction(
        action_id="act_ins_c",
        action_type=ActionTypeEnum.INSERT_COLUMN,
        sheet_name="Orders",
        column_index=4,
    )
    GridMutator.execute_action(act_ins_col, grid)

    # Column 4 shifted to Column 5 (E)
    assert grid.get_cell(2, 5).parsed_value == initial_d2_val
    assert grid.total_cols == 6


# ============================================================================
# 4. PLACEMENT POLICY & EXPLICIT USER DESTINATIONS
# ============================================================================

def test_placement_policy_explicit_user_cell():
    """Verify user request with explicit cell destination (e.g. 'di cell H15') uses that cell."""
    index, grid, _ = _create_test_environment(row_count=10)
    tbl = index.sheets["Orders"].tables[0]
    sales_col = tbl.columns[3]

    placement = PlacementPolicy.determine_placement(
        table=tbl,
        measure_col=sales_col,
        grid=grid,
        query="buat total penjualan di cell H15",
    )
    assert placement.target_cell == "H15"
    assert placement.target_row == 15
    assert placement.target_col == 8
    assert placement.placement_type == "EXPLICIT_TARGET"


# ============================================================================
# 5. CLEAR CONTENT EXECUTION
# ============================================================================

def test_grid_clear_content_execution():
    """Verify CLEAR_CONTENT sets targeted cells to empty/null without affecting neighboring cells."""
    _, grid, _ = _create_test_environment(row_count=5)
    assert grid.get_cell(2, 4).is_empty is False

    act_clear = SpreadsheetAction(
        action_id="act_clr",
        action_type=ActionTypeEnum.CLEAR_CONTENT,
        sheet_name="Orders",
        target_cell="D2",
    )
    GridMutator.execute_action(act_clear, grid)

    assert grid.get_cell(2, 4).is_empty is True
    # Neighboring cells remain intact
    assert grid.get_cell(2, 3).is_empty is False
    assert grid.get_cell(3, 4).is_empty is False


# ============================================================================
# 6. MULTI-SHEET CROSS-SHEET FORMULA EVALUATION
# ============================================================================

def test_cross_sheet_formula_evaluation():
    """Verify formula referencing another worksheet '=SUM(Orders!D2:D11)' is evaluated accurately."""
    _, grid_orders, grid_cust = _create_test_environment(row_count=10)
    sheet_grids = {"Orders": grid_orders, "Customers": grid_cust}

    val, dt = FormulaEvaluator.evaluate("=SUM(Orders!D2:D11)", grid_cust, sheet_grids)
    assert val == 2000.0
    assert dt == DataTypeEnum.FLOAT


# ============================================================================
# 7. AMBIGUITY INTEGRATION & ZERO-MUTATION SAFETY
# ============================================================================

def test_competing_columns_triggers_clarification():
    """Verify when competing columns exist ('Sales' vs 'Net Sales'), clarification is requested and NO mutation occurs."""
    index, grid_orders, _ = _create_test_environment(row_count=10)
    tbl = index.sheets["Orders"].tables[0]

    # Add competing 'Net Sales' column
    col_net_sales = ColumnIndexEntry(
        index=5, name="Net Sales", normalized_name="net sales",
        source_column_letter="F", data_type=DataTypeEnum.FLOAT,
        semantic_type=SemanticTypeEnum.NUMERIC_MEASURE,
        total_count=10, unique_count=10, sample_values=[90.0, 240.0],
    )
    tbl.columns.append(col_net_sales)

    actions, status, req, _ = SpreadsheetAgentPlanner.plan_agent_actions(
        user_request="buatkan total penjualan",
        workbook_index=index,
        grid=grid_orders,
    )

    assert status == AgentResponseStatusEnum.CLARIFICATION
    assert req is not None
    assert len(actions) == 0  # Zero planned actions!
    assert "Sales" in req.options and "Net Sales" in req.options


# ============================================================================
# 8. NUMBER FORMAT INHERITANCE
# ============================================================================

def test_currency_number_format_inheritance():
    """Verify number format inherits currency symbol ($ vs Rp) deterministically."""
    col_usd = ColumnIndexEntry(
        index=0, name="Sales", normalized_name="sales", source_column_letter="D",
        data_type=DataTypeEnum.CURRENCY, semantic_type=SemanticTypeEnum.NUMERIC_MEASURE,
        total_count=10, unique_count=10, sample_values=["$100.00", "$250.00"],
    )
    assert PlacementPolicy._inherit_number_format(col_usd) == "$#,##0.00"

    col_idr = ColumnIndexEntry(
        index=1, name="Omset", normalized_name="omset", source_column_letter="E",
        data_type=DataTypeEnum.CURRENCY, semantic_type=SemanticTypeEnum.NUMERIC_MEASURE,
        total_count=10, unique_count=10, sample_values=["Rp100.000", "Rp250.000"],
    )
    assert PlacementPolicy._inherit_number_format(col_idr) == "Rp#,##0.00"

