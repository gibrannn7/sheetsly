"""Visualization API routes for deterministic chart generation, recommendation, and retrieval."""

from fastapi import APIRouter, HTTPException, Path
from fastapi.responses import FileResponse

from app.engine.analytics import AnalyticalResult, analytical_engine
from app.engine.visualization import (
    ChartRecommendation,
    InstructionVisualizationRequest,
    VisualizationEngine,
    VisualizationRequest,
    VisualizationResponse,
    visualization_engine,
)

router = APIRouter(tags=["Visualization Engine"])


@router.post("/datasets/{dataset_id}/visualize", response_model=VisualizationResponse)
async def generate_chart_from_result(
    dataset_id: str = Path(..., description="Target dataset UUID"),
    request: VisualizationRequest = ...,
) -> VisualizationResponse:
    """
    Renders a deterministic chart from a verified AnalyticalResult payload.
    Validates compatibility against requested chart type and returns chart metadata + image URL.
    """
    request.dataset_id = dataset_id
    return visualization_engine.render(request)


@router.post("/datasets/{dataset_id}/visualize/from-instruction", response_model=VisualizationResponse)
async def generate_chart_from_instruction(
    dataset_id: str = Path(..., description="Target dataset UUID"),
    request: InstructionVisualizationRequest = ...,
) -> VisualizationResponse:
    """
    Executes an AnalyticalInstruction via the AnalyticalEngine, and immediately passes the verified
    AnalyticalResult to the VisualizationEngine to generate a chart.
    """
    request.instruction.dataset_id = dataset_id
    # Step 1: Execute deterministically
    analytical_result = analytical_engine.execute(request.instruction)

    # Step 2: Render presentation chart
    viz_request = VisualizationRequest(
        dataset_id=dataset_id,
        analytical_result=analytical_result,
        chart_type=request.chart_type,
        title=request.title,
        include_base64=request.include_base64,
    )
    return visualization_engine.render(viz_request)


@router.post("/visualization/recommend", response_model=ChartRecommendation)
async def recommend_chart(
    result: AnalyticalResult = ...,
) -> ChartRecommendation:
    """
    Deterministically recommends the preferred chart type and lists all compatible chart types
    for a given AnalyticalResult.
    """
    return visualization_engine.recommend(result)


@router.get("/datasets/{dataset_id}/charts/{chart_id}/image")
async def get_chart_image(
    dataset_id: str = Path(..., description="Target dataset UUID"),
    chart_id: str = Path(..., description="Unique chart identifier"),
):
    """
    Serves the static PNG image artifact for a generated chart.
    """
    chart_path = visualization_engine.get_chart_file(chart_id, dataset_id=dataset_id)
    if not chart_path or not chart_path.exists():
        raise HTTPException(status_code=404, detail=f"Chart artifact '{chart_id}' not found.")

    return FileResponse(chart_path, media_type="image/png", filename=f"{chart_id}.png")
