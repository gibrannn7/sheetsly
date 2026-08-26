"""Evidence-based cross-sheet relationship discovery engine."""

from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field

from app.engine.parser.sheet_reader import RawSheetGrid
from app.engine.profiler.workbook_index import (
    ColumnIndexEntry,
    SheetIndexEntry,
    TableIndexEntry,
    WorkbookMetadataIndex,
)
from app.models.schemas import DataTypeEnum, SemanticTypeEnum


class RelationshipDirectionEnum(str, Enum):
    """Directionality of detected relationship."""

    ONE_TO_MANY = "ONE_TO_MANY"
    MANY_TO_ONE = "MANY_TO_ONE"
    ONE_TO_ONE = "ONE_TO_ONE"
    UNKNOWN = "UNKNOWN"


class RelationshipStatusEnum(str, Enum):
    """Authoritative qualification status of a relationship candidate."""

    VERIFIED = "VERIFIED"      # Confidence >= 0.85 with strong evidence
    POTENTIAL = "POTENTIAL"    # Partial match, insufficient overlap or confidence
    REJECTED = "REJECTED"      # Incompatible types, zero overlap, or conflicting roles


class RelationshipEvidence(BaseModel):
    """Detailed factual evidence supporting a cross-sheet relational link."""

    source_sheet: str
    source_table_id: str
    source_column: str
    target_sheet: str
    target_table_id: str
    target_column: str
    type_compatible: bool
    semantic_compatible: bool
    source_unique_count: int
    target_unique_count: int
    overlap_ratio: float = Field(0.0, ge=0.0, le=1.0, description="Intersection / min(unique_A, unique_B)")
    directionality: RelationshipDirectionEnum = RelationshipDirectionEnum.UNKNOWN
    confidence_score: float = Field(0.0, ge=0.0, le=1.0)
    status: RelationshipStatusEnum = RelationshipStatusEnum.REJECTED
    evidence_notes: List[str] = Field(default_factory=list)


class RelationshipGraph(BaseModel):
    """Container of cross-sheet relationships across an entire workbook."""

    dataset_id: str
    relationships: List[RelationshipEvidence] = Field(default_factory=list)

    def get_verified_relationships(self) -> List[RelationshipEvidence]:
        """Returns only relationships with status VERIFIED and confidence >= 0.85."""
        return [r for r in self.relationships if r.status == RelationshipStatusEnum.VERIFIED and r.confidence_score >= 0.85]

    def find_relationships_for_sheets(self, sheet_a: str, sheet_b: str) -> List[RelationshipEvidence]:
        """Finds all verified links connecting two specific sheets."""
        return [
            r for r in self.get_verified_relationships()
            if (r.source_sheet == sheet_a and r.target_sheet == sheet_b)
            or (r.source_sheet == sheet_b and r.target_sheet == sheet_a)
        ]


