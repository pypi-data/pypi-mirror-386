"""
PostgreSQL Database Adapter

PostgreSQL-specific database adapter implementation.
"""

import logging
from typing import Any, Dict, List, Tuple

from .base import DatabaseAdapter
from .exceptions import AdapterError, ConnectionError, QueryError, TransactionError

logger = logging.getLogger(__name__)


class PostgreSQLAdapter(DatabaseAdapter):
    """PostgreSQL database adapter."""

    @property
    def database_type(self) -> str:
        return "postgresql"

    @property
    def default_port(self) -> int:
        return 5432

    def __init__(self, connection_string: str, **kwargs):
        super().__init__(connection_string, **kwargs)

        # PostgreSQL-specific configuration
        self.ssl_mode = self.query_params.get("sslmode", "prefer")
        self.application_name = kwargs.get("application_name", "dataflow")

        # Use actual port or default
        if self.port is None:
            self.port = self.default_port

    async def connect(self) -> None:
        """Establish PostgreSQL connection (legacy method - use create_connection_pool)."""
        await self.create_connection_pool()

    async def disconnect(self) -> None:
        """Close PostgreSQL connection (legacy method - use close_connection_pool)."""
        await self.close_connection_pool()

    async def create_connection_pool(self) -> None:
        """Create PostgreSQL connection pool using asyncpg."""
        try:
            import asyncpg

            # Build connection parameters
            params = self.get_connection_parameters()

            # Create connection pool
            self.connection_pool = await asyncpg.create_pool(**params)
            self.is_connected = True

            logger.info(
                f"Created PostgreSQL connection pool: {self.host}:{self.port}/{self.database}"
            )

        except ImportError:
            raise ConnectionError(
                "asyncpg is required for PostgreSQL support. Install with: pip install asyncpg"
            )
        except Exception as e:
            logger.error(f"Failed to create PostgreSQL connection pool: {e}")
            raise ConnectionError(f"Connection failed: {e}")

    async def close_connection_pool(self) -> None:
        """Close PostgreSQL connection pool."""
        if self.connection_pool:
            await self.connection_pool.close()
            self.connection_pool = None
            self.is_connected = False
            logger.info("PostgreSQL connection pool closed")

    async def execute_query(self, query: str, params: List[Any] = None) -> List[Dict]:
        """Execute PostgreSQL query and return results."""
        if not self.is_connected or not self.connection_pool:
            raise ConnectionError("Not connected to database")

        try:
            # Format query for PostgreSQL parameter style
            pg_query, pg_params = self.format_query(query, params)

            # Execute query using connection pool
            async with self.connection_pool.acquire() as connection:
                if pg_params:
                    rows = await connection.fetch(pg_query, *pg_params)
                else:
                    rows = await connection.fetch(pg_query)

                # Convert asyncpg Records to dictionaries
                return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"PostgreSQL query execution failed: {e}")
            raise QueryError(f"Query execution failed: {e}")

    async def execute_insert(self, query: str, params: List[Any] = None) -> Any:
        """Execute INSERT query and return result."""
        if not self.is_connected or not self.connection_pool:
            raise ConnectionError("Not connected to database")

        try:
            pg_query, pg_params = self.format_query(query, params)

            async with self.connection_pool.acquire() as connection:
                if pg_params:
                    return await connection.execute(pg_query, *pg_params)
                else:
                    return await connection.execute(pg_query)

        except Exception as e:
            logger.error(f"PostgreSQL insert failed: {e}")
            raise QueryError(f"Insert failed: {e}")

    async def execute_bulk_insert(self, query: str, params_list: List[Tuple]) -> None:
        """Execute bulk insert operation."""
        if not self.is_connected or not self.connection_pool:
            raise ConnectionError("Not connected to database")

        try:
            pg_query, _ = self.format_query(query, [])

            async with self.connection_pool.acquire() as connection:
                await connection.executemany(pg_query, params_list)

        except Exception as e:
            logger.error(f"PostgreSQL bulk insert failed: {e}")
            raise QueryError(f"Bulk insert failed: {e}")

    def transaction(self):
        """Return transaction context manager."""
        if not self.is_connected or not self.connection_pool:
            raise ConnectionError("Not connected to database")

        return PostgreSQLTransaction(self.connection_pool)

    async def execute_transaction(
        self, queries: List[Tuple[str, List[Any]]]
    ) -> List[Any]:
        """Execute multiple queries in PostgreSQL transaction."""
        if not self.is_connected:
            raise ConnectionError("Not connected to database")

        try:
            results = []
            logger.debug(f"Starting transaction with {len(queries)} queries")

            for query, params in queries:
                result = await self.execute_query(query, params)
                results.append(result)

            logger.debug("Transaction completed successfully")
            return results
        except Exception as e:
            logger.error(f"Transaction failed: {e}")
            raise TransactionError(f"Transaction failed: {e}")

    async def get_table_schema(self, table_name: str) -> Dict[str, Dict]:
        """Get PostgreSQL table schema using INFORMATION_SCHEMA."""
        if not self.is_connected:
            raise ConnectionError("Not connected to database")

        try:
            query = """
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_default,
                character_maximum_length,
                numeric_precision,
                numeric_scale
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = $1
            ORDER BY ordinal_position
            """

            rows = await self.execute_query(query, [table_name])

            # Get primary key information
            pk_query = """
            SELECT a.attname
            FROM pg_index i
            JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
            WHERE i.indrelid = $1::regclass AND i.indisprimary
            """
            pk_rows = await self.execute_query(pk_query, [table_name])
            primary_keys = {row["attname"] for row in pk_rows}

            schema = {}
            for row in rows:
                column_info = {
                    "type": row["data_type"],
                    "nullable": row["is_nullable"] == "YES",
                    "primary_key": row["column_name"] in primary_keys,
                }

                if row["column_default"] is not None:
                    column_info["default"] = row["column_default"]

                if row["character_maximum_length"] is not None:
                    column_info["max_length"] = row["character_maximum_length"]

                if row["numeric_precision"] is not None:
                    column_info["precision"] = row["numeric_precision"]

                if row["numeric_scale"] is not None:
                    column_info["scale"] = row["numeric_scale"]

                schema[row["column_name"]] = column_info

            return schema

        except Exception as e:
            logger.error(f"Failed to get table schema: {e}")
            raise QueryError(f"Failed to get table schema: {e}")

    async def create_table(self, table_name: str, schema: Dict[str, Dict]) -> None:
        """Create PostgreSQL table."""
        if not self.is_connected:
            raise ConnectionError("Not connected to database")

        try:
            # Build CREATE TABLE statement
            columns = []
            primary_keys = []

            for col_name, col_info in schema.items():
                col_type = col_info["type"]

                # Handle max_length for varchar/char types
                if (
                    col_type.lower() in ["varchar", "character varying"]
                    and "max_length" in col_info
                ):
                    col_def = f'"{col_name}" VARCHAR({col_info["max_length"]})'
                elif (
                    col_type.lower() in ["char", "character"]
                    and "max_length" in col_info
                ):
                    col_def = f'"{col_name}" CHAR({col_info["max_length"]})'
                else:
                    col_def = f'"{col_name}" {col_type.upper()}'

                if not col_info.get("nullable", True):
                    col_def += " NOT NULL"

                if "default" in col_info and col_info["default"] is not None:
                    col_def += f" DEFAULT {col_info['default']}"

                columns.append(col_def)

                if col_info.get("primary_key"):
                    primary_keys.append(f'"{col_name}"')

            if primary_keys:
                columns.append(f"PRIMARY KEY ({', '.join(primary_keys)})")

            query = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns)})"

            await self.execute_query(query)
            logger.info(f"Created table: {table_name}")

        except Exception as e:
            logger.error(f"Failed to create table: {e}")
            raise QueryError(f"Failed to create table: {e}")

    async def drop_table(self, table_name: str) -> None:
        """Drop PostgreSQL table."""
        if not self.is_connected:
            raise ConnectionError("Not connected to database")

        try:
            query = f"DROP TABLE IF EXISTS {table_name}"
            await self.execute_query(query)
            logger.info(f"Dropped table: {table_name}")

        except Exception as e:
            logger.error(f"Failed to drop table: {e}")
            raise QueryError(f"Failed to drop table: {e}")

    def get_dialect(self) -> str:
        """Get PostgreSQL dialect."""
        return "postgresql"

    def supports_feature(self, feature: str) -> bool:
        """Check PostgreSQL feature support."""
        postgresql_features = {
            "json": True,
            "arrays": True,
            "regex": True,
            "window_functions": True,
            "cte": True,
            "upsert": True,
            "hstore": True,
            "fulltext_search": True,
            "spatial_indexes": True,
            "mysql_specific": False,
            "sqlite_specific": False,
        }
        return postgresql_features.get(feature, False)

    def format_query(
        self, query: str, params: List[Any] = None
    ) -> Tuple[str, List[Any]]:
        """Format query for PostgreSQL parameter style ($1, $2, etc.)."""
        if params is None:
            params = []

        # Convert ? placeholders to $1, $2, etc.
        formatted_query = query
        param_count = 1

        while "?" in formatted_query:
            formatted_query = formatted_query.replace("?", f"${param_count}", 1)
            param_count += 1

        return formatted_query, params

    def get_connection_parameters(self) -> Dict[str, Any]:
        """Get asyncpg connection parameters."""
        return {
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "user": self.username,
            "password": self.password,
            "min_size": self.pool_size,
            "max_size": self.pool_size + self.max_overflow,
            "command_timeout": self.pool_timeout,
        }

    def get_tables_query(self) -> str:
        """Get query to list all tables."""
        return """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_type = 'BASE TABLE'
        ORDER BY table_name
        """

    def get_columns_query(self, table_name: str) -> str:
        """Get query to list table columns."""
        return f"""
        SELECT
            column_name,
            data_type,
            is_nullable,
            column_default,
            character_maximum_length
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = '{table_name}'
        ORDER BY ordinal_position
        """

    async def get_server_version(self) -> str:
        """Get PostgreSQL server version."""
        if not self.is_connected:
            raise ConnectionError("Not connected to database")

        try:
            result = await self.execute_query("SELECT version() as version")
            return result[0]["version"]
        except Exception as e:
            logger.error(f"Failed to get server version: {e}")
            return "unknown"

    async def get_database_size(self) -> int:
        """Get database size in bytes."""
        if not self.is_connected:
            raise ConnectionError("Not connected to database")

        try:
            query = "SELECT pg_database_size(current_database()) as size_bytes"
            result = await self.execute_query(query)
            return result[0]["size_bytes"] or 0
        except Exception as e:
            logger.error(f"Failed to get database size: {e}")
            return 0

    @property
    def supports_transactions(self) -> bool:
        """PostgreSQL supports transactions."""
        return True

    @property
    def supports_savepoints(self) -> bool:
        """PostgreSQL supports savepoints."""
        return True


class PostgreSQLTransaction:
    """PostgreSQL transaction context manager."""

    def __init__(self, connection_pool):
        self.connection_pool = connection_pool
        self.connection = None
        self.transaction = None

    async def __aenter__(self):
        """Enter transaction context."""
        self.connection = await self.connection_pool.acquire()
        self.transaction = self.connection.transaction()
        await self.transaction.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit transaction context."""
        if exc_type is None:
            # No exception, commit transaction
            await self.transaction.commit()
        else:
            # Exception occurred, rollback transaction
            await self.transaction.rollback()

        # Release connection back to pool
        await self.connection_pool.release(self.connection)
