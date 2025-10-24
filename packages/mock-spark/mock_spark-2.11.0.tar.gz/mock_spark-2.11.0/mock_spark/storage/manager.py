"""
Storage manager module.

This module provides a unified storage manager that can use different backends.
"""

from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import gc
import psutil
import os
from .interfaces import IStorageManager
from .backends.memory import MemoryStorageManager
from .backends.file import FileStorageManager
from mock_spark.backend.duckdb import DuckDBStorageManager
from mock_spark.spark_types import MockStructType, MockStructField


class TableMetadata:
    """Metadata for a table in the catalog."""

    def __init__(
        self,
        name: str,
        schema: str,
        created_at: datetime,
        table_schema: MockStructType,
        properties: dict,
    ):
        """Initialize table metadata.

        Args:
            name: Table name.
            schema: Schema/database name.
            created_at: Creation timestamp.
            table_schema: Table schema structure.
            properties: Table properties.
        """
        self.name = name
        self.schema = schema
        self.created_at = created_at
        self.table_schema = table_schema
        self.properties = properties
        self.qualified_name = f"{schema}.{name}"


class StorageManagerFactory:
    """Factory for creating storage managers."""

    @staticmethod
    def create_memory_manager() -> IStorageManager:
        """Create a memory storage manager.

        Returns:
            Memory storage manager instance.
        """
        return MemoryStorageManager()

    @staticmethod
    def create_file_manager(base_path: str = "mock_spark_storage") -> IStorageManager:
        """Create a file storage manager.

        Args:
            base_path: Base path for storage files.

        Returns:
            File storage manager instance.
        """
        return FileStorageManager(base_path)

    @staticmethod
    def create_duckdb_manager(db_path: Optional[str] = None) -> IStorageManager:
        """Create a DuckDB storage manager with in-memory storage by default.

        Args:
            db_path: Optional path to DuckDB database file. If None, uses in-memory storage.

        Returns:
            DuckDB storage manager instance.
        """
        return DuckDBStorageManager(db_path)


