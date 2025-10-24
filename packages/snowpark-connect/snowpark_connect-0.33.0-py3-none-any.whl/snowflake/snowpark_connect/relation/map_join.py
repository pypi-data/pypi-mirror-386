#
# Copyright (c) 2012-2025 Snowflake Computing Inc. All rights reserved.
#
import dataclasses
from enum import Enum
from functools import reduce
from typing import Optional

import pyspark.sql.connect.proto.relations_pb2 as relation_proto
from pyspark.errors import AnalysisException

import snowflake.snowpark.functions as snowpark_fn
from snowflake import snowpark
from snowflake.snowpark.types import StructField, StructType
from snowflake.snowpark_connect.column_name_handler import (
    JoinColumnNameMap,
    make_unique_snowpark_name,
)
from snowflake.snowpark_connect.column_qualifier import ColumnQualifier
from snowflake.snowpark_connect.config import global_config
from snowflake.snowpark_connect.constants import COLUMN_METADATA_COLLISION_KEY
from snowflake.snowpark_connect.dataframe_container import DataFrameContainer
from snowflake.snowpark_connect.error.error_codes import ErrorCodes
from snowflake.snowpark_connect.error.error_utils import (
    SparkException,
    attach_custom_error_code,
)
from snowflake.snowpark_connect.expression.map_expression import (
    map_single_column_expression,
)
from snowflake.snowpark_connect.expression.typer import JoinExpressionTyper
from snowflake.snowpark_connect.relation.map_relation import (
    NATURAL_JOIN_TYPE_BASE,
    map_relation,
)
from snowflake.snowpark_connect.relation.read.metadata_utils import (
    filter_metadata_columns,
)
from snowflake.snowpark_connect.utils.context import (
    push_evaluating_join_condition,
    push_sql_scope,
    set_plan_id_map,
    set_sql_plan_name,
)
from snowflake.snowpark_connect.utils.telemetry import (
    SnowparkConnectNotImplementedError,
)

USING_COLUMN_NOT_FOUND_ERROR = "[UNRESOLVED_USING_COLUMN_FOR_JOIN] USING column `{0}` not found on the {1} side of the join. The {1}-side columns: {2}"


class ConditionType(Enum):
    USING_COLUMNS = 1
    JOIN_CONDITION = 2
    NO_CONDITION = 3


@dataclasses.dataclass
class JoinInfo:
    join_type: str
    condition_type: ConditionType
    join_columns: Optional[list[str]]

    def has_join_condition(self) -> bool:
        return self.condition_type == ConditionType.JOIN_CONDITION

    def is_using_columns(self):
        return self.condition_type == ConditionType.USING_COLUMNS


