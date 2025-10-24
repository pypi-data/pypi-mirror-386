"""Tests for SQL tools."""

import json

import pytest

from sqlsaber.database import SQLiteConnection
from sqlsaber.tools.sql_tools import (
    ExecuteSQLTool,
    IntrospectSchemaTool,
    ListTablesTool,
)


class MockDatabaseConnection(SQLiteConnection):
    """Mock database connection for testing."""

    def __init__(self):
        self.queries = []
        self.mock_results = []

    def to_connection_string(self) -> str:
        return "mock://test"

    async def test_connection(self) -> bool:
        return True

    async def execute_query(self, query: str) -> list[dict]:
        self.queries.append(query)
        return self.mock_results

    async def get_pool(self):
        return None

    async def close(self):
        pass


class MockSchemaManager:
    """Mock schema manager for testing."""

    def __init__(self, db_connection):
        self.db = db_connection

    async def list_tables(self) -> dict:
        return {
            "tables": [
                {"name": "users", "row_count": 100},
                {"name": "orders", "row_count": 500},
            ]
        }

    async def get_schema_info(self, table_pattern=None) -> dict:
        schema = {
            "users": {
                "columns": {
                    "id": {"data_type": "integer", "nullable": False, "default": None},
                    "name": {"data_type": "varchar", "nullable": True, "default": None},
                },
                "primary_keys": ["id"],
                "foreign_keys": [],
                "indexes": [],
            }
        }
        if table_pattern and table_pattern in schema:
            return {table_pattern: schema[table_pattern]}
        return schema


class TestListTablesTool:
    """Test the ListTablesTool."""

    def test_tool_properties(self):
        """Test tool properties."""
        tool = ListTablesTool()
        assert tool.name == "list_tables"
        assert "tables" in tool.description.lower()

    @pytest.mark.asyncio
    async def test_execute_without_connection(self):
        """Test execution without database connection."""
        tool = ListTablesTool()
        result = await tool.execute()
        data = json.loads(result)
        assert "error" in data
        assert "no database connection" in data["error"].lower()

    @pytest.mark.asyncio
    async def test_execute_with_connection(self):
        """Test execution with database connection."""
        tool = ListTablesTool()
        tool.db = MockDatabaseConnection()

        # Mock the schema_manager directly
        mock_schema_manager = MockSchemaManager(None)
        tool.schema_manager = mock_schema_manager

        result = await tool.execute()
        data = json.loads(result)

        assert "tables" in data
        assert len(data["tables"]) == 2
        assert data["tables"][0]["name"] == "users"


class TestIntrospectSchemaTool:
    """Test the IntrospectSchemaTool."""

    def test_tool_properties(self):
        """Test tool properties."""
        tool = IntrospectSchemaTool()
        assert tool.name == "introspect_schema"
        assert "schema" in tool.description.lower()

    @pytest.mark.asyncio
    async def test_execute_with_pattern(self):
        """Test execution with table pattern."""
        tool = IntrospectSchemaTool()
        tool.db = MockDatabaseConnection()

        # Mock the schema_manager directly
        mock_schema_manager = MockSchemaManager(None)
        tool.schema_manager = mock_schema_manager

        result = await tool.execute(table_pattern="users")
        data = json.loads(result)

        assert "users" in data
        assert "columns" in data["users"]
        assert "id" in data["users"]["columns"]


class TestExecuteSQLTool:
    """Test the ExecuteSQLTool."""

    def test_tool_properties(self):
        """Test tool properties."""
        tool = ExecuteSQLTool()
        assert tool.name == "execute_sql"
        assert "query" in tool.input_schema["properties"]

    @pytest.mark.asyncio
    async def test_execute_select_query(self):
        """Test executing a SELECT query."""
        tool = ExecuteSQLTool()
        db = MockDatabaseConnection()
        db.mock_results = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
        tool.db = db  # Set db directly, skip schema manager

        result = await tool.execute(query="SELECT * FROM users")
        data = json.loads(result)

        assert data["success"] is True
        assert data["row_count"] == 2
        assert len(data["results"]) == 2
        assert db.queries[-1] == "SELECT * FROM users LIMIT 100;"

    @pytest.mark.asyncio
    async def test_execute_with_limit(self):
        """Test executing with custom limit."""
        tool = ExecuteSQLTool()
        db = MockDatabaseConnection()
        db.mock_results = [{"id": i} for i in range(10)]
        tool.db = db  # Set db directly, skip schema manager

        result = await tool.execute(query="SELECT * FROM users", limit=5)
        data = json.loads(result)

        assert data["row_count"] == 10
        assert len(data["results"]) == 5
        assert data["truncated"] is True

    @pytest.mark.asyncio
    async def test_block_write_operations(self):
        """Test that write operations are blocked."""
        tool = ExecuteSQLTool()
        tool.set_connection(MockDatabaseConnection())

        # Test various write operations
        write_queries = [
            "INSERT INTO users VALUES (1, 'test')",
            "UPDATE users SET name = 'test'",
            "DELETE FROM users",
            "DROP TABLE users",
            "CREATE TABLE test (id INT)",
            "ALTER TABLE users ADD COLUMN test",
            "TRUNCATE TABLE users",
        ]

        for query in write_queries:
            result = await tool.execute(query=query)
            data = json.loads(result)
            assert "error" in data
            assert "only select" in data["error"].lower()

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling."""
        tool = ExecuteSQLTool()
        db = MockDatabaseConnection()

        # Simulate database error
        async def mock_execute_error(query):
            raise Exception("Table 'unknown_table' does not exist")

        db.execute_query = mock_execute_error
        tool.db = db  # Set db directly, skip schema manager

        result = await tool.execute(query="SELECT * FROM unknown_table")
        data = json.loads(result)

        assert "error" in data
        assert "unknown_table" in data["error"]
        assert "suggestions" in data
        assert len(data["suggestions"]) > 0
