"""
DataFlow Bulk Operations

High-performance bulk database operations.
"""

from typing import Any, Dict, List


class BulkOperations:
    """High-performance bulk operations for DataFlow."""

    def __init__(self, dataflow_instance):
        self.dataflow = dataflow_instance

    async def bulk_create(
        self,
        model_name: str,
        data: List[Dict[str, Any]],
        batch_size: int = 1000,
        **kwargs,
    ) -> Dict[str, Any]:
        """Perform bulk create operation."""
        import logging

        logger = logging.getLogger(__name__)

        logger.warning(
            f"BULK_CREATE ENTRY: model={model_name}, data_count={len(data) if data else 0}, kwargs={kwargs}"
        )

        # Handle None data
        if data is None:
            return {"success": False, "error": "Data cannot be None"}

        # Handle empty data list (valid - insert 0 records)
        if len(data) == 0:
            return {
                "records_processed": 0,
                "success_count": 0,
                "failure_count": 0,
                "batches": 0,
                "batch_size": batch_size,
                "success": True,
            }

        # Apply tenant context if multi-tenant
        if self.dataflow.config.security.multi_tenant and self.dataflow._tenant_context:
            tenant_id = self.dataflow._tenant_context.get("tenant_id")
            for record in data:
                record["tenant_id"] = tenant_id

        # Auto-convert ISO datetime strings to datetime objects for each record
        from ..core.nodes import convert_datetime_fields

        model_fields = self.dataflow.get_model_fields(model_name)
        for record in data:
            convert_datetime_fields(record, model_fields, logger)

        # Perform actual database insertion
        try:
            connection_string = self.dataflow.config.database.get_connection_url(
                self.dataflow.config.environment
            )
            database_type = self.dataflow._detect_database_type()
            table_name = self.dataflow._class_name_to_table_name(model_name)

            logger.warning(
                f"BULK_CREATE: conn={connection_string[:50]}..., db_type={database_type}, table={table_name}"
            )

            # Build INSERT query from data
            if not data:
                return {
                    "records_processed": 0,
                    "success_count": 0,
                    "failure_count": 0,
                    "batches": 0,
                    "batch_size": batch_size,
                    "success": True,
                }

            # Get column names from first record
            columns = list(data[0].keys())
            column_names = ", ".join(columns)

            # Build VALUES clause with placeholders
            total_inserted = 0
            batches_processed = 0

            # Process in batches
            for i in range(0, len(data), batch_size):
                batch = data[i : i + batch_size]
                values_placeholders = []
                params = []

                for record in batch:
                    if database_type.lower() == "postgresql":
                        placeholders = ", ".join(
                            [
                                f"${j + 1}"
                                for j in range(len(params), len(params) + len(columns))
                            ]
                        )
                    elif database_type.lower() == "mysql":
                        placeholders = ", ".join(["%s"] * len(columns))
                    else:  # sqlite
                        placeholders = ", ".join(["?"] * len(columns))

                    values_placeholders.append(f"({placeholders})")
                    params.extend([record.get(col) for col in columns])

                values_clause = ", ".join(values_placeholders)
                query = (
                    f"INSERT INTO {table_name} ({column_names}) VALUES {values_clause}"
                )

                logger.warning(
                    f"BULK_CREATE: Executing batch {batches_processed + 1}, query='{query[:100]}...', param_count={len(params)}"
                )

                # Execute using AsyncSQLDatabaseNode
                from kailash.nodes.data.async_sql import AsyncSQLDatabaseNode

                sql_node = AsyncSQLDatabaseNode(
                    connection_string=connection_string,
                    database_type=database_type,
                    query=query,
                    params=params,
                    fetch_mode="all",
                    validate_queries=False,
                    transaction_mode="auto",
                )
                result = await sql_node.async_run()

                logger.warning(f"BULK_CREATE: SQL result={result}")

                # Extract rows_affected from result
                # For INSERT: AsyncSQLDatabaseNode returns row_count at result level
                # For DELETE: returns rows_affected in data[0]
                rows_affected = 0
                if result and "result" in result:
                    result_data = result["result"]
                    # Try row_count first (INSERT operations)
                    if "row_count" in result_data:
                        rows_affected = result_data.get("row_count", 0)
                    # Fall back to rows_affected in data (DELETE operations)
                    elif "data" in result_data and len(result_data["data"]) > 0:
                        rows_affected = result_data["data"][0].get("rows_affected", 0)

                total_inserted += rows_affected
                batches_processed += 1

            success_result = {
                "records_processed": total_inserted,
                "success_count": total_inserted,
                "failure_count": 0,
                "batches": batches_processed,
                "batch_size": batch_size,
                "success": True,
            }
            logger.warning(f"BULK_CREATE SUCCESS: {success_result}")
            return success_result

        except Exception as e:
            error_result = {
                "success": False,
                "error": f"Bulk create operation failed: {str(e)}",
                "records_processed": 0,
            }
            logger.error(f"BULK_CREATE EXCEPTION: {e}", exc_info=True)
            logger.error(f"BULK_CREATE ERROR RESULT: {error_result}")
            return error_result

    async def bulk_update(
        self,
        model_name: str,
        data: List[Dict[str, Any]] = None,
        filter_criteria: Dict[str, Any] = None,
        update_values: Dict[str, Any] = None,
        batch_size: int = 1000,
        **kwargs,
    ) -> Dict[str, Any]:
        """Perform bulk update operation."""
        import logging

        logger = logging.getLogger(__name__)

        logger.warning(
            f"BULK_UPDATE ENTRY: model={model_name}, data={data}, filter={filter_criteria}, update={update_values}, kwargs={kwargs}"
        )

        # Extract safe_mode and confirmed parameters
        safe_mode = kwargs.get("safe_mode", True)
        confirmed = kwargs.get("confirmed", False)

        # Determine operation mode based on which parameters have actual content
        # Filter-based: has non-empty update_values (filter can be empty = update all)
        # Data-based: has data parameter (can be empty list)
        has_update_values = update_values is not None and bool(update_values)
        has_data = data is not None

        is_filter_based = has_update_values
        is_data_based = has_data and not has_update_values

        # Validation: Empty filter requires confirmation (only for filter-based updates)
        if is_filter_based and not filter_criteria:
            # Empty dict {} means update ALL records - require confirmation
            logger.warning("BULK_UPDATE: Empty filter detected, checking confirmation")
            if safe_mode and not confirmed:
                error_result = {
                    "success": False,
                    "error": "Bulk update with empty filter requires confirmed=True. "
                    "Empty filter will update ALL records in the table. "
                    "Set confirmed=True to proceed or provide a specific filter.",
                    "records_processed": 0,
                }
                logger.error(f"BULK_UPDATE VALIDATION FAILED: {error_result}")
                return error_result

        if is_filter_based:
            # Filter-based bulk update - perform actual database operation
            logger.warning("BULK_UPDATE: Processing filter-based update")
            try:
                # Auto-convert ISO datetime strings to datetime objects in update_values
                from ..core.nodes import convert_datetime_fields

                model_fields = self.dataflow.get_model_fields(model_name)
                update_values = convert_datetime_fields(
                    update_values, model_fields, logger
                )

                # Get database connection and execute UPDATE
                connection_string = self.dataflow.config.database.get_connection_url(
                    self.dataflow.config.environment
                )
                database_type = self.dataflow._detect_database_type()
                table_name = self.dataflow._class_name_to_table_name(model_name)

                logger.warning(
                    f"BULK_UPDATE: conn={connection_string[:50]}..., db_type={database_type}, table={table_name}"
                )

                # Build SET clause from update_values
                set_parts = []
                params = []
                for field, value in update_values.items():
                    if database_type.lower() == "postgresql":
                        set_parts.append(f"{field} = ${len(params) + 1}")
                    elif database_type.lower() == "mysql":
                        set_parts.append(f"{field} = %s")
                    else:  # sqlite
                        set_parts.append(f"{field} = ?")
                    params.append(value)

                set_clause = "SET " + ", ".join(set_parts)

                # Build WHERE clause from filter
                if filter_criteria:
                    # Has specific filter criteria
                    where_parts = []
                    for field, value in filter_criteria.items():
                        if database_type.lower() == "postgresql":
                            where_parts.append(f"{field} = ${len(params) + 1}")
                        elif database_type.lower() == "mysql":
                            where_parts.append(f"{field} = %s")
                        else:  # sqlite
                            where_parts.append(f"{field} = ?")
                        params.append(value)
                    where_clause = "WHERE " + " AND ".join(where_parts)
                else:
                    # Empty filter = update all (requires confirmation, already checked above)
                    where_clause = ""

                query = f"UPDATE {table_name} {set_clause} {where_clause}"
                logger.warning(
                    f"BULK_UPDATE: Executing query='{query}' with params={params}"
                )

                # Execute using AsyncSQLDatabaseNode
                from kailash.nodes.data.async_sql import AsyncSQLDatabaseNode

                sql_node = AsyncSQLDatabaseNode(
                    connection_string=connection_string,
                    database_type=database_type,
                    query=query,
                    params=params,
                    fetch_mode="all",
                    validate_queries=False,
                    transaction_mode="auto",
                )
                result = await sql_node.async_run()

                logger.warning(f"BULK_UPDATE: SQL result={result}")

                # Extract rows_affected from result
                # AsyncSQLDatabaseNode returns: {'result': {'data': [{'rows_affected': N}], ...}}
                rows_affected = 0
                if result and "result" in result:
                    result_data = result["result"]
                    if "data" in result_data and len(result_data["data"]) > 0:
                        rows_affected = result_data["data"][0].get("rows_affected", 0)

                success_result = {
                    "filter": filter_criteria,
                    "update": update_values,
                    "records_processed": rows_affected,
                    "success_count": rows_affected,
                    "failure_count": 0,
                    "success": True,
                }
                logger.warning(f"BULK_UPDATE SUCCESS: {success_result}")
                return success_result
            except Exception as e:
                error_result = {
                    "success": False,
                    "error": f"Bulk update operation failed: {str(e)}",
                    "records_processed": 0,
                }
                logger.error(f"BULK_UPDATE EXCEPTION: {e}", exc_info=True)
                logger.error(f"BULK_UPDATE ERROR RESULT: {error_result}")
                return error_result
        elif data is not None:
            # Data-based bulk update - update records by id
            logger.warning("BULK_UPDATE: Processing data-based update")

            # Handle empty data list (valid - update 0 records)
            if len(data) == 0:
                return {
                    "records_processed": 0,
                    "success_count": 0,
                    "failure_count": 0,
                    "batches": 0,
                    "batch_size": batch_size,
                    "success": True,
                }

            # Auto-convert ISO datetime strings to datetime objects for each record
            from ..core.nodes import convert_datetime_fields

            model_fields = self.dataflow.get_model_fields(model_name)
            for record in data:
                convert_datetime_fields(record, model_fields, logger)

            try:
                connection_string = self.dataflow.config.database.get_connection_url(
                    self.dataflow.config.environment
                )
                database_type = self.dataflow._detect_database_type()
                table_name = self.dataflow._class_name_to_table_name(model_name)

                logger.warning(
                    f"BULK_UPDATE: conn={connection_string[:50]}..., db_type={database_type}, table={table_name}"
                )

                total_updated = 0
                batches_processed = 0

                # Process in batches
                for i in range(0, len(data), batch_size):
                    batch = data[i : i + batch_size]

                    # Execute individual UPDATEs for each record
                    for record in batch:
                        if "id" not in record:
                            logger.warning(
                                f"BULK_UPDATE: Skipping record without id: {record}"
                            )
                            continue

                        # Build SET clause from record (exclude id)
                        set_parts = []
                        params = []
                        for field, value in record.items():
                            if field == "id":
                                continue
                            if database_type.lower() == "postgresql":
                                set_parts.append(f"{field} = ${len(params) + 1}")
                            elif database_type.lower() == "mysql":
                                set_parts.append(f"{field} = %s")
                            else:  # sqlite
                                set_parts.append(f"{field} = ?")
                            params.append(value)

                        if not set_parts:
                            logger.warning(
                                f"BULK_UPDATE: No fields to update for record: {record}"
                            )
                            continue

                        set_clause = "SET " + ", ".join(set_parts)

                        # Build WHERE clause for id
                        if database_type.lower() == "postgresql":
                            where_clause = f"WHERE id = ${len(params) + 1}"
                        elif database_type.lower() == "mysql":
                            where_clause = "WHERE id = %s"
                        else:  # sqlite
                            where_clause = "WHERE id = ?"
                        params.append(record["id"])

                        query = f"UPDATE {table_name} {set_clause} {where_clause}"

                        # Execute using AsyncSQLDatabaseNode
                        from kailash.nodes.data.async_sql import AsyncSQLDatabaseNode

                        sql_node = AsyncSQLDatabaseNode(
                            connection_string=connection_string,
                            database_type=database_type,
                            query=query,
                            params=params,
                            fetch_mode="all",
                            validate_queries=False,
                            transaction_mode="auto",
                        )
                        result = await sql_node.async_run()

                        # Extract rows_affected
                        rows_affected = 0
                        if result and "result" in result:
                            result_data = result["result"]
                            if "data" in result_data and len(result_data["data"]) > 0:
                                rows_affected = result_data["data"][0].get(
                                    "rows_affected", 0
                                )

                        total_updated += rows_affected

                    batches_processed += 1

                success_result = {
                    "records_processed": total_updated,
                    "success_count": total_updated,
                    "failure_count": 0,
                    "batches": batches_processed,
                    "batch_size": batch_size,
                    "success": True,
                }
                logger.warning(f"BULK_UPDATE SUCCESS: {success_result}")
                return success_result
            except Exception as e:
                error_result = {
                    "success": False,
                    "error": f"Bulk update operation failed: {str(e)}",
                    "records_processed": 0,
                }
                logger.error(f"BULK_UPDATE EXCEPTION: {e}", exc_info=True)
                logger.error(f"BULK_UPDATE ERROR RESULT: {error_result}")
                return error_result

        return {"success": False, "error": "Either data or filter+update required"}

    async def bulk_delete(
        self,
        model_name: str,
        data: List[Dict[str, Any]] = None,
        filter_criteria: Dict[str, Any] = None,
        batch_size: int = 1000,
        **kwargs,
    ) -> Dict[str, Any]:
        """Perform bulk delete operation."""
        import logging

        logger = logging.getLogger(__name__)

        logger.warning(
            f"BULK_DELETE ENTRY: model={model_name}, data={data}, filter={filter_criteria}, kwargs={kwargs}"
        )

        # Extract safe_mode and confirmed parameters
        safe_mode = kwargs.get("safe_mode", True)
        confirmed = kwargs.get("confirmed", False)

        logger.warning(
            f"BULK_DELETE VALIDATION: safe_mode={safe_mode}, confirmed={confirmed}"
        )

        # Validation: Empty filter requires confirmation
        if filter_criteria is not None and not filter_criteria:
            # Empty dict {} means delete ALL records - require confirmation
            logger.warning("BULK_DELETE: Empty filter detected, checking confirmation")
            if safe_mode and not confirmed:
                error_result = {
                    "success": False,
                    "error": "Bulk delete with empty filter requires confirmed=True. "
                    "Empty filter will delete ALL records in the table. "
                    "Set confirmed=True to proceed or provide a specific filter.",
                    "records_processed": 0,
                }
                logger.error(f"BULK_DELETE VALIDATION FAILED: {error_result}")
                return error_result

        if filter_criteria is not None:
            # Filter-based bulk delete - perform actual database operation
            logger.warning("BULK_DELETE: Processing filter-based delete")
            try:
                # Get database connection and execute DELETE
                connection_string = self.dataflow.config.database.get_connection_url(
                    self.dataflow.config.environment
                )
                database_type = self.dataflow._detect_database_type()
                table_name = self.dataflow._class_name_to_table_name(model_name)

                logger.warning(
                    f"BULK_DELETE: conn={connection_string[:50]}..., db_type={database_type}, table={table_name}"
                )

                # Build WHERE clause from filter
                if filter_criteria:
                    # Has specific filter criteria
                    where_parts = []
                    params = []
                    for field, value in filter_criteria.items():
                        if database_type.lower() == "postgresql":
                            where_parts.append(f"{field} = ${len(params) + 1}")
                        elif database_type.lower() == "mysql":
                            where_parts.append(f"{field} = %s")
                        else:  # sqlite
                            where_parts.append(f"{field} = ?")
                        params.append(value)
                    where_clause = "WHERE " + " AND ".join(where_parts)
                else:
                    # Empty filter = delete all (requires confirmation, already checked above)
                    where_clause = ""
                    params = []

                query = f"DELETE FROM {table_name} {where_clause}"
                logger.warning(
                    f"BULK_DELETE: Executing query='{query}' with params={params}"
                )

                # Execute using AsyncSQLDatabaseNode
                from kailash.nodes.data.async_sql import AsyncSQLDatabaseNode

                sql_node = AsyncSQLDatabaseNode(
                    connection_string=connection_string,
                    database_type=database_type,
                    query=query,
                    params=params,
                    fetch_mode="all",
                    validate_queries=False,
                    transaction_mode="auto",
                )
                result = await sql_node.async_run()

                logger.warning(f"BULK_DELETE: SQL result={result}")

                # Extract rows_affected from result
                # AsyncSQLDatabaseNode returns: {'result': {'data': [{'rows_affected': N}], ...}}
                rows_affected = 0
                if result and "result" in result:
                    result_data = result["result"]
                    if "data" in result_data and len(result_data["data"]) > 0:
                        rows_affected = result_data["data"][0].get("rows_affected", 0)

                success_result = {
                    "filter": filter_criteria,
                    "records_processed": rows_affected,
                    "success_count": rows_affected,
                    "failure_count": 0,
                    "success": True,
                }
                logger.warning(f"BULK_DELETE SUCCESS: {success_result}")
                return success_result
            except Exception as e:
                error_result = {
                    "success": False,
                    "error": f"Bulk delete operation failed: {str(e)}",
                    "records_processed": 0,
                }
                logger.error(f"BULK_DELETE EXCEPTION: {e}", exc_info=True)
                logger.error(f"BULK_DELETE ERROR RESULT: {error_result}")
                return error_result
        elif data is not None:
            # Data-based bulk delete (empty list [] is valid)
            return {
                "records_processed": len(data),
                "success_count": len(data),
                "failure_count": 0,
                "batch_size": batch_size,
                "success": True,
            }

        return {"success": False, "error": "Either data or filter required"}

    async def bulk_upsert(
        self,
        model_name: str,
        data: List[Dict[str, Any]],
        conflict_resolution: str = "update",
        batch_size: int = 1000,
        **kwargs,
    ) -> Dict[str, Any]:
        """Perform bulk upsert (insert or update) operation.

        Args:
            model_name: Name of the model
            data: List of dictionaries with record data (must include 'id' field)
            conflict_resolution: Strategy for conflicts - "update" or "skip"/"ignore"
            batch_size: Number of records per batch

        Returns:
            Dict with records_processed, inserted, updated, skipped, success
        """
        import logging

        logger = logging.getLogger(__name__)

        logger.warning(
            f"BULK_UPSERT ENTRY: model={model_name}, data_count={len(data) if data else 0}, "
            f"conflict_resolution={conflict_resolution}, batch_size={batch_size}, kwargs={kwargs}"
        )

        # Handle None data
        if data is None:
            return {"success": False, "error": "Data cannot be None"}

        # Handle empty data list (valid - upsert 0 records)
        if len(data) == 0:
            return {
                "records_processed": 0,
                "inserted": 0,
                "updated": 0,
                "skipped": 0,
                "batches": 0,
                "batch_size": batch_size,
                "conflict_resolution": conflict_resolution,
                "success": True,
            }

        # Validate conflict_resolution
        if conflict_resolution not in ["update", "skip", "ignore"]:
            return {
                "success": False,
                "error": f"Invalid conflict_resolution '{conflict_resolution}'. "
                "Must be 'update', 'skip', or 'ignore'.",
            }

        # Validate all records have 'id' field
        for i, record in enumerate(data):
            if "id" not in record:
                return {
                    "success": False,
                    "error": f"Record at index {i} missing required 'id' field. "
                    "All records must have an 'id' for upsert operations.",
                }

        # Apply tenant context if multi-tenant
        if self.dataflow.config.security.multi_tenant and self.dataflow._tenant_context:
            tenant_id = self.dataflow._tenant_context.get("tenant_id")
            for record in data:
                record["tenant_id"] = tenant_id

        # Auto-convert ISO datetime strings to datetime objects for each record
        from ..core.nodes import convert_datetime_fields

        model_fields = self.dataflow.get_model_fields(model_name)
        for record in data:
            convert_datetime_fields(record, model_fields, logger)

        # Perform actual database upsert
        try:
            connection_string = self.dataflow.config.database.get_connection_url(
                self.dataflow.config.environment
            )
            database_type = self.dataflow._detect_database_type()
            table_name = self.dataflow._class_name_to_table_name(model_name)

            logger.warning(
                f"BULK_UPSERT: conn={connection_string[:50]}..., db_type={database_type}, "
                f"table={table_name}, conflict_resolution={conflict_resolution}"
            )

            # Get column names from first record
            columns = list(data[0].keys())
            column_names = ", ".join(columns)

            # Build upsert query based on database type
            total_inserted = 0
            total_updated = 0
            total_skipped = 0
            batches_processed = 0

            # Process in batches
            for i in range(0, len(data), batch_size):
                batch = data[i : i + batch_size]

                # Build database-specific upsert query
                if database_type.lower() == "postgresql":
                    # PostgreSQL: INSERT ... ON CONFLICT (id) DO UPDATE SET ...
                    query, params = self._build_postgresql_upsert(
                        table_name, columns, batch, conflict_resolution
                    )
                elif database_type.lower() == "mysql":
                    # MySQL: INSERT ... ON DUPLICATE KEY UPDATE ...
                    query, params = self._build_mysql_upsert(
                        table_name, columns, batch, conflict_resolution
                    )
                else:  # sqlite
                    # SQLite: INSERT ... ON CONFLICT (id) DO UPDATE SET ...
                    query, params = self._build_sqlite_upsert(
                        table_name, columns, batch, conflict_resolution
                    )

                logger.warning(
                    f"BULK_UPSERT: Executing batch {batches_processed + 1}, "
                    f"query='{query[:200]}...', param_count={len(params)}"
                )

                # Execute using AsyncSQLDatabaseNode
                from kailash.nodes.data.async_sql import AsyncSQLDatabaseNode

                sql_node = AsyncSQLDatabaseNode(
                    connection_string=connection_string,
                    database_type=database_type,
                    query=query,
                    params=params,
                    fetch_mode="all",
                    validate_queries=False,
                    transaction_mode="auto",
                )
                result = await sql_node.async_run()

                logger.warning(f"BULK_UPSERT: SQL result={result}")

                # Extract operation counts from result
                # For UPSERT operations, we need to parse the result to determine
                # inserted vs updated vs skipped counts
                batch_inserted, batch_updated, batch_skipped = (
                    self._parse_upsert_result(
                        result, database_type, len(batch), conflict_resolution
                    )
                )

                total_inserted += batch_inserted
                total_updated += batch_updated
                total_skipped += batch_skipped
                batches_processed += 1

            records_processed = total_inserted + total_updated + total_skipped
            success_result = {
                "records_processed": records_processed,
                "inserted": total_inserted,
                "updated": total_updated,
                "skipped": total_skipped,
                "batches": batches_processed,
                "batch_size": batch_size,
                "conflict_resolution": conflict_resolution,
                "success": True,
            }
            logger.warning(f"BULK_UPSERT SUCCESS: {success_result}")
            return success_result

        except Exception as e:
            error_result = {
                "success": False,
                "error": f"Bulk upsert operation failed: {str(e)}",
                "records_processed": 0,
                "inserted": 0,
                "updated": 0,
                "skipped": 0,
            }
            logger.error(f"BULK_UPSERT EXCEPTION: {e}", exc_info=True)
            logger.error(f"BULK_UPSERT ERROR RESULT: {error_result}")
            return error_result

    def _build_postgresql_upsert(
        self,
        table_name: str,
        columns: List[str],
        batch: List[Dict[str, Any]],
        conflict_resolution: str,
    ) -> tuple:
        """Build PostgreSQL upsert query with ON CONFLICT clause."""
        column_names = ", ".join(columns)
        values_placeholders = []
        params = []

        # Build VALUES clause
        for record in batch:
            placeholders = ", ".join(
                [f"${j + 1}" for j in range(len(params), len(params) + len(columns))]
            )
            values_placeholders.append(f"({placeholders})")
            params.extend([record.get(col) for col in columns])

        values_clause = ", ".join(values_placeholders)

        # Build ON CONFLICT clause
        if conflict_resolution in ["skip", "ignore"]:
            # Skip conflicts - do nothing
            conflict_clause = "ON CONFLICT (id) DO NOTHING"
        else:  # update
            # Update all columns except 'id' on conflict
            update_columns = [col for col in columns if col != "id"]
            if update_columns:
                set_parts = [f"{col} = EXCLUDED.{col}" for col in update_columns]
                conflict_clause = (
                    f"ON CONFLICT (id) DO UPDATE SET {', '.join(set_parts)}"
                )
            else:
                # Only 'id' column - skip on conflict
                conflict_clause = "ON CONFLICT (id) DO NOTHING"

        query = f"INSERT INTO {table_name} ({column_names}) VALUES {values_clause} {conflict_clause}"
        return query, params

    def _build_mysql_upsert(
        self,
        table_name: str,
        columns: List[str],
        batch: List[Dict[str, Any]],
        conflict_resolution: str,
    ) -> tuple:
        """Build MySQL upsert query with ON DUPLICATE KEY UPDATE clause."""
        column_names = ", ".join(columns)
        values_placeholders = []
        params = []

        # Build VALUES clause
        for record in batch:
            placeholders = ", ".join(["%s"] * len(columns))
            values_placeholders.append(f"({placeholders})")
            params.extend([record.get(col) for col in columns])

        values_clause = ", ".join(values_placeholders)

        # Build ON DUPLICATE KEY UPDATE clause
        if conflict_resolution in ["skip", "ignore"]:
            # MySQL doesn't support DO NOTHING in ON DUPLICATE KEY
            # Workaround: update id to itself (no actual change)
            duplicate_clause = "ON DUPLICATE KEY UPDATE id = id"
        else:  # update
            # Update all columns except 'id' on duplicate
            update_columns = [col for col in columns if col != "id"]
            if update_columns:
                set_parts = [f"{col} = VALUES({col})" for col in update_columns]
                duplicate_clause = f"ON DUPLICATE KEY UPDATE {', '.join(set_parts)}"
            else:
                # Only 'id' column - no update needed
                duplicate_clause = "ON DUPLICATE KEY UPDATE id = id"

        query = f"INSERT INTO {table_name} ({column_names}) VALUES {values_clause} {duplicate_clause}"
        return query, params

    def _build_sqlite_upsert(
        self,
        table_name: str,
        columns: List[str],
        batch: List[Dict[str, Any]],
        conflict_resolution: str,
    ) -> tuple:
        """Build SQLite upsert query with ON CONFLICT clause."""
        column_names = ", ".join(columns)
        values_placeholders = []
        params = []

        # Build VALUES clause
        for record in batch:
            placeholders = ", ".join(["?"] * len(columns))
            values_placeholders.append(f"({placeholders})")
            params.extend([record.get(col) for col in columns])

        values_clause = ", ".join(values_placeholders)

        # Build ON CONFLICT clause
        if conflict_resolution in ["skip", "ignore"]:
            # Skip conflicts - do nothing
            conflict_clause = "ON CONFLICT (id) DO NOTHING"
        else:  # update
            # Update all columns except 'id' on conflict
            update_columns = [col for col in columns if col != "id"]
            if update_columns:
                set_parts = [f"{col} = excluded.{col}" for col in update_columns]
                conflict_clause = (
                    f"ON CONFLICT (id) DO UPDATE SET {', '.join(set_parts)}"
                )
            else:
                # Only 'id' column - skip on conflict
                conflict_clause = "ON CONFLICT (id) DO NOTHING"

        query = f"INSERT INTO {table_name} ({column_names}) VALUES {values_clause} {conflict_clause}"
        return query, params

    def _parse_upsert_result(
        self,
        result: Dict[str, Any],
        database_type: str,
        batch_size: int,
        conflict_resolution: str,
    ) -> tuple:
        """Parse upsert result to extract inserted, updated, and skipped counts.

        Returns:
            tuple: (inserted, updated, skipped)
        """
        # Extract row_count from result
        rows_affected = 0
        if result and "result" in result:
            result_data = result["result"]
            # Try row_count first (INSERT operations)
            if "row_count" in result_data:
                rows_affected = result_data.get("row_count", 0)
            # Fall back to rows_affected in data (other operations)
            elif "data" in result_data and len(result_data["data"]) > 0:
                rows_affected = result_data["data"][0].get("rows_affected", 0)

        # For PostgreSQL and SQLite with ON CONFLICT:
        # - row_count includes both inserts and updates
        # - We can't distinguish between insert/update from row_count alone
        # - If conflict_resolution is "skip", all affected rows are inserts
        # - If conflict_resolution is "update", we estimate based on batch_size

        if conflict_resolution in ["skip", "ignore"]:
            # All affected rows are inserts (conflicts were skipped)
            inserted = rows_affected
            updated = 0
            skipped = batch_size - rows_affected
        else:  # update
            # For MySQL: ON DUPLICATE KEY UPDATE affects 1 row for insert, 2 for update
            if database_type.lower() == "mysql":
                # MySQL returns row_count = (inserts * 1) + (updates * 2)
                # If row_count > batch_size, some rows were updated
                if rows_affected > batch_size:
                    # row_count = inserts + (updates * 2)
                    # rows_affected - batch_size = extra count from updates
                    extra = rows_affected - batch_size
                    updated = extra
                    inserted = batch_size - updated
                else:
                    # All inserts, no updates
                    inserted = rows_affected
                    updated = 0
                skipped = 0
            else:
                # PostgreSQL/SQLite: Can't distinguish insert from update
                # Assume all affected rows were processed (insert or update)
                # Conservative estimate: all are inserts
                inserted = rows_affected
                updated = 0
                skipped = batch_size - rows_affected

        return (inserted, updated, skipped)