def map_join(rel: relation_proto.Relation) -> DataFrameContainer:
    left_container: DataFrameContainer = map_relation(rel.join.left)
    right_container: DataFrameContainer = map_relation(rel.join.right)

    # Remove any metadata columns(like metada$filename) present in the dataframes.
    # We cannot support inputfilename for multisources as each dataframe has it's own source.
    left_container = filter_metadata_columns(left_container)
    right_container = filter_metadata_columns(right_container)

    left_input: snowpark.DataFrame = left_container.dataframe
    right_input: snowpark.DataFrame = right_container.dataframe

    join_info = _get_join_info(rel, left_container, right_container)
    join_type = join_info.join_type

    if join_info.has_join_condition():
        left_columns = list(left_container.column_map.spark_to_col.keys())
        right_columns = list(right_container.column_map.spark_to_col.keys())

        # All PySpark join types are in the format of JOIN_TYPE_XXX.
        # We remove the first 10 characters (JOIN_TYPE_) and replace all underscores with spaces to match the exception.
        pyspark_join_type = relation_proto.Join.JoinType.Name(rel.join.join_type)[
            10:
        ].replace("_", " ")
        with push_sql_scope(), push_evaluating_join_condition(
            pyspark_join_type, left_columns, right_columns
        ):
            if left_container.alias is not None:
                set_sql_plan_name(left_container.alias, rel.join.left.common.plan_id)
            if right_container.alias is not None:
                set_sql_plan_name(right_container.alias, rel.join.right.common.plan_id)
            _, join_expression = map_single_column_expression(
                rel.join.join_condition,
                column_mapping=JoinColumnNameMap(
                    left_container.column_map,
                    right_container.column_map,
                ),
                typer=JoinExpressionTyper(left_input, right_input),
            )
        result: snowpark.DataFrame = left_input.join(
            right=right_input,
            on=join_expression.col,
            how="inner" if join_info.join_type == "cross" else join_info.join_type,
            lsuffix="_left",
            rsuffix="_right",
        )
    elif join_info.is_using_columns():
        # TODO: disambiguate snowpark columns for all join condition types
        # disambiguation temporarily done only for using_columns/natural joins to reduce changes
        left_container, right_container = _disambiguate_snowpark_columns(
            left_container, right_container
        )
        left_input = left_container.dataframe
        right_input = right_container.dataframe

        join_columns = join_info.join_columns

        def _validate_using_column(
            column: str, container: DataFrameContainer, side: str
        ) -> None:
            if (
                container.column_map.get_snowpark_column_name_from_spark_column_name(
                    column, allow_non_exists=True, return_first=True
                )
                is None
            ):
                exception = AnalysisException(
                    USING_COLUMN_NOT_FOUND_ERROR.format(
                        column, side, container.column_map.get_spark_columns()
                    )
                )
                attach_custom_error_code(exception, ErrorCodes.COLUMN_NOT_FOUND)
                raise exception

        for col in join_columns:
            _validate_using_column(col, left_container, "left")
            _validate_using_column(col, right_container, "right")

        # We cannot assume that Snowpark will have the same names for left and right columns,
        # so we convert ["a", "b"] into (left["a"] == right["a"] & left["b"] == right["b"]),
        # then drop right["a"] and right["b"].
        snowpark_using_columns = [
            (
                left_input[
                    left_container.column_map.get_snowpark_column_name_from_spark_column_name(
                        spark_name, return_first=True
                    )
                ],
                right_input[
                    right_container.column_map.get_snowpark_column_name_from_spark_column_name(
                        spark_name, return_first=True
                    )
                ],
            )
            for spark_name in join_columns
        ]
        joined_df = left_input.join(
            right=right_input,
            on=reduce(
                snowpark.Column.__and__,
                (left == right for left, right in snowpark_using_columns),
            ),
            how=join_type,
        )
        # For outer joins, we need to preserve join keys from both sides using COALESCE
        if join_type == "full_outer":
            coalesced_columns = []
            columns_to_drop = []
            for i, (left_col, right_col) in enumerate(snowpark_using_columns):
                # Use the original user-specified column name to preserve case sensitivity
                original_column_name = rel.join.using_columns[i]
                coalesced_col = snowpark_fn.coalesce(left_col, right_col).alias(
                    original_column_name
                )
                coalesced_columns.append(coalesced_col)
                columns_to_drop.extend([left_col, right_col])

            other_columns = [
                snowpark_fn.col(col_name)
                for col_name in joined_df.columns
                if col_name not in [col.getName() for col in columns_to_drop]
            ]
            result = joined_df.select(coalesced_columns + other_columns)
        else:
            result = joined_df.drop(*(right for _, right in snowpark_using_columns))
    else:
        if join_type != "cross" and not global_config.spark_sql_crossJoin_enabled:
            exception = SparkException.implicit_cartesian_product("inner")
            attach_custom_error_code(exception, ErrorCodes.UNSUPPORTED_OPERATION)
            raise exception
        # For outer joins without a condition, we need to use a TRUE condition
        # to match Spark's behavior.
        if join_type in ["left", "right", "full_outer"]:
            result: snowpark.DataFrame = left_input.join(
                right=right_input,
                on=snowpark_fn.lit(True),
                how=join_type,
            )
        else:
            result: snowpark.DataFrame = left_input.join(
                right=right_input,
                how=join_type,
            )

    if join_type in ["leftanti", "leftsemi"]:
        # Join types that only return columns from the left side:
        # - LEFT SEMI JOIN: Returns left rows that have matches in right table (no right columns)
        # - LEFT ANTI JOIN: Returns left rows that have NO matches in right table (no right columns)
        # Both preserve only the columns from the left DataFrame without adding any columns from the right.
        spark_cols_after_join: list[str] = left_container.column_map.get_spark_columns()
        qualifiers = left_container.column_map.get_qualifiers()
    else:
        if not join_info.is_using_columns():
            spark_cols_after_join: list[str] = (
                left_container.column_map.get_spark_columns()
                + right_container.column_map.get_spark_columns()
            )
            qualifiers: list[set[ColumnQualifier]] = (
                left_container.column_map.get_qualifiers()
                + right_container.column_map.get_qualifiers()
            )
        else:
            # get columns after join
            joined_columns = left_container.column_map.get_columns_after_join(
                right_container.column_map, join_info.join_columns
            )
            spark_cols_after_join: list[str] = [c.spark_name for c in joined_columns]
            qualifiers: list[set[ColumnQualifier]] = [
                c.qualifiers for c in joined_columns
            ]

    column_metadata = dict(left_container.column_map.column_metadata or {})
    if right_container.column_map.column_metadata:
        for key, value in right_container.column_map.column_metadata.items():
            if key not in column_metadata:
                column_metadata[key] = value
            else:
                # In case of collision, use snowpark's column's expr_id as prefix.
                # this is a temporary solution until SNOW-1926440 is resolved.
                try:
                    snowpark_name = right_container.column_map.get_snowpark_column_name_from_spark_column_name(
                        key
                    )
                    expr_id = right_input[snowpark_name]._expression.expr_id
                    updated_key = COLUMN_METADATA_COLLISION_KEY.format(
                        expr_id=expr_id, key=snowpark_name
                    )
                    column_metadata[updated_key] = value
                except Exception:
                    # ignore any errors that happens while fetching the metadata
                    pass

    result_container = DataFrameContainer.create_with_column_mapping(
        dataframe=result,
        spark_column_names=spark_cols_after_join,
        snowpark_column_names=result.columns,
        column_metadata=column_metadata,
        column_qualifiers=qualifiers,
    )

    # Fix for USING join column references with different plan IDs
    # After a USING join, references to the right dataframe's columns should resolve
    # to the result dataframe that contains the merged columns
    if (
        join_info.is_using_columns()
        and rel.join.right.HasField("common")
        and rel.join.right.common.HasField("plan_id")
    ):
        right_plan_id = rel.join.right.common.plan_id
        set_plan_id_map(right_plan_id, result_container)

    # For FULL OUTER joins, we also need to map the left dataframe's plan_id
    # since both columns are replaced with a coalesced column
    if (
        join_info.is_using_columns()
        and join_type == "full_outer"
        and rel.join.left.HasField("common")
        and rel.join.left.common.HasField("plan_id")
    ):
        left_plan_id = rel.join.left.common.plan_id
        set_plan_id_map(left_plan_id, result_container)

    if join_info.is_using_columns():
        # When join 'using_columns', the 'join columns' should go first in result DF.
        # we're only shifting left side columns, since we dropped the right-side ones
        idxs_to_shift = left_container.column_map.get_column_indexes(
            join_info.join_columns
        )

        def reorder(lst: list) -> list:
            to_move = [lst[i] for i in idxs_to_shift]
            remaining = [el for i, el in enumerate(lst) if i not in idxs_to_shift]
            return to_move + remaining

        # Create reordered DataFrame
        reordered_df = result_container.dataframe.select(
            [snowpark_fn.col(c) for c in reorder(result_container.dataframe.columns)]
        )

        # Create new container with reordered metadata
        original_df = result_container.dataframe
        return DataFrameContainer.create_with_column_mapping(
            dataframe=reordered_df,
            spark_column_names=reorder(result_container.column_map.get_spark_columns()),
            snowpark_column_names=reorder(
                result_container.column_map.get_snowpark_columns()
            ),
            column_metadata=column_metadata,
            column_qualifiers=reorder(qualifiers),
            table_name=result_container.table_name,
            cached_schema_getter=lambda: snowpark.types.StructType(
                reorder(original_df.schema.fields)
            ),
        )

    return result_container


