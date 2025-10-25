"""
Memory storage backend.

This module provides an in-memory storage implementation.
"""

from typing import List, Dict, Any, Optional, Union
from ...core.interfaces.storage import IStorageManager, ITable
from mock_spark.spark_types import MockStructType, MockStructField


class MemoryTable(ITable):
    """In-memory table implementation."""

    def __init__(self, name: str, schema: MockStructType):
        """Initialize memory table.

        Args:
            name: Table name.
            schema: Table schema.
        """
        self._name = name
        self._schema = schema
        self.data: List[Dict[str, Any]] = []
        self._metadata = {
            "created_at": "2024-01-01T00:00:00Z",
            "row_count": 0,
            "schema_version": "1.0",
        }

    @property
    def name(self) -> str:
        """Get table name."""
        return self._name

    @property
    def schema(self) -> MockStructType:
        """Get table schema."""
        return self._schema

    @property
    def metadata(self) -> Dict[str, Any]:
        """Get table metadata."""
        return self._metadata

    def insert_data(self, data: List[Dict[str, Any]], mode: str = "append") -> None:
        """Insert data into table.

        Args:
            data: Data to insert.
            mode: Insert mode ("append", "overwrite", "ignore").
        """
        if mode == "overwrite":
            self.data = data.copy()
        elif mode == "append":
            self.data.extend(data)
        elif mode == "ignore":
            # Only insert if table is empty
            if not self.data:
                self.data.extend(data)

        self._metadata["row_count"] = len(self.data)

    def query_data(self, filter_expr: Optional[str] = None) -> List[Dict[str, Any]]:
        """Query data from table.

        Args:
            filter_expr: Optional filter expression.

        Returns:
            List of data rows.
        """
        if filter_expr is None:
            return self.data.copy()

        # Simple filter implementation
        # In a real implementation, this would parse and evaluate the filter expression
        return self.data.copy()

    def get_schema(self) -> MockStructType:
        """Get table schema.

        Returns:
            Table schema.
        """
        return self.schema

    def get_metadata(self) -> Dict[str, Any]:
        """Get table metadata.

        Returns:
            Table metadata.
        """
        return self._metadata.copy()

    def insert(self, data: List[Dict[str, Any]]) -> None:
        """Insert data into table."""
        self.insert_data(data)

    def query(self, **filters: Any) -> List[Dict[str, Any]]:
        """Query data from table."""
        return self.query_data()

    def count(self) -> int:
        """Count rows in table."""
        return len(self.data)

    def truncate(self) -> None:
        """Truncate table."""
        self.data.clear()
        self._metadata["row_count"] = 0

    def drop(self) -> None:
        """Drop table."""
        self.data.clear()
        self._metadata.clear()


class MemorySchema:
    """In-memory database schema (namespace) implementation."""

    def __init__(self, name: str):
        """Initialize memory schema.

        Args:
            name: Schema name.
        """
        self.name = name
        self.tables: Dict[str, MemoryTable] = {}

    def create_table(
        self, table: str, columns: Union[List[MockStructField], MockStructType]
    ) -> None:
        """Create a new table in this schema.

        Args:
            table: Name of the table.
            columns: Table columns definition.
        """
        if isinstance(columns, list):
            schema = MockStructType(columns)
        else:
            schema = columns

        self.tables[table] = MemoryTable(table, schema)

    def table_exists(self, table: str) -> bool:
        """Check if table exists in this schema.

        Args:
            table: Name of the table.

        Returns:
            True if table exists, False otherwise.
        """
        return table in self.tables

    def drop_table(self, table: str) -> None:
        """Drop a table from this schema.

        Args:
            table: Name of the table.
        """
        if table in self.tables:
            del self.tables[table]

    def list_tables(self) -> List[str]:
        """List all tables in this schema.

        Returns:
            List of table names.
        """
        return list(self.tables.keys())


