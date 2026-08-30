"""Central AI Orchestrator coordinating natural language query planning, guardrail validation, execution, visualization, and explanation."""

import json
import logging
import re
import time
from typing import List, Optional, Tuple

from app.core.config import settings
from app.engine.ai.client import ai_client, gemini_client, qwen_client
from app.engine.ai.explainer import evidence_explainer
from app.engine.ai.guardrail import ai_guardrail
from app.engine.ai.models import (
    AIQueryStatus,
    ClarificationRequest,
    DEFAULT_AI_MODEL,
    NaturalLanguageQueryRequest,
    NaturalLanguageQueryResponse,
    QueryPlanOnlyResponse,
    SuggestedQueriesResponse,
    TimingBreakdown,
)
from app.engine.ai.planner import query_planner
from app.engine.ai.prompts import SUGGESTION_PROMPT
from app.engine.analytics.engine import analytical_engine
from app.engine.analytics.instruction_model import (
    AggregationOpEnum,
    AggregationSpec,
    AnalyticalInstruction,
    OperationEnum,
    SortSpec,
)
from app.engine.pipeline import ingestion_pipeline
from app.engine.visualization.chart_model import VisualizationRequest
from app.engine.visualization.engine import visualization_engine
from app.models.schemas import DataTypeEnum, SemanticTypeEnum, TableRegion
from app.storage.file_manager import file_manager

logger = logging.getLogger("sheetsly.ai.orchestrator")


class SheetResolutionError(Exception):
    """Raised when a specific sheet is requested in the query or parameter but not found in workbook."""
    def __init__(self, requested_sheet: str, available_sheets: List[str]):
        super().__init__(f"Sheet '{requested_sheet}' not found in workbook.")
        self.requested_sheet = requested_sheet
        self.available_sheets = available_sheets


