"""Evidence-Based Explainer generating factual explanations grounded strictly in AnalyticalResult and CalculationLineage."""

import json
import logging
from typing import Optional

from app.engine.ai.client import AIProviderError, ai_client, qwen_client
from app.engine.ai.models import EvidenceExplanation
from app.engine.ai.prompts import EXPLAINER_SYSTEM_PROMPT
from app.engine.analytics.result_model import AnalyticalResult

logger = logging.getLogger("sheetsly.ai.explainer")


class EvidenceExplainer:
    """Generates grounded factual summaries citing exact cells and numbers from verified AnalyticalResult."""

    def _generate_fallback_explanation(self, result: AnalyticalResult, query: str) -> EvidenceExplanation:
        """Deterministic rule-based explanation fallback when AI provider is offline."""
        source_evidence = (
            f"{result.lineage.sheet_name}!{result.lineage.source_range} "
            f"({result.lineage.rows_included} of {result.lineage.total_table_rows} rows included)"
        )

        if result.result_type == "SCALAR":
            formatted_val = result.scalar_formatted or str(result.scalar_value)
            col_target = ", ".join(result.lineage.source_columns) if result.lineage.source_columns else result.operation
            factual_statement = f"The {result.operation} of {col_target} is {formatted_val}."
            summary = f"Calculated {result.operation} across {result.lineage.rows_included} records."
        else:
            row_count = len(result.table_data.rows) if result.table_data else 0
            cols_str = ", ".join(result.table_data.columns) if result.table_data else ""
            factual_statement = f"Generated table with {row_count} grouped records across columns [{cols_str}]."
            summary = f"Grouped {result.lineage.rows_included} records into {row_count} distinct categories."

        return EvidenceExplanation(
            summary=summary,
            factual_statement=factual_statement,
            source_evidence=source_evidence,
            calculation_steps=result.lineage.calculation_steps,
            warnings=[],
        )

    async def explain_result(
        self,
        result: AnalyticalResult,
        user_query: str,
        model: Optional[str] = None,
    ) -> EvidenceExplanation:
        """
        Explains verified result using selected AI model with strict evidence grounding,
        falling back to deterministic template if provider is unconfigured or unavailable.
        """
        if not ai_client.is_configured(model):
            return self._generate_fallback_explanation(result, user_query)

        # Prepare verified metadata payload for LLM
        lineage = result.lineage
        result_payload = {
            "operation": result.operation,
            "result_type": result.result_type,
            "scalar_value": result.scalar_value,
            "scalar_formatted": result.scalar_formatted,
            "table_data_preview": result.table_data.rows[:10] if result.table_data else None,
            "source_sheet": lineage.sheet_name,
            "source_range": lineage.source_range,
            "rows_included": lineage.rows_included,
            "total_table_rows": lineage.total_table_rows,
            "rows_excluded": lineage.rows_excluded,
            "filters_applied": lineage.filters_applied,
            "calculation_steps": lineage.calculation_steps,
            "execution_time_ms": lineage.execution_time_ms,
            "warnings": [],
        }

        user_prompt = (
            f"USER QUESTION:\n\"{user_query}\"\n\n"
            f"VERIFIED DETERMINISTIC CALCULATION RESULT:\n{json.dumps(result_payload, indent=2)}\n\n"
            f"Generate the grounded explanation JSON:"
        )

        try:
            llm_response = await ai_client.generate_json(
                system_prompt=EXPLAINER_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                temperature=0.0,
                model=model,
            )

            # Ensure source evidence strictly cites calculation lineage
            source_evidence = (
                f"{lineage.sheet_name}!{lineage.source_range} "
                f"({lineage.rows_included} of {lineage.total_table_rows} rows)"
            )

            return EvidenceExplanation(
                summary=llm_response.get("summary", f"Result for {result.operation}"),
                factual_statement=llm_response.get("factual_statement", str(result.scalar_formatted or result.scalar_value)),
                source_evidence=llm_response.get("source_evidence") or source_evidence,
                calculation_steps=lineage.calculation_steps,
                warnings=llm_response.get("warnings", []),
            )

        except Exception as ex:
            logger.warning(f"AI explainer failed ({str(ex)}), falling back to deterministic explanation.")
            return self._generate_fallback_explanation(result, user_query)


evidence_explainer = EvidenceExplainer()