def _get_join_info(
    rel: relation_proto.Relation, left: DataFrameContainer, right: DataFrameContainer
) -> JoinInfo:
    """
    Gathers basic information about the join, and performs basic assertions
    """

    is_natural_join = rel.join.join_type >= NATURAL_JOIN_TYPE_BASE
    join_columns = rel.join.using_columns
    if is_natural_join:
        rel.join.join_type -= NATURAL_JOIN_TYPE_BASE
        left_spark_columns = left.column_map.get_spark_columns()
        right_spark_columns = right.column_map.get_spark_columns()
        common_spark_columns = [
            x for x in left_spark_columns if x in right_spark_columns
        ]
        join_columns = common_spark_columns

    match rel.join.join_type:
        case relation_proto.Join.JOIN_TYPE_UNSPECIFIED:
            # TODO: Understand what UNSPECIFIED Join type is
            exception = SnowparkConnectNotImplementedError("Unspecified Join Type")
            attach_custom_error_code(exception, ErrorCodes.UNSUPPORTED_OPERATION)
            raise exception
        case relation_proto.Join.JOIN_TYPE_INNER:
            join_type = "inner"
        case relation_proto.Join.JOIN_TYPE_FULL_OUTER:
            join_type = "full_outer"
        case relation_proto.Join.JOIN_TYPE_LEFT_OUTER:
            join_type = "left"
        case relation_proto.Join.JOIN_TYPE_RIGHT_OUTER:
            join_type = "right"
        case relation_proto.Join.JOIN_TYPE_LEFT_ANTI:
            join_type = "leftanti"
        case relation_proto.Join.JOIN_TYPE_LEFT_SEMI:
            join_type = "leftsemi"
        case relation_proto.Join.JOIN_TYPE_CROSS:
            join_type = "cross"
        case other:
            exception = SnowparkConnectNotImplementedError(f"Other Join Type: {other}")
            attach_custom_error_code(exception, ErrorCodes.UNSUPPORTED_OPERATION)
            raise exception

    has_join_condition = rel.join.HasField("join_condition")
    is_using_columns = bool(join_columns)

    if has_join_condition:
        assert not is_using_columns

    condition_type = ConditionType.NO_CONDITION
    if has_join_condition:
        condition_type = ConditionType.JOIN_CONDITION
    elif is_using_columns:
        condition_type = ConditionType.USING_COLUMNS

    return JoinInfo(join_type, condition_type, join_columns)


