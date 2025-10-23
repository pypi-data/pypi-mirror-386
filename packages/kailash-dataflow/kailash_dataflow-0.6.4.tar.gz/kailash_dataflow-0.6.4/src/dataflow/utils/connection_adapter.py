"""
ConnectionManagerAdapter for MigrationLockManager Integration

Bridges the gap between DataFlow's connection management system and
MigrationLockManager's expected interface, handling parameter format
conversion and result normalization.

Uses DataFlow's WorkflowBuilder pattern for actual query execution.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Union

from kailash.runtime.local import LocalRuntime
from kailash.workflow.builder import WorkflowBuilder

logger = logging.getLogger(__name__)


class ConnectionManagerAdapter:
    """
    Adapter that bridges DataFlow's connection manager interface
    to MigrationLockManager's expected database interface.

    Features:
    - Parameter placeholder conversion (%s to $1, $2, etc.)
    - DML result normalization (empty results → success indicator)
    - Transaction state tracking
    - Error handling and logging
    """

    def __init__(self, dataflow_instance, parameter_style: str = "postgresql"):
        """
        Initialize connection manager adapter.

        Args:
            dataflow_instance: DataFlow instance with connection config
            parameter_style: Database parameter style ('postgresql' or 'sqlite')
        """
        self.dataflow = dataflow_instance
        self._parameter_style = parameter_style
        self._transaction_started = False
        self._runtime = LocalRuntime()

        # Get connection details from DataFlow config
        self._connection_string = self.dataflow.config.database.get_connection_url(
            self.dataflow.config.environment
        )
        self._database_type = self._detect_database_type()

    async def execute_query(
        self, sql: str, params: Optional[List] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute query with parameter conversion and result normalization.

        Args:
            sql: SQL query string (may use %s placeholders)
            params: Query parameters

        Returns:
            List of result dictionaries, or success indicator for DML operations
        """
        try:
            # Convert parameter placeholders if needed
            converted_sql, converted_params = self._convert_parameters(sql, params)

            # Use WorkflowBuilder pattern for query execution (DataFlow standard)
            workflow = WorkflowBuilder()
            workflow.add_node(
                "AsyncSQLDatabaseNode",
                "query_execution",
                {
                    "connection_string": self._connection_string,
                    "database_type": self._database_type,
                    "query": converted_sql,
                    "params": converted_params,
                    "validate_queries": False,
                },
            )

            results, _ = self._runtime.execute(workflow.build())

            if "query_execution" not in results or results["query_execution"].get(
                "error"
            ):
                error_msg = results.get("query_execution", {}).get(
                    "error", "Unknown error"
                )
                raise RuntimeError(f"Query execution failed: {error_msg}")

            # Get the raw result
            raw_result = results["query_execution"].get("result", [])

            # Normalize results for MigrationLockManager expectations
            return self._normalize_result(raw_result, sql)

        except Exception as e:
            logger.error(f"ConnectionManagerAdapter query execution failed: {e}")
            logger.error(f"SQL: {sql}")
            logger.error(f"Params: {params}")
            raise

    async def begin_transaction(self) -> None:
        """Begin database transaction."""
        try:
            # Use WorkflowBuilder for transaction operations
            workflow = WorkflowBuilder()
            workflow.add_node(
                "AsyncSQLDatabaseNode",
                "begin_transaction",
                {
                    "connection_string": self._connection_string,
                    "database_type": self._database_type,
                    "query": "BEGIN",
                    "validate_queries": False,
                },
            )

            results, _ = self._runtime.execute(workflow.build())

            if "begin_transaction" not in results or results["begin_transaction"].get(
                "error"
            ):
                error_msg = results.get("begin_transaction", {}).get(
                    "error", "Unknown error"
                )
                raise RuntimeError(f"Begin transaction failed: {error_msg}")

            self._transaction_started = True
            logger.debug("Transaction started via ConnectionManagerAdapter")
        except Exception as e:
            logger.error(f"Failed to begin transaction: {e}")
            raise

    async def commit_transaction(self) -> None:
        """Commit database transaction."""
        try:
            workflow = WorkflowBuilder()
            workflow.add_node(
                "AsyncSQLDatabaseNode",
                "commit_transaction",
                {
                    "connection_string": self._connection_string,
                    "database_type": self._database_type,
                    "query": "COMMIT",
                    "validate_queries": False,
                },
            )

            results, _ = self._runtime.execute(workflow.build())

            if "commit_transaction" not in results or results["commit_transaction"].get(
                "error"
            ):
                error_msg = results.get("commit_transaction", {}).get(
                    "error", "Unknown error"
                )
                raise RuntimeError(f"Commit transaction failed: {error_msg}")

            self._transaction_started = False
            logger.debug("Transaction committed via ConnectionManagerAdapter")
        except Exception as e:
            logger.error(f"Failed to commit transaction: {e}")
            raise

    async def rollback_transaction(self) -> None:
        """Rollback database transaction."""
        try:
            workflow = WorkflowBuilder()
            workflow.add_node(
                "AsyncSQLDatabaseNode",
                "rollback_transaction",
                {
                    "connection_string": self._connection_string,
                    "database_type": self._database_type,
                    "query": "ROLLBACK",
                    "validate_queries": False,
                },
            )

            results, _ = self._runtime.execute(workflow.build())

            if "rollback_transaction" not in results or results[
                "rollback_transaction"
            ].get("error"):
                error_msg = results.get("rollback_transaction", {}).get(
                    "error", "Unknown error"
                )
                raise RuntimeError(f"Rollback transaction failed: {error_msg}")

            self._transaction_started = False
            logger.debug("Transaction rolled back via ConnectionManagerAdapter")
        except Exception as e:
            logger.error(f"Failed to rollback transaction: {e}")
            raise

    def _convert_parameters(
        self, sql: str, params: Optional[List]
    ) -> Tuple[str, Optional[List]]:
        """
        Convert parameter placeholders from %s format to database-specific format.

        Args:
            sql: SQL string with %s placeholders
            params: Parameter values

        Returns:
            Tuple of (converted_sql, params)
        """
        if not sql or "%s" not in sql:
            return sql, params

        if self._parameter_style == "postgresql":
            # Convert %s to $1, $2, $3, etc. for PostgreSQL
            converted_sql = sql
            placeholder_count = sql.count("%s")

            for i in range(placeholder_count):
                converted_sql = converted_sql.replace("%s", f"${i + 1}", 1)

            return converted_sql, params

        elif self._parameter_style == "sqlite":
            # SQLite uses ? placeholders
            converted_sql = sql.replace("%s", "?")
            return converted_sql, params

        else:
            # Unknown parameter style - return as-is
            logger.warning(f"Unknown parameter style: {self._parameter_style}")
            return sql, params

    def _normalize_result(self, result: Any, original_sql: str) -> List[Dict[str, Any]]:
        """
        Normalize query results for MigrationLockManager compatibility.

        Args:
            result: Raw result from AsyncSQLDatabaseNode
            original_sql: Original SQL query for context

        Returns:
            Normalized result list
        """
        if result is None:
            return []

        # Handle AsyncSQLDatabaseNode result format
        if isinstance(result, list) and len(result) > 0 and isinstance(result[0], dict):
            # Extract data from AsyncSQLDatabaseNode structured result
            node_result = result[0]
            if "data" in node_result:
                data = node_result["data"]
                if isinstance(data, list):
                    if len(data) == 0:
                        # Check if this was a DML operation that should indicate success
                        sql_upper = original_sql.upper().strip()
                        if any(
                            sql_upper.startswith(dml)
                            for dml in [
                                "INSERT",
                                "UPDATE",
                                "DELETE",
                                "CREATE",
                                "DROP",
                                "ALTER",
                            ]
                        ):
                            return [{"success": True}]
                        else:
                            return []
                    else:
                        # Convert dictionaries to tuples if needed for legacy compatibility
                        return self._convert_to_legacy_format(data, original_sql)
                else:
                    return [data] if data is not None else []
            else:
                # No 'data' field - might be a direct result
                return [node_result]

        elif isinstance(result, list):
            if len(result) == 0:
                # Check if this was a DML operation that should indicate success
                sql_upper = original_sql.upper().strip()
                if any(
                    sql_upper.startswith(dml)
                    for dml in ["INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER"]
                ):
                    return [{"success": True}]
                else:
                    return []
            else:
                return result

        elif isinstance(result, dict):
            # Single result - wrap in list
            return [result]

        else:
            # Unexpected result type - try to handle gracefully
            logger.warning(
                f"Unexpected result type from AsyncSQLDatabaseNode: {type(result)}"
            )
            logger.debug(f"Raw result: {result}")
            return []

    def is_transaction_active(self) -> bool:
        """Check if a transaction is currently active."""
        return self._transaction_started

    def _detect_database_type(self) -> str:
        """Detect database type from connection string."""
        connection_lower = self._connection_string.lower()

        if (
            connection_lower.startswith("sqlite")
            or connection_lower == ":memory:"
            or connection_lower.endswith(".db")
            or connection_lower.endswith(".sqlite")
            or connection_lower.endswith(".sqlite3")
        ):
            return "sqlite"
        elif connection_lower.startswith("postgresql") or connection_lower.startswith(
            "postgres"
        ):
            return "postgresql"
        else:
            # Default to PostgreSQL
            return "postgresql"

    def _convert_to_legacy_format(
        self, data: List[Dict[str, Any]], original_sql: str
    ) -> List:
        """
        Convert dictionary results to tuple format for MigrationLockManager compatibility.

        The MigrationLockManager expects specific queries to return tuples, not dictionaries.
        This method detects those queries and converts the format accordingly.

        Args:
            data: List of dictionary results from AsyncSQLDatabaseNode
            original_sql: Original SQL query to detect expected format

        Returns:
            List in the format expected by MigrationLockManager
        """
        if not data or not isinstance(data, list):
            return data

        # Check if this is a MigrationLockManager query that expects tuples
        sql_lower = original_sql.lower().strip()

        # Lock status check query - expects tuples of (holder_process_id, acquired_at)
        if (
            "holder_process_id" in sql_lower
            and "acquired_at" in sql_lower
            and "select" in sql_lower
            and "from dataflow_migration_locks" in sql_lower
        ):
            tuple_results = []
            for row in data:
                if isinstance(row, dict):
                    tuple_results.append(
                        (row.get("holder_process_id"), row.get("acquired_at"))
                    )
                else:
                    tuple_results.append(row)
            return tuple_results

        # For other queries, return as-is
        return data
