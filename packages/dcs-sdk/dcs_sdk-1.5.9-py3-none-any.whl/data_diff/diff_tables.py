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

"""Provides classes for performing a table diff"""

import threading
from abc import ABC, abstractmethod
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from enum import Enum
from operator import methodcaller
from typing import Any, Dict, Iterator, List, Optional, Set, Tuple, Union

import attrs

# logger = getLogger(__name__)
from loguru import logger

from data_diff.abcs.database_types import IKey, Integer, StringType
from data_diff.errors import DataDiffMismatchingKeyTypesError
from data_diff.info_tree import InfoTree, SegmentInfo
from data_diff.table_segment import TableSegment, create_mesh_from_points
from data_diff.thread_utils import ThreadedYielder
from data_diff.utils import Vector, getLogger, safezip


class Algorithm(Enum):
    AUTO = "auto"
    JOINDIFF = "joindiff"
    HASHDIFF = "hashdiff"


DiffResult = Iterator[Tuple[str, tuple]]  # Iterator[Tuple[Literal["+", "-"], tuple]]
DiffResultList = Iterator[List[Tuple[str, tuple]]]


@attrs.define(frozen=False)
class ThreadBase:
    "Provides utility methods for optional threading"

    threaded: bool = True
    max_threadpool_size: Optional[int] = 1

    def _thread_map(self, func, iterable):
        if not self.threaded:
            return map(func, iterable)

        with ThreadPoolExecutor(max_workers=self.max_threadpool_size) as task_pool:
            return task_pool.map(func, iterable)

    def _threaded_call(self, func, iterable):
        "Calls a method for each object in iterable."
        return list(self._thread_map(methodcaller(func), iterable))

    def _thread_as_completed(self, func, iterable):
        if not self.threaded:
            yield from map(func, iterable)
            return

        with ThreadPoolExecutor(max_workers=self.max_threadpool_size) as task_pool:
            futures = [task_pool.submit(func, item) for item in iterable]
            for future in as_completed(futures):
                yield future.result()

    def _threaded_call_as_completed(self, func, iterable):
        "Calls a method for each object in iterable. Returned in order of completion."
        return self._thread_as_completed(methodcaller(func), iterable)

    @contextmanager
    def _run_in_background(self, *funcs):
        with ThreadPoolExecutor(max_workers=self.max_threadpool_size) as task_pool:
            futures = [task_pool.submit(f) for f in funcs if f is not None]
            yield futures
            for f in futures:
                f.result()


@attrs.define(frozen=True)
class DiffStats:
    diff_by_sign: Dict[str, int]
    table1_count: int
    table2_count: int
    unchanged: int
    # diff_percent: float
    extra_column_diffs: Optional[Dict[str, int]]
    exclusive_source_ids: List[tuple]
    exclusive_target_ids: List[tuple]
    duplicate_source_ids: List[tuple]
    duplicate_target_ids: List[tuple]
    diff_values_ids: List[tuple]
    diff_pk_percent: float
    rows_downloaded: int
    comparison_tracker: Optional[List] = []