class MemoryStorageManager(IStorageManager):
    """In-memory storage manager implementation."""

    def __init__(self) -> None:
        """Initialize memory storage manager."""
        self.schemas: Dict[str, MemorySchema] = {}
        # Create default schema
        self.schemas["default"] = MemorySchema("default")

    def create_schema(self, schema: str) -> None:
        """Create a new schema.

        Args:
            schema: Name of the schema to create.
        """
        if schema not in self.schemas:
            self.schemas[schema] = MemorySchema(schema)

    def schema_exists(self, schema: str) -> bool:
        """Check if schema exists.

        Args:
            schema: Name of the schema to check.

        Returns:
            True if schema exists, False otherwise.
        """
        return schema in self.schemas

    def drop_schema(self, schema_name: str, cascade: bool = False) -> None:
        """Drop a schema.

        Args:
            schema_name: Name of the schema to drop.
            cascade: Whether to cascade the drop operation.
        """
        if schema_name in self.schemas and schema_name != "default":
            del self.schemas[schema_name]

    def list_schemas(self) -> List[str]:
        """List all schemas.

        Returns:
            List of schema names.
        """
        return list(self.schemas.keys())

    def table_exists(self, schema: str, table: str) -> bool:
        """Check if table exists.

        Args:
            schema: Name of the schema.
            table: Name of the table.

        Returns:
            True if table exists, False otherwise.
        """
        if schema not in self.schemas:
            return False
        return self.schemas[schema].table_exists(table)

    def create_table(
        self,
        schema_name: str,
        table_name: str,
        fields: Union[List[Any], MockStructType],
    ) -> None:
        """Create a new table.

        Args:
            schema_name: Name of the schema.
            table_name: Name of the table.
            fields: Table fields definition.
        """
        if schema_name not in self.schemas:
            self.create_schema(schema_name)

        self.schemas[schema_name].create_table(table_name, fields)

    def drop_table(self, schema_name: str, table_name: str) -> None:
        """Drop a table.

        Args:
            schema_name: Name of the schema.
            table_name: Name of the table.
        """
        if schema_name in self.schemas:
            self.schemas[schema_name].drop_table(table_name)

    def insert_data(
        self, schema_name: str, table_name: str, data: List[Dict[str, Any]]
    ) -> None:
        """Insert data into table.

        Args:
            schema_name: Name of the schema.
            table_name: Name of the table.
            data: Data to insert.
        """
        if (
            schema_name in self.schemas
            and table_name in self.schemas[schema_name].tables
        ):
            self.schemas[schema_name].tables[table_name].insert_data(data)

    def query_data(
        self, schema_name: str, table_name: str, **filters: Any
    ) -> List[Dict[str, Any]]:
        """Query data from table.

        Args:
            schema_name: Name of the schema.
            table_name: Name of the table.
            **filters: Optional filter parameters.

        Returns:
            List of data rows.
        """
        if (
            schema_name in self.schemas
            and table_name in self.schemas[schema_name].tables
        ):
            return self.schemas[schema_name].tables[table_name].query_data()
        return []

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
        if schema in self.schemas and table in self.schemas[schema].tables:
            return self.schemas[schema].tables[table].query_data(filter_expr)
        return []

    def get_table_schema(self, schema_name: str, table_name: str) -> MockStructType:
        """Get table schema.

        Args:
            schema_name: Name of the schema.
            table_name: Name of the table.

        Returns:
            Table schema.
        """
        if (
            schema_name in self.schemas
            and table_name in self.schemas[schema_name].tables
        ):
            return self.schemas[schema_name].tables[table_name].get_schema()
        # Return empty schema if table doesn't exist
        return MockStructType([])

    def get_data(self, schema: str, table: str) -> List[Dict[str, Any]]:
        """Get all data from table.

        Args:
            schema: Name of the schema.
            table: Name of the table.

        Returns:
            List of data rows.
        """
        return self.query_table(schema, table)

    def create_temp_view(self, name: str, dataframe: Any) -> None:
        """Create a temporary view from a DataFrame.

        Args:
            name: Name of the temporary view.
            dataframe: DataFrame to create view from.
        """
        # Create a schema and table for the temporary view
        schema = "default"
        self.create_schema(schema)

        # Convert DataFrame data to table format
        data = dataframe.data
        schema_obj = dataframe.schema

        # Create the table
        self.create_table(schema, name, schema_obj)

        # Insert the data
        self.insert_data(schema, name, data)

    def list_tables(self, schema_name: Optional[str] = None) -> List[str]:
        """List tables in schema.

        Args:
            schema_name: Name of the schema. If None, list tables in all schemas.

        Returns:
            List of table names.
        """
        if schema_name is None:
            # List tables from all schemas
            all_tables = []
            for schema in self.schemas.values():
                all_tables.extend(schema.list_tables())
            return all_tables

        if schema_name not in self.schemas:
            return []
        return self.schemas[schema_name].list_tables()

    def get_table_metadata(self, schema_name: str, table_name: str) -> Dict[str, Any]:
        """Get table metadata including Delta-specific fields.

        Args:
            schema_name: Name of the schema.
            table_name: Name of the table.

        Returns:
            Table metadata dictionary.
        """
        if schema_name not in self.schemas:
            return {}
        if table_name not in self.schemas[schema_name].tables:
            return {}
        return self.schemas[schema_name].tables[table_name].get_metadata()

    def update_table_metadata(
        self, schema_name: str, table_name: str, metadata_updates: Dict[str, Any]
    ) -> None:
        """Update table metadata fields.

        Args:
            schema_name: Name of the schema.
            table_name: Name of the table.
            metadata_updates: Dictionary of metadata fields to update.
        """
        if (
            schema_name in self.schemas
            and table_name in self.schemas[schema_name].tables
        ):
            table_obj = self.schemas[schema_name].tables[table_name]
            table_obj._metadata.update(metadata_updates)

    def close(self) -> None:
        """Close storage backend and clean up resources.

        For in-memory storage, this is a no-op as there are no external resources.
        """
        pass
