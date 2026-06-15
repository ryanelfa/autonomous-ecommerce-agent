"""Tool abstraction: every agent capability is a Tool subclass with a strict JSON schema.

This is the OOP backbone of the project: Agent -> ToolRegistry -> Tool.execute().
"""
from abc import ABC, abstractmethod
from typing import Any

from sqlmodel import Session


class Tool(ABC):
    name: str
    description: str
    input_schema: dict[str, Any]
    terminal: bool = False  # terminal tools end the agent loop (refund, substitute, voucher, escalate)

    @abstractmethod
    async def execute(self, db: Session, **kwargs: Any) -> dict[str, Any]:
        """Must return a JSON-serializable dict with at least {"ok": bool}."""
        raise NotImplementedError

    def to_anthropic(self) -> dict[str, Any]:
        return {"name": self.name, "description": self.description, "input_schema": self.input_schema}


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def is_terminal(self, name: str) -> bool:
        tool = self._tools.get(name)
        return bool(tool and tool.terminal)

    def to_anthropic_tools(self) -> list[dict[str, Any]]:
        return [t.to_anthropic() for t in self._tools.values()]

    async def dispatch(self, name: str, args: dict[str, Any], db: Session) -> dict[str, Any]:
        tool = self._tools.get(name)
        if tool is None:
            return {"ok": False, "error": f"unknown_tool:{name}"}
        try:
            return await tool.execute(db, **args)
        except TypeError as exc:
            return {"ok": False, "error": f"bad_arguments: {exc}"}
        except Exception as exc:
            return {"ok": False, "error": f"tool_error: {exc}"}