@attrs.define(frozen=True)
class DiffResultWrapper:
    diff: iter  # DiffResult
    info_tree: InfoTree
    stats: dict
    result_list: list = attrs.field(factory=list)

    def __iter__(self) -> Iterator[Any]:
        yield from self.result_list
        for i in self.diff:
            self.result_list.append(i)
            yield i

    def _get_stats(self) -> DiffStats:
        list(self)  # Consume the iterator into result_list, if we haven't already

        key_columns = self.info_tree.info.tables[0].key_columns
        len_key_columns = len(key_columns)
        diff_by_key = {}
        extra_column_values_store = {}
        extra_columns = self.info_tree.info.tables[0].extra_columns
        extra_column_diffs = {k: 0 for k in extra_columns}
        source_rows_by_key = defaultdict(int)
        target_rows_by_key = defaultdict(int)
        exclusive_source_ids = []
        exclusive_target_ids = []
        duplicate_source_ids = []
        duplicate_target_ids = []
        diff_values_ids = []

        for sign, values in self.result_list:
            k = values[:len_key_columns]
            if sign == "-":
                source_rows_by_key[k] += 1
            elif sign == "+":
                target_rows_by_key[k] += 1

        for sign, values in self.result_list:
            k = values[:len_key_columns]
            if sign == "-":
                if source_rows_by_key[k] > 1 and k not in duplicate_source_ids:
                    duplicate_source_ids.append(k)
                if k not in target_rows_by_key:
                    exclusive_source_ids.append(k)
            elif sign == "+":
                if target_rows_by_key[k] > 1 and k not in duplicate_target_ids:
                    duplicate_target_ids.append(k)
                if k not in source_rows_by_key:
                    exclusive_target_ids.append(k)

        for sign, values in self.result_list:
            k = values[:len_key_columns]
            if k in diff_by_key:
                if sign != diff_by_key[k]:
                    diff_by_key[k] = "!"
                    if source_rows_by_key[k] <= 1 and target_rows_by_key[k] <= 1:
                        diff_values_ids.append(k)
                        extra_column_values = values[len_key_columns:]
                        for i in range(0, len(extra_columns)):
                            if extra_column_values[i] != extra_column_values_store[k][i]:
                                extra_column_diffs[extra_columns[i]] += 1
            else:
                diff_by_key[k] = sign
                extra_column_values_store[k] = values[len_key_columns:]

        diff_by_sign = {k: 0 for k in "+-!"}
        for sign in diff_by_key.values():
            diff_by_sign[sign] += 1

        table1_count = self.info_tree.info.tables[0].count()
        table2_count = self.info_tree.info.tables[1].count()

        total_exclusive_pks = len(exclusive_source_ids) + len(exclusive_target_ids)
        total_source_unique_pks = table1_count - len(duplicate_source_ids)
        total_unique_pks = total_source_unique_pks + len(exclusive_target_ids)
        diff_pk_percent = (total_exclusive_pks / total_unique_pks) if total_unique_pks > 0 else 0.0
        differing_pks = diff_by_sign["!"]
        exclusive_pks = total_exclusive_pks
        unchanged = total_unique_pks - differing_pks - exclusive_pks
        # diff_percent = 1 - unchanged / max(table1_count, table2_count) if max(table1_count, table2_count) > 0 else 0.0
        rows_downloaded = self.stats.get("rows_downloaded", 0)
        comparison_tracker = self.stats.get("comparison_tracker", [])
        return DiffStats(
            diff_by_sign,
            table1_count,
            table2_count,
            unchanged,
            # diff_percent,
            extra_column_diffs,
            exclusive_source_ids,
            exclusive_target_ids,
            duplicate_source_ids,
            duplicate_target_ids,
            diff_values_ids,
            diff_pk_percent,
            rows_downloaded,
            comparison_tracker,
        )

    def get_stats_string(self):
        diff_stats = self._get_stats()

        string_output = ""
        # string_output += f"{diff_stats.table1_count} rows in table A\n"
        # string_output += f"{diff_stats.table2_count} rows in table B\n"
        string_output += f"{diff_stats.diff_by_sign['-']} rows exclusive to table A (not present in B)\n"
        string_output += f"{diff_stats.diff_by_sign['+']} rows exclusive to table B (not present in A)\n"
        string_output += f"{diff_stats.diff_by_sign['!']} rows updated\n"
        # string_output += f"{diff_stats.unchanged} rows unchanged\n"
        # string_output += f"{100*diff_stats.diff_percent:.2f}% difference score\n"

        # if self.stats:
        #     string_output += "\nExtra-Info:\n"
        #     for k, v in sorted(self.stats.items()):
        #         string_output += f"  {k} = {v}\n"
        for k, v in diff_stats.extra_column_diffs.items():
            string_output += f"{v} rows with different values in column: {k}\n"
        json_output = {
            "rows_A": diff_stats.table1_count,
            "rows_B": diff_stats.table2_count,
            "exclusive_A": diff_stats.diff_by_sign["-"],
            "exclusive_B": diff_stats.diff_by_sign["+"],
            "updated": diff_stats.diff_by_sign["!"],
            "total": sum(diff_stats.diff_by_sign.values()),
        }
        json_output["values"] = diff_stats.extra_column_diffs or {}
        return string_output, json_output

    def get_stats_dict(self):
        diff_stats = self._get_stats()
        json_output = {
            "rows_A": diff_stats.table1_count,
            "rows_B": diff_stats.table2_count,
            "exclusive_A": diff_stats.diff_by_sign["-"],
            "exclusive_B": diff_stats.diff_by_sign["+"],
            # "updated": diff_stats.diff_by_sign["!"],
            # "total": sum(diff_stats.diff_by_sign.values()),
            "exclusive_source_ids": diff_stats.exclusive_source_ids,
            "exclusive_target_ids": diff_stats.exclusive_target_ids,
            "duplicate_source_ids": diff_stats.duplicate_source_ids,
            "duplicate_target_ids": diff_stats.duplicate_target_ids,
            "diff_values_ids": diff_stats.diff_values_ids,
            "diff_pk_percent": diff_stats.diff_pk_percent,
            "unchanged": diff_stats.unchanged,
            "rows_downloaded": diff_stats.rows_downloaded,
            "comparison_tracker": diff_stats.comparison_tracker,
        }
        json_output["values"] = diff_stats.extra_column_diffs or {}
        return json_output


