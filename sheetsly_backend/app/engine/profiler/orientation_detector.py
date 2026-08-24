"""Multi-signal deterministic table orientation detector."""

import re
from dataclasses import dataclass, field
from typing import Any, List, Optional, Tuple

from app.engine.parser.sheet_reader import RawSheetGrid
from app.models.schemas import DataTypeEnum, OrientationEnum
from .type_detector import TypeDetector

PERIOD_HEADER_REGEX = re.compile(
    r"^(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|"
    r"january|february|march|april|may|june|july|august|september|october|november|december|"
    r"q[1-4]|kuartal\s*[1-4]|20\d\d|19\d\d|w\d{1,2}|week\s*\d+|minggu\s*\d+|bulan\s*\d+|"
    r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4})$",
    re.IGNORECASE,
)


@dataclass
class OrientationAssessment:
    """Result of orientation analysis with structural reasons and confidence score."""

    orientation: OrientationEnum
    confidence: float
    reasons: List[str] = field(default_factory=list)
    vertical_score: float = 0.0
    horizontal_score: float = 0.0


class OrientationDetector:
    """Detects table orientation using multiple independent structural signals."""

    @classmethod
    def detect_orientation(
        cls,
        grid: RawSheetGrid,
        min_row: int,
        min_col: int,
        max_row: int,
        max_col: int,
    ) -> OrientationAssessment:
        """
        Evaluates rectangular region to determine whether it is VERTICAL, HORIZONTAL, AMBIGUOUS, or IRREGULAR.
        """
        row_count = max_row - min_row + 1
        col_count = max_col - min_col + 1

        if row_count <= 0 or col_count <= 0:
            return OrientationAssessment(
                orientation=OrientationEnum.AMBIGUOUS,
                confidence=0.0,
                reasons=["Region has zero dimensions."],
            )

        if row_count == 1 and col_count == 1:
            return OrientationAssessment(
                orientation=OrientationEnum.AMBIGUOUS,
                confidence=0.5,
                reasons=["Single cell block."],
            )

        # 1-row table or 1-col table edge cases
        if row_count == 1:
            return OrientationAssessment(
                orientation=OrientationEnum.VERTICAL,
                confidence=0.6,
                reasons=["Single row of data or headers."],
            )
        if col_count == 1:
            return OrientationAssessment(
                orientation=OrientationEnum.HORIZONTAL,
                confidence=0.6,
                reasons=["Single column of data or attributes."],
            )

        # Extract 2D matrix of cell values and types
        cells_matrix = grid.get_2d_slice(min_row, min_col, max_row, max_col)
        types_matrix: List[List[DataTypeEnum]] = []
        raw_vals_matrix: List[List[Any]] = []

        for r_cells in cells_matrix:
            r_types = []
            r_vals = []
            for c in r_cells:
                dt, _ = TypeDetector.detect_value_type(c.original_value)
                r_types.append(dt)
                r_vals.append(c.original_value)
            types_matrix.append(r_types)
            raw_vals_matrix.append(r_vals)

        reasons: List[str] = []
        v_points = 0.0
        h_points = 0.0
        total_weights = 0.0

        # -------------------------------------------------------------
        # SIGNAL 1: Data Type Homogeneity (Column vs Row)
        # -------------------------------------------------------------
        weight_homogeneity = 3.0
        total_weights += weight_homogeneity

        col_homogeneities = []
        for col_idx in range(col_count):
            col_types = [types_matrix[r_idx][col_idx] for r_idx in range(1, row_count)]
            non_null_types = [t for t in col_types if t != DataTypeEnum.NULL]
            if non_null_types:
                dominant_count = max(non_null_types.count(t) for t in set(non_null_types))
                col_homogeneities.append(dominant_count / len(non_null_types))

        row_homogeneities = []
        for r_idx in range(row_count):
            row_types = [types_matrix[r_idx][c_idx] for c_idx in range(1, col_count)]
            non_null_types = [t for t in row_types if t != DataTypeEnum.NULL]
            if non_null_types:
                dominant_count = max(non_null_types.count(t) for t in set(non_null_types))
                row_homogeneities.append(dominant_count / len(non_null_types))

        avg_col_homogeneity = sum(col_homogeneities) / len(col_homogeneities) if col_homogeneities else 0.5
        avg_row_homogeneity = sum(row_homogeneities) / len(row_homogeneities) if row_homogeneities else 0.5

        if avg_col_homogeneity > avg_row_homogeneity + 0.15:
            v_points += weight_homogeneity * avg_col_homogeneity
            h_points += weight_homogeneity * (1.0 - avg_col_homogeneity)
            reasons.append(f"Column data types are significantly more homogeneous ({avg_col_homogeneity:.1%}) than rows ({avg_row_homogeneity:.1%}).")
        elif avg_row_homogeneity > avg_col_homogeneity + 0.15:
            h_points += weight_homogeneity * avg_row_homogeneity
            v_points += weight_homogeneity * (1.0 - avg_row_homogeneity)
            reasons.append(f"Row data types are significantly more homogeneous ({avg_row_homogeneity:.1%}) than columns ({avg_col_homogeneity:.1%}).")
        else:
            v_points += weight_homogeneity * 0.5
            h_points += weight_homogeneity * 0.5

        # -------------------------------------------------------------
        # SIGNAL 2: Header Distinctiveness (Top Row vs Left Column)
        # -------------------------------------------------------------
        weight_headers = 2.5
        total_weights += weight_headers

        top_row_vals = [raw_vals_matrix[0][c] for c in range(col_count)]
        top_row_non_null = [str(v).strip() for v in top_row_vals if v is not None and str(v).strip() != ""]
        top_row_str_count = sum(1 for v in top_row_vals if TypeDetector.detect_value_type(v)[0] == DataTypeEnum.STRING)
        top_row_uniqueness = len(set(top_row_non_null)) / len(top_row_non_null) if top_row_non_null else 0.0
        top_row_string_ratio = top_row_str_count / col_count

        left_col_vals = [raw_vals_matrix[r][0] for r in range(row_count)]
        left_col_non_null = [str(v).strip() for v in left_col_vals if v is not None and str(v).strip() != ""]
        left_col_str_count = sum(1 for v in left_col_vals if TypeDetector.detect_value_type(v)[0] == DataTypeEnum.STRING)
        left_col_uniqueness = len(set(left_col_non_null)) / len(left_col_non_null) if left_col_non_null else 0.0
        left_col_string_ratio = left_col_str_count / row_count

        v_header_score = (top_row_string_ratio * 0.6) + (top_row_uniqueness * 0.4)
        h_header_score = (left_col_string_ratio * 0.6) + (left_col_uniqueness * 0.4)

        if v_header_score > h_header_score + 0.15 and top_row_string_ratio >= 0.7:
            v_points += weight_headers * v_header_score
            reasons.append(f"Top row forms a distinct string header line with high uniqueness ({top_row_uniqueness:.1%}).")
        elif h_header_score > v_header_score + 0.15 and left_col_string_ratio >= 0.7:
            h_points += weight_headers * h_header_score
            reasons.append(f"First column forms a distinct attribute header list with high uniqueness ({left_col_uniqueness:.1%}).")
        else:
            v_points += weight_headers * (v_header_score / 2.0)
            h_points += weight_headers * (h_header_score / 2.0)

        # -------------------------------------------------------------
        # SIGNAL 3: Period / Time Sequence Headers (Horizontal indicator)
        # -------------------------------------------------------------
        weight_period_headers = 4.0
        total_weights += weight_period_headers

        top_row_period_matches = sum(1 for v in top_row_non_null if PERIOD_HEADER_REGEX.match(v))
        left_col_period_matches = sum(1 for v in left_col_non_null if PERIOD_HEADER_REGEX.match(v))

        if top_row_period_matches >= 3 and top_row_period_matches >= (len(top_row_non_null) * 0.4):
            # If top row has time periods across columns and left column has metrics, strong horizontal evidence
            if left_col_string_ratio >= 0.6:
                h_points += weight_period_headers
                reasons.append(f"Top row represents time series periods ({top_row_period_matches} period headers) with metric attributes on left column.")
            else:
                v_points += weight_period_headers * 0.5
                h_points += weight_period_headers * 0.5
        elif left_col_period_matches >= 3 and left_col_period_matches >= (len(left_col_non_null) * 0.4):
            v_points += weight_period_headers
            reasons.append("First column contains chronological dates/periods per row record.")
        else:
            v_points += weight_period_headers * 0.5
            h_points += weight_period_headers * 0.5

        # -------------------------------------------------------------
        # SIGNAL 4: Repetitive Categorical Patterns in Body
        # -------------------------------------------------------------
        weight_cardinality = 1.5
        total_weights += weight_cardinality

        has_vertical_cat_repetition = False
        if row_count >= 5:
            for c_idx in range(col_count):
                body_vals = [str(raw_vals_matrix[r][c_idx]) for r in range(1, row_count) if raw_vals_matrix[r][c_idx] is not None]
                if len(body_vals) >= 5:
                    u_ratio = len(set(body_vals)) / len(body_vals)
                    if 0.05 < u_ratio <= 0.6:
                        has_vertical_cat_repetition = True
                        break

        if has_vertical_cat_repetition:
            v_points += weight_cardinality
            reasons.append("Detected repeating categorical variables arranged in vertical column attributes.")
        else:
            v_points += weight_cardinality * 0.5
            h_points += weight_cardinality * 0.5

        # -------------------------------------------------------------
        # FINAL SCORING & ARBITRATION
        # -------------------------------------------------------------
        final_v_score = round(v_points / total_weights, 3)
        final_h_score = round(h_points / total_weights, 3)

        if final_v_score >= 0.60 and (final_v_score - final_h_score) >= 0.10:
            return OrientationAssessment(
                orientation=OrientationEnum.VERTICAL,
                confidence=final_v_score,
                reasons=reasons,
                vertical_score=final_v_score,
                horizontal_score=final_h_score,
            )
        elif final_h_score >= 0.60 and (final_h_score - final_v_score) >= 0.10:
            return OrientationAssessment(
                orientation=OrientationEnum.HORIZONTAL,
                confidence=final_h_score,
                reasons=reasons,
                vertical_score=final_v_score,
                horizontal_score=final_h_score,
            )
        elif abs(final_v_score - final_h_score) < 0.10:
            return OrientationAssessment(
                orientation=OrientationEnum.AMBIGUOUS,
                confidence=round(max(final_v_score, final_h_score), 3),
                reasons=["Structural signals for vertical vs horizontal layout are evenly balanced or weak."] + reasons,
                vertical_score=final_v_score,
                horizontal_score=final_h_score,
            )
        else:
            return OrientationAssessment(
                orientation=OrientationEnum.IRREGULAR,
                confidence=0.5,
                reasons=["Grid exhibits irregular or fragmented structural alignment."] + reasons,
                vertical_score=final_v_score,
                horizontal_score=final_h_score,
            )