class AIOrchestrator:
    """Coordinates end-to-end natural-language analytical query workflows."""

    def _build_workbook_summary(self, dataset_id: str) -> str:
        """Generates concise structural summary of all sheets and detected tables in the workbook."""
        try:
            overview = ingestion_pipeline.get_overview(dataset_id)
            if not overview or not overview.sheets:
                return ""
            lines = []
            for s in overview.sheets:
                tables_info = []
                for t in s.tables:
                    col_names = [c.name for c in t.columns]
                    col_preview = ", ".join(col_names[:6]) + ("..." if len(col_names) > 6 else "")
                    tables_info.append(f"Table '{t.table_id}' ({len(t.columns)} cols: [{col_preview}])")
                lines.append(f"- Sheet '{s.name}': {s.total_rows} rows, {len(s.tables)} table(s) [{'; '.join(tables_info)}]")
            return "\n".join(lines)
        except Exception:
            return ""

    def _resolve_target_table(
        self,
        dataset_id: str,
        sheet_name: Optional[str] = None,
        table_id: Optional[str] = None,
        query: Optional[str] = None,
    ) -> tuple[str, TableRegion]:
        """Resolves target worksheet and table region from dataset inspection cache with query-aware sheet resolution."""
        overview = ingestion_pipeline.get_overview(dataset_id)
        if not overview.sheets:
            raise ValueError(f"Dataset '{dataset_id}' contains no detected sheets.")

        available_sheet_names = [s.name for s in overview.sheets]

        # Resolve sheet (respect explicit sheet_name or detect sheet mention in query)
        target_sheet = None
        if sheet_name:
            target_sheet = next((s for s in overview.sheets if s.name.lower() == sheet_name.lower()), None)
            if not target_sheet:
                raise SheetResolutionError(sheet_name, available_sheet_names)
        elif query:
            q_lower = query.lower()
            sheet_match = re.search(r"\b(?:pada sheet|di sheet|in sheet|sheet)\s+['\"]?([A-Za-z0-9_ -]+)['\"]?", q_lower)
            if sheet_match:
                extracted_sheet = sheet_match.group(1).strip()
                target_sheet = next((s for s in overview.sheets if s.name.lower() == extracted_sheet.lower()), None)
                if not target_sheet:
                    raise SheetResolutionError(extracted_sheet, available_sheet_names)

        if not target_sheet:
            target_sheet = overview.sheets[0]

        actual_sheet_name = target_sheet.name
        if not target_sheet.tables:
            raise ValueError(f"Worksheet '{actual_sheet_name}' contains no detected tables.")

        # Resolve table
        target_table = None
        if table_id:
            target_table = next((t for t in target_sheet.tables if t.table_id == table_id), None)
        if not target_table:
            target_table = target_sheet.tables[0]

        return actual_sheet_name, target_table

    def _build_multi_analysis_specs(self, dataset_id: str, table_region: TableRegion) -> List[Tuple[str, AnalyticalInstruction]]:
        """Constructs canonical instructions for comprehensive multi-analysis report."""
        date_col = next(
            (c.name for c in table_region.columns if c.data_type in {DataTypeEnum.DATE, DataTypeEnum.DATETIME} or c.semantic_type == SemanticTypeEnum.TEMPORAL),
            None,
        ) or "Order Date"

        # Metric column
        metric_col = "Sales"
        for col in table_region.columns:
            if col.name.lower() in {"sales", "revenue", "penjualan", "total", "amount"}:
                metric_col = col.name
                break
        else:
            for col in table_region.columns:
                if col.data_type in {DataTypeEnum.FLOAT, DataTypeEnum.INTEGER, DataTypeEnum.CURRENCY}:
                    metric_col = col.name
                    break

        col_map = {c.name.lower(): c.name for c in table_region.columns}
        region_col = col_map.get("region", "Region")
        cat_col = col_map.get("category", col_map.get("kategori", "Category"))

        specs = [
            (
                f"Tren Penjualan Bulanan ({metric_col})",
                AnalyticalInstruction(
                    operation=OperationEnum.GROUP_BY,
                    dataset_id=dataset_id,
                    sheet_name=table_region.sheet_name,
                    table_id=table_region.table_id,
                    group_by_columns=[f"YEAR_MONTH({date_col})"],
                    aggregations=[AggregationSpec(column=metric_col, operation=AggregationOpEnum.SUM, alias=f"Total_{metric_col}")],
                ),
            ),
            (
                f"Total {metric_col} per Region",
                AnalyticalInstruction(
                    operation=OperationEnum.GROUP_BY,
                    dataset_id=dataset_id,
                    sheet_name=table_region.sheet_name,
                    table_id=table_region.table_id,
                    group_by_columns=[region_col],
                    aggregations=[AggregationSpec(column=metric_col, operation=AggregationOpEnum.SUM, alias=f"Total_{metric_col}")],
                    sort=SortSpec(column=f"Total_{metric_col}", ascending=False),
                ),
            ),
            (
                f"Total {metric_col} per Kategori",
                AnalyticalInstruction(
                    operation=OperationEnum.GROUP_BY,
                    dataset_id=dataset_id,
                    sheet_name=table_region.sheet_name,
                    table_id=table_region.table_id,
                    group_by_columns=[cat_col],
                    aggregations=[AggregationSpec(column=metric_col, operation=AggregationOpEnum.SUM, alias=f"Total_{metric_col}")],
                    sort=SortSpec(column=f"Total_{metric_col}", ascending=False),
                ),
            ),
            (
                f"Pola Musiman Bulanan ({metric_col})",
                AnalyticalInstruction(
                    operation=OperationEnum.GROUP_BY,
                    dataset_id=dataset_id,
                    sheet_name=table_region.sheet_name,
                    table_id=table_region.table_id,
                    group_by_columns=[f"MONTH_NAME({date_col})"],
                    aggregations=[AggregationSpec(column=metric_col, operation=AggregationOpEnum.AVERAGE, alias=f"Avg_{metric_col}")],
                ),
            ),
        ]
        return specs

    async def plan_only(self, request: NaturalLanguageQueryRequest) -> QueryPlanOnlyResponse:
        """Plans an AnalyticalInstruction or ClarificationRequest without running calculations."""
        t0 = time.perf_counter()
        t_resolve_ms = 0.0
        t_plan_ms = 0.0
        t_guard_ms = 0.0

        try:
            t_res_start = time.perf_counter()
            sheet_name, table_region = self._resolve_target_table(
                request.dataset_id,
                request.sheet_name,
                request.table_id,
                query=request.query,
            )
            workbook_summary = self._build_workbook_summary(request.dataset_id)
            t_resolve_ms = (time.perf_counter() - t_res_start) * 1000
        except SheetResolutionError as sre:
            t_resolve_ms = (time.perf_counter() - t_res_start) * 1000
            clarification = ClarificationRequest(
                question=f"Sheet '{sre.requested_sheet}' tidak ditemukan dalam workbook. Silakan pilih sheet yang tersedia:",
                reason=f"Sheet '{sre.requested_sheet}' tidak ada dalam metadata workbook.",
                target_parameter="sheet_name",
                options=sre.available_sheets,
            )
            return QueryPlanOnlyResponse(
                status=AIQueryStatus.CLARIFICATION_REQUIRED,
                user_query=request.query,
                intent_summary=f"Clarification required: sheet '{sre.requested_sheet}' not found",
                clarification=clarification,
                timing=TimingBreakdown(
                    schema_resolution_ms=round(t_resolve_ms, 2),
                    total_duration_ms=round((time.perf_counter() - t0) * 1000, 2),
                ),
            )
        except Exception as ex:
            return QueryPlanOnlyResponse(
                status=AIQueryStatus.EXECUTION_ERROR,
                user_query=request.query,
                intent_summary="Failed to resolve dataset table context",
                error_message=str(ex),
                timing=TimingBreakdown(
                    schema_resolution_ms=round(t_resolve_ms, 2),
                    total_duration_ms=round((time.perf_counter() - t0) * 1000, 2),
                ),
            )

        target_model = request.model or settings.GEMINI_DEFAULT_MODEL or DEFAULT_AI_MODEL

        # Check for multi-analysis "Semua Analisis" selection
        is_multi_all = bool(
            request.clarification_selection
            and "multi_analysis_scope" in request.clarification_selection
            and any(kw in str(request.clarification_selection["multi_analysis_scope"]).lower() for kw in ["semua", "all", "menyeluruh"])
        )

        if is_multi_all:
            specs = self._build_multi_analysis_specs(request.dataset_id, table_region)
            sub_plans = []
            for label, inst in specs:
                sub_plans.append(
                    QueryPlanOnlyResponse(
                        status=AIQueryStatus.EXECUTION_READY,
                        user_query=label,
                        intent_summary=label,
                        model_used=target_model,
                        planned_instruction=inst,
                    )
                )
            return QueryPlanOnlyResponse(
                status=AIQueryStatus.EXECUTION_READY,
                user_query=request.query,
                intent_summary="Laporan Analisis Menyeluruh (Multi-Analysis Report)",
                model_used=target_model,
                planned_instruction=specs[0][1],
                sub_plans=sub_plans,
                timing=TimingBreakdown(
                    schema_resolution_ms=round(t_resolve_ms, 2),
                    total_duration_ms=round((time.perf_counter() - t0) * 1000, 2),
                ),
            )

        t_plan_start = time.perf_counter()
        status, intent_summary, instruction, clarification, error_msg = await query_planner.plan_query(
            query=request.query,
            dataset_id=request.dataset_id,
            sheet_name=sheet_name,
            table_region=table_region,
            clarification_selection=request.clarification_selection,
            model=target_model,
            workbook_summary=workbook_summary,
        )
        t_plan_ms = (time.perf_counter() - t_plan_start) * 1000

        if status == AIQueryStatus.EXECUTION_READY and instruction:
            t_guard_start = time.perf_counter()
            is_valid, validation_err = ai_guardrail.validate_instruction(instruction, table_region)
            t_guard_ms = (time.perf_counter() - t_guard_start) * 1000
            if not is_valid:
                return QueryPlanOnlyResponse(
                    status=AIQueryStatus.VALIDATION_FAILED,
                    user_query=request.query,
                    intent_summary=intent_summary,
                    model_used=target_model,
                    planned_instruction=instruction,
                    error_message=f"Instruction validation rejected: {validation_err}",
                    timing=TimingBreakdown(
                        schema_resolution_ms=round(t_resolve_ms, 2),
                        qwen_planning_ms=round(t_plan_ms, 2),
                        guardrail_validation_ms=round(t_guard_ms, 2),
                        total_duration_ms=round((time.perf_counter() - t0) * 1000, 2),
                    ),
                )

        return QueryPlanOnlyResponse(
            status=status,
            user_query=request.query,
            intent_summary=intent_summary,
            model_used=target_model,
            planned_instruction=instruction,
            clarification=clarification,
            error_message=error_msg,
            timing=TimingBreakdown(
                schema_resolution_ms=round(t_resolve_ms, 2),
                qwen_planning_ms=round(t_plan_ms, 2),
                guardrail_validation_ms=round(t_guard_ms, 2),
                total_duration_ms=round((time.perf_counter() - t0) * 1000, 2),
            ),
        )

    async def execute_query(self, request: NaturalLanguageQueryRequest) -> NaturalLanguageQueryResponse:
        """
        Executes the mandatory end-to-end analytical pipeline with exact stage timing:
        Dataset Lookup -> Qwen Planning -> Guardrail Validation -> Python Execution -> Visualization -> Grounded Explanation
        """
        t0 = time.perf_counter()
        t_resolve_ms = 0.0
        t_plan_ms = 0.0
        t_guard_ms = 0.0
        t_exec_ms = 0.0
        t_viz_ms = 0.0
        t_explain_ms = 0.0

        # Stage 1: Dataset & Table Resolution
        try:
            t_res_start = time.perf_counter()
            sheet_name, table_region = self._resolve_target_table(
                request.dataset_id,
                request.sheet_name,
                request.table_id,
                query=request.query,
            )
            workbook_summary = self._build_workbook_summary(request.dataset_id)
            t_resolve_ms = (time.perf_counter() - t_res_start) * 1000
        except SheetResolutionError as sre:
            t_resolve_ms = (time.perf_counter() - t_res_start) * 1000
            clarification = ClarificationRequest(
                question=f"Sheet '{sre.requested_sheet}' tidak ditemukan dalam workbook. Silakan pilih sheet yang tersedia:",
                reason=f"Sheet '{sre.requested_sheet}' tidak ada dalam metadata workbook.",
                target_parameter="sheet_name",
                options=sre.available_sheets,
            )
            return NaturalLanguageQueryResponse(
                status=AIQueryStatus.CLARIFICATION_REQUIRED,
                user_query=request.query,
                intent_summary=f"Clarification required: sheet '{sre.requested_sheet}' not found",
                clarification=clarification,
                timing=TimingBreakdown(
                    schema_resolution_ms=round(t_resolve_ms, 2),
                    total_duration_ms=round((time.perf_counter() - t0) * 1000, 2),
                ),
            )
        except Exception as ex:
            return NaturalLanguageQueryResponse(
                status=AIQueryStatus.EXECUTION_ERROR,
                user_query=request.query,
                intent_summary="Dataset target resolution error",
                error_message=str(ex),
                timing=TimingBreakdown(
                    schema_resolution_ms=round(t_resolve_ms, 2),
                    total_duration_ms=round((time.perf_counter() - t0) * 1000, 2),
                ),
            )

        target_model = request.model or settings.QWEN_MODEL or "qwen3.5-397b-a17b"

        # Check for multi-analysis "Semua Analisis" selection
        is_multi_all = bool(
            request.clarification_selection
            and "multi_analysis_scope" in request.clarification_selection
            and any(kw in str(request.clarification_selection["multi_analysis_scope"]).lower() for kw in ["semua", "all", "menyeluruh"])
        )

        if is_multi_all:
            specs = self._build_multi_analysis_specs(request.dataset_id, table_region)
            sub_analyses: List[NaturalLanguageQueryResponse] = []

            for label, inst in specs:
                sub_res = analytical_engine.execute(inst)
                sub_viz = None
                if request.generate_visualization:
                    try:
                        sub_viz = visualization_engine.render(
                            VisualizationRequest(dataset_id=request.dataset_id, analytical_result=sub_res)
                        )
                    except Exception:
                        pass
                sub_exp = await evidence_explainer.explain_result(sub_res, label, model=target_model)
                sub_analyses.append(
                    NaturalLanguageQueryResponse(
                        status=AIQueryStatus.EXECUTION_READY,
                        user_query=label,
                        intent_summary=label,
                        model_used=target_model,
                        planned_instruction=inst,
                        analytical_result=sub_res,
                        visualization=sub_viz,
                        explanation=sub_exp,
                    )
                )

            total_ms = (time.perf_counter() - t0) * 1000
            return NaturalLanguageQueryResponse(
                status=AIQueryStatus.EXECUTION_READY,
                user_query=request.query,
                intent_summary="Laporan Analisis Menyeluruh (Multi-Analysis Report)",
                model_used=target_model,
                planned_instruction=specs[0][1],
                analytical_result=sub_analyses[0].analytical_result,
                visualization=sub_analyses[0].visualization,
                explanation=sub_analyses[0].explanation,
                sub_analyses=sub_analyses,
                suggested_next_queries=self._derive_followup_suggestions(table_region, specs[0][1]),
                timing=TimingBreakdown(
                    schema_resolution_ms=round(t_resolve_ms, 2),
                    deterministic_execution_ms=round(total_ms - t_resolve_ms, 2),
                    total_duration_ms=round(total_ms, 2),
                ),
            )

        # Stage 2: Query Planning (or use preplanned instruction)
        if request.preplanned_instruction:
            instruction = request.preplanned_instruction
            intent_summary = f"Execution of pre-planned instruction: {instruction.operation.value}"
            status = AIQueryStatus.EXECUTION_READY
            clarification = None
            error_msg = None
            t_plan_ms = 0.0
        else:
            t_plan_start = time.perf_counter()
            status, intent_summary, instruction, clarification, error_msg = await query_planner.plan_query(
                query=request.query,
                dataset_id=request.dataset_id,
                sheet_name=sheet_name,
                table_region=table_region,
                clarification_selection=request.clarification_selection,
                model=target_model,
                workbook_summary=workbook_summary,
            )
            t_plan_ms = (time.perf_counter() - t_plan_start) * 1000

        if status != AIQueryStatus.EXECUTION_READY or not instruction:
            return NaturalLanguageQueryResponse(
                status=status,
                user_query=request.query,
                intent_summary=intent_summary,
                model_used=target_model,
                clarification=clarification,
                error_message=error_msg,
                timing=TimingBreakdown(
                    schema_resolution_ms=round(t_resolve_ms, 2),
                    qwen_planning_ms=round(t_plan_ms, 2),
                    total_duration_ms=round((time.perf_counter() - t0) * 1000, 2),
                ),
            )

        # Stage 3: AI Guardrail validation (mandatory prior to execution)
        t_guard_start = time.perf_counter()
        is_valid, validation_err = ai_guardrail.validate_instruction(instruction, table_region)
        t_guard_ms = (time.perf_counter() - t_guard_start) * 1000

        if not is_valid:
            return NaturalLanguageQueryResponse(
                status=AIQueryStatus.VALIDATION_FAILED,
                user_query=request.query,
                intent_summary=intent_summary,
                model_used=target_model,
                planned_instruction=instruction,
                error_message=f"AI Guardrail blocked execution: {validation_err}",
                timing=TimingBreakdown(
                    schema_resolution_ms=round(t_resolve_ms, 2),
                    qwen_planning_ms=round(t_plan_ms, 2),
                    guardrail_validation_ms=round(t_guard_ms, 2),
                    total_duration_ms=round((time.perf_counter() - t0) * 1000, 2),
                ),
            )

        # Stage 4: Authoritative deterministic Python execution
        t_exec_start = time.perf_counter()
        try:
            analytical_result = analytical_engine.execute(instruction)
            t_exec_ms = (time.perf_counter() - t_exec_start) * 1000
        except Exception as exec_err:
            t_exec_ms = (time.perf_counter() - t_exec_start) * 1000
            logger.error(f"Deterministic execution failed: {str(exec_err)}")
            return NaturalLanguageQueryResponse(
                status=AIQueryStatus.EXECUTION_ERROR,
                user_query=request.query,
                intent_summary=intent_summary,
                model_used=target_model,
                planned_instruction=instruction,
                error_message=f"Calculation engine execution failure: {str(exec_err)}",
                timing=TimingBreakdown(
                    schema_resolution_ms=round(t_resolve_ms, 2),
                    qwen_planning_ms=round(t_plan_ms, 2),
                    guardrail_validation_ms=round(t_guard_ms, 2),
                    deterministic_execution_ms=round(t_exec_ms, 2),
                    total_duration_ms=round((time.perf_counter() - t0) * 1000, 2),
                ),
            )

        # Stage 5: Optional deterministic visualization
        viz_response = None
        if request.generate_visualization:
            t_viz_start = time.perf_counter()
            try:
                viz_req = VisualizationRequest(
                    dataset_id=request.dataset_id,
                    analytical_result=analytical_result,
                )
                viz_response = visualization_engine.render(viz_req)
            except Exception as viz_err:
                logger.info(f"Visualization omitted or not applicable: {str(viz_err)}")
            finally:
                t_viz_ms = (time.perf_counter() - t_viz_start) * 1000

        # Stage 6: Evidence-based grounded explanation
        t_explain_start = time.perf_counter()
        explanation = await evidence_explainer.explain_result(analytical_result, request.query, model=target_model)
        t_explain_ms = (time.perf_counter() - t_explain_start) * 1000

        # Stage 7: Derive contextual follow-up query suggestions
        suggested_queries = self._derive_followup_suggestions(table_region, instruction)

        total_ms = (time.perf_counter() - t0) * 1000

        timing = TimingBreakdown(
            schema_resolution_ms=round(t_resolve_ms, 2),
            qwen_planning_ms=round(t_plan_ms, 2),
            guardrail_validation_ms=round(t_guard_ms, 2),
            deterministic_execution_ms=round(t_exec_ms, 2),
            visualization_ms=round(t_viz_ms, 2),
            evidence_explanation_ms=round(t_explain_ms, 2),
            total_duration_ms=round(total_ms, 2),
        )

        return NaturalLanguageQueryResponse(
            status=AIQueryStatus.EXECUTION_READY,
            user_query=request.query,
            intent_summary=intent_summary,
            model_used=target_model,
            planned_instruction=instruction,
            analytical_result=analytical_result,
            visualization=viz_response,
            explanation=explanation,
            suggested_next_queries=suggested_queries,
            timing=timing,
        )

    def _derive_followup_suggestions(self, table: TableRegion, last_instruction) -> List[str]:
        """Derives 2-3 logical follow-up analytical questions based on schema."""
        numeric_types = {"integer", "float", "currency", "percentage"}
        numeric_cols = [
            c.name
            for c in table.columns
            if (c.data_type.value if hasattr(c.data_type, "value") else str(c.data_type)) in numeric_types
        ]
        cat_cols = [
            c.name
            for c in table.columns
            if (c.data_type.value if hasattr(c.data_type, "value") else str(c.data_type)) in {"string", "category"}
            and (c.semantic_type.value if hasattr(c.semantic_type, "value") else str(c.semantic_type)) != "identifier"
        ]
        
        suggestions = []
        if cat_cols and numeric_cols:
            suggestions.append(f"Break down {numeric_cols[0]} by {cat_cols[0]}")
            if len(cat_cols) > 1:
                suggestions.append(f"Compare {numeric_cols[0]} across {cat_cols[1]}")
            if len(numeric_cols) > 1:
                suggestions.append(f"What is the average {numeric_cols[1]}?")
        elif numeric_cols:
            suggestions.append(f"What is the average {numeric_cols[0]}?")
            suggestions.append(f"Find the highest {numeric_cols[0]}")

        return suggestions[:3]

    async def generate_suggested_queries(
        self,
        dataset_id: str,
        sheet_name: Optional[str] = None,
    ) -> SuggestedQueriesResponse:
        """Generates schema-derived sample queries."""
        actual_sheet, table = self._resolve_target_table(dataset_id, sheet_name)

        if not qwen_client.is_configured and not gemini_client.is_configured:
            fallback_qs = self._derive_followup_suggestions(table, None)
            return SuggestedQueriesResponse(
                dataset_id=dataset_id,
                sheet_name=actual_sheet,
                suggested_queries=fallback_qs or ["What is the total row count?"],
            )

        schema_context = query_planner._format_schema_context(table)
        user_prompt = f"TABLE SCHEMA:\n{schema_context}\n\nGenerate sample questions JSON:"

        try:
            res = await ai_client.generate_json(
                system_prompt=SUGGESTION_PROMPT,
                user_prompt=user_prompt,
                temperature=0.3,
            )
            queries = res.get("suggested_queries", [])
            return SuggestedQueriesResponse(
                dataset_id=dataset_id,
                sheet_name=actual_sheet,
                suggested_queries=queries[:5] if queries else ["What is the total row count?"],
            )
        except Exception:
            fallback_qs = self._derive_followup_suggestions(table, None)
            return SuggestedQueriesResponse(
                dataset_id=dataset_id,
                sheet_name=actual_sheet,
                suggested_queries=fallback_qs or ["What is the total row count?"],
            )


ai_orchestrator = AIOrchestrator()
