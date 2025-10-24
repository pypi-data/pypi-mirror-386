#
# Copyright (c) 2012-2025 Snowflake Computing Inc. All rights reserved.
#

from __future__ import annotations

import re
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass
from functools import cached_property

from pyspark.errors.exceptions.base import AnalysisException

from snowflake.snowpark import DataFrame
from snowflake.snowpark._internal.analyzer.analyzer_utils import unquote_if_quoted
from snowflake.snowpark._internal.utils import quote_name
from snowflake.snowpark.types import StructType
from snowflake.snowpark_connect.column_qualifier import ColumnQualifier
from snowflake.snowpark_connect.config import global_config
from snowflake.snowpark_connect.error.error_codes import ErrorCodes
from snowflake.snowpark_connect.error.error_utils import attach_custom_error_code
from snowflake.snowpark_connect.utils.context import (
    get_current_operation_scope,
    get_is_processing_order_by,
)
from snowflake.snowpark_connect.utils.identifiers import (
    split_fully_qualified_spark_name,
)
from snowflake.snowpark_connect.utils.sequence import next_unique_num

ALREADY_QUOTED = re.compile('^(".+")$', re.DOTALL)


def schema_getter(df: DataFrame) -> Callable[[], StructType]:
    schema_property = type(df).schema
    getter = schema_property.func
    return lambda: getter(df)


def set_schema_getter(df: DataFrame, get_schema: Callable[[], StructType]) -> None:
    class PatchedDataFrame(type(df)):
        @cached_property
        def schema(self):
            return get_schema()

    df.__class__ = PatchedDataFrame


# TODO replace plan_id-offset with single unique value
def make_column_names_snowpark_compatible(
    names: list[str], plan_id: int, offset: int = 0
) -> list[str]:
    """
    Create Snowpark column names for the given Spark column names. We have several requirements for Snowpark names:
    - need to be unique even if Spark names have duplicates
    - need to be unique across different dataframes, to handle correlated subqueries correctly
    - should contain Spark names for debugging purposes
    To satisfy these, we append the plan ID and the column index to the Spark column name.

    For example: Spark columns [a, b, c] in plan ID 5 will be converted to ["a-00000005-0", "b-00000005-1", "c-00000005-2"].

    The offset argument is used to offset the column index. It should be set to non-zero when generating new column
    names for an existing dataframe to avoid potential naming conflict.

    For example: Suppose we have a dataframe `df` with plan_id=5 that contains column a and b.
        Now we need to append a few more columns to the dataframe, which is very common in unpivot and withColumn.
        `df.unpivot(['a', 'b'], None, 'a', 'b')` will result in this Spark dataframe:
        +---+---+---+---+
        |  a|  b|  a|  b|
        +---+---+---+---+
        ...
        +---+---+---+---+
        To avoid duplicated column names, the corresponding Snowpark dataframe should be:
        +-------------+-------------+-------------+-------------+
        | a-00000005-0| b-00000005-1| a-00000005-2| b-00000005-3|
        +-------------+-------------+-------------+-------------+
        ...
        +-------------+-------------+-------------+-------------+
        In this case the function call should be `make_column_names_snowpark_compatible(['a', 'b'], 5, 2)`,
        to avoid naming conflicts between the new columns and the old columns.
    """
    from snowflake.snowpark_connect.relation.read.metadata_utils import (
        METADATA_FILENAME_COLUMN,
    )

    return [
        # Skip METADATA$FILENAME - preserve original name without quoting
        name if name == METADATA_FILENAME_COLUMN else
        # Use `-` in the name to force df.column to return double-quoted names
        quote_name(f"{unquote_if_quoted(name)}-{plan_id:08x}-{i + offset}")
        for i, name in enumerate(names)
    ]


def make_unique_snowpark_name(spark_name: str) -> str:
    """
    Returns a snowpark column name that's guaranteed to be unique in this session,
    by appending "#<unique number>" to the given spark name.
    """
    return quote_name(f"{spark_name}#{next_unique_num()}")


