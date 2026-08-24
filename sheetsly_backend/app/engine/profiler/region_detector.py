"""Data region detector for identifying table blocks, title/metadata rows, headers, and footers."""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from app.engine.parser.sheet_reader import RawSheetGrid
from app.models.schemas import DataTypeEnum
from .type_detector import TypeDetector

FOOTER_KEYWORDS = re.compile(
    r"^(?:total|grand\s*total|subtotal|jumlah|ringkasan|summary|average|rata-rata|note|catatan|\*|\#)",
    re.IGNORECASE,
)


@dataclass
class ClassifiedRegion:
    """Structure breakdown of a detected table region block."""

    bounding_box: Tuple[int, int, int, int]  # (min_row, min_col, max_row, max_col) 1-indexed
    title_rows: List[int] = field(default_factory=list)
    header_rows: List[int] = field(default_factory=list)
    data_rows: List[int] = field(default_factory=list)
    footer_rows: List[int] = field(default_factory=list)
    active_cols: List[int] = field(default_factory=list)


class RegionDetector:
    """Detects distinct rectangular data regions and partitions rows into functional zones."""

    @classmethod
    def detect_regions(cls, grid: RawSheetGrid) -> List[ClassifiedRegion]:
        """
        Scans a sheet grid and extracts all candidate data regions.
        Handles single table, multiple tables separated by blank space, titles, and footers.
        """
        if grid.total_rows == 0 or grid.total_cols == 0:
            return []

        # Find candidate bounding blocks separated by full blank rows / columns
        blocks = cls._find_contiguous_blocks(grid)
        if not blocks:
            # Fallback to whole used range
            blocks = [(grid.min_row, grid.min_col, grid.max_row, grid.max_col)]

        classified: List[ClassifiedRegion] = []
        for block in blocks:
            # Skip isolated 1-2 row blocks that are just standalone title/metadata text
            min_r, min_c, max_r, max_c = block
            block_rows = max_r - min_r + 1
            block_cols = max_c - min_c + 1

            # Count total populated cells in block
            populated_count = 0
            for r in range(min_r, max_r + 1):
                for c in range(min_c, max_c + 1):
                    if not grid.get_cell(r, c).is_empty:
                        populated_count += 1

            # If a block is just 1 or 2 rows with only 1-2 total cells (like a title/metadata banner), don't treat it as a data table
            if block_rows <= 2 and populated_count <= 2 and block_cols <= 2:
                continue

            region = cls._classify_block(grid, block)
            # Only keep regions that have actual data rows or at least 2 columns with header
            if region.data_rows or (len(region.active_cols) >= 2 and region.header_rows):
                classified.append(region)

        # If everything was filtered out, return whole bounding box as fallback
        if not classified and blocks:
            fallback = cls._classify_block(grid, (grid.min_row, grid.min_col, grid.max_row, grid.max_col))
            classified.append(fallback)

        return classified

    @classmethod
    def _find_contiguous_blocks(cls, grid: RawSheetGrid) -> List[Tuple[int, int, int, int]]:
        """
        Finds contiguous data rectangles separated by completely empty rows or columns.
        """
        min_r, max_r = grid.min_row, grid.max_row
        min_c, max_c = grid.min_col, grid.max_col

        # Identify populated rows and columns
        populated_rows = [r for r in range(min_r, max_r + 1) if not grid.is_row_empty(r)]
        if not populated_rows:
            return []

        # Split into row clusters separated by 1 or more blank rows
        row_clusters: List[Tuple[int, int]] = []
        c_start = populated_rows[0]
        c_end = populated_rows[0]

        for r in populated_rows[1:]:
            if r == c_end + 1:
                c_end = r
            else:
                row_clusters.append((c_start, c_end))
                c_start = r
                c_end = r
        row_clusters.append((c_start, c_end))

        blocks: List[Tuple[int, int, int, int]] = []
        for r_start, r_end in row_clusters:
            # Within this row band, find active column boundaries
            populated_cols = [
                c for c in range(min_c, max_c + 1) if not grid.is_col_empty(c, min_row=r_start, max_row=r_end)
            ]
            if not populated_cols:
                continue

            # Split column clusters if there are >= 2 consecutive blank columns
            col_clusters: List[Tuple[int, int]] = []
            col_start = populated_cols[0]
            col_end = populated_cols[0]

            for c in populated_cols[1:]:
                if c == col_end + 1:
                    col_end = c
                elif c > col_end + 1:
                    # If gap is 2 or more columns, split into separate tables
                    if c - col_end >= 2:
                        col_clusters.append((col_start, col_end))
                        col_start = c
                        col_end = c
                    else:
                        col_end = c
            col_clusters.append((col_start, col_end))

            for c_s, c_e in col_clusters:
                blocks.append((r_start, c_s, r_end, c_e))

        return blocks

    @classmethod
    def _classify_block(cls, grid: RawSheetGrid, block: Tuple[int, int, int, int]) -> ClassifiedRegion:
        """
        Classifies rows inside a candidate block into title, header, data, and footer.
        """
        min_r, min_c, max_r, max_c = block
        active_cols = list(range(min_c, max_c + 1))
        num_cols = len(active_cols)
        total_block_rows = max_r - min_r + 1

        title_rows: List[int] = []
        header_rows: List[int] = []
        data_rows: List[int] = []
        footer_rows: List[int] = []

        # If block is very small (1 row)
        if total_block_rows == 1:
            return ClassifiedRegion(
                bounding_box=block,
                header_rows=[min_r],
                data_rows=[],
                active_cols=active_cols,
            )

        # 1. Check top rows for Title / Report Metadata
        curr_r = min_r
        while curr_r <= max_r:
            row_cells = grid.get_row_cells(curr_r, min_c, max_c)
            non_empty_cells = [c for c in row_cells if not c.is_empty]
            non_empty_count = len(non_empty_cells)

            if non_empty_count == 0:
                curr_r += 1
                continue

            # If row has only 1 non-empty cell in a >= 3 column table, it's very likely a title/metadata banner
            if non_empty_count == 1 and num_cols >= 3:
                title_rows.append(curr_r)
                curr_r += 1
                continue

            # Check if row is metadata string (e.g. "Period: ...", "Report: ...") spanning 1-2 cells
            if non_empty_count <= 2 and num_cols >= 4:
                first_val = str(non_empty_cells[0].original_value or "").lower()
                if any(kw in first_val for kw in ["period", "prepared by", "tanggal", "laporan", "report"]):
                    title_rows.append(curr_r)
                    curr_r += 1
                    continue

            # Otherwise, this row might be header
            break

        # 2. Check candidate header row at curr_r
        header_candidate_row = curr_r
        if header_candidate_row <= max_r:
            header_rows.append(header_candidate_row)
            curr_r += 1

        # 3. Check for multi-level header: if the next row also has mostly string values and merged cells
        if curr_r <= max_r and total_block_rows >= 4:
            next_row_cells = grid.get_row_cells(curr_r, min_c, max_c)
            next_non_empty = [c for c in next_row_cells if not c.is_empty]
            types = [TypeDetector.detect_value_type(c.original_value)[0] for c in next_non_empty]
            string_ratio = sum(1 for t in types if t == DataTypeEnum.STRING) / len(types) if types else 0

            # Check if there are merged headers or sub-headers
            has_merged_in_header = any(
                any(r in range(header_candidate_row, curr_r + 1) for r in [header_candidate_row, curr_r])
                for m in grid.merged_ranges
            )
            # If next row is 100% strings and looks like sub-headers
            if string_ratio == 1.0 and len(next_non_empty) >= (num_cols / 2) and has_merged_in_header:
                header_rows.append(curr_r)
                curr_r += 1

        # 4. Scan remaining rows for data and footer
        remaining_rows = list(range(curr_r, max_r + 1))
        if not remaining_rows:
            return ClassifiedRegion(
                bounding_box=block,
                title_rows=title_rows,
                header_rows=header_rows,
                data_rows=[],
                footer_rows=[],
                active_cols=active_cols,
            )

        # Check from bottom upward for footer / totals
        data_end_idx = len(remaining_rows) - 1
        while data_end_idx >= 0:
            r = remaining_rows[data_end_idx]
            row_cells = grid.get_row_cells(r, min_c, max_c)
            non_empty = [c for c in row_cells if not c.is_empty]

            if not non_empty:
                data_end_idx -= 1
                continue

            # Check first non-empty cell text for total / summary / subtotal keywords
            first_val_str = str(non_empty[0].original_value or "").strip()
            has_summary_formula = any(
                c.formula and ("SUM" in c.formula.upper() or "SUBTOTAL" in c.formula.upper() or "AVERAGE" in c.formula.upper())
                for c in row_cells
            )

            if FOOTER_KEYWORDS.match(first_val_str) or has_summary_formula:
                footer_rows.insert(0, r)
                data_end_idx -= 1
                continue
            break

        # The rows between header and footer are data rows
        for idx in range(0, data_end_idx + 1):
            r = remaining_rows[idx]
            if not grid.is_row_empty(r, min_c, max_c):
                data_rows.append(r)

        return ClassifiedRegion(
            bounding_box=block,
            title_rows=title_rows,
            header_rows=header_rows,
            data_rows=data_rows,
            footer_rows=footer_rows,
            active_cols=active_cols,
        )
