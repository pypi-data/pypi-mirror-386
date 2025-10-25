#  Copyright 2022-present, the Waterdip Labs Pvt. Ltd.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from typing import Iterator, Optional, Sequence, Tuple, Union

from data_diff.abcs.database_types import DbPath, DbTime
from data_diff.databases import Database
from data_diff.databases._connect import connect
from data_diff.diff_tables import Algorithm
from data_diff.hashdiff_tables import (
    DEAFULT_TIMEOUT,
    DEFAULT_BISECTION_FACTOR,
    DEFAULT_BISECTION_THRESHOLD,
    DEFAULT_ENGRESS_LIMIT,
    DEFAULT_PER_COLUMN_DIFF_LIMIT,
    HashDiffer,
)
from data_diff.joindiff_tables import TABLE_WRITE_LIMIT, JoinDiffer
from data_diff.table_segment import TableSegment
from data_diff.utils import Vector, eval_name_template


def connect_to_table(
    db_info: Union[str, dict],
    table_name: Union[DbPath, str],
    key_columns: str = ("id",),
    thread_count: Optional[int] = 1,
    **kwargs,
) -> TableSegment:
    """Connects to the given database, and creates a TableSegment instance

    Parameters:
        db_info: Either a URI string, or a dict of connection options.
        table_name: Name of the table as a string, or a tuple that signifies the path.
        key_columns: Names of the key columns
        thread_count: Number of threads for this connection (only if using a threadpooled db implementation)

    See Also:
        :meth:`connect`
    """
    if isinstance(db_info, dict):
        keys_to_remove = [k for k, v in db_info.items() if v is None]
        for k in keys_to_remove:
            db_info.pop(k)
    if isinstance(key_columns, str):
        key_columns = (key_columns,)

    db: Database = connect(db_info, thread_count=thread_count)

    if isinstance(table_name, str):
        table_name = db.dialect.parse_table_name(table_name)

    return TableSegment(db, table_name, key_columns, **kwargs)


