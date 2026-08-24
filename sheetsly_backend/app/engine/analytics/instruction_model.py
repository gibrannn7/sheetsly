"""Analytical Instruction contract and domain models for deterministic execution."""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator


class OperationEnum(str, Enum):
    """Supported analytical operations in Sheetsly."""

    # Scalar Calculations
    SUM = "SUM"
    COUNT_ROWS = "COUNT_ROWS"
    COUNT_VALUES = "COUNT_VALUES"
    DISTINCT_COUNT = "DISTINCT_COUNT"
    AVERAGE = "AVERAGE"
    MIN = "MIN"
    MAX = "MAX"
    MEDIAN = "MEDIAN"

    # Tabular / Structural Operations
    FILTER = "FILTER"
    SORT = "SORT"
    GROUP_BY = "GROUP_BY"

    # Conditional Calculations (composable primitives)
    SUMIF = "SUMIF"
    SUMIFS = "SUMIFS"
    COUNTIF = "COUNTIF"
    COUNTIFS = "COUNTIFS"


class AggregationOpEnum(str, Enum):
    """Aggregation functions supported inside GROUP_BY specifications."""

    SUM = "SUM"
    COUNT_ROWS = "COUNT_ROWS"
    COUNT_VALUES = "COUNT_VALUES"
    DISTINCT_COUNT = "DISTINCT_COUNT"
    AVERAGE = "AVERAGE"
    MIN = "MIN"
    MAX = "MAX"
    MEDIAN = "MEDIAN"


class FilterOperatorEnum(str, Enum):
    """Deterministic filter comparison operators."""

    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_OR_EQUAL = "greater_or_equal"
    LESS_OR_EQUAL = "less_or_equal"
    BETWEEN = "between"
    IS_EMPTY = "is_empty"
    IS_NOT_EMPTY = "is_not_empty"
    IN_LIST = "in_list"


class FilterCombinationEnum(str, Enum):
    """Boolean combination logic for multiple filters."""

    AND = "AND"
    OR = "OR"


class FilterCondition(BaseModel):
    """Single filtering rule applied to a column."""

    column: str = Field(..., description="Target column name")
    operator: FilterOperatorEnum = Field(..., description="Filter comparison operator")
    value: Optional[Any] = Field(None, description="Comparison operand (single value or [min, max] list for between)")
    case_sensitive: bool = Field(False, description="Case sensitivity for string matching")

    @field_validator("operator", mode="before")
    @classmethod
    def normalize_operator(cls, v: Any) -> Any:
        if isinstance(v, str):
            mapping = {
                "=": FilterOperatorEnum.EQUALS,
                "==": FilterOperatorEnum.EQUALS,
                "eq": FilterOperatorEnum.EQUALS,
                "!=": FilterOperatorEnum.NOT_EQUALS,
                "neq": FilterOperatorEnum.NOT_EQUALS,
                ">": FilterOperatorEnum.GREATER_THAN,
                "gt": FilterOperatorEnum.GREATER_THAN,
                "<": FilterOperatorEnum.LESS_THAN,
                "lt": FilterOperatorEnum.LESS_THAN,
                ">=": FilterOperatorEnum.GREATER_OR_EQUAL,
                "gte": FilterOperatorEnum.GREATER_OR_EQUAL,
                "<=": FilterOperatorEnum.LESS_OR_EQUAL,
                "lte": FilterOperatorEnum.LESS_OR_EQUAL,
                "in": FilterOperatorEnum.IN_LIST,
                "is_null": FilterOperatorEnum.IS_EMPTY,
                "is_not_null": FilterOperatorEnum.IS_NOT_EMPTY,
            }
            norm = v.lower().strip()
            return mapping.get(norm, norm)
        return v


class AggregationSpec(BaseModel):
    """Aggregation specification for GROUP_BY queries."""

    column: str = Field(..., description="Column to aggregate")
    operation: AggregationOpEnum = Field(..., description="Aggregation operation")
    alias: Optional[str] = Field(None, description="Result column header alias (e.g. 'Total_Revenue')")


class SortSpec(BaseModel):
    """Sorting specification."""

    column: str = Field(..., description="Column name to sort by")
    ascending: bool = Field(True, description="True for ascending order, False for descending")


class AnalyticalInstruction(BaseModel):
    """
    Standardized analytical instruction contract consumed by the deterministic Python engine.
    Used identically by UI Click-based operations and AI query planning.
    """

    operation: OperationEnum = Field(..., description="Analytical operation to execute")
    dataset_id: str = Field(..., description="Target dataset UUID")
    sheet_name: str = Field(..., description="Target worksheet name")
    table_id: Optional[str] = Field(None, description="Optional target table ID (defaults to primary table in sheet)")

    # Target column for scalar calculations (SUM, AVG, MIN, MAX, COUNT_VALUES, etc.)
    target_column: Optional[str] = Field(None, description="Primary column for scalar calculations")

    # Grouping and Multi-Aggregation specifications
    group_by_columns: List[str] = Field(default_factory=list, description="Columns to group by")
    aggregations: List[AggregationSpec] = Field(default_factory=list, description="List of aggregations for GROUP_BY")

    # Filtering
    filters: List[FilterCondition] = Field(default_factory=list, description="Filter criteria")
    filter_combination: FilterCombinationEnum = Field(FilterCombinationEnum.AND, description="AND or OR filter combining")

    # Ordering & Slicing
    sort: Optional[SortSpec] = Field(None, description="Sorting instruction")
    limit: Optional[int] = Field(None, ge=1, description="Row limit for top/bottom results")

    # Extra parameters (e.g. for conditional classification)
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Optional operation-specific parameters")