@dataclass(frozen=True)
class ColumnNames:
    spark_name: str
    snowpark_name: str
    qualifiers: set[ColumnQualifier]
    catalog_info: str | None = None  # Catalog from fully qualified name
    database_info: str | None = None  # Database from fully qualified name

    def all_spark_names_including_qualified_names(self):
        all_names = [self.spark_name]
        for qualifier in self.qualifiers:
            all_names.extend(qualifier.all_qualified_names(self.spark_name))
        return all_names


class ColumnNameMap:
    def __init__(
        self,
        spark_column_names: list[str],
        snowpark_column_names: list[str],
        is_case_sensitive: Callable[
            [], bool
        ] = lambda: global_config.spark_sql_caseSensitive,
        column_metadata: dict | None = None,
        column_qualifiers: list[set[ColumnQualifier]] = None,
        parent_column_name_map: ColumnNameMap | None = None,
    ) -> None:
        """
        spark_column_names: Original spark column names
        snowpark_column_names: Snowpark column names
        column_metadata: This field is used to store metadata related to columns. Since Snowpark's Struct type does not support metadata,
        we use this attribute to store any metadata related to the columns.
        The key is the original Spark column name, and the value is the metadata.
        example: Dict('age', {'foo': 'bar'})
        column_qualifiers: Optional qualifiers for the columns, used to handle table aliases or DataFrame aliases.
        parent_column_name_map: parent ColumnNameMap
        """
        self.columns: list[ColumnNames] = []
        self.spark_to_col: defaultdict[str, list[ColumnNames]] = defaultdict(list)
        self.uppercase_spark_to_col = defaultdict(list)
        self.snowpark_to_col = defaultdict(list)
        self.is_case_sensitive = is_case_sensitive
        self.column_metadata = column_metadata

        # Rename chain dictionary to track column renaming history
        self.rename_chains: dict[str, str] = {}  # old_name -> new_name mapping
        self.current_columns: set[str] = set()  # current column names

        # Parent ColumnNameMap classes
        self._parent_column_name_map = parent_column_name_map

        assert len(spark_column_names) == (
            len(column_qualifiers) if column_qualifiers else len(snowpark_column_names)
        ), (
            "Number of Spark column names must match number of Snowpark column names and "
            "number of column qualifiers if provided."
        )

        for i in range(len(spark_column_names)):
            # Extract catalog/database info from fully qualified spark column names
            spark_name = spark_column_names[i]
            catalog_info = None
            database_info = None

            # Parse fully qualified names to extract catalog.database.table.column format
            name_parts = split_fully_qualified_spark_name(spark_name)
            if len(name_parts) >= 4:
                # Format: catalog.database.table.column[.field...]
                # Only extract if this looks like a valid SQL table reference
                # Catalog.database.column (3 parts) is invalid - missing table
                # Only catalog.database.table.column (4+ parts) is potentially valid
                catalog_info = name_parts[0]
                database_info = name_parts[1]

            c = ColumnNames(
                spark_name=spark_name,
                snowpark_name=snowpark_column_names[i],
                qualifiers=column_qualifiers[i]
                if column_qualifiers and column_qualifiers[i]
                else set(),
                catalog_info=catalog_info,
                database_info=database_info,
            )
            self.columns.append(c)

            for spark_name in c.all_spark_names_including_qualified_names():
                # the same spark name can map to multiple snowpark names
                self.spark_to_col[spark_name].append(c)
                self.uppercase_spark_to_col[spark_name.upper()].append(c)

            # the same snowpark name can map to multiple spark column
            # e.g. df.select(date_format('dt', 'yyy'), date_format('dt', 'yyyy')) ->
            # [
            #   to_char( TRY_CAST (to_char("dt-0") AS TIMESTAMP), 'YYYY'),
            #   to_char( TRY_CAST (to_char("dt-0") AS TIMESTAMP), 'YYYY'),
            # ]
            self.snowpark_to_col[c.snowpark_name].append(c)

            self.current_columns.add(c.spark_name)

        if not global_config.spark_sql_caseSensitive:
            # Store the current column names in lowercase for case-insensitive lookups
            self.current_columns = {col.lower() for col in self.current_columns}

    def get_parent_column_name_map(self) -> ColumnNameMap | None:
        return self._parent_column_name_map

    def get_current_column_name(self, historical_name: str) -> str:
        """
        Follow the rename chain to get the most current name for a column.

        Args:
            historical_name: A possibly historical column name

        Returns:
            The most current name for this column after following the rename chain
        """
        current = (
            historical_name
            if global_config.spark_sql_caseSensitive
            else historical_name.lower()
        )
        visited = set()  # Prevent infinite loops in case of circular references

        while current in self.rename_chains and current not in visited:
            visited.add(current)
            current = self.rename_chains[current]

        return current

    @staticmethod
    def _allows_historical_name_lookup(operation: str) -> bool:
        """
        Determines if an operation should use historical name resolution based on
        observed Spark behavior.

        Args:
            operation: The operation type (e.g., 'filter', 'select', 'join')
            expr_context: Optional context about the expression (e.g., 'function_arg')

        Returns:
            True if historical name lookup should be used
        """
        # Operations that can use historical name lookup
        # Add more operations to this as needed.
        ops_with_history_lookup_support = [
            "filter",  # filter(col("old_name") === lit("value"))
            "sort",  # sort(col("old_name"))
            "orderBy",  # orderBy(col("old_name"))
            "with_columns_renamed",  # .withColumnRenamed("name", "new_name")
        ]
        return operation in ops_with_history_lookup_support

    def resolve_column_name(self, column_name: str) -> str | None:
        """
        Resolve a column name based on operation context, applying historical
        name lookup when appropriate according to Spark's behavior.
        Returns:
            The resolved column name or original column name if column name is not found in the rename history.
        """
        column_name = (
            column_name
            if global_config.spark_sql_caseSensitive
            else column_name.lower()
        )
        if column_name in self.current_columns:
            return column_name

        operation = get_current_operation_scope()
        if self._allows_historical_name_lookup(operation):
            current_name = self.get_current_column_name(column_name)
            if current_name != column_name:
                if current_name in self.current_columns:
                    return current_name

        return column_name

    def get_snowpark_column_names_from_spark_column_names(
        self,
        spark_column_names: list[str],
        return_first: bool = False,
    ) -> list[str]:
        snowpark_column_names = self._get_snowpark_column_names_from_spark_column_names(
            spark_column_names, return_first
        )
        if snowpark_column_names:
            return snowpark_column_names

        current_operation = get_current_operation_scope()

        # If Spark column name was not found in the current ColumnNameMap and current operation
        # allows it, perform a reverse DFS lookup
        if (
            self._allows_historical_name_lookup(current_operation)
            and self._parent_column_name_map is not None
        ):
            snowpark_column_names = self._parent_column_name_map.get_snowpark_column_names_from_spark_column_names(
                spark_column_names, return_first
            )

        return snowpark_column_names

    def _get_snowpark_column_names_from_spark_column_names(
        self,
        spark_column_names: list[str],
        return_first: bool = False,
    ) -> list[str]:
        snowpark_column_names = []
        for name in spark_column_names:
            if not global_config.spark_sql_caseSensitive:
                name = name.upper()
                mapping = self.uppercase_spark_to_col
            else:
                mapping = self.spark_to_col
            if name not in mapping:
                # column may still be prefixed with df alias, but we don't know that here
                continue

            columns = mapping[name]

            if return_first:
                snowpark_column_names.append(columns[0].snowpark_name)
            else:
                snowpark_column_names.extend([c.snowpark_name for c in columns])

        return snowpark_column_names

    def get_snowpark_column_name_from_spark_column_name(
        self,
        spark_column_name: str,
        *,
        allow_non_exists: bool = False,
        return_first: bool = False,
    ) -> str | None:
        assert isinstance(spark_column_name, str)
        resolved_name = (
            self.resolve_column_name(spark_column_name)
            if self.rename_chains
            else spark_column_name
        )
        snowpark_names = self.get_snowpark_column_names_from_spark_column_names(
            [resolved_name], return_first
        )

        snowpark_names_len = len(snowpark_names)
        if snowpark_names_len > 1:
            # Check if this is a case where we have identical expressions that can be safely resolved to the first one
            # This commonly happens with GROUP BY expressions that also appear in SELECT clauses
            if (
                get_is_processing_order_by()
                and self._can_resolve_ambiguous_identical_expressions(
                    resolved_name, snowpark_names
                )
            ):
                # All the ambiguous columns represent the same expression, so we can safely use the first one
                return snowpark_names[0]
            else:
                exception = AnalysisException(
                    f"Ambiguous spark column name {spark_column_name}, potential snowpark column names {snowpark_names}"
                )
                attach_custom_error_code(exception, ErrorCodes.AMBIGUOUS_COLUMN_NAME)
                raise exception
        elif snowpark_names_len == 0:
            if allow_non_exists:
                return None
            else:
                exception = AnalysisException(
                    f"Spark column name {spark_column_name} does not exist"
                )
                attach_custom_error_code(exception, ErrorCodes.COLUMN_NOT_FOUND)
                raise exception
        return snowpark_names[0]

    def _can_resolve_ambiguous_identical_expressions(
        self, spark_column_name: str, snowpark_names: list[str]
    ) -> bool:
        """
        Determine if ambiguous columns represent identical expressions that can be safely resolved to the first one.

        This handles the common case where the same expression (like a UDF call) appears multiple times
        in a SELECT clause within a GROUP BY query. Since they're the same expression operating on the
        same grouped data, they will have identical values, so we can safely resolve to any of them.

        Args:
            spark_column_name: The Spark column name that has multiple mappings, make sure resolve this reforehand
            snowpark_names: List of Snowpark column names that map to this Spark column name

        Returns:
            True if we can safely resolve to the first snowpark column, False otherwise
        """
        if spark_column_name not in self.spark_to_col:
            return False

        columns: list[ColumnNames] = self.spark_to_col[spark_column_name]

        # If we don't have multiple columns, there's no ambiguity to resolve
        if len(columns) <= 1:
            return False

        # Check if all the snowpark names correspond to columns that have identical underlying expressions
        # We'll compare the actual column objects to see if they represent the same computation
        first_column = columns[0]

        for column in columns[1:]:
            if first_column.qualifiers != column.qualifiers:
                return False

        # Additional safety check: ensure all snowpark names are actually in our mapping
        for snowpark_name in snowpark_names:
            if snowpark_name not in self.snowpark_to_col:
                return False

        # If we reach here, the columns appear to be identical expressions from the same context
        # This commonly happens in GROUP BY scenarios where the same expression appears in both
        # the grouping clause and the select clause
        return True

    def get_spark_column_names_from_snowpark_column_names(
        self,
        snowpark_column_names: list[str],
    ) -> list[str]:
        assert isinstance(snowpark_column_names, list)
        spark_column_names = []
        for n in snowpark_column_names:
            if n not in self.snowpark_to_col:
                continue

            spark_column_names.extend([c.spark_name for c in self.snowpark_to_col[n]])
        return spark_column_names

    def get_spark_column_name_from_snowpark_column_name(
        self,
        snowpark_column_name: str,
        allow_non_exists: bool = False,
    ) -> str | None:
        assert isinstance(snowpark_column_name, str)

        spark_names = self.get_spark_column_names_from_snowpark_column_names(
            [snowpark_column_name]
        )
        spark_names_len = len(spark_names)
        if spark_names_len > 1:
            exception = AnalysisException(
                f"Ambiguous snowpark column name {snowpark_column_name}, potential spark column names {spark_names}"
            )
            attach_custom_error_code(exception, ErrorCodes.AMBIGUOUS_COLUMN_NAME)
            raise exception
        elif spark_names_len == 0:
            if allow_non_exists:
                return None
            else:
                exception = AnalysisException(
                    f"Snowpark column name {snowpark_column_name} does not exist"
                )
                attach_custom_error_code(exception, ErrorCodes.COLUMN_NOT_FOUND)
                raise exception
        return spark_names[0]

    def get_spark_column_name(self, idx: int) -> str:
        return self.columns[idx].spark_name

    def get_spark_columns(self) -> list[str]:
        return [c.spark_name for c in self.columns]

    def get_spark_and_snowpark_columns_with_qualifier_for_qualifier(
        self, target_qualifier: ColumnQualifier
    ) -> tuple[list[str], list[str], list[set[ColumnQualifier]]]:
        """
        Returns the Spark and Snowpark column names along with their qualifiers for the specified qualifier.
        """
        spark_columns: list[str] = []
        snowpark_columns: list[str] = []
        qualifiers: list[set[ColumnQualifier]] = []

        normalized_qualifier = target_qualifier
        if not self.is_case_sensitive():
            normalized_qualifier = target_qualifier.to_upper()

        for column in self.columns:
            # Normalize all qualifiers for comparison
            column_qualifiers: set[ColumnQualifier] = (
                {q.to_upper() for q in iter(column.qualifiers)}
                if not self.is_case_sensitive()
                else column.qualifiers
            )
            if any([q.matches(normalized_qualifier) for q in column_qualifiers]):
                spark_columns.append(column.spark_name)
                snowpark_columns.append(column.snowpark_name)
                qualifiers.append(column.qualifiers)

        return spark_columns, snowpark_columns, qualifiers

    def get_snowpark_columns(self) -> list[str]:
        return [c.snowpark_name for c in self.columns]

    def get_snowpark_columns_after_drop(self, cols_to_drop: list[str]) -> list[str]:
        return [
            c
            for c in self.get_snowpark_columns()
            if self._quote_if_unquoted(c) not in cols_to_drop
        ]

    def get_qualifiers(self) -> list[set[ColumnQualifier]]:
        """
        Returns the qualifiers for the columns.
        """
        return [c.qualifiers for c in self.columns]

    def get_qualifiers_for_columns_after_drop(
        self, cols_to_drop: list[str]
    ) -> list[set[ColumnQualifier]]:
        """
        Returns the qualifiers for the columns after dropping the specified columns.
        """
        return [
            c.qualifiers
            for c in self.columns
            if self._quote_if_unquoted(c.snowpark_name) not in cols_to_drop
        ]

    def get_qualifiers_for_spark_column(
        self,
        spark_column_name: str,
    ) -> set[ColumnQualifier]:
        """
        Returns the qualifier for the specified Spark column name.
        If the column does not exist, returns empty ColumnQualifier.
        """
        if not self.is_case_sensitive():
            name = spark_column_name.upper()
            mapping = self.uppercase_spark_to_col
        else:
            name = spark_column_name
            mapping = self.spark_to_col

        col = mapping.get(name)

        if col is None or len(col) == 0:
            return set()

        return col[0].qualifiers

    @staticmethod
    def _quote_if_unquoted(s: str) -> str:
        if not ALREADY_QUOTED.match(s):
            s = s.replace('"', '\\"')
            return f'"{s}"'
        return s

    def has_spark_column(self, spark_column_name: str) -> bool:
        if self.is_case_sensitive():
            return spark_column_name in self.spark_to_col
        else:
            return spark_column_name.upper() in self.uppercase_spark_to_col

    def snowpark_to_spark_map(self) -> dict[str, str]:
        return {c.snowpark_name: c.spark_name for c in self.columns}

    def spark_to_snowpark_for_pattern(self, pattern: str) -> list[tuple[str, str]]:
        pattern_regex = re.compile(
            pattern, 0 if self.is_case_sensitive() else re.IGNORECASE
        )
        return [
            (c.spark_name, c.snowpark_name)
            for c in self.columns
            if pattern_regex.fullmatch(c.spark_name)
        ]

    def with_columns(
        self, new_spark_columns: list[str], new_snowpark_columns: list[str]
    ) -> tuple[list[str], list[str], list[set[ColumnQualifier]]]:
        """
        Returns an ordered list of spark and snowpark column names after adding the new columns through a withColumns call.
        All replaced columns retain their ordering in the dataframe. The new columns are added to the end of the list.
        """

        assert len(new_spark_columns) == len(new_snowpark_columns)

        spark_name_to_snowpark_name_map: dict[str, deque[int]] = {}

        for i, c in enumerate(new_spark_columns):
            column_name = self._normalized_spark_name(c)
            if column_name in spark_name_to_snowpark_name_map:
                spark_name_to_snowpark_name_map[column_name].append(i)
            else:
                spark_name_to_snowpark_name_map[column_name] = deque([i])

        spark_columns = []
        snowpark_columns = []
        removed_index: set[int] = set()
        qualifiers = []

        for c in self.columns:
            column_name = self._normalized_spark_name(c.spark_name)
            if column_name in spark_name_to_snowpark_name_map:
                index = spark_name_to_snowpark_name_map[column_name].popleft()
                removed_index.add(index)
                spark_columns.append(new_spark_columns[index])
                snowpark_columns.append(new_snowpark_columns[index])
                qualifiers.append(set())
            else:
                spark_columns.append(c.spark_name)
                snowpark_columns.append(c.snowpark_name)
                qualifiers.append(c.qualifiers)

        for i, _ in enumerate(new_spark_columns):
            if i not in removed_index:
                spark_columns.append(new_spark_columns[i])
                snowpark_columns.append(new_snowpark_columns[i])
                qualifiers.append(set())

        return spark_columns, snowpark_columns, qualifiers

    def _normalized_spark_name(self, spark_name: str) -> str:
        if self.is_case_sensitive():
            return spark_name
        else:
            return spark_name.upper()

    def get_columns_after_join(
        self, other: ColumnNameMap, join_columns: list[str]
    ) -> list[ColumnNames]:
        """
        Returns a list of columns (names and qualifiers) after a using_columns join with the given column map
        """

        join_column_names = {self._normalized_spark_name(c) for c in join_columns}
        other_join_columns: dict[str, ColumnNames] = {}
        other_remaining_columns: list[ColumnNames] = []
        for oc in other.columns:
            col_name = self._normalized_spark_name(oc.spark_name)
            # only take the first matching column
            if col_name in join_column_names and col_name not in other_join_columns:
                other_join_columns[col_name] = oc
            else:
                other_remaining_columns.append(oc)

        joined_columns: list[ColumnNames] = []
        visited: set[str] = set()
        # add local columns first, we're in the left side of the join
        for c in self.columns:
            col_name = self._normalized_spark_name(c.spark_name)
            if col_name in join_column_names and col_name not in visited:
                visited.add(col_name)
                qualifiers = c.qualifiers | other_join_columns[col_name].qualifiers
                joined_columns.append(
                    ColumnNames(c.spark_name, c.snowpark_name, qualifiers)
                )
            else:
                joined_columns.append(c)

        # add other columns, excluding join columns
        return joined_columns + other_remaining_columns

    def get_column_indexes(self, spark_names: list[str]) -> list[int]:
        """
        Returns the first positions of the given spark_names in this column mapping.
        Used to reorder columns after a using_columns join.
        """
        # mapping from normalized spark name ot the first index of the column in the mapping
        column_indexes = {}

        for i, c in enumerate(self.columns):
            col_name = self._normalized_spark_name(c.spark_name)
            if col_name not in column_indexes:
                column_indexes[col_name] = i

        # return indexes for given columns
        return [column_indexes[self._normalized_spark_name(c)] for c in spark_names]

    def get_conflicting_snowpark_columns(self, other: ColumnNameMap) -> set[str]:
        conflicting_columns = set()
        snowpark_names = {c.snowpark_name for c in self.columns}

        for c in other.columns:
            if c.snowpark_name in snowpark_names:
                conflicting_columns.add(c.snowpark_name)

        return conflicting_columns