@attrs.define(frozen=False)
class TableDiffer(ThreadBase, ABC):
    INFO_TREE_CLASS = InfoTree

    bisection_factor = 32
    stats: dict = {}

    ignored_columns1: Set[str] = attrs.field(factory=set)
    ignored_columns2: Set[str] = attrs.field(factory=set)
    _ignored_columns_lock: threading.Lock = attrs.field(factory=threading.Lock, init=False)
    yield_list: bool = False
    t1_row_count: int = attrs.field(default=0, init=False)
    t2_row_count: int = attrs.field(default=0, init=False)

    def diff_tables(self, table1: TableSegment, table2: TableSegment, info_tree: InfoTree = None) -> DiffResultWrapper:
        """Diff the given tables.

        Parameters:
            table1 (TableSegment): The "before" table to compare. Or: source table
            table2 (TableSegment): The "after" table to compare. Or: target table

        Returns:
            An iterator that yield pair-tuples, representing the diff. Items can be either -
            ('-', row) for items in table1 but not in table2.
            ('+', row) for items in table2 but not in table1.
            Where `row` is a tuple of values, corresponding to the diffed columns.
        """
        if info_tree is None:
            segment_info = self.INFO_TREE_CLASS.SEGMENT_INFO_CLASS([table1, table2])
            info_tree = self.INFO_TREE_CLASS(segment_info)
        return DiffResultWrapper(self._diff_tables_wrapper(table1, table2, info_tree), info_tree, self.stats)

    def _diff_tables_wrapper(self, table1: TableSegment, table2: TableSegment, info_tree: InfoTree) -> DiffResult:
        if table1.database.dialect.PREVENT_OVERFLOW_WHEN_CONCAT or table2.database.dialect.PREVENT_OVERFLOW_WHEN_CONCAT:
            table1.database.dialect.enable_preventing_type_overflow()
            table2.database.dialect.enable_preventing_type_overflow()

        error = None
        try:
            # Query and validate schema
            table1, table2 = self._threaded_call("with_schema", [table1, table2])
            self._validate_and_adjust_columns(table1, table2)

            yield from self._diff_tables_root(table1, table2, info_tree)

        except BaseException as e:  # Catch KeyboardInterrupt too
            error = e
        finally:
            info_tree.aggregate_info()
            if error:
                raise error

    def _validate_and_adjust_columns(self, table1: TableSegment, table2: TableSegment) -> None:
        pass

    def _diff_tables_root(
        self, table1: TableSegment, table2: TableSegment, info_tree: InfoTree
    ) -> Union[DiffResult, DiffResultList]:
        return self._bisect_and_diff_tables(table1, table2, info_tree)

    @abstractmethod
    def _diff_segments(
        self,
        ti: ThreadedYielder,
        table1: TableSegment,
        table2: TableSegment,
        info_tree: InfoTree,
        max_rows: int,
        level=0,
        segment_index=None,
        segment_count=None,
    ): ...

    def _bisect_and_diff_tables(self, table1: TableSegment, table2: TableSegment, info_tree):
        if len(table1.key_columns) != len(table2.key_columns):
            raise ValueError("Tables should have an equivalent number of key columns!")

        key_types1 = [table1._schema[i] for i in table1.key_columns]
        key_types2 = [table2._schema[i] for i in table2.key_columns]

        for kt in key_types1 + key_types2:
            if not isinstance(kt, IKey):
                raise NotImplementedError(f"Cannot use a column of type {kt} as a key")

        mismatched_key_types = False
        for i, (kt1, kt2) in enumerate(safezip(key_types1, key_types2)):
            if kt1.python_type is not kt2.python_type:
                # Allow integer vs string, and string vs string variants for diffing, but mark as mismatched
                if (isinstance(kt1, Integer) and isinstance(kt2, StringType)) or (
                    isinstance(kt2, Integer) and isinstance(kt1, StringType)
                ):
                    mismatched_key_types = True
                elif isinstance(kt1, StringType) and isinstance(kt2, StringType):
                    mismatched_key_types = True
                else:
                    k1 = table1.key_columns[i]
                    k2 = table2.key_columns[i]
                    raise DataDiffMismatchingKeyTypesError(
                        f"Key columns {k1} type: {kt1.python_type} and {k2} type: {kt2.python_type} can't be compared due to different types."
                    )

        # Query min/max values
        key_ranges = self._threaded_call_as_completed("query_key_range", [table1, table2])

        # Start with the first completed value, so we don't waste time waiting
        min_key1, max_key1 = self._parse_key_range_result(key_types1, next(key_ranges))

        btable1 = table1.new_key_bounds(min_key=min_key1, max_key=max_key1, key_types=key_types1)
        btable2 = table2.new_key_bounds(min_key=min_key1, max_key=max_key1, key_types=key_types2)

        logger.info(
            f"Diffing segments at key-range: {btable1.min_key}..{btable2.max_key}. "
            f"size: table1 <= {btable1.approximate_size(self.t1_row_count)}, table2 <= {btable2.approximate_size(self.t2_row_count)}"
        )

        ti = ThreadedYielder(self.max_threadpool_size, self.yield_list)
        # Bisect (split) the table into segments, and diff them recursively.
        ti.submit(self._bisect_and_diff_segments, ti, btable1, btable2, info_tree, priority=999)

        # Now we check for the second min-max, to diff the portions we "missed".
        # This is achieved by subtracting the table ranges, and dividing the resulting space into aligned boxes.
        # For example, given tables A & B, and a 2D compound key, where A was queried first for key-range,
        # the regions of B we need to diff in this second pass are marked by B1..8:
        # ┌──┬──────┬──┐
        # │B1│  B2  │B3│
        # ├──┼──────┼──┤
        # │B4│  A   │B5│
        # ├──┼──────┼──┤
        # │B6│  B7  │B8│
        # └──┴──────┴──┘
        # Overall, the max number of new regions in this 2nd pass is 3^|k| - 1

        # Note: python types can be the same, but the rendering parameters (e.g. casing) can differ.
        # If key types mismatched (e.g., int vs string), skip the second meshing pass to avoid
        # attempting to sort mixed-type tuples (e.g., ArithAlphanumeric vs int).
        if not mismatched_key_types:
            min_key2, max_key2 = self._parse_key_range_result(key_types2, next(key_ranges))

            points = [list(sorted(p)) for p in safezip(min_key1, min_key2, max_key1, max_key2)]
            box_mesh = create_mesh_from_points(*points)

            new_regions = [(p1, p2) for p1, p2 in box_mesh if p1 < p2 and not (p1 >= min_key1 and p2 <= max_key1)]

            for p1, p2 in new_regions:
                extra_table1 = table1.new_key_bounds(min_key=p1, max_key=p2, key_types=key_types1)
                extra_table2 = table2.new_key_bounds(min_key=p1, max_key=p2, key_types=key_types2)
                ti.submit(
                    self._bisect_and_diff_segments,
                    ti,
                    extra_table1,
                    extra_table2,
                    info_tree,
                    priority=999,
                )

        return ti

    def _parse_key_range_result(self, key_types, key_range) -> Tuple[Vector, Vector]:
        min_key_values, max_key_values = key_range

        # We add 1 because our ranges are exclusive of the end (like in Python)
        try:
            min_key = Vector(key_type.make_value(mn) for key_type, mn in safezip(key_types, min_key_values))
            max_key = Vector(key_type.make_value(mx) + 1 for key_type, mx in safezip(key_types, max_key_values))
        except (TypeError, ValueError) as e:
            raise type(e)(f"Cannot apply {key_types} to '{min_key_values}', '{max_key_values}'.") from e

        return min_key, max_key

    def _bisect_and_diff_segments(
        self,
        ti: ThreadedYielder,
        table1: TableSegment,
        table2: TableSegment,
        info_tree: InfoTree,
        level=0,
        max_rows=None,
    ):
        assert table1.is_bounded and table2.is_bounded

        # Choose evenly spaced checkpoints (according to min_key and max_key)
        biggest_table = max(
            table1, table2, key=methodcaller("approximate_size", max(self.t1_row_count, self.t2_row_count))
        )
        checkpoints = biggest_table.choose_checkpoints(self.bisection_factor - 1)

        # Get it thread-safe, to avoid segment misalignment because of bad timing.
        with self._ignored_columns_lock:
            table1 = attrs.evolve(table1, ignored_columns=frozenset(self.ignored_columns1))
            table2 = attrs.evolve(table2, ignored_columns=frozenset(self.ignored_columns2))

        # Create new instances of TableSegment between each checkpoint
        segmented1 = table1.segment_by_checkpoints(checkpoints)
        segmented2 = table2.segment_by_checkpoints(checkpoints)

        # Recursively compare each pair of corresponding segments between table1 and table2
        for i, (t1, t2) in enumerate(safezip(segmented1, segmented2)):
            info_node = info_tree.add_node(t1, t2, max_rows=max_rows)
            ti.submit(
                self._diff_segments,
                ti,
                t1,
                t2,
                info_node,
                max_rows,
                level + 1,
                i + 1,
                len(segmented1),
                priority=level,
            )

    def ignore_column(self, column_name1: str, column_name2: str) -> None:
        """
        Ignore the column (by name on sides A & B) in md5s & diffs from now on.

        This affects 2 places:

        - The columns are not checksumed for new(!) segments.
        - The columns are ignored in in-memory diffing for running segments.

        The columns are never ignored in the fetched values, whether they are
        the same or different — for data consistency.

        Use this feature to collect relatively well-represented differences
        across all columns if one of them is highly different in the beginning
        of a table (as per the order of segmentation/bisection). Otherwise,
        that one column might easily hit the limit and stop the whole diff.
        """
        with self._ignored_columns_lock:
            self.ignored_columns1.add(column_name1)
            self.ignored_columns2.add(column_name2)
