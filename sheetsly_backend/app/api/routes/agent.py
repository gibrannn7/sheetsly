"""FastAPI routes for Spreadsheet Agent actions, transactions, and undo operations."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.engine.agent import (
    AgentExecutionResult,
    AgentOrchestrator,
    AgentResponseStatusEnum,
    MemoryManager,
    TransactionAuditRecord,
    TransactionManager,
)
from app.engine.pipeline import IngestionPipeline

router = APIRouter(tags=["Spreadsheet Agent"])

# Global session orchestrator registry
_orchestrators: Dict[str, AgentOrchestrator] = {}


def get_or_create_orchestrator(dataset_id: str) -> AgentOrchestrator:
    if dataset_id not in _orchestrators:
        _orchestrators[dataset_id] = AgentOrchestrator(
            memory_manager=MemoryManager(),
            transaction_manager=TransactionManager(max_history=20),
        )
    return _orchestrators[dataset_id]


class AgentActionRequest(BaseModel):
    """Payload for submitting a natural language instruction to the Spreadsheet Agent."""
    model_config = {"protected_namespaces": ()}

    dataset_id: str = Field(..., description="Target dataset identifier")
    user_request: str = Field(..., description="User natural language request e.g. 'buatkan total penjualan'")
    active_sheet_name: Optional[str] = Field(None, description="Active sheet name")
    selected_range: Optional[str] = Field(None, description="Currently selected range e.g. 'A1:D10'")
    confirmation_context: Optional[Dict[str, Any]] = Field(None, description="User confirmation or choice from clarification")
    expected_version: Optional[int] = Field(None, description="Expected workbook version for concurrency safety")
    model_id: Optional[str] = Field(None, description="Optional active AI model identifier override")


class AgentUndoRequest(BaseModel):
    """Payload for requesting an undo of the last committed transaction."""

    dataset_id: str = Field(..., description="Target dataset identifier")
    active_sheet_name: Optional[str] = Field(None, description="Active sheet name")


class AgentRedoRequest(BaseModel):
    """Payload for requesting a redo of the last reverted transaction."""

    dataset_id: str = Field(..., description="Target dataset identifier")
    active_sheet_name: Optional[str] = Field(None, description="Active sheet name")


class AgentHistoryResponse(BaseModel):
    """Audit trail and undo/redo availability status for a dataset."""

    dataset_id: str
    current_version: int
    can_undo: bool
    can_redo: bool = False
    history: List[TransactionAuditRecord]


@router.post("/action", response_model=AgentExecutionResult)
async def execute_agent_action(request: AgentActionRequest) -> AgentExecutionResult:
    """
    Executes an end-to-end spreadsheet agent instruction:
    Plan -> Ambiguity Check -> Action Validation -> Transaction Execution -> Verification -> Commit / Rollback.
    """
    from app.engine.pipeline import ingestion_pipeline

    try:
        workbook_index = ingestion_pipeline.get_workbook_index(request.dataset_id)
        active_sheet = request.active_sheet_name or workbook_index.active_sheet_name
        grid = ingestion_pipeline.get_sheet_grid(request.dataset_id, active_sheet)
        sheet_grids = ingestion_pipeline._grids_cache.get(request.dataset_id, {active_sheet: grid})
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Dataset or sheet not found: {str(e)}")

    orchestrator = get_or_create_orchestrator(request.dataset_id)

    result = orchestrator.process_request(
        user_request=request.user_request,
        workbook_index=workbook_index,
        grid=grid,
        sheet_grids=sheet_grids,
        expected_version=request.expected_version,
        active_sheet_name=active_sheet,
        selected_range=request.selected_range,
    )

    return result


@router.post("/undo", response_model=AgentExecutionResult)
async def undo_agent_action(request: AgentUndoRequest) -> AgentExecutionResult:
    """
    Undoes the most recent committed transaction and restores grid state.
    """
    from app.engine.pipeline import ingestion_pipeline

    try:
        workbook_index = ingestion_pipeline.get_workbook_index(request.dataset_id)
        active_sheet = request.active_sheet_name or workbook_index.active_sheet_name
        grid = ingestion_pipeline.get_sheet_grid(request.dataset_id, active_sheet)
        sheet_grids = ingestion_pipeline._grids_cache.get(request.dataset_id, {active_sheet: grid})
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Dataset or sheet not found: {str(e)}")

    orchestrator = get_or_create_orchestrator(request.dataset_id)
    return orchestrator.undo_last(grid, sheet_grids)


@router.post("/redo", response_model=AgentExecutionResult)
async def redo_agent_action(request: AgentRedoRequest) -> AgentExecutionResult:
    """
    Redoes the most recent undone transaction and restores grid state.
    """
    from app.engine.pipeline import ingestion_pipeline

    try:
        workbook_index = ingestion_pipeline.get_workbook_index(request.dataset_id)
        active_sheet = request.active_sheet_name or workbook_index.active_sheet_name
        grid = ingestion_pipeline.get_sheet_grid(request.dataset_id, active_sheet)
        sheet_grids = ingestion_pipeline._grids_cache.get(request.dataset_id, {active_sheet: grid})
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Dataset or sheet not found: {str(e)}")

    orchestrator = get_or_create_orchestrator(request.dataset_id)
    return orchestrator.redo_last(grid, workbook_index, sheet_grids)


@router.get("/history/{dataset_id}", response_model=AgentHistoryResponse)
async def get_agent_history(dataset_id: str) -> AgentHistoryResponse:
    """
    Returns transaction audit history and undo/redo availability for a dataset.
    """
    orchestrator = get_or_create_orchestrator(dataset_id)
    return AgentHistoryResponse(
        dataset_id=dataset_id,
        current_version=orchestrator.tx_manager.current_version,
        can_undo=len(orchestrator.tx_manager.committed_transactions) > 0,
        can_redo=len(orchestrator.tx_manager.undone_transactions) > 0,
        history=orchestrator.tx_manager.history,
    )