class JoinColumnNameMap(ColumnNameMap):
    def __init__(
        self,
        left_colmap: ColumnNameMap,
        right_colmap: ColumnNameMap,
    ) -> None:
        self.left_column_mapping: ColumnNameMap = left_colmap
        self.right_column_mapping: ColumnNameMap = right_colmap

    def get_snowpark_column_name_from_spark_column_name(
        self,
        spark_column_name: str,
        *,
        allow_non_exists: bool = False,
        return_first: bool = False,
    ) -> str | None:
        snowpark_column_name_in_left = (
            self.left_column_mapping.get_snowpark_column_name_from_spark_column_name(
                spark_column_name,
                allow_non_exists=True,
            )
        )
        snowpark_column_name_in_right = (
            self.right_column_mapping.get_snowpark_column_name_from_spark_column_name(
                spark_column_name,
                allow_non_exists=True,
            )
        )

        if (
            snowpark_column_name_in_left is None
            and snowpark_column_name_in_right is None
        ):
            if allow_non_exists:
                return None
            else:
                exception = AnalysisException(
                    f"Spark column name {spark_column_name} does not exist in either left or right DataFrame"
                )
                attach_custom_error_code(exception, ErrorCodes.COLUMN_NOT_FOUND)
                raise exception

        if (snowpark_column_name_in_right is not None) and (
            snowpark_column_name_in_left is not None
        ):
            exception = AnalysisException(f"Ambiguous column name {spark_column_name}")
            attach_custom_error_code(exception, ErrorCodes.AMBIGUOUS_COLUMN_NAME)
            raise exception

        snowpark_name = (
            snowpark_column_name_in_right
            if snowpark_column_name_in_left is None
            else snowpark_column_name_in_left
        )

        # this means that the reference is for the column in right dataframe but same snowpark name exist in left dataframe as well
        # or vice versa, so we need to append _left or _right to the snowpark name
        if (
            snowpark_name in self.left_column_mapping.get_snowpark_columns()
            and snowpark_column_name_in_right is not None
        ):
            snowpark_name = quote_name(f"{unquote_if_quoted(snowpark_name)}_right")
        elif (
            snowpark_name in self.right_column_mapping.get_snowpark_columns()
            and snowpark_column_name_in_left is not None
        ):
            snowpark_name = quote_name(f"{unquote_if_quoted(snowpark_name)}_left")

        return snowpark_name

    def get_snowpark_column_names_from_spark_column_names(
        self, spark_column_names: list[str], return_first: bool = False
    ) -> list[str]:
        exception = NotImplementedError("Method not implemented!")
        attach_custom_error_code(exception, ErrorCodes.INTERNAL_ERROR)
        raise exception

    def get_spark_column_names_from_snowpark_column_names(
        self,
        snowpark_column_names: list[str],
    ) -> list[str]:
        exception = NotImplementedError("Method not implemented!")
        attach_custom_error_code(exception, ErrorCodes.INTERNAL_ERROR)
        raise exception

    def get_spark_column_name_from_snowpark_column_name(
        self,
        snowpark_column_name: str,
        allow_non_exists: bool = False,
    ) -> str:
        exception = NotImplementedError("Method not implemented!")
        attach_custom_error_code(exception, ErrorCodes.INTERNAL_ERROR)
        raise exception

    def get_spark_columns(self) -> list[str]:
        exception = NotImplementedError("Method not implemented!")
        attach_custom_error_code(exception, ErrorCodes.INTERNAL_ERROR)
        raise exception

    def get_snowpark_columns(self) -> list[str]:
        exception = NotImplementedError("Method not implemented!")
        attach_custom_error_code(exception, ErrorCodes.INTERNAL_ERROR)
        raise exception

    def get_snowpark_columns_after_drop(self, cols_to_drop: list[str]) -> list[str]:
        exception = NotImplementedError("Method not implemented!")
        attach_custom_error_code(exception, ErrorCodes.INTERNAL_ERROR)
        raise exception

    def get_renamed_nested_column_name(self, name) -> str | None:
        exception = NotImplementedError("Method not implemented!")
        attach_custom_error_code(exception, ErrorCodes.INTERNAL_ERROR)
        raise exception

    def has_spark_column(self, spark_column_name: str) -> bool:
        exception = NotImplementedError("Method not implemented!")
        attach_custom_error_code(exception, ErrorCodes.INTERNAL_ERROR)
        raise exception

    def snowpark_to_spark_map(self) -> dict[str, str]:
        exception = NotImplementedError("Method not implemented!")
        attach_custom_error_code(exception, ErrorCodes.INTERNAL_ERROR)
        raise exception

    def spark_to_snowpark_for_pattern(self, pattern: str) -> list[tuple[str, str]]:
        exception = NotImplementedError("Method not implemented!")
        attach_custom_error_code(exception, ErrorCodes.INTERNAL_ERROR)
        raise exception

    def with_columns(
        self, new_spark_columns: list[str], new_snowpark_columns: list[str]
    ) -> tuple[list[str], list[str], list[set[ColumnQualifier]]]:
        exception = NotImplementedError("Method not implemented!")
        attach_custom_error_code(exception, ErrorCodes.INTERNAL_ERROR)
        raise exception

    def get_qualifiers(self) -> list[set[ColumnQualifier]]:
        exception = NotImplementedError("Method not implemented!")
        attach_custom_error_code(exception, ErrorCodes.INTERNAL_ERROR)
        raise exception

    def get_qualifiers_for_columns_after_drop(
        self, cols_to_drop: list[str]
    ) -> list[set[ColumnQualifier]]:
        exception = NotImplementedError("Method not implemented!")
        attach_custom_error_code(exception, ErrorCodes.INTERNAL_ERROR)
        raise exception

    def get_spark_and_snowpark_columns_with_qualifier_for_qualifier(
        self, target_qualifier: list[str]
    ) -> tuple[list[str], list[str], list[set[ColumnQualifier]]]:
        exception = NotImplementedError("Method not implemented!")
        attach_custom_error_code(exception, ErrorCodes.INTERNAL_ERROR)
        raise exception

    def get_qualifiers_for_spark_column(
        self, spark_column_name: str
    ) -> set[ColumnQualifier]:
        qualifiers_left = self.left_column_mapping.get_qualifiers_for_spark_column(
            spark_column_name
        )
        qualifiers_right = self.right_column_mapping.get_qualifiers_for_spark_column(
            spark_column_name
        )

        if (len(qualifiers_left) > 0) and (len(qualifiers_right) > 0):
            exception = AnalysisException(f"Ambiguous column name {spark_column_name}")
            attach_custom_error_code(exception, ErrorCodes.AMBIGUOUS_COLUMN_NAME)
            raise exception

        return qualifiers_right if len(qualifiers_left) == 0 else qualifiers_left

    def get_columns_after_join(
        self, other: ColumnNameMap, join_columns: list[str]
    ) -> list[ColumnNames]:
        exception = NotImplementedError("Method not implemented!")
        attach_custom_error_code(exception, ErrorCodes.INTERNAL_ERROR)
        raise exception

    def get_column_indexes(self, spark_names: list[str]) -> list[int]:
        exception = NotImplementedError("Method not implemented!")
        attach_custom_error_code(exception, ErrorCodes.INTERNAL_ERROR)
        raise exception
