import asyncio
import io
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

import asyncpg  # type: ignore[import-untyped]
import connectorx as cx
from asyncpg import Connection
from dbt.adapters.contracts.connection import Credentials
from dbt.adapters.postgres.connections import PostgresCredentials

from .result import ExecutionResult

DataFrameType = TypeVar("DataFrameType")


@dataclass
class SourceInfo:
    full_name: str
    schema: str
    table: str


class AbstractPythonExecutor(ABC, Generic[DataFrameType]):
    """
    Base executor for running Python models in dbt with different DataFrame libraries.
    Subclasses must set `library_name` and implement `prepare_bulk_write`.
    Auto-registers implementations to a central registry.
    """

    registry: dict[str, type["AbstractPythonExecutor[Any]"]] = {}
    type_mapping: dict[str, str] = {}
    library_name: str | None = None
    handled_types: list[str] = []

    def __init_subclass__(cls, **kwargs: Any):
        """Automatically registers the executor to a registry"""
        super().__init_subclass__(**kwargs)
        if cls.library_name is not None:
            AbstractPythonExecutor.registry[cls.library_name] = cls
            # Build the type mapping from handled_types
            for type_hint in getattr(cls, "handled_types", []):
                AbstractPythonExecutor.type_mapping[type_hint] = cls.library_name

    @classmethod
    def get_library_for_type(cls, type_hint: str) -> str | None:
        """Get the library name for a given type hint."""
        return cls.type_mapping.get(type_hint)

    def __init__(self, parsed: dict[str, Any], db: Credentials, lib: str = "polars"):
        if not isinstance(db, PostgresCredentials):
            raise ValueError("Currently just postgres is supported")
        if lib not in self.registry:
            raise ValueError(f"Only {', '.join(self.registry)} supported")

        self.parsed_model = parsed
        self.library = lib
        self.conn_string = self.get_connection_string(db)

    @staticmethod
    def get_source_info(table_name: str) -> SourceInfo:
        clean_name = table_name.replace('"', "")
        _, schema, table = clean_name.split(".")
        return SourceInfo(f"{schema}.{table}", schema, table)

    def read_df(self, table_name: str) -> DataFrameType:
        # TODO: Support filtering
        """Reads all data from the table using connectorx"""
        source = self.get_source_info(table_name)
        query = f'SELECT * FROM "{source.schema}"."{source.table}"'

        # connectorx is untyped
        result = cx.read_sql(
            self.conn_string, query, return_type=self.library, protocol="binary"
        )
        return result  # type: ignore[return-value]

    def write_df(self, table_name: str, dataframe: DataFrameType) -> ExecutionResult:
        """Write DataFrame to database table using async bulk copy."""
        return asyncio.run(self.async_write_df(table_name, dataframe))

    @abstractmethod
    def prepare_bulk_write(self, df: DataFrameType, table: str, schema: str) -> str:
        """
        Convert DataFrame to TSV string for PostgreSQL COPY command.

        Implementations should:
        1. Ensure table exists (e.g., write single row first)
        2. Convert DataFrame to TSV format with \\N for nulls

        Args:
            df: DataFrame to prepare
            table: Target table name
            schema: Target schema name

        Returns:
            TSV-formatted string ready for COPY
        """
        raise NotImplementedError

    async def async_write_df(
        self, table_name: str, df: DataFrameType
    ) -> ExecutionResult:
        """Asynchronously bulk write DataFrame using PostgreSQL COPY."""

        parts = table_name.replace('"', "").split(".")
        schema, table = parts[-2], parts[-1]

        conn: Connection = await asyncpg.connect(dsn=self.conn_string)

        csv_buffer = io.BytesIO()
        csv_string = self.prepare_bulk_write(df, table, schema)
        csv_buffer.write(csv_string.encode("utf-8"))
        csv_buffer.seek(0)

        rows_copied: str = await conn.copy_to_table(
            table_name=table,
            schema_name=schema,
            source=csv_buffer,
            format="csv",
            delimiter="\t",
            null="\\N",
        )

        await conn.close()

        # Extract row count from COPY result
        rows_effected = int(rows_copied.split(sep=" ")[-1])
        return ExecutionResult(
            rows_affected=rows_effected,
            table_name=table_name,
            schema=schema,
            table=table,
        )

    def submit(self, compiled_code: str) -> ExecutionResult:
        """Execute compiled dbt Python model code."""
        local_vars: dict[str, Any] = {}
        exec(compiled_code, local_vars)
        if "main" not in local_vars:
            raise RuntimeError("No main function found in compiled code")
        result = local_vars["main"](self.read_df, self.write_df)
        return ExecutionResult(**result) if isinstance(result, dict) else result

    @staticmethod
    def get_connection_string(db_creds: PostgresCredentials) -> str:
        # TODO: support more database types
        """Build PostgreSQL connection string from credentials."""
        return f"postgresql://{db_creds.user}:{db_creds.password}@{db_creds.host}:{db_creds.port}/{db_creds.database}"
