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

from typing import Any, ClassVar, Dict, Type, Union

import attrs
from packaging.version import parse as parse_version

from data_diff.abcs.database_types import (
    Boolean,
    ColType,
    DbPath,
    Decimal,
    Float,
    FractionalType,
    Integer,
    Native_UUID,
    TemporalType,
    Text,
    Timestamp,
    TimestampTZ,
)
from data_diff.databases.base import (
    CHECKSUM_HEXDIGITS,
    CHECKSUM_OFFSET,
    MD5_HEXDIGITS,
    TIMESTAMP_PRECISION_POS,
    BaseDialect,
    ConnectError,
    Database,
    ThreadLocalInterpreter,
    import_helper,
)
from data_diff.schema import RawColumnInfo
from data_diff.utils import match_regexps
from data_diff.version import __version__


@import_helper("duckdb")
def import_duckdb():
    import duckdb

    return duckdb


@attrs.define(frozen=False)
class Dialect(BaseDialect):
    name = "DuckDB"
    ROUNDS_ON_PREC_LOSS = False
    SUPPORTS_PRIMARY_KEY = True
    SUPPORTS_INDEXES = True

    # https://duckdb.org/docs/sql/data_types/numeric#fixed-point-decimals
    # The default WIDTH and SCALE is DECIMAL(18, 3), if none are specified.
    DEFAULT_NUMERIC_PRECISION = 3

    TYPE_CLASSES = {
        # Timestamps
        "TIMESTAMP WITH TIME ZONE": TimestampTZ,
        "TIMESTAMP": Timestamp,
        # Numbers
        "DOUBLE": Float,
        "FLOAT": Float,
        "DECIMAL": Decimal,
        "INTEGER": Integer,
        "BIGINT": Integer,
        # Text
        "VARCHAR": Text,
        "TEXT": Text,
        # UUID
        "UUID": Native_UUID,
        # Bool
        "BOOLEAN": Boolean,
    }

    def quote(self, s: str, is_table: bool = False):
        return f'"{s}"'

    def to_string(self, s: str):
        return f"{s}::VARCHAR"

    def _convert_db_precision_to_digits(self, p: int) -> int:
        # Subtracting 2 due to wierd precision issues in PostgreSQL
        return super()._convert_db_precision_to_digits(p) - 2

    def parse_type(self, table_path: DbPath, info: RawColumnInfo) -> ColType:
        regexps = {
            r"DECIMAL\((\d+),(\d+)\)": Decimal,
        }

        for m, t_cls in match_regexps(regexps, info.data_type):
            precision = int(m.group(2))
            return t_cls(precision=precision)

        return super().parse_type(table_path, info)

    def set_timezone_to_utc(self) -> str:
        return "SET GLOBAL TimeZone='UTC'"

    def current_timestamp(self) -> str:
        return "current_timestamp"

    def md5_as_int(self, s: str) -> str:
        return f"('0x' || SUBSTRING(md5({s}), {1+MD5_HEXDIGITS-CHECKSUM_HEXDIGITS},{CHECKSUM_HEXDIGITS}))::BIGINT - {CHECKSUM_OFFSET}"

    def md5_as_hex(self, s: str) -> str:
        return f"md5({s})"

    def normalize_timestamp(self, value: str, coltype: TemporalType) -> str:
        # It's precision 6 by default. If precision is less than 6 -> we remove the trailing numbers.
        if coltype.rounds and coltype.precision > 0:
            return f"CONCAT(SUBSTRING(STRFTIME({value}::TIMESTAMP, '%Y-%m-%d %H:%M:%S.'),1,23), LPAD(((ROUND(strftime({value}::timestamp, '%f')::DECIMAL(15,7)/100000,{coltype.precision-1})*100000)::INT)::VARCHAR,6,'0'))"

        return f"rpad(substring(strftime({value}::timestamp, '%Y-%m-%d %H:%M:%S.%f'),1,{TIMESTAMP_PRECISION_POS+coltype.precision}),26,'0')"

    def normalize_number(self, value: str, coltype: FractionalType) -> str:
        return self.to_string(f"{value}::DECIMAL(38, {coltype.precision})")

    def normalize_boolean(self, value: str, _coltype: Boolean) -> str:
        return self.to_string(f"{value}::INTEGER")


@attrs.define(frozen=False, init=False, kw_only=True)
class DuckDB(Database):
    DIALECT_CLASS: ClassVar[Type[BaseDialect]] = Dialect
    SUPPORTS_UNIQUE_CONSTAINT = False  # Temporary, until we implement it
    CONNECT_URI_HELP = "duckdb://<dbname>@<filepath>"
    CONNECT_URI_PARAMS = ["database", "dbpath"]

    _args: Dict[str, Any] = attrs.field(init=False)
    _conn: Any = attrs.field(init=False)

    def __init__(self, **kw) -> None:
        super().__init__()
        self._args = kw
        self._conn = self.create_connection()
        self.default_schema = "main"

    @property
    def is_autocommit(self) -> bool:
        return True

    def _query(self, sql_code: Union[str, ThreadLocalInterpreter]):
        "Uses the standard SQL cursor interface"
        return self._query_conn(self._conn, sql_code)

    def close(self):
        super().close()
        self._conn.close()

    def create_connection(self):
        ddb = import_duckdb()
        try:
            # custom_user_agent is only available in duckdb >= 0.9.2
            if parse_version(ddb.__version__) >= parse_version("0.9.2"):
                custom_user_agent = f"dcs-diff/v{__version__}"
                config = {"custom_user_agent": custom_user_agent}
                connection = ddb.connect(database=self._args["filepath"], config=config)
                custom_user_agent_results = connection.sql("PRAGMA USER_AGENT;").fetchall()
                custom_user_agent_filtered = custom_user_agent_results[0][0]
                assert custom_user_agent in custom_user_agent_filtered
            else:
                connection = ddb.connect(database=self._args["filepath"])
            return connection
        except ddb.OperationalError as e:
            raise ConnectError(*e.args) from e
        except AssertionError:
            raise ConnectError("Assertion failed: Custom user agent is invalid.") from None

    def select_table_schema(self, path: DbPath) -> str:
        database, schema, table = self._normalize_table_path(path)

        info_schema_path = ["information_schema", "columns"]

        if database:
            info_schema_path.insert(0, database)
            dynamic_database_clause = f"'{database}'"
        else:
            dynamic_database_clause = "current_catalog()"

        return (
            f"SELECT column_name, data_type, datetime_precision, numeric_precision, numeric_scale, collation_name, character_maximum_length FROM {'.'.join(info_schema_path)} "
            f"WHERE table_name = '{table}' AND table_schema = '{schema}' and table_catalog = {dynamic_database_clause}"
        )

    def _normalize_table_path(self, path: DbPath) -> DbPath:
        if len(path) == 1:
            return None, self.default_schema, path[0]
        elif len(path) == 2:
            return None, path[0], path[1]
        elif len(path) == 3:
            return path

        raise ValueError(
            f"{self.name}: Bad table path for {self}: '{'.'.join(path)}'. Expected format: table, schema.table, or database.schema.table"
        )