class UnifiedStorageManager(IStorageManager):
    """Unified storage manager that can switch between backends."""

    def __init__(self, backend: IStorageManager):
        """Initialize unified storage manager.

        Args:
            backend: Storage backend to use.
        """
        self.backend = backend
        self._table_metadata: Dict[str, TableMetadata] = {}

    def create_schema(self, schema: str) -> None:
        """Create a new schema.

        Args:
            schema: Name of the schema to create.
        """
        self.backend.create_schema(schema)

    def schema_exists(self, schema: str) -> bool:
        """Check if schema exists.

        Args:
            schema: Name of the schema to check.

        Returns:
            True if schema exists, False otherwise.
        """
        return self.backend.schema_exists(schema)

    def drop_schema(self, schema: str) -> None:
        """Drop a schema.

        Args:
            schema: Name of the schema to drop.
        """
        self.backend.drop_schema(schema)

    def list_schemas(self) -> List[str]:
        """List all schemas.

        Returns:
            List of schema names.
        """
        return self.backend.list_schemas()

    def table_exists(self, schema: str, table: str) -> bool:
        """Check if table exists.

        Args:
            schema: Name of the schema.
            table: Name of the table.

        Returns:
            True if table exists, False otherwise.
        """
        return self.backend.table_exists(schema, table)

    def create_table(
        self,
        schema: str,
        table: str,
        columns: Union[List[MockStructField], MockStructType],
    ) -> None:
        """Create a new table.

        Args:
            schema: Name of the schema.
            table: Name of the table.
            columns: Table columns definition.
        """
        self.backend.create_table(schema, table, columns)

    def drop_table(self, schema: str, table: str) -> None:
        """Drop a table.

        Args:
            schema: Name of the schema.
            table: Name of the table.
        """
        self.backend.drop_table(schema, table)

    def insert_data(
        self, schema: str, table: str, data: List[Dict[str, Any]], mode: str = "append"
    ) -> None:
        """Insert data into table.

        Args:
            schema: Name of the schema.
            table: Name of the table.
            data: Data to insert.
            mode: Insert mode ("append", "overwrite", "ignore").
        """
        self.backend.insert_data(schema, table, data, mode)

    def query_table(
        self, schema: str, table: str, filter_expr: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Query data from table.

        Args:
            schema: Name of the schema.
            table: Name of the table.
            filter_expr: Optional filter expression.

        Returns:
            List of data rows.
        """
        return self.backend.query_table(schema, table, filter_expr)

    def get_table_schema(self, schema: str, table: str) -> Optional[MockStructType]:
        """Get table schema.

        Args:
            schema: Name of the schema.
            table: Name of the table.

        Returns:
            Table schema or None if table doesn't exist.
        """
        return self.backend.get_table_schema(schema, table)

    def get_data(self, schema: str, table: str) -> List[Dict[str, Any]]:
        """Get all data from table.

        Args:
            schema: Name of the schema.
            table: Name of the table.

        Returns:
            List of data rows.
        """
        return self.backend.get_data(schema, table)

    def create_temp_view(self, name: str, dataframe: Any) -> None:
        """Create a temporary view from a DataFrame.

        Args:
            name: Name of the temporary view.
            dataframe: DataFrame to create view from.
        """
        self.backend.create_temp_view(name, dataframe)

    def list_tables(self, schema: str) -> List[str]:
        """List tables in schema.

        Args:
            schema: Name of the schema.

        Returns:
            List of table names.
        """
        return self.backend.list_tables(schema)

    def get_table_metadata(self, schema: str, table: str) -> Optional[Dict[str, Any]]:
        """Get table metadata including Delta-specific fields.

        Args:
            schema: Name of the schema.
            table: Name of the table.

        Returns:
            Table metadata dictionary or None if table doesn't exist.
        """
        return self.backend.get_table_metadata(schema, table)

    def update_table_metadata(
        self, schema: str, table: str, metadata_updates: Dict[str, Any]
    ) -> None:
        """Update table metadata fields.

        Args:
            schema: Name of the schema.
            table: Name of the table.
            metadata_updates: Dictionary of metadata fields to update.
        """
        self.backend.update_table_metadata(schema, table, metadata_updates)

    def switch_backend(self, backend: IStorageManager) -> None:
        """Switch to a different storage backend.

        Args:
            backend: New storage backend to use.
        """
        self.backend = backend

    def save_table_metadata(self, qualified_name: str, metadata: TableMetadata) -> None:
        """Store table metadata.

        Args:
            qualified_name: Qualified table name (schema.table).
            metadata: Table metadata to store.
        """
        self._table_metadata[qualified_name] = metadata

    def get_table_metadata_by_name(
        self, qualified_name: str
    ) -> Optional[TableMetadata]:
        """Retrieve table metadata by qualified name.

        Args:
            qualified_name: Qualified table name (schema.table).

        Returns:
            Table metadata or None if not found.
        """
        return self._table_metadata.get(qualified_name)

    def list_table_metadata(self, schema: str) -> List[TableMetadata]:
        """List all table metadata for a schema.

        Args:
            schema: Schema name.

        Returns:
            List of table metadata objects.
        """
        return [
            metadata
            for qualified_name, metadata in self._table_metadata.items()
            if metadata.schema == schema
        ]

    def cleanup_temp_tables(self) -> None:
        """Clean up temporary tables to free memory."""
        try:
            if hasattr(self.backend, "cleanup_temp_tables"):
                self.backend.cleanup_temp_tables()
        except Exception:
            # Ignore errors during cleanup
            pass

    def optimize_storage(self) -> None:
        """Optimize storage by cleaning up and compacting data."""
        try:
            if hasattr(self.backend, "optimize_storage"):
                self.backend.optimize_storage()
        except Exception:
            # Ignore errors during optimization
            pass

    def get_memory_usage(self) -> Dict[str, Any]:
        """Get current memory usage statistics.

        Returns:
            Dictionary with memory usage information.
        """
        try:
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()

            return {
                "rss": memory_info.rss,  # Resident Set Size
                "vms": memory_info.vms,  # Virtual Memory Size
                "percent": process.memory_percent(),
                "available": psutil.virtual_memory().available,
                "total": psutil.virtual_memory().total,
            }
        except Exception:
            return {"rss": 0, "vms": 0, "percent": 0, "available": 0, "total": 0}

    def force_garbage_collection(self) -> None:
        """Force garbage collection to free memory."""
        gc.collect()

    def get_table_sizes(self) -> Dict[str, int]:
        """Get estimated sizes of all tables.

        Returns:
            Dictionary mapping table names to estimated sizes.
        """
        sizes = {}
        for qualified_name, metadata in self._table_metadata.items():
            try:
                # Estimate size based on metadata
                estimated_size = (
                    metadata.table_schema.get_field_count() * 100
                )  # Rough estimate
                sizes[qualified_name] = estimated_size
            except Exception:
                sizes[qualified_name] = 0
        return sizes

    def cleanup_old_tables(self, max_age_hours: int = 24) -> int:
        """Clean up tables older than specified age.

        Args:
            max_age_hours: Maximum age in hours before cleanup.

        Returns:
            Number of tables cleaned up.
        """
        from datetime import timedelta

        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        cleaned_count = 0

        for qualified_name, metadata in list(self._table_metadata.items()):
            if metadata.created_at < cutoff_time:
                try:
                    # Remove from metadata
                    del self._table_metadata[qualified_name]

                    # Remove from backend if possible
                    if hasattr(self.backend, "drop_table"):
                        schema, table = qualified_name.split(".", 1)
                        self.backend.drop_table(schema, table)

                    cleaned_count += 1
                except Exception:
                    # Ignore errors during cleanup
                    pass

        return cleaned_count
