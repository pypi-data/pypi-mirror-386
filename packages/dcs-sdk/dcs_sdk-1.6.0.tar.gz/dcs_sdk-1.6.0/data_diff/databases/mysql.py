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

from typing import Any, ClassVar, Dict, Tuple, Type, Union

import attrs

from data_diff.abcs.database_types import (
    Boolean,
    ColType_UUID,
    Date,
    Datetime,
    DbPath,
    Decimal,
    Float,
    FractionalType,
    Integer,
    TemporalType,
    Text,
    Timestamp,
)
from data_diff.databases.base import (
    CHECKSUM_HEXDIGITS,
    CHECKSUM_OFFSET,
    MD5_HEXDIGITS,
    TIMESTAMP_PRECISION_POS,
    BaseDialect,
    ConnectError,
    ThreadedDatabase,
    ThreadLocalInterpreter,
    import_helper,
)


@import_helper("mysql")
def import_mysql():
    import mysql.connector

    return mysql.connector


@attrs.define(frozen=False)
class Dialect(BaseDialect):
    name = "MySQL"
    ROUNDS_ON_PREC_LOSS = True
    SUPPORTS_PRIMARY_KEY: ClassVar[bool] = True
    SUPPORTS_INDEXES = True
    TYPE_CLASSES = {
        # Dates
        "datetime": Datetime,
        "timestamp": Timestamp,
        "date": Date,
        # Numbers
        "double": Float,
        "float": Float,
        "decimal": Decimal,
        "int": Integer,
        "bigint": Integer,
        "mediumint": Integer,
        "smallint": Integer,
        "tinyint": Integer,
        # Text
        "varchar": Text,
        "char": Text,
        "varbinary": Text,
        "binary": Text,
        "text": Text,
        "mediumtext": Text,
        "longtext": Text,
        "tinytext": Text,
        # Boolean
        "boolean": Boolean,
    }

    def quote(self, s: str, is_table: bool = False) -> str:
        if s in self.TABLE_NAMES and self.default_schema and is_table:
            return f"`{self.default_schema}`.`{s}`"
        return f"`{s}`"

    def to_string(self, s: str) -> str:
        return f"cast({s} as char)"

    def is_distinct_from(self, a: str, b: str) -> str:
        return f"not ({a} <=> {b})"

    def random(self) -> str:
        return "RAND()"

    def type_repr(self, t) -> str:
        try:
            return {
                str: "VARCHAR(1024)",
            }[t]
        except KeyError:
            return super().type_repr(t)

    def explain_as_text(self, query: str) -> str:
        return f"EXPLAIN FORMAT=TREE {query}"

    def optimizer_hints(self, s: str):
        return f"/*+ {s} */ "

    def set_timezone_to_utc(self) -> str:
        return "SET @@session.time_zone='+00:00'"

    def md5_as_int(self, s: str) -> str:
        return f"conv(substring(md5({s}), {1+MD5_HEXDIGITS-CHECKSUM_HEXDIGITS}), 16, 10) - {CHECKSUM_OFFSET}"

    def md5_as_hex(self, s: str) -> str:
        return f"md5({s})"

    def normalize_timestamp(self, value: str, coltype: TemporalType) -> str:
        if coltype.rounds:
            return self.to_string(f"cast( cast({value} as datetime({coltype.precision})) as datetime(6))")

        s = self.to_string(f"cast({value} as datetime(6))")
        return f"RPAD(RPAD({s}, {TIMESTAMP_PRECISION_POS+coltype.precision}, '.'), {TIMESTAMP_PRECISION_POS+6}, '0')"

    def normalize_number(self, value: str, coltype: FractionalType) -> str:
        return self.to_string(f"cast({value} as decimal(38, {coltype.precision}))")

    def normalize_uuid(self, value: str, coltype: ColType_UUID) -> str:
        return f"TRIM(CAST({value} AS char))"

    def parse_table_name(self, name: str) -> DbPath:
        "Parse the given table name into a DbPath"
        self.TABLE_NAMES.append(name.split(".")[-1])
        return tuple(name.split("."))


@attrs.define(frozen=False, init=False, kw_only=True)
class MySQL(ThreadedDatabase):
    DIALECT_CLASS: ClassVar[Type[BaseDialect]] = Dialect
    SUPPORTS_ALPHANUMS = False
    SUPPORTS_UNIQUE_CONSTAINT = True
    CONNECT_URI_HELP = "mysql://<user>:<password>@<host>/<database>"
    CONNECT_URI_PARAMS = ["database?"]

    _args: Dict[str, Any]

    def __init__(self, *, thread_count, **kw) -> None:
        super().__init__(thread_count=thread_count)
        self._args = kw
        self._args = {k: v for k, v in self._args.items() if v}
        self._args.pop("schema", None)
        # In MySQL schema and database are synonymous
        try:
            self.default_schema = kw["database"]
            self.dialect.default_schema = self.default_schema
        except KeyError:
            raise ValueError("MySQL URL must specify a database")

    def create_connection(self):
        mysql = import_mysql()
        try:
            return mysql.connect(charset="utf8", use_unicode=True, **self._args)
        except mysql.Error as e:
            if e.errno == mysql.errorcode.ER_ACCESS_DENIED_ERROR:
                raise ConnectError("Bad user name or password") from e
            elif e.errno == mysql.errorcode.ER_BAD_DB_ERROR:
                raise ConnectError("Database does not exist") from e
            raise ConnectError(*e.args) from e

    def _query_in_worker(self, sql_code: Union[str, ThreadLocalInterpreter]):
        "This method runs in a worker thread"
        if self._init_error:
            raise self._init_error
        if not self.thread_local.conn.is_connected():
            self.thread_local.conn.ping(reconnect=True, attempts=3, delay=5)
        return self._query_conn(self.thread_local.conn, sql_code)

    def select_table_schema(self, path):
        schema, name = self._normalize_table_path(path)
        return (
            "SELECT column_name, data_type, datetime_precision, numeric_precision, numeric_scale, NULL as collation_name, character_maximum_length "
            "FROM information_schema.columns "
            f"WHERE table_name = '{name}' AND table_schema = '{schema}'"
        )