def diff_tables(
    table1: TableSegment,
    table2: TableSegment,
    *,
    # Name of the key column, which uniquely identifies each row (usually id)
    key_columns: Sequence[str] = None,
    # Name of updated column, which signals that rows changed (usually updated_at or last_update)
    update_column: str = None,
    # Extra columns to compare
    extra_columns: Tuple[str, ...] = None,
    # Start/end key_column values, used to restrict the segment
    min_key: Vector = None,
    max_key: Vector = None,
    # Start/end update_column values, used to restrict the segment
    min_update: DbTime = None,
    max_update: DbTime = None,
    # Enable/disable threaded diffing. Needed to take advantage of database threads.
    threaded: bool = True,
    # Maximum size of each threadpool. None = auto. Only relevant when threaded is True.
    # There may be many pools, so number of actual threads can be a lot higher.
    max_threadpool_size: Optional[int] = 1,
    # Algorithm
    algorithm: Algorithm = Algorithm.AUTO,
    # An additional 'where' expression to restrict the search space.
    where: str = None,
    # Into how many segments to bisect per iteration (hashdiff only)
    bisection_factor: int = DEFAULT_BISECTION_FACTOR,
    # When should we stop bisecting and compare locally (in row count; hashdiff only)
    bisection_threshold: int = DEFAULT_BISECTION_THRESHOLD,
    # Enable/disable validating that the key columns are unique. (joindiff only)
    validate_unique_key: bool = True,
    # Enable/disable sampling of exclusive rows. Creates a temporary table. (joindiff only)
    sample_exclusive_rows: bool = False,
    # Path of new table to write diff results to. Disabled if not provided. (joindiff only)
    materialize_to_table: Union[str, DbPath] = None,
    # Materialize every row, not just those that are different. (joindiff only)
    materialize_all_rows: bool = False,
    # Maximum number of rows to write when materializing, per thread. (joindiff only)
    table_write_limit: int = TABLE_WRITE_LIMIT,
    # Skips diffing any rows with null keys. (joindiff only)
    skip_null_keys: bool = False,
    # Type check
    strict: bool = True,
    # Maximum number diff per column
    per_column_diff_limit: int = DEFAULT_PER_COLUMN_DIFF_LIMIT,
    # Maximum number of rows to download
    egress_limit: int = DEFAULT_ENGRESS_LIMIT,
    # Timeout limit in minutes
    # (used for diffing large tables, to avoid long-running queries)
    timeout_limit: int = DEAFULT_TIMEOUT,
    in_memory_diff: bool = False,
) -> Iterator:
    """Finds the diff between table1 and table2.

    Parameters:
        key_columns (Tuple[str, ...]): Name of the key column, which uniquely identifies each row (usually id)
        update_column (str, optional): Name of updated column, which signals that rows changed.
                                       Usually updated_at or last_update.  Used by `min_update` and `max_update`.
        extra_columns (Tuple[str, ...], optional): Extra columns to compare
        min_key (:data:`Vector`, optional): Lowest key value, used to restrict the segment
        max_key (:data:`Vector`, optional): Highest key value, used to restrict the segment
        min_update (:data:`DbTime`, optional): Lowest update_column value, used to restrict the segment
        max_update (:data:`DbTime`, optional): Highest update_column value, used to restrict the segment
        threaded (bool): Enable/disable threaded diffing. Needed to take advantage of database threads.
        max_threadpool_size (int): Maximum size of each threadpool. ``None`` means auto.
                                   Only relevant when `threaded` is ``True``.
                                   There may be many pools, so number of actual threads can be a lot higher.
        where (str, optional): An additional 'where' expression to restrict the search space.
        algorithm (:class:`Algorithm`): Which diffing algorithm to use (`HASHDIFF` or `JOINDIFF`. Default=`AUTO`)
        bisection_factor (int): Into how many segments to bisect per iteration. (Used when algorithm is `HASHDIFF`)
        bisection_threshold (Number): Minimal row count of segment to bisect, otherwise download
                                      and compare locally. (Used when algorithm is `HASHDIFF`).
        validate_unique_key (bool): Enable/disable validating that the key columns are unique. (used for `JOINDIFF`. default: True)
                                    Single query, and can't be threaded, so it's very slow on non-cloud dbs.
                                    Future versions will detect UNIQUE constraints in the schema.
        sample_exclusive_rows (bool): Enable/disable sampling of exclusive rows. Creates a temporary table. (used for `JOINDIFF`. default: False)
        materialize_to_table (Union[str, DbPath], optional): Path of new table to write diff results to. Disabled if not provided. Used for `JOINDIFF`.
        materialize_all_rows (bool): Materialize every row, not just those that are different. (used for `JOINDIFF`. default: False)
        table_write_limit (int): Maximum number of rows to write when materializing, per thread.
        skip_null_keys (bool): Skips diffing any rows with null PKs (displays a warning if any are null) (used for `JOINDIFF`. default: False)

    Note:
        The following parameters are used to override the corresponding attributes of the given :class:`TableSegment` instances:
        `key_columns`, `update_column`, `extra_columns`, `min_key`, `max_key`, `where`.
        If different values are needed per table, it's possible to omit them here, and instead set
        them directly when creating each :class:`TableSegment`.

    Example:
        >>> table1 = connect_to_table('postgresql:///', 'Rating', 'id')
        >>> list(diff_tables(table1, table1))
        []

    See Also:
        :class:`TableSegment`
        :class:`HashDiffer`
        :class:`JoinDiffer`

    """
    if isinstance(key_columns, str):
        key_columns = (key_columns,)

    tables = [table1, table2]
    override_attrs = {
        k: v
        for k, v in dict(
            key_columns=key_columns,
            update_column=update_column,
            extra_columns=extra_columns,
            min_key=min_key,
            max_key=max_key,
            min_update=min_update,
            max_update=max_update,
            where=where,
        ).items()
        if v is not None
    }

    segments = [t.new(**override_attrs) for t in tables] if override_attrs else tables

    algorithm = Algorithm(algorithm)
    if algorithm == Algorithm.AUTO:
        algorithm = Algorithm.JOINDIFF if table1.database is table2.database else Algorithm.HASHDIFF

    if algorithm == Algorithm.HASHDIFF:
        differ = HashDiffer(
            bisection_factor=bisection_factor,
            bisection_threshold=bisection_threshold,
            threaded=threaded,
            max_threadpool_size=max_threadpool_size,
            strict=strict,
            t1_row_count=table1.count(),
            t2_row_count=table2.count(),
            per_column_diff_limit=per_column_diff_limit,
            egress_limit=egress_limit,
            timeout_limit=timeout_limit,
            in_memory_diff=in_memory_diff,
        )
    elif algorithm == Algorithm.JOINDIFF:
        if isinstance(materialize_to_table, str):
            table_name = eval_name_template(materialize_to_table)
            materialize_to_table = table1.database.dialect.parse_table_name(table_name)
        differ = JoinDiffer(
            threaded=threaded,
            max_threadpool_size=max_threadpool_size,
            validate_unique_key=validate_unique_key,
            sample_exclusive_rows=sample_exclusive_rows,
            materialize_to_table=materialize_to_table,
            materialize_all_rows=materialize_all_rows,
            table_write_limit=table_write_limit,
            skip_null_keys=skip_null_keys,
        )
    else:
        raise ValueError(f"Unknown algorithm: {algorithm}")

    return differ.diff_tables(*segments)
