"""
Tool Registry — agent tool schema, registration, and execution.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Callable

from app.domain.ports.tool_registry_port import ToolRegistryPort

logger = logging.getLogger(__name__)


class ToolRegistry(ToolRegistryPort):
    def __init__(self):
        self._tools: dict[str, dict[str, Any]] = {}
        self._handlers: dict[str, Callable] = {}
        self._register_defaults()

    def _register_defaults(self):
        self.register_sync(
            "calculator",
            {
                "name": "calculator",
                "description": "Evaluate a mathematical expression. Supports +, -, *, /, **, and parentheses.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {"type": "string", "description": "Math expression to evaluate"},
                    },
                    "required": ["expression"],
                },
            },
            self._calculator,
        )
        self.register_sync(
            "file_search",
            {
                "name": "file_search",
                "description": "Search for files matching a pattern in the workspace.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "pattern": {"type": "string", "description": "File glob pattern"},
                    },
                    "required": ["pattern"],
                },
            },
            self._file_search,
        )
        self.register_sync(
            "web_search",
            {
                "name": "web_search",
                "description": "Search the web for information. Returns top results.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query string"},
                    },
                    "required": ["query"],
                },
            },
            self._web_search,
        )

    def register_sync(self, name: str, schema: dict, handler: Callable) -> None:
        self._tools[name] = schema
        self._handlers[name] = handler

    async def register(self, name: str, schema: dict, handler: Callable) -> None:
        self.register_sync(name, schema, handler)

    async def unregister(self, name: str) -> None:
        self._tools.pop(name, None)
        self._handlers.pop(name, None)

    async def lookup(self, name: str) -> tuple[dict, Callable] | None:
        schema = self._tools.get(name)
        handler = self._handlers.get(name)
        if schema and handler:
            return schema, handler
        return None

    async def list_tools(self) -> list[dict[str, Any]]:
        return list(self._tools.values())

    async def execute(self, name: str, input_payload: dict[str, Any]) -> Any:
        handler = self._handlers.get(name)
        if handler is None:
            raise ValueError(f"Tool not found: {name}")
        t0 = time.monotonic()
        try:
            result = handler(input_payload)
            elapsed = (time.monotonic() - t0) * 1000
            logger.info("Tool %s executed in %.1fms", name, elapsed)
            return {"status": "success", "result": result, "latency_ms": elapsed}
        except Exception as e:
            elapsed = (time.monotonic() - t0) * 1000
            return {"status": "error", "error": str(e), "latency_ms": elapsed}

    @staticmethod
    def _calculator(payload: dict) -> str:
        expression = payload.get("expression", "")
        allowed = set("0123456789+-*/().% ")
        if not all(c in allowed for c in expression):
            return "Error: expression contains disallowed characters"
        try:
            result = eval(expression, {"__builtins__": {}}, {})
            return str(result)
        except Exception as e:
            return f"Error: {e}"

    @staticmethod
    def _file_search(payload: dict) -> str:
        import glob
        import os
        pattern = payload.get("pattern", "*")
        try:
            matches = glob.glob(pattern, recursive=True)
            return f"Found {len(matches)} files: {', '.join(matches[:10])}"
        except Exception as e:
            return f"Error: {e}"

    @staticmethod
    def _web_search(payload: dict) -> str:
        query = payload.get("query", "")
        return f"[Mock] Web search results for: '{query}'\n1. Result A (relevance: 0.95)\n2. Result B (relevance: 0.82)\n3. Result C (relevance: 0.71)"