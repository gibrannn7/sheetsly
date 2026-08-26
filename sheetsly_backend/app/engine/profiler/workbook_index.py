"""Workbook Metadata Index for multi-sheet discovery, schema indexing, and minimal context generation."""

import re
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from app.models.schemas import (
    ColumnMetadata,
    DataTypeEnum,
    OrientationEnum,
    SemanticTypeEnum,
    SheetMetadata,
    TableRegion,
    WorkbookOverview,
)


class ColumnIndexEntry(BaseModel):
    """Indexed column profile with semantic role, statistics, and temporal bounds."""

    index: int = Field(..., description="0-indexed position within table")
    name: str = Field(..., description="Original column header name")
    normalized_name: str = Field(..., description="Normalized lookup name (lowercase, stripped)")
    source_column_letter: str = Field(..., description="Excel column letter e.g. 'A'")
    data_type: DataTypeEnum = Field(..., description="Dominant physical data type")
    semantic_type: SemanticTypeEnum = Field(..., description="Inferred semantic role")
    type_confidence: float = Field(1.0, ge=0.0, le=1.0)
    total_count: int = Field(0)
    null_count: int = Field(0)
    null_ratio: float = Field(0.0, ge=0.0, le=1.0)
    unique_count: int = Field(0)
    cardinality_ratio: float = Field(0.0, ge=0.0, le=1.0)
    sample_values: List[Any] = Field(default_factory=list)
    temporal_bounds: Optional[Dict[str, Any]] = Field(None)
    numeric_statistics: Optional[Dict[str, float]] = Field(None)
    is_key_candidate: bool = Field(False)


class TableIndexEntry(BaseModel):
    """Indexed table profile within a sheet."""

    table_id: str = Field(..., description="Unique table ID")
    name: str = Field(..., description="Table name")
    sheet_name: str = Field(..., description="Parent worksheet name")
    range_address: str = Field(..., description="Bounding box e.g. 'A1:F50'")
    header_range: Optional[str] = Field(None)
    data_range: Optional[str] = Field(None)
    orientation: OrientationEnum = Field(OrientationEnum.VERTICAL)
    row_count: int = Field(0)
    column_count: int = Field(0)
    columns: List[ColumnIndexEntry] = Field(default_factory=list)
    confidence_score: float = Field(1.0)


class SheetIndexEntry(BaseModel):
    """Indexed sheet profile containing tables, dimensions, and quality summary."""

    name: str = Field(..., description="Worksheet name")
    index: int = Field(..., description="0-indexed position in workbook")
    is_hidden: bool = Field(False)
    dimensions: str = Field("A1:A1")
    total_rows: int = Field(0)
    total_columns: int = Field(0)
    used_range: str = Field("A1:A1")
    empty_rows_count: int = Field(0)
    empty_cols_count: int = Field(0)
    formula_cells_count: int = Field(0)
    is_empty: bool = Field(False)
    tables: List[TableIndexEntry] = Field(default_factory=list)
    quality_score: float = Field(100.0)


