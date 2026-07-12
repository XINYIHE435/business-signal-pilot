"""
测试 Tool Registry 和 Database Tool
"""

import pytest
import asyncio
from app.tools.registry import BaseTool, ToolRegistry
from app.tools.database_tool import DatabaseTool
from app.adapters.database.duckdb import DuckDBAdapter


class MockTool(BaseTool):
    """Mock Tool for testing"""

    name = "mock_tool"
    description = "A mock tool for testing"

    def get_schema(self):
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "param": {"type": "string"}
                }
            }
        }

    async def execute(self, param: str = "", **kwargs):
        return {"success": True, "param": param}


def test_tool_registry_register():
    """测试工具注册"""
    registry = ToolRegistry()
    registry.clear()

    tool = MockTool()
    registry.register(tool)

    assert "mock_tool" in registry.list_tools()
    assert registry.get("mock_tool") is not None


def test_tool_registry_get_schema():
    """测试获取 Tool Schema"""
    registry = ToolRegistry()
    registry.clear()

    tool = MockTool()
    registry.register(tool)

    schemas = registry.get_tools_for_llm()
    assert len(schemas) == 1
    assert schemas[0]["name"] == "mock_tool"


@pytest.mark.asyncio
async def test_tool_registry_execute():
    """测试执行 Tool"""
    registry = ToolRegistry()
    registry.clear()

    tool = MockTool()
    registry.register(tool)

    result = await registry.execute_tool("mock_tool", param="test_value")

    assert result["success"] is True
    assert result["param"] == "test_value"


@pytest.mark.asyncio
async def test_tool_registry_execute_not_found():
    """测试执行不存在的 Tool"""
    registry = ToolRegistry()
    registry.clear()

    with pytest.raises(ValueError, match="not found"):
        await registry.execute_tool("nonexistent_tool")


@pytest.mark.asyncio
async def test_database_tool():
    """测试 Database Tool"""
    # 注意：这个测试需要实际的数据库文件
    # 在 CI 环境中可能需要 skip
    import os
    db_path = "data/signal.db"

    if not os.path.exists(db_path):
        pytest.skip(f"Database file not found: {db_path}")

    adapter = DuckDBAdapter(db_path, read_only=True)
    tool = DatabaseTool(adapter)

    # 测试 schema
    schema = tool.get_schema()
    assert schema["name"] == "execute_sql"
    assert "sql" in schema["input_schema"]["properties"]

    # 测试执行简单查询
    result = await tool.execute(
        sql="SELECT 1 as test_value",
        explanation="Test query"
    )

    assert result["success"] is True
    assert result["row_count"] > 0
    assert result["data"][0]["test_value"] == 1

    adapter.close()


@pytest.mark.asyncio
async def test_database_tool_error_handling():
    """测试 Database Tool 错误处理"""
    import os
    db_path = "data/signal.db"

    if not os.path.exists(db_path):
        pytest.skip(f"Database file not found: {db_path}")

    adapter = DuckDBAdapter(db_path, read_only=True)
    tool = DatabaseTool(adapter)

    # 测试错误的 SQL
    result = await tool.execute(
        sql="SELECT * FROM nonexistent_table",
        explanation="This should fail"
    )

    assert result["success"] is False
    assert "error" in result

    adapter.close()


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