def _disambiguate_snowpark_columns(
    left: DataFrameContainer, right: DataFrameContainer
) -> tuple[DataFrameContainer, DataFrameContainer]:
    conflicting_snowpark_columns = left.column_map.get_conflicting_snowpark_columns(
        right.column_map
    )

    if not conflicting_snowpark_columns:
        return left, right

    # rename and create new containers
    return _disambiguate_container(
        left, conflicting_snowpark_columns
    ), _disambiguate_container(right, conflicting_snowpark_columns)


def _disambiguate_container(
    container: DataFrameContainer, conflicting_snowpark_columns: set[str]
) -> DataFrameContainer:
    column_map = container.column_map
    disambiguated_columns = []
    disambiguated_snowpark_names = []
    for c in column_map.columns:
        if c.snowpark_name in conflicting_snowpark_columns:
            # alias snowpark column with a new unique name
            new_name = make_unique_snowpark_name(c.spark_name)
            disambiguated_snowpark_names.append(new_name)
            disambiguated_columns.append(
                snowpark_fn.col(c.snowpark_name).alias(new_name)
            )
        else:
            disambiguated_snowpark_names.append(c.snowpark_name)
            disambiguated_columns.append(snowpark_fn.col(c.snowpark_name))

    disambiguated_df = container.dataframe.select(*disambiguated_columns)

    def _get_new_schema():
        old_schema = container.dataframe.schema
        if not old_schema.fields:
            return StructType([])

        new_fields = []
        for i, name in enumerate(disambiguated_snowpark_names):
            f = old_schema.fields[i]
            new_fields.append(
                StructField(name, f.datatype, nullable=f.nullable, _is_column=True)
            )
        return StructType(new_fields)

    return DataFrameContainer.create_with_column_mapping(
        dataframe=disambiguated_df,
        spark_column_names=column_map.get_spark_columns(),
        snowpark_column_names=disambiguated_snowpark_names,
        column_metadata=column_map.column_metadata,
        column_qualifiers=column_map.get_qualifiers(),
        table_name=container.table_name,
        cached_schema_getter=_get_new_schema,
    )
