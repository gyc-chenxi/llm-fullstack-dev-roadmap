"""
System probes — monitor macOS memory, llama.cpp metrics, and Ollama health.
"""

from __future__ import annotations

import logging
import subprocess
from typing import Optional

import httpx

from app.domain.ports.system_probe import SystemProbePort

logger = logging.getLogger(__name__)


class MacOSMemoryProbe(SystemProbePort):
    def __init__(self):
        self._page_size = 16384  # M-series default

    async def get_memory_pressure(self) -> float:
        try:
            result = subprocess.run(
                ["memory_pressure"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            for line in result.stdout.splitlines():
                if "System-wide memory free percentage" in line:
                    pct = float(line.split(":")[-1].strip().replace("%", ""))
                    return 1.0 - pct / 100.0
            return 0.0
        except Exception as e:
            logger.debug("memory_pressure failed: %s", e)
            return 0.0

    async def get_available_memory_mb(self) -> int:
        try:
            result = subprocess.run(
                ["sysctl", "hw.memsize"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            total_bytes = int(result.stdout.strip().split(":")[-1].strip())
            return total_bytes // (1024 * 1024)
        except Exception:
            return 0

    async def get_cpu_usage_percent(self) -> float:
        try:
            result = subprocess.run(
                ["ps", "-A", "-o", "%cpu"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            lines = result.stdout.strip().split("\n")[1:]
            total = sum(float(line.strip()) for line in lines if line.strip())
            return min(100.0, total)
        except Exception:
            return 0.0

    async def get_system_snapshot(self) -> dict:
        return {
            "memory_pressure": await self.get_memory_pressure(),
            "available_memory_mb": await self.get_available_memory_mb(),
            "cpu_usage_percent": await self.get_cpu_usage_percent(),
        }


class LlamacppMetricsProbe:
    """Probes llama.cpp server's /metrics and /slots endpoints."""

    def __init__(self, base_url: str = "http://127.0.0.1:8080"):
        self.base_url = base_url.rstrip("/")
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=httpx.Timeout(10.0))
        return self._client

    async def get_metrics(self) -> dict:
        try:
            client = await self._get_client()
            response = await client.get(f"{self.base_url}/metrics")
            response.raise_for_status()
            return {"status": "ok", "raw": response.text}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def get_slot_status(self) -> list[dict]:
        try:
            client = await self._get_client()
            response = await client.get(f"{self.base_url}/slots")
            response.raise_for_status()
            return response.json()
        except Exception:
            return []

    async def is_healthy(self) -> bool:
        try:
            client = await self._get_client()
            response = await client.get(f"{self.base_url}/health")
            return response.status_code == 200
        except Exception:
            return False


class OllamaProbe:
    """Probes Ollama server health and model list."""

    def __init__(self, base_url: str = "http://127.0.0.1:11434"):
        self.base_url = base_url.rstrip("/")
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=httpx.Timeout(10.0))
        return self._client

    async def get_tags(self) -> list[str]:
        try:
            client = await self._get_client()
            response = await client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            data = response.json()
            return [m.get("name", "") for m in data.get("models", [])]
        except Exception:
            return []

    async def is_healthy(self) -> bool:
        try:
            client = await self._get_client()
            response = await client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except Exception:
            return False
