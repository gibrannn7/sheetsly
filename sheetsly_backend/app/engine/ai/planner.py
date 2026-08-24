"""Natural Language Query Planner translating user questions into verified AnalyticalInstructions."""

import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from app.engine.ai.client import AIProviderError, qwen_client
from app.engine.ai.models import AIQueryStatus, ClarificationRequest
from app.engine.ai.prompts import PLANNER_SYSTEM_PROMPT
from app.engine.analytics.instruction_model import (
    AggregationSpec,
    AnalyticalInstruction,
    FilterCondition,
    OperationEnum,
    SortSpec,
)
from app.models.schemas import TableRegion

logger = logging.getLogger("sheetsly.ai.planner")


class QwenQueryPlanner:
    """Translates user natural-language questions into structured AnalyticalInstruction objects."""

    def _format_schema_context(self, table_region: TableRegion) -> str:
        """Formats table schema into rich structural context for the LLM prompt."""
        cols_summary = []
        for col in table_region.columns:
            samples_str = ", ".join([f"'{s}'" for s in col.sample_values[:4]]) if col.sample_values else "N/A"
            dt_str = col.data_type.value if hasattr(col.data_type, "value") else str(col.data_type)
            st_str = col.semantic_type.value if hasattr(col.semantic_type, "value") else str(col.semantic_type)
            cols_summary.append(
                f"- {col.name} (type: {dt_str}, role: {st_str}, nulls: {col.null_count}, samples: [{samples_str}])"
            )

        return (
            f"Table ID: {table_region.table_id}\n"
            f"Range: {table_region.range_address} (Data: {table_region.data_range})\n"
            f"Total Data Rows: {table_region.row_count}\n"
            f"Columns ({len(table_region.columns)}):\n" + "\n".join(cols_summary)
        )

    async def plan_query(
        self,
        query: str,
        dataset_id: str,
        sheet_name: str,
        table_region: TableRegion,
        clarification_selection: Optional[Dict[str, str]] = None,
    ) -> Tuple[AIQueryStatus, str, Optional[AnalyticalInstruction], Optional[ClarificationRequest], Optional[str]]:
        """
        Translates a natural language query into an AnalyticalInstruction or ClarificationRequest.
        Returns (status, intent_summary, planned_instruction, clarification, error_message).
        """
        schema_context = self._format_schema_context(table_region)
        
        clarification_context = ""
        if clarification_selection:
            clarification_context = (
                f"\nUser previously resolved clarification with selections: {json.dumps(clarification_selection)}\n"
                f"You MUST use these confirmed selections in the AnalyticalInstruction."
            )

        user_prompt = (
            f"SPREADSHEET TABLE SCHEMA:\n{schema_context}\n"
            f"{clarification_context}\n\n"
            f"USER QUERY:\n\"{query}\"\n\n"
            f"Produce the JSON plan:"
        )

        try:
            llm_response = await qwen_client.generate_json(
                system_prompt=PLANNER_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                temperature=0.0,
            )

            res_type = llm_response.get("type", "").upper()
            intent_summary = llm_response.get("intent_summary", query)

            if res_type == "CLARIFICATION":
                options = llm_response.get("options", [])
                # Ensure options are valid strings from table columns or explicit choices
                valid_options = [str(opt) for opt in options if opt]
                clarification = ClarificationRequest(
                    question=llm_response.get("question", "Please clarify your request."),
                    reason=llm_response.get("reason", "Ambiguous query context."),
                    target_parameter=llm_response.get("target_parameter", "target_column"),
                    options=valid_options,
                )
                return AIQueryStatus.CLARIFICATION_REQUIRED, intent_summary, None, clarification, None

            if res_type == "UNSUPPORTED":
                reason = llm_response.get("reason", "Query cannot be mapped to the available dataset operations.")
                return AIQueryStatus.UNSUPPORTED_QUERY, intent_summary, None, None, reason

            if res_type == "INSTRUCTION":
                raw_inst = llm_response.get("instruction", {})
                if not raw_inst or not isinstance(raw_inst, dict):
                    return (
                        AIQueryStatus.VALIDATION_FAILED,
                        intent_summary,
                        None,
                        None,
                        "LLM produced 'INSTRUCTION' response type but 'instruction' object was missing or empty.",
                    )

                # Parse and validate operation
                op_str = raw_inst.get("operation", "").upper()
                try:
                    op_enum = OperationEnum(op_str)
                except ValueError:
                    return (
                        AIQueryStatus.VALIDATION_FAILED,
                        intent_summary,
                        None,
                        None,
                        f"Unsupported or unknown analytical operation '{op_str}'.",
                    )

                # Parse filters
                filters_list = []
                for f_data in raw_inst.get("filters", []):
                    if isinstance(f_data, dict) and "column" in f_data and "operator" in f_data:
                        val = f_data.get("value") if "value" in f_data else f_data.get("operand")
                        filters_list.append(
                            FilterCondition(
                                column=f_data["column"],
                                operator=f_data["operator"],
                                value=val,
                            )
                        )

                # Parse aggregations (for GROUP_BY)
                aggs_list = []
                for agg_data in raw_inst.get("aggregations", []):
                    if isinstance(agg_data, dict) and "column" in agg_data and "operation" in agg_data:
                        try:
                            agg_op = OperationEnum(agg_data["operation"].upper())
                            aggs_list.append(
                                AggregationSpec(
                                    column=agg_data["column"],
                                    operation=agg_op,
                                    alias=agg_data.get("alias"),
                                )
                            )
                        except ValueError:
                            pass

                # Parse sort
                sort_spec = None
                sort_data = raw_inst.get("sort")
                if isinstance(sort_data, dict) and sort_data.get("column"):
                    sort_spec = SortSpec(
                        column=sort_data["column"],
                        ascending=bool(sort_data.get("ascending", True)),
                    )

                instruction = AnalyticalInstruction(
                    operation=op_enum,
                    dataset_id=dataset_id,
                    sheet_name=sheet_name,
                    table_id=table_region.table_id,
                    target_column=raw_inst.get("target_column") or None,
                    filters=filters_list,
                    filter_combination=raw_inst.get("filter_combination", "AND"),
                    group_by_columns=raw_inst.get("group_by_columns", []),
                    aggregations=aggs_list,
                    sort=sort_spec,
                    limit=raw_inst.get("limit"),
                )

                return AIQueryStatus.EXECUTION_READY, intent_summary, instruction, None, None

            # Unrecognized JSON structure
            return (
                AIQueryStatus.VALIDATION_FAILED,
                intent_summary,
                None,
                None,
                f"LLM output contained unrecognized response type: '{res_type}'.",
            )

        except AIProviderError as pe:
            logger.warning(f"AI Provider error during query planning: {pe.message}")
            return AIQueryStatus.PROVIDER_ERROR, query, None, None, pe.message
        except Exception as ex:
            logger.error(f"Unexpected error in query planner: {str(ex)}")
            return AIQueryStatus.EXECUTION_ERROR, query, None, None, f"Failed to plan query: {str(ex)}"


query_planner = QwenQueryPlanner()
