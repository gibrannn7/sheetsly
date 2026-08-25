"""Pre-execution validation engine for analytical instructions."""

from typing import List, Optional
from app.core.errors import SheetslyError
from app.models.schemas import DataTypeEnum, SemanticTypeEnum, TableRegion
from .expressions import DimensionParser
from .instruction_model import (
    AggregationOpEnum,
    AnalyticalInstruction,
    FilterCondition,
    FilterOperatorEnum,
    OperationEnum,
)

NUMERIC_TYPES = {
    DataTypeEnum.INTEGER,
    DataTypeEnum.FLOAT,
    DataTypeEnum.CURRENCY,
    DataTypeEnum.PERCENTAGE,
}

DATE_COMPATIBLE_TYPES = {
    DataTypeEnum.DATE,
    DataTypeEnum.DATETIME,
}

ORDERABLE_TYPES = NUMERIC_TYPES | DATE_COMPATIBLE_TYPES


class AnalyticalValidationError(SheetslyError):
    """Raised when an analytical instruction fails pre-execution validation."""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(
            message=message,
            code="ANALYTICAL_VALIDATION_ERROR",
            status_code=422,
            details=details or {},
        )


class InstructionValidator:
    """Validates analytical instructions against physical table schemas and data types."""

    @classmethod
    def validate(cls, instruction: AnalyticalInstruction, table: TableRegion) -> None:
        """
        Runs comprehensive schema, operation, and data type validation on the instruction.
        Raises AnalyticalValidationError if any rule is violated.
        """
        table_columns_map = {c.name: c for c in table.columns}
        col_names = set(table_columns_map.keys())

        # -------------------------------------------------------------
        # 1. Operation-Specific Column Validation
        # -------------------------------------------------------------
        op = instruction.operation

        if op in {
            OperationEnum.SUM,
            OperationEnum.AVERAGE,
            OperationEnum.MEDIAN,
            OperationEnum.MIN,
            OperationEnum.MAX,
            OperationEnum.COUNT_VALUES,
            OperationEnum.DISTINCT_COUNT,
            OperationEnum.SUMIF,
            OperationEnum.SUMIFS,
            OperationEnum.COUNTIF,
            OperationEnum.COUNTIFS,
        }:
            if not instruction.target_column:
                raise AnalyticalValidationError(
                    f"Operation '{op.value}' requires a 'target_column' to be specified.",
                    details={"operation": op.value},
                )
            if instruction.target_column not in col_names:
                raise AnalyticalValidationError(
                    f"Target column '{instruction.target_column}' not found in table '{table.name}'. Available columns: {sorted(col_names)}",
                    details={"target_column": instruction.target_column, "available_columns": list(col_names)},
                )

            target_meta = table_columns_map[instruction.target_column]

            # Enforce numeric types for arithmetic aggregations
            if op in {OperationEnum.SUM, OperationEnum.AVERAGE, OperationEnum.MEDIAN, OperationEnum.SUMIF, OperationEnum.SUMIFS}:
                if target_meta.data_type not in NUMERIC_TYPES:
                    raise AnalyticalValidationError(
                        f"Cannot perform numeric operation '{op.value}' on non-numeric column '{instruction.target_column}' (detected type: {target_meta.data_type.value}).",
                        details={
                            "operation": op.value,
                            "column": instruction.target_column,
                            "detected_type": target_meta.data_type.value,
                        },
                    )

        # -------------------------------------------------------------
        # 2. GROUP_BY Validation (Supports Physical & Derived Dimensions)
        # -------------------------------------------------------------
        if op == OperationEnum.GROUP_BY:
            if not instruction.group_by_columns:
                raise AnalyticalValidationError(
                    "GROUP_BY operation requires at least one column in 'group_by_columns'.",
                    details={"operation": op.value},
                )
            for g_col in instruction.group_by_columns:
                if g_col in col_names:
                    continue

                dim_spec = DimensionParser.parse(g_col)
                if dim_spec is None:
                    raise AnalyticalValidationError(
                        f"Group-by column '{g_col}' not found in table '{table.name}'. Available columns: {sorted(col_names)}",
                        details={"group_by_column": g_col, "available_columns": list(col_names)},
                    )

                if dim_spec.source_column not in col_names:
                    raise AnalyticalValidationError(
                        f"Source column '{dim_spec.source_column}' for derived dimension '{g_col}' not found in table '{table.name}'. Available columns: {sorted(col_names)}",
                        details={
                            "derived_dimension": g_col,
                            "source_column": dim_spec.source_column,
                            "available_columns": list(col_names),
                        },
                    )

                source_col_meta = table_columns_map[dim_spec.source_column]
                is_date_compatible = (
                    source_col_meta.data_type in DATE_COMPATIBLE_TYPES
                    or source_col_meta.semantic_type == SemanticTypeEnum.TEMPORAL
                    or (source_col_meta.data_type == DataTypeEnum.STRING and source_col_meta.data_type not in NUMERIC_TYPES)
                )

                if source_col_meta.data_type in NUMERIC_TYPES or not is_date_compatible:
                    raise AnalyticalValidationError(
                        f"Cannot apply date dimension '{dim_spec.operation.value}' to non-date column '{dim_spec.source_column}' (detected type: {source_col_meta.data_type.value}).",
                        details={
                            "operation": dim_spec.operation.value,
                            "column": dim_spec.source_column,
                            "detected_type": source_col_meta.data_type.value,
                        },
                    )

            if not instruction.aggregations:
                raise AnalyticalValidationError(
                    "GROUP_BY operation requires at least one aggregation specification in 'aggregations'.",
                    details={"operation": op.value},
                )

            for agg in instruction.aggregations:
                if agg.column not in col_names:
                    raise AnalyticalValidationError(
                        f"Aggregation column '{agg.column}' not found in table '{table.name}'.",
                        details={"aggregation_column": agg.column, "available_columns": list(col_names)},
                    )
                agg_meta = table_columns_map[agg.column]
                if agg.operation in {AggregationOpEnum.SUM, AggregationOpEnum.AVERAGE, AggregationOpEnum.MEDIAN}:
                    if agg_meta.data_type not in NUMERIC_TYPES:
                        raise AnalyticalValidationError(
                            f"Cannot perform numeric aggregation '{agg.operation.value}' on non-numeric column '{agg.column}' (detected type: {agg_meta.data_type.value}).",
                            details={"operation": agg.operation.value, "column": agg.column},
                        )

            if instruction.top_n_per_group is not None:
                if len(instruction.group_by_columns) < 2:
                    raise AnalyticalValidationError(
                        f"top_n_per_group requires at least two columns in 'group_by_columns' (primary group and ranking group). Found: {instruction.group_by_columns}",
                        details={"top_n_per_group": instruction.top_n_per_group, "group_by_columns": instruction.group_by_columns},
                    )
                if instruction.top_n_per_group < 1:
                    raise AnalyticalValidationError(
                        f"top_n_per_group must be an integer >= 1. Found: {instruction.top_n_per_group}",
                        details={"top_n_per_group": instruction.top_n_per_group},
                    )

        # -------------------------------------------------------------
        # 3. Filter Validation (Supports Physical & Derived Dimensions)
        # -------------------------------------------------------------
        for f in instruction.filters:
            is_derived_filter = False
            f_meta = None

            if f.column in col_names:
                f_meta = table_columns_map[f.column]
            else:
                dim_spec = DimensionParser.parse(f.column)
                if dim_spec is None:
                    raise AnalyticalValidationError(
                        f"Filter column '{f.column}' not found in table '{table.name}'. Available columns: {sorted(col_names)}",
                        details={"filter_column": f.column, "available_columns": list(col_names)},
                    )

                if dim_spec.source_column not in col_names:
                    raise AnalyticalValidationError(
                        f"Source column '{dim_spec.source_column}' for derived dimension filter '{f.column}' not found in table '{table.name}'. Available columns: {sorted(col_names)}",
                        details={
                            "derived_filter": f.column,
                            "source_column": dim_spec.source_column,
                            "available_columns": list(col_names),
                        },
                    )

                source_col_meta = table_columns_map[dim_spec.source_column]
                is_date_compatible = (
                    source_col_meta.data_type in DATE_COMPATIBLE_TYPES
                    or source_col_meta.semantic_type == SemanticTypeEnum.TEMPORAL
                    or (source_col_meta.data_type == DataTypeEnum.STRING and source_col_meta.data_type not in NUMERIC_TYPES)
                )

                if source_col_meta.data_type in NUMERIC_TYPES or not is_date_compatible:
                    raise AnalyticalValidationError(
                        f"Cannot apply date dimension '{dim_spec.operation.value}' to non-date column '{dim_spec.source_column}' (detected type: {source_col_meta.data_type.value}).",
                        details={
                            "operation": dim_spec.operation.value,
                            "column": dim_spec.source_column,
                            "detected_type": source_col_meta.data_type.value,
                        },
                    )
                is_derived_filter = True

            # Validate BETWEEN operand
            if f.operator == FilterOperatorEnum.BETWEEN:
                if not isinstance(f.value, (list, tuple)) or len(f.value) != 2:
                    raise AnalyticalValidationError(
                        f"Filter 'between' on column '{f.column}' requires a 2-element list [min, max] as value.",
                        details={"filter_column": f.column, "provided_value": f.value},
                    )

            # Validate IN_LIST operand
            if f.operator == FilterOperatorEnum.IN_LIST:
                if not isinstance(f.value, (list, tuple, set)):
                    raise AnalyticalValidationError(
                        f"Filter 'in_list' on column '{f.column}' requires a list of values.",
                        details={"filter_column": f.column, "provided_value": f.value},
                    )

            # Validate inequality operators on orderable types
            if f.operator in {
                FilterOperatorEnum.GREATER_THAN,
                FilterOperatorEnum.LESS_THAN,
                FilterOperatorEnum.GREATER_OR_EQUAL,
                FilterOperatorEnum.LESS_OR_EQUAL,
                FilterOperatorEnum.BETWEEN,
            }:
                if not is_derived_filter and f_meta:
                    if f_meta.data_type not in ORDERABLE_TYPES and f_meta.semantic_type != SemanticTypeEnum.TEMPORAL:
                        raise AnalyticalValidationError(
                            f"Comparison filter '{f.operator.value}' cannot be applied to non-orderable column '{f.column}' of type {f_meta.data_type.value}.",
                            details={"filter_operator": f.operator.value, "column": f.column, "data_type": f_meta.data_type.value},
                        )

        # -------------------------------------------------------------
        # 4. Sort Validation
        # -------------------------------------------------------------
        if instruction.sort:
            sort_col = instruction.sort.column
            valid_sort_targets = col_names.copy()
            if op == OperationEnum.GROUP_BY:
                for g in instruction.group_by_columns:
                    valid_sort_targets.add(g)
                    dim_parsed = DimensionParser.parse(g)
                    if dim_parsed:
                        valid_sort_targets.add(dim_parsed.source_column)
                        valid_sort_targets.add(dim_parsed.operation.value)

                for agg in instruction.aggregations:
                    if agg.alias:
                        valid_sort_targets.add(agg.alias)
                    valid_sort_targets.add(f"{agg.operation.value}_{agg.column}")
                    valid_sort_targets.add(agg.column)

            if sort_col not in valid_sort_targets:
                matched = any(sort_col.lower() == v.lower() for v in valid_sort_targets)
                if not matched and DimensionParser.parse(sort_col) is None:
                    raise AnalyticalValidationError(
                        f"Sort column '{sort_col}' not recognized.",
                        details={"sort_column": sort_col, "valid_sort_targets": list(valid_sort_targets)},
                    )