class RelationshipDetector:
    """Discovers and validates cross-sheet relationships based on mathematical and semantic evidence."""

    @classmethod
    def detect_relationships(
        cls,
        index: WorkbookMetadataIndex,
        grids: Optional[Dict[str, RawSheetGrid]] = None,
    ) -> RelationshipGraph:
        """
        Discovers candidate relationships across distinct sheets in a workbook.
        Strictly requires evidence (type match, semantic role, cardinality, value overlap).
        """
        relationships: List[RelationshipEvidence] = []

        # Single sheet workbook has no cross-sheet relationships
        if index.sheet_count <= 1:
            return RelationshipGraph(dataset_id=index.dataset_id, relationships=[])

        sheet_names = list(index.sheets.keys())

        # Pairwise comparison across distinct sheets
        for i in range(len(sheet_names)):
            for j in range(i + 1, len(sheet_names)):
                sheet_a_name = sheet_names[i]
                sheet_b_name = sheet_names[j]

                sheet_a = index.sheets[sheet_a_name]
                sheet_b = index.sheets[sheet_b_name]

                # Compare tables between Sheet A and Sheet B
                for tbl_a in sheet_a.tables:
                    for tbl_b in sheet_b.tables:
                        for col_a in tbl_a.columns:
                            for col_b in tbl_b.columns:
                                rel = cls._evaluate_candidate_link(
                                    sheet_a_name, tbl_a, col_a,
                                    sheet_b_name, tbl_b, col_b,
                                    grids,
                                )
                                if rel:
                                    relationships.append(rel)

        return RelationshipGraph(dataset_id=index.dataset_id, relationships=relationships)

    @classmethod
    def _evaluate_candidate_link(
        cls,
        sheet_a: str,
        tbl_a: TableIndexEntry,
        col_a: ColumnIndexEntry,
        sheet_b: str,
        tbl_b: TableIndexEntry,
        col_b: ColumnIndexEntry,
        grids: Optional[Dict[str, RawSheetGrid]],
    ) -> Optional[RelationshipEvidence]:
        """Evaluates whether col_a and col_b form a valid cross-sheet relationship."""
        # 1. Reject numeric measures (e.g. Sales <-> Profit is never a key relationship)
        if col_a.semantic_type == SemanticTypeEnum.NUMERIC_MEASURE or col_b.semantic_type == SemanticTypeEnum.NUMERIC_MEASURE:
            return None

        # 2. Type Compatibility Check
        type_compat = (
            col_a.data_type == col_b.data_type
            or (col_a.data_type in {DataTypeEnum.INTEGER, DataTypeEnum.FLOAT} and col_b.data_type in {DataTypeEnum.INTEGER, DataTypeEnum.FLOAT})
        )
        if not type_compat:
            return None

        # 3. Name Similarity / Normalization
        name_match = (
            col_a.normalized_name == col_b.normalized_name
            or col_a.normalized_name.endswith(col_b.normalized_name)
            or col_b.normalized_name.endswith(col_a.normalized_name)
            or (col_a.normalized_name.replace(" ", "") == col_b.normalized_name.replace(" ", ""))
        )

        # 4. Semantic Role Check
        sem_compat = (
            col_a.semantic_type == col_b.semantic_type
            or (col_a.semantic_type in {SemanticTypeEnum.IDENTIFIER, SemanticTypeEnum.CATEGORICAL} and col_b.semantic_type in {SemanticTypeEnum.IDENTIFIER, SemanticTypeEnum.CATEGORICAL})
        )

        # If neither name nor semantic roles align, skip early
        if not name_match and not (col_a.is_key_candidate and col_b.is_key_candidate):
            return None

        # 5. Overlap Ratio Calculation
        overlap_ratio = 0.0
        notes: List[str] = []

        if grids and sheet_a in grids and sheet_b in grids:
            vals_a = cls._extract_clean_values(grids[sheet_a], col_a.source_column_letter)
            vals_b = cls._extract_clean_values(grids[sheet_b], col_b.source_column_letter)

            if vals_a and vals_b:
                intersection = vals_a.intersection(vals_b)
                denom = min(len(vals_a), len(vals_b))
                overlap_ratio = round(len(intersection) / max(1, denom), 3)
                notes.append(f"Overlap: {len(intersection)} matching unique values out of {denom} ({overlap_ratio*100}%)")
        else:
            # Heuristic overlap based on sample values if grids not supplied
            samples_a = {str(s).strip().lower() for s in col_a.sample_values if s is not None and str(s).strip()}
            samples_b = {str(s).strip().lower() for s in col_b.sample_values if s is not None and str(s).strip()}
            if samples_a and samples_b:
                common = samples_a.intersection(samples_b)
                denom = min(len(samples_a), len(samples_b))
                overlap_ratio = round(len(common) / max(1, denom), 3)
                notes.append(f"Sample Overlap: {len(common)}/{denom} ({overlap_ratio*100}%)")

        # 6. Directionality Evaluation
        direction = RelationshipDirectionEnum.UNKNOWN
        if col_a.unique_count == col_a.total_count and col_b.unique_count < col_b.total_count:
            direction = RelationshipDirectionEnum.ONE_TO_MANY  # A is primary key, B is foreign key
        elif col_b.unique_count == col_b.total_count and col_a.unique_count < col_a.total_count:
            direction = RelationshipDirectionEnum.MANY_TO_ONE  # A is foreign key, B is primary key
        elif col_a.unique_count == col_a.total_count and col_b.unique_count == col_b.total_count:
            direction = RelationshipDirectionEnum.ONE_TO_ONE

        # 7. Confidence Score Calculation
        confidence = 0.0
        if type_compat:
            confidence += 0.20
        if sem_compat:
            confidence += 0.20
        if name_match:
            confidence += 0.25
        if col_a.is_key_candidate or col_b.is_key_candidate:
            confidence += 0.15
        if overlap_ratio >= 0.70:
            confidence += 0.20
        elif overlap_ratio >= 0.30:
            confidence += 0.10

        confidence = round(min(1.0, confidence), 3)

        # 8. Status Decision
        status = RelationshipStatusEnum.REJECTED
        if confidence >= 0.85 and (overlap_ratio >= 0.50 or (name_match and (col_a.is_key_candidate or col_b.is_key_candidate))):
            status = RelationshipStatusEnum.VERIFIED
            notes.append("Status: VERIFIED based on high confidence and structural key alignment.")
        elif confidence >= 0.50:
            status = RelationshipStatusEnum.POTENTIAL
            notes.append("Status: POTENTIAL candidate; insufficient overlap or naming certainty.")
        else:
            notes.append("Status: REJECTED; weak evidence.")

        return RelationshipEvidence(
            source_sheet=sheet_a,
            source_table_id=tbl_a.table_id,
            source_column=col_a.name,
            target_sheet=sheet_b,
            target_table_id=tbl_b.table_id,
            target_column=col_b.name,
            type_compatible=type_compat,
            semantic_compatible=sem_compat,
            source_unique_count=col_a.unique_count,
            target_unique_count=col_b.unique_count,
            overlap_ratio=overlap_ratio,
            directionality=direction,
            confidence_score=confidence,
            status=status,
            evidence_notes=notes,
        )

    @classmethod
    def _extract_clean_values(cls, grid: RawSheetGrid, col_letter: str) -> Set[str]:
        """Extracts normalized, non-null unique string representations from a column."""
        from openpyxl.utils.cell import column_index_from_string
        unique_vals = set()
        try:
            target_col_idx = column_index_from_string(col_letter)
        except Exception:
            target_col_idx = 1

        for (r, c), cell in grid.cells.items():
            if c == target_col_idx:
                val = cell.original_value
                if val is not None:
                    clean = str(val).strip().lower()
                    if clean and clean != "null" and clean != "none" and clean != "":
                        unique_vals.add(clean)
        return unique_vals