class WorkbookMetadataIndex(BaseModel):
    """Authoritative, deterministic multi-sheet metadata index for an entire workbook."""

    dataset_id: str = Field(..., description="Unique dataset/session ID")
    filename: str = Field(..., description="Original filename")
    file_type: str = Field("xlsx", description="File extension e.g. 'xlsx', 'csv'")
    sheet_count: int = Field(0)
    sheet_names: List[str] = Field(default_factory=list)
    active_sheet_name: str = Field("")
    sheets: Dict[str, SheetIndexEntry] = Field(default_factory=dict)
    
    # Global Catalogs for Fast Lookups
    global_column_catalog: Dict[str, List[Tuple[str, str, str]]] = Field(
        default_factory=dict,
        description="Maps normalized_column_name -> [(sheet_name, table_id, original_col_name)]",
    )
    temporal_catalog: List[Tuple[str, str, str, Dict[str, Any]]] = Field(
        default_factory=list,
        description="List of (sheet_name, table_id, col_name, temporal_bounds)",
    )
    measure_catalog: List[Tuple[str, str, str, DataTypeEnum]] = Field(
        default_factory=list,
        description="List of (sheet_name, table_id, col_name, data_type)",
    )
    identifier_catalog: List[Tuple[str, str, str, int]] = Field(
        default_factory=list,
        description="List of candidate keys (sheet_name, table_id, col_name, unique_count)",
    )

    @classmethod
    def from_overview(cls, overview: WorkbookOverview) -> "WorkbookMetadataIndex":
        """
        Deterministically compiles a complete WorkbookMetadataIndex from a WorkbookOverview.
        Zero redundant file scans; pure O(columns) indexing.
        """
        ext = "csv" if overview.filename.lower().endswith(".csv") else "xlsx"
        sheet_names = [s.name for s in overview.sheets]
        active_sheet = sheet_names[0] if sheet_names else ""

        sheets_dict: Dict[str, SheetIndexEntry] = {}
        col_catalog: Dict[str, List[Tuple[str, str, str]]] = {}
        temp_catalog: List[Tuple[str, str, str, Dict[str, Any]]] = []
        meas_catalog: List[Tuple[str, str, str, DataTypeEnum]] = []
        id_catalog: List[Tuple[str, str, str, int]] = []

        for s_meta in overview.sheets:
            tables_entries: List[TableIndexEntry] = []
            is_sheet_empty = (s_meta.total_rows == 0 or s_meta.total_columns == 0)

            for t_meta in s_meta.tables:
                col_entries: List[ColumnIndexEntry] = []
                for c_meta in t_meta.columns:
                    norm_name = c_meta.name.strip().lower().replace("_", " ").replace("-", " ")
                    norm_name = re.sub(r"\s+", " ", norm_name)

                    null_ratio = round(c_meta.null_count / max(1, c_meta.total_count), 3) if c_meta.total_count > 0 else 0.0
                    non_null_count = c_meta.total_count - c_meta.null_count
                    card_ratio = round(c_meta.unique_count / max(1, non_null_count), 3) if non_null_count > 0 else 0.0

                    # Key candidate heuristic: identifier semantic or high cardinality non-null
                    is_key = (
                        c_meta.semantic_type == SemanticTypeEnum.IDENTIFIER
                        or (c_meta.unique_count == non_null_count and non_null_count > 3 and c_meta.semantic_type != SemanticTypeEnum.NUMERIC_MEASURE)
                    )

                    col_entry = ColumnIndexEntry(
                        index=c_meta.index,
                        name=c_meta.name,
                        normalized_name=norm_name,
                        source_column_letter=c_meta.source_column_letter,
                        data_type=c_meta.data_type,
                        semantic_type=c_meta.semantic_type,
                        type_confidence=c_meta.type_confidence,
                        total_count=c_meta.total_count,
                        null_count=c_meta.null_count,
                        null_ratio=null_ratio,
                        unique_count=c_meta.unique_count,
                        cardinality_ratio=card_ratio,
                        sample_values=c_meta.sample_values[:5] if c_meta.sample_values else [],
                        temporal_bounds=c_meta.temporal_bounds,
                        is_key_candidate=is_key,
                    )
                    col_entries.append(col_entry)

                    # Populate Catalogs
                    if norm_name not in col_catalog:
                        col_catalog[norm_name] = []
                    col_catalog[norm_name].append((s_meta.name, t_meta.table_id, c_meta.name))

                    if c_meta.temporal_bounds:
                        temp_catalog.append((s_meta.name, t_meta.table_id, c_meta.name, c_meta.temporal_bounds))

                    if c_meta.semantic_type == SemanticTypeEnum.NUMERIC_MEASURE or c_meta.data_type in {
                        DataTypeEnum.FLOAT, DataTypeEnum.INTEGER, DataTypeEnum.CURRENCY, DataTypeEnum.PERCENTAGE
                    }:
                        meas_catalog.append((s_meta.name, t_meta.table_id, c_meta.name, c_meta.data_type))

                    if is_key:
                        id_catalog.append((s_meta.name, t_meta.table_id, c_meta.name, c_meta.unique_count))

                table_entry = TableIndexEntry(
                    table_id=t_meta.table_id,
                    name=t_meta.name,
                    sheet_name=s_meta.name,
                    range_address=t_meta.range_address,
                    header_range=t_meta.header_range,
                    data_range=t_meta.data_range,
                    orientation=t_meta.orientation,
                    row_count=t_meta.row_count,
                    column_count=t_meta.column_count,
                    columns=col_entries,
                    confidence_score=t_meta.confidence_score,
                )
                tables_entries.append(table_entry)

            sheet_entry = SheetIndexEntry(
                name=s_meta.name,
                index=s_meta.index,
                is_hidden=s_meta.is_hidden,
                dimensions=s_meta.dimensions,
                total_rows=s_meta.total_rows,
                total_columns=s_meta.total_columns,
                used_range=s_meta.used_range,
                empty_rows_count=s_meta.empty_rows_count,
                empty_cols_count=s_meta.empty_cols_count,
                formula_cells_count=s_meta.formula_cells_count,
                is_empty=is_sheet_empty,
                tables=tables_entries,
                quality_score=s_meta.quality_report.overall_score if s_meta.quality_report else 100.0,
            )
            sheets_dict[s_meta.name] = sheet_entry

        return cls(
            dataset_id=overview.dataset_id,
            filename=overview.filename,
            file_type=ext,
            sheet_count=overview.sheet_count,
            sheet_names=sheet_names,
            active_sheet_name=active_sheet,
            sheets=sheets_dict,
            global_column_catalog=col_catalog,
            temporal_catalog=temp_catalog,
            measure_catalog=meas_catalog,
            identifier_catalog=id_catalog,
        )

    def find_columns_by_name(self, column_name: str, sheet_name: Optional[str] = None) -> List[Tuple[str, str, ColumnIndexEntry]]:
        """
        Finds matching ColumnIndexEntry across sheets (or scoped to a specific sheet).
        Returns: [(sheet_name, table_id, ColumnIndexEntry)]
        """
        norm_target = column_name.strip().lower().replace("_", " ").replace("-", " ")
        norm_target = re.sub(r"\s+", " ", norm_target)

        matches = []
        target_sheets = [sheet_name] if sheet_name and sheet_name in self.sheets else self.sheet_names

        for s_name in target_sheets:
            s_entry = self.sheets.get(s_name)
            if not s_entry:
                continue
            for t_entry in s_entry.tables:
                for c_entry in t_entry.columns:
                    if c_entry.normalized_name == norm_target or norm_target in c_entry.normalized_name:
                        matches.append((s_name, t_entry.table_id, c_entry))
        return matches

    def find_columns_by_role(self, role: SemanticTypeEnum, sheet_name: Optional[str] = None) -> List[Tuple[str, str, ColumnIndexEntry]]:
        """
        Finds columns matching a specific SemanticTypeEnum role.
        """
        matches = []
        target_sheets = [sheet_name] if sheet_name and sheet_name in self.sheets else self.sheet_names

        for s_name in target_sheets:
            s_entry = self.sheets.get(s_name)
            if not s_entry:
                continue
            for t_entry in s_entry.tables:
                for c_entry in t_entry.columns:
                    if c_entry.semantic_type == role:
                        matches.append((s_name, t_entry.table_id, c_entry))
        return matches

    def get_minimal_ai_context(self, active_sheet_name: Optional[str] = None) -> str:
        """
        Constructs a compact, minimal structured multi-sheet context string for the AI Query Planner.
        Active sheet is rendered with full column and temporal metadata.
        Peer sheets are rendered in concise summary to protect prompt context tokens.
        """
        cur_sheet = active_sheet_name or self.active_sheet_name
        lines = [
            f"Workbook: '{self.filename}' ({self.sheet_count} sheet{'s' if self.sheet_count != 1 else ''}: {', '.join(self.sheet_names)})",
            f"Active Sheet: '{cur_sheet}'",
            "--- ACTIVE SHEET SCHEMA ---",
        ]

        active_entry = self.sheets.get(cur_sheet)
        if active_entry and active_entry.tables:
            for t in active_entry.tables:
                lines.append(f"Table: {t.name} (Range: {t.range_address}, Rows: {t.row_count}, Orientation: {t.orientation.value})")
                lines.append("Columns:")
                for c in t.columns:
                    t_info = ""
                    if c.temporal_bounds:
                        min_y = c.temporal_bounds.get("min_year")
                        max_y = c.temporal_bounds.get("max_year")
                        latest_y = c.temporal_bounds.get("latest_year")
                        latest_ym = c.temporal_bounds.get("latest_year_month")
                        t_info = f", temporal_bounds: {min_y}..{max_y}, latest_year: {latest_y}, latest_year_month: '{latest_ym}'"
                    samples_str = ", ".join([f"'{s}'" for s in c.sample_values[:4]]) if c.sample_values else "N/A"
                    lines.append(
                        f"- {c.name} (type: {c.data_type.value}, role: {c.semantic_type.value}, nulls: {c.null_count}, samples: <untrusted_table_data>[{samples_str}]</untrusted_table_data>{t_info})"
                    )
        else:
            lines.append(f"Active sheet '{cur_sheet}' contains no detected structured tables.")

        # Peer Sheets Summary
        peer_sheets = [s for s in self.sheet_names if s != cur_sheet]
        if peer_sheets:
            lines.append("--- OTHER WORKBOOK SHEETS (PEER CONTEXT) ---")
            for p_name in peer_sheets:
                p_entry = self.sheets.get(p_name)
                if not p_entry:
                    continue
                p_tables_summary = []
                for pt in p_entry.tables:
                    col_names = [f"{pc.name} ({pc.semantic_type.value})" for pc in pt.columns[:8]]
                    overflow = f" +{len(pt.columns) - 8} more" if len(pt.columns) > 8 else ""
                    p_tables_summary.append(f"Table '{pt.name}' [{', '.join(col_names)}{overflow}]")
                lines.append(f"- Sheet '{p_name}' ({p_entry.total_rows} rows, Used: {p_entry.used_range}): {'; '.join(p_tables_summary) if p_tables_summary else 'No tables'}")

        return "\n".join(lines)
