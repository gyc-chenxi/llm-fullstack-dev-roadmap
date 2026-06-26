"""
Tool Registry port — abstract interface for agent tool registration and lookup.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ToolRegistryPort(ABC):
    @abstractmethod
    async def register(self, name: str, schema: dict, handler: callable) -> None:
        ...

    @abstractmethod
    async def unregister(self, name: str) -> None:
        ...

    @abstractmethod
    async def lookup(self, name: str) -> tuple[dict, callable] | None:
        ...

    @abstractmethod
    async def list_tools(self) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def execute(self, name: str, input_payload: dict[str, Any]) -> Any:
        ...
