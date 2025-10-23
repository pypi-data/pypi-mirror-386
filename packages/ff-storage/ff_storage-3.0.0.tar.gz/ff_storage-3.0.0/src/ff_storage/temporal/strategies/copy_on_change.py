"""
Copy-on-Change strategy - Field-level audit trail.

Main table: Standard CRUD (like none strategy)
Audit table: {table}_audit with field-level change tracking

Benefits:
- Lightweight: Only changed fields are stored
- Concurrent: Field-level updates don't conflict
- Granular: See exactly which fields changed when
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from ...db.schema_sync.models import ColumnType
from ..enums import TemporalStrategyType
from ..models import AuditEntry
from ..registry import register_strategy
from .base import T, TemporalStrategy


@register_strategy(TemporalStrategyType.COPY_ON_CHANGE)
class CopyOnChangeStrategy(TemporalStrategy[T]):
    """
    Field-level audit trail strategy.

    Main table: Standard CRUD with timestamps
    Audit table: Field-level change history

    Each UPDATE creates N audit rows (N = number of changed fields).
    Grouped by transaction_id for multi-field updates.
    """

    def get_temporal_fields(self) -> Dict[str, tuple[type, Any]]:
        """No additional fields in main table beyond base."""
        return self._get_base_fields()

    def get_temporal_indexes(self, table_name: str, schema: str = "public") -> List[dict]:
        """Return base indexes."""
        return self._get_base_indexes(table_name)

    def get_auxiliary_tables(self, table_name: str, schema: str = "public") -> List[dict]:
        """
        Return audit table definition.

        Audit table tracks field-level changes:
        - One row per changed field
        - Groups multi-field updates by transaction_id
        """

        audit_table_name = f"{table_name}_audit"

        columns = [
            {
                "name": "audit_id",
                "column_type": ColumnType.UUID,
                "native_type": "UUID",
                "nullable": False,
                "is_primary_key": True,
                "default": "gen_random_uuid()",
            },
            {
                "name": "record_id",
                "column_type": ColumnType.UUID,
                "native_type": "UUID",
                "nullable": False,
            },
        ]

        # Add tenant_id to audit table if multi_tenant
        if self.multi_tenant:
            columns.append(
                {
                    "name": self.tenant_field,
                    "column_type": ColumnType.UUID,
                    "native_type": "UUID",
                    "nullable": False,
                }
            )

        # Field-level tracking columns
        columns.extend(
            [
                {
                    "name": "field_name",
                    "column_type": ColumnType.STRING,
                    "native_type": "VARCHAR(255)",
                    "max_length": 255,
                    "nullable": False,
                },
                {
                    "name": "old_value",
                    "column_type": ColumnType.JSONB,
                    "native_type": "JSONB",
                    "nullable": True,
                },
                {
                    "name": "new_value",
                    "column_type": ColumnType.JSONB,
                    "native_type": "JSONB",
                    "nullable": True,
                },
                {
                    "name": "operation",
                    "column_type": ColumnType.STRING,
                    "native_type": "VARCHAR(10)",
                    "max_length": 10,
                    "nullable": False,
                },
                {
                    "name": "changed_at",
                    "column_type": ColumnType.TIMESTAMPTZ,
                    "native_type": "TIMESTAMP WITH TIME ZONE",
                    "nullable": False,
                    "default": "NOW()",
                },
                {
                    "name": "changed_by",
                    "column_type": ColumnType.UUID,
                    "native_type": "UUID",
                    "nullable": True,
                },
                {
                    "name": "transaction_id",
                    "column_type": ColumnType.UUID,
                    "native_type": "UUID",
                    "nullable": True,
                },
                {
                    "name": "metadata",
                    "column_type": ColumnType.JSONB,
                    "native_type": "JSONB",
                    "nullable": True,
                },
            ]
        )

        # Indexes for audit table
        indexes = [
            {
                "name": f"idx_{audit_table_name}_record_field",
                "table_name": audit_table_name,
                "columns": ["record_id", "field_name"],
                "index_type": "btree",
            },
            {
                "name": f"idx_{audit_table_name}_changed_at",
                "table_name": audit_table_name,
                "columns": ["changed_at"],
                "index_type": "btree",
            },
        ]

        if self.multi_tenant:
            indexes.append(
                {
                    "name": f"idx_{audit_table_name}_{self.tenant_field}",
                    "table_name": audit_table_name,
                    "columns": [self.tenant_field],
                    "index_type": "btree",
                }
            )

        return [
            {
                "name": audit_table_name,
                "schema": schema,
                "columns": columns,
                "indexes": indexes,
            }
        ]

    async def create(
        self,
        data: Dict[str, Any],
        db_pool,
        tenant_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
    ) -> T:
        """
        Create record with INSERT audit entries.

        Creates:
        1. Main table row
        2. Audit entries for each field (operation=INSERT)
        """
        # Ensure ID
        if "id" not in data:
            data["id"] = uuid4()

        record_id = data["id"]

        # Set timestamps
        now = datetime.now(timezone.utc)
        data["created_at"] = now
        data["updated_at"] = now

        # Set created_by
        if user_id:
            data["created_by"] = user_id

        # Set tenant_id
        if self.multi_tenant:
            if not tenant_id:
                raise ValueError("tenant_id required for multi-tenant model")
            data[self.tenant_field] = tenant_id

        # Initialize soft delete fields
        if self.soft_delete:
            data["deleted_at"] = None
            data["deleted_by"] = None

        # Transaction ID for grouping audit entries
        transaction_id = uuid4()

        # Build INSERT query for main table
        table_name = self._get_table_name()
        audit_table_name = f"{table_name}_audit"

        columns = list(data.keys())
        placeholders = [f"${i + 1}" for i in range(len(columns))]

        main_insert = f"""
            INSERT INTO {table_name} ({", ".join(columns)})
            VALUES ({", ".join(placeholders)})
            RETURNING *
        """

        # Build audit entries (one per field)
        audit_entries = []
        user_fields = self._get_user_fields(data)

        for field_name, new_value in user_fields.items():
            entry = {
                "audit_id": uuid4(),
                "record_id": record_id,
                "field_name": field_name,
                "old_value": None,  # NULL for INSERT
                "new_value": self._serialize_value(new_value),
                "operation": "INSERT",
                "changed_at": now,
                "changed_by": user_id,
                "transaction_id": transaction_id,
            }
            # Only add tenant_id if multi-tenant is enabled
            if self.multi_tenant:
                entry["tenant_id"] = tenant_id
            audit_entries.append(entry)

        # Execute in transaction
        async with db_pool.acquire() as conn:
            async with conn.transaction():
                # Insert main record with JSONB serialization
                serialized_data = self._serialize_jsonb_fields(data)
                row = await conn.fetchrow(main_insert, *serialized_data.values())

                # Insert audit entries
                await self._insert_audit_entries(conn, audit_table_name, audit_entries)

        return self._row_to_model(row)

    async def update(
        self,
        id: UUID,
        data: Dict[str, Any],
        db_pool,
        tenant_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
    ) -> T:
        """
        Update record with field-level audit entries and row-level locking.

        Process:
        1. SELECT current record FOR UPDATE (lock row)
        2. Compute field diff (which fields changed)
        3. UPDATE main table
        4. INSERT audit entries (one per changed field)

        Concurrency:
        Uses SELECT ... FOR UPDATE to prevent race conditions where concurrent
        updates might miss field changes. This holds an exclusive lock on the row
        during diff computation, reducing write concurrency but ensuring correctness.

        Trade-off: Acceptable for moderate update rates (<100/sec per row).
        For higher concurrency needs, consider database triggers or optimistic locking.
        """
        table_name = self._get_table_name()
        audit_table_name = f"{table_name}_audit"

        # Auto-set updated_at
        data["updated_at"] = datetime.now(timezone.utc)

        # Track who made the update
        if user_id:
            data["updated_by"] = user_id

        # Transaction ID for grouping
        transaction_id = uuid4()
        now = datetime.now(timezone.utc)

        # Build WHERE clause
        where_parts = ["id = $1"]
        where_values = [id]

        if self.multi_tenant:
            if not tenant_id:
                raise ValueError("tenant_id required for multi-tenant model")
            where_parts.append(f"{self.tenant_field} = ${len(where_values) + 1}")
            where_values.append(tenant_id)

        if self.soft_delete:
            where_parts.append("deleted_at IS NULL")

        # Execute in transaction
        async with db_pool.acquire() as conn:
            async with conn.transaction():
                # 1. Get current record with row-level lock
                select_query = f"""
                    SELECT * FROM {table_name}
                    WHERE {" AND ".join(where_parts)}
                    FOR UPDATE
                """
                current_row = await conn.fetchrow(select_query, *where_values)

                if not current_row:
                    raise ValueError(f"Record not found: {id}")

                # 2. Compute field diff
                current_data = dict(current_row)
                audit_entries = []

                for field_name, new_value in data.items():
                    old_value = current_data.get(field_name)

                    # Skip if no change
                    if old_value == new_value:
                        continue

                    # Create audit entry for this field
                    entry = {
                        "audit_id": uuid4(),
                        "record_id": id,
                        "field_name": field_name,
                        "old_value": self._serialize_value(old_value),
                        "new_value": self._serialize_value(new_value),
                        "operation": "UPDATE",
                        "changed_at": now,
                        "changed_by": user_id,
                        "transaction_id": transaction_id,
                    }
                    # Only add tenant_id if multi-tenant is enabled
                    if self.multi_tenant:
                        entry["tenant_id"] = tenant_id
                    audit_entries.append(entry)

                # 3. UPDATE main table
                set_parts = []
                set_values = []
                for key, value in data.items():
                    set_values.append(value)
                    set_parts.append(f"{key} = ${len(where_values) + len(set_values)}")

                update_query = f"""
                    UPDATE {table_name}
                    SET {", ".join(set_parts)}
                    WHERE {" AND ".join(where_parts)}
                    RETURNING *
                """

                row = await conn.fetchrow(update_query, *where_values, *set_values)

                # 4. INSERT audit entries
                if audit_entries:
                    await self._insert_audit_entries(conn, audit_table_name, audit_entries)

        return self._row_to_model(row)

    async def delete(
        self,
        id: UUID,
        db_pool,
        tenant_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
    ) -> bool:
        """
        Delete record with DELETE audit entry.

        If soft_delete: Update main table, create audit entry for deleted_at
        Otherwise: Hard DELETE, create audit entry
        """
        table_name = self._get_table_name()
        audit_table_name = f"{table_name}_audit"
        now = datetime.now(timezone.utc)
        transaction_id = uuid4()

        # Build WHERE clause
        where_parts = ["id = $1"]
        where_values = [id]

        if self.multi_tenant:
            if not tenant_id:
                raise ValueError("tenant_id required for multi-tenant model")
            where_parts.append(f"{self.tenant_field} = ${len(where_values) + 1}")
            where_values.append(tenant_id)

        async with db_pool.acquire() as conn:
            async with conn.transaction():
                # Get current record for audit
                select_query = f"""
                    SELECT * FROM {table_name}
                    WHERE {" AND ".join(where_parts)}
                """
                if self.soft_delete:
                    select_query += " AND deleted_at IS NULL"

                current_row = await conn.fetchrow(select_query, *where_values)

                if not current_row:
                    return False

                if self.soft_delete:
                    # Soft delete
                    delete_query = f"""
                        UPDATE {table_name}
                        SET deleted_at = ${len(where_values) + 1},
                            deleted_by = ${len(where_values) + 2}
                        WHERE {" AND ".join(where_parts)} AND deleted_at IS NULL
                        RETURNING id
                    """
                    await conn.fetchrow(delete_query, *where_values, now, user_id)

                    # Audit entry for deleted_at field
                    entry = {
                        "audit_id": uuid4(),
                        "record_id": id,
                        "field_name": "deleted_at",
                        "old_value": None,
                        "new_value": self._serialize_value(now),
                        "operation": "DELETE",
                        "changed_at": now,
                        "changed_by": user_id,
                        "transaction_id": transaction_id,
                    }
                    # Only add tenant_id if multi-tenant is enabled
                    if self.multi_tenant:
                        entry["tenant_id"] = tenant_id
                    audit_entries = [entry]
                else:
                    # Hard delete
                    delete_query = f"""
                        DELETE FROM {table_name}
                        WHERE {" AND ".join(where_parts)}
                        RETURNING id
                    """
                    await conn.fetchrow(delete_query, *where_values)

                    # Audit entry for DELETE
                    user_fields = self._get_user_fields(dict(current_row))
                    audit_entries = []

                    for field_name, old_value in user_fields.items():
                        entry = {
                            "audit_id": uuid4(),
                            "record_id": id,
                            "field_name": field_name,
                            "old_value": self._serialize_value(old_value),
                            "new_value": None,
                            "operation": "DELETE",
                            "changed_at": now,
                            "changed_by": user_id,
                            "transaction_id": transaction_id,
                        }
                        # Only add tenant_id if multi-tenant is enabled
                        if self.multi_tenant:
                            entry["tenant_id"] = tenant_id
                        audit_entries.append(entry)

                # Insert audit entries
                await self._insert_audit_entries(conn, audit_table_name, audit_entries)

        return True

    async def get(
        self,
        id: UUID,
        db_pool,
        tenant_id: Optional[UUID] = None,
        include_deleted: bool = False,
        **kwargs,
    ) -> Optional[T]:
        """Get record by ID (same as none strategy)."""
        table_name = self._get_table_name()

        # Build WHERE clause
        where_parts = ["id = $1"]
        where_values = [id]

        if self.multi_tenant:
            if not tenant_id:
                raise ValueError("tenant_id required for multi-tenant model")
            where_parts.append(f"{self.tenant_field} = ${len(where_values) + 1}")
            where_values.append(tenant_id)

        if self.soft_delete and not include_deleted:
            where_parts.append("deleted_at IS NULL")

        query = f"""
            SELECT * FROM {table_name}
            WHERE {" AND ".join(where_parts)}
        """

        async with db_pool.acquire() as conn:
            row = await conn.fetchrow(query, *where_values)

        if not row:
            return None

        return self._row_to_model(row)

    async def list(
        self,
        filters: Optional[Dict[str, Any]],
        db_pool,
        tenant_id: Optional[UUID] = None,
        limit: int = 100,
        offset: int = 0,
        include_deleted: bool = False,
        **kwargs,
    ) -> List[T]:
        """List records (same as none strategy)."""
        table_name = self._get_table_name()
        filters = filters or {}

        # Build WHERE clause
        where_parts = []
        where_values = []

        if self.multi_tenant:
            if not tenant_id:
                raise ValueError("tenant_id required for multi-tenant model")
            where_parts.append(f"{self.tenant_field} = ${len(where_values) + 1}")
            where_values.append(tenant_id)

        if self.soft_delete and not include_deleted:
            where_parts.append("deleted_at IS NULL")

        # User filters (with validation to prevent SQL injection)
        if filters:
            filter_clauses, filter_values = self._validate_and_build_filter_clauses(
                filters, base_param_count=len(where_values)
            )
            where_parts.extend(filter_clauses)
            where_values.extend(filter_values)

        where_clause = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""
        query = f"""
            SELECT * FROM {table_name}
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ${len(where_values) + 1}
            OFFSET ${len(where_values) + 2}
        """

        async with db_pool.acquire() as conn:
            rows = await conn.fetch(query, *where_values, limit, offset)

        return [self._row_to_model(row) for row in rows]

    # ==================== Audit Query Methods ====================

    async def get_audit_history(
        self,
        record_id: UUID,
        db_pool,
        tenant_id: Optional[UUID] = None,
    ) -> List[AuditEntry]:
        """
        Get full audit history for a record.

        Returns list of AuditEntry objects ordered by changed_at.
        """
        table_name = self._get_table_name()
        audit_table_name = f"{table_name}_audit"

        where_parts = ["record_id = $1"]
        where_values = [record_id]

        if self.multi_tenant:
            if not tenant_id:
                raise ValueError("tenant_id required for multi-tenant model")
            where_parts.append(f"{self.tenant_field} = ${len(where_values) + 1}")
            where_values.append(tenant_id)

        query = f"""
            SELECT * FROM {audit_table_name}
            WHERE {" AND ".join(where_parts)}
            ORDER BY changed_at ASC
        """

        async with db_pool.acquire() as conn:
            rows = await conn.fetch(query, *where_values)

        return [AuditEntry(**dict(row)) for row in rows]

    async def get_field_history(
        self,
        record_id: UUID,
        field_name: str,
        db_pool,
        tenant_id: Optional[UUID] = None,
    ) -> List[AuditEntry]:
        """Get history of specific field."""
        table_name = self._get_table_name()
        audit_table_name = f"{table_name}_audit"

        where_parts = ["record_id = $1", "field_name = $2"]
        where_values = [record_id, field_name]

        if self.multi_tenant:
            if not tenant_id:
                raise ValueError("tenant_id required for multi-tenant model")
            where_parts.append(f"{self.tenant_field} = ${len(where_values) + 1}")
            where_values.append(tenant_id)

        query = f"""
            SELECT * FROM {audit_table_name}
            WHERE {" AND ".join(where_parts)}
            ORDER BY changed_at ASC
        """

        async with db_pool.acquire() as conn:
            rows = await conn.fetch(query, *where_values)

        return [AuditEntry(**dict(row)) for row in rows]

    # ==================== Helper Methods ====================

    async def _insert_audit_entries(
        self, conn, audit_table_name: str, entries: List[Dict[str, Any]]
    ):
        """Bulk insert audit entries."""
        if not entries:
            return

        # Get columns from first entry
        columns = list(entries[0].keys())

        # Build multi-row INSERT
        values_clauses = []
        all_values = []

        for i, entry in enumerate(entries):
            placeholders = []
            for j, col in enumerate(columns):
                idx = i * len(columns) + j + 1
                placeholders.append(f"${idx}")
                all_values.append(entry[col])

            values_clauses.append(f"({', '.join(placeholders)})")

        query = f"""
            INSERT INTO {audit_table_name} ({", ".join(columns)})
            VALUES {", ".join(values_clauses)}
        """

        await conn.execute(query, *all_values)

    def _get_user_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Filter out system fields, return only user-defined fields."""
        system_fields = {
            "id",
            "created_at",
            "updated_at",
            "created_by",
            self.tenant_field,
            "deleted_at",
            "deleted_by",
        }

        return {k: v for k, v in data.items() if k not in system_fields}

    def _serialize_value(self, value: Any) -> Any:
        """
        Serialize value for JSONB storage.

        Returns JSON-compatible Python values that asyncpg can serialize to JSONB.
        We don't pre-serialize to JSON strings - let asyncpg handle the encoding.
        """
        if value is None:
            return None

        from datetime import date
        from decimal import Decimal
        from enum import Enum

        # Convert to JSON-compatible Python types (asyncpg will handle JSON encoding)
        if isinstance(value, datetime):
            return value.isoformat()
        elif isinstance(value, date):
            return value.isoformat()
        elif isinstance(value, UUID):
            return str(value)
        elif isinstance(value, Decimal):
            return str(value)  # Preserve exact precision as string
        elif isinstance(value, Enum):
            return value.value  # Return the underlying value
        elif isinstance(value, bytes):
            return value.hex()
        elif isinstance(value, (dict, list, str, int, float, bool)):
            return value  # Already JSON-compatible

        # For complex types, verify JSON compatibility
        try:
            json.dumps(value)
            return value
        except (TypeError, ValueError):
            # Fallback: convert to string for non-serializable types
            return str(value)

    def _get_table_name(self) -> str:
        """
        Get fully-qualified table name from model class.

        Returns schema-qualified name (e.g., "ix_ds_v2.umr") to ensure queries
        work regardless of PostgreSQL search_path configuration.
        """
        # Get schema (default to "public" if not specified)
        schema = getattr(self.model_class, "__schema__", "public")

        # Get table name
        if hasattr(self.model_class, "table_name"):
            table = self.model_class.table_name()
        elif hasattr(self.model_class, "__table_name__"):
            table = self.model_class.__table_name__
        else:
            table = self.model_class.__name__.lower() + "s"

        # Return schema-qualified name
        return f"{schema}.{table}"

    def _row_to_model(self, row) -> T:
        """Convert database row to model instance."""
        # Deserialize JSONB fields from JSON strings back to Python objects
        row_dict = self._deserialize_jsonb_fields(dict(row))

        if hasattr(self.model_class, "model_validate"):
            # Pydantic v2
            return self.model_class.model_validate(row_dict)
        elif hasattr(self.model_class, "from_orm"):
            # Pydantic v1
            return self.model_class.from_orm(row_dict)
        else:
            # Dataclass or other
            return self.model_class(**row_dict)
