"""AI Guardrail Layer enforcing strict schema and operation validation on planned AnalyticalInstructions."""

import logging
from typing import Optional, Tuple

from app.engine.analytics.instruction_model import AnalyticalInstruction
from app.engine.analytics.validator import AnalyticalValidationError, InstructionValidator
from app.models.schemas import TableRegion

logger = logging.getLogger("sheetsly.ai.guardrail")


class AIGuardrail:
    """
    Enforces that every AI-planned AnalyticalInstruction strictly complies with
    the authoritative Phase 5 InstructionValidator and dataset table schema before execution.
    """

    @staticmethod
    def validate_instruction(
        instruction: AnalyticalInstruction,
        table_region: TableRegion,
    ) -> Tuple[bool, Optional[str]]:
        """
        Validates an AI-planned instruction against the table schema.
        Returns (is_valid, error_message).
        """
        try:
            InstructionValidator.validate(instruction, table_region)
            return True, None
        except AnalyticalValidationError as ave:
            logger.warning(f"AI Guardrail rejected invalid AnalyticalInstruction: {ave.message}")
            return False, ave.message
        except Exception as ex:
            logger.error(f"Unexpected error in AI Guardrail validation: {str(ex)}")
            return False, f"Instruction validation failure: {str(ex)}"


ai_guardrail = AIGuardrail()
