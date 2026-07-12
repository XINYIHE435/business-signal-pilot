"""
Tool Registry - 工具注册和管理系统

所有业务逻辑通过 Tool 暴露，Agent 只负责调度。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
import structlog

logger = structlog.get_logger()


class BaseTool(ABC):
    """Tool 基类 - 所有 Tool 必须继承此类"""

    name: str
    description: str

    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """
        返回 LLM Function Calling Schema

        Returns:
            符合 Anthropic/OpenAI Tool Schema 格式的字典
        """
        pass

    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行 Tool

        Args:
            **kwargs: Tool 参数

        Returns:
            执行结果字典，至少包含 'success' 字段
        """
        pass


class ToolRegistry:
    """Tool 注册表 - 单例模式"""

    _instance = None
    _tools: Dict[str, BaseTool] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ToolRegistry, cls).__new__(cls)
            cls._instance._tools = {}
        return cls._instance

    def register(self, tool: BaseTool) -> None:
        """
        注册 Tool

        Args:
            tool: Tool 实例
        """
        if tool.name in self._tools:
            logger.warning("tool_already_registered", tool_name=tool.name)

        self._tools[tool.name] = tool
        logger.info("tool_registered", tool_name=tool.name, description=tool.description)

    def get(self, name: str) -> Optional[BaseTool]:
        """
        获取 Tool

        Args:
            name: Tool 名称

        Returns:
            Tool 实例或 None
        """
        return self._tools.get(name)

    def list_tools(self) -> List[str]:
        """列出所有已注册的 Tool 名称"""
        return list(self._tools.keys())

    def get_tools_for_llm(self) -> List[Dict[str, Any]]:
        """
        获取所有 Tool 的 Schema（用于 LLM Function Calling）

        Returns:
            Tool Schema 列表
        """
        return [tool.get_schema() for tool in self._tools.values()]

    async def execute_tool(self, name: str, **kwargs) -> Dict[str, Any]:
        """
        执行指定的 Tool

        Args:
            name: Tool 名称
            **kwargs: Tool 参数

        Returns:
            执行结果

        Raises:
            ValueError: Tool 不存在
        """
        tool = self.get(name)
        if not tool:
            logger.error("tool_not_found", tool_name=name)
            raise ValueError(f"Tool '{name}' not found in registry")

        logger.info("executing_tool", tool_name=name, params=kwargs)

        try:
            result = await tool.execute(**kwargs)
            logger.info("tool_executed", tool_name=name, success=result.get("success", False))
            return result
        except Exception as e:
            logger.error("tool_execution_failed", tool_name=name, error=str(e))
            return {
                "success": False,
                "error": str(e),
                "tool": name
            }

    def clear(self) -> None:
        """清空所有已注册的 Tool（测试用）"""
        self._tools.clear()
        logger.info("tool_registry_cleared")


# 全局 Tool Registry 实例
tool_registry = ToolRegistry()
