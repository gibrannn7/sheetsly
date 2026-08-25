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
            
            # Check for extreme period and seasonality notes in calculation steps
            evidence_highlights = [
                step for step in result.lineage.calculation_steps
                if any(kw in step for kw in ["Highest period", "Lowest period", "Seasonality evidence"])
            ]
            
            if evidence_highlights:
                factual_statement = (
                    f"Generated {row_count} grouped periods across [{cols_str}]. "
                    + " ".join(evidence_highlights)
                )
                summary = f"Grouped {result.lineage.rows_included} records into {row_count} periods with verified trend & seasonality analysis."
            else:
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
        total_records = len(result.table_data.rows) if result.table_data and result.table_data.rows else 0
        first_record = result.table_data.rows[0] if total_records > 0 else None
        last_record = result.table_data.rows[-1] if total_records > 0 else None

        temporal_span = None
        if total_records > 0 and result.table_data.columns:
            first_col = result.table_data.columns[0]
            if any(kw in first_col.lower() for kw in ["year", "month", "quarter", "date", "period"]):
                first_val = first_record.get(first_col)
                last_val = last_record.get(first_col)
                temporal_span = f"From '{first_val}' to '{last_val}' (total {total_records} chronological periods)"

        table_data_payload = None
        if result.table_data and result.table_data.rows:
            if len(result.table_data.rows) <= 50:
                table_data_payload = result.table_data.rows
            else:
                table_data_payload = {
                    "total_records": total_records,
                    "first_10_records": result.table_data.rows[:10],
                    "last_10_records": result.table_data.rows[-10:],
                    "period_span": temporal_span,
                }

        result_payload = {
            "operation": result.operation,
            "result_type": result.result_type,
            "scalar_value": result.scalar_value,
            "scalar_formatted": result.scalar_formatted,
            "total_result_records": total_records if result.table_data else 1,
            "temporal_period_span": temporal_span,
            "table_data": table_data_payload,
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
