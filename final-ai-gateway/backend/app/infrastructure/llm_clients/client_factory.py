"""
LLM Client factory — creates the appropriate client based on backend type.
"""

from __future__ import annotations

import logging
from typing import Optional

from app.domain.ports.llm_client import LLMClientPort
from app.infrastructure.llm_clients.llamacpp_client import LlamacppClient
from app.infrastructure.llm_clients.ollama_client import OllamaClient
from app.infrastructure.llm_clients.openai_compatible_client import OpenAICompatibleClient

logger = logging.getLogger(__name__)


class LLMClientFactory:
    @staticmethod
    def create(backend: str, base_url: str = "", api_key: str = "",
                timeout: float = 120.0) -> LLMClientPort:
        if backend == "llamacpp":
            url = base_url or "http://127.0.0.1:8080"
            logger.info("Creating llama.cpp client: %s", url)
            return LlamacppClient(base_url=url, timeout=timeout)

        elif backend == "ollama":
            url = base_url or "http://127.0.0.1:11434"
            logger.info("Creating Ollama client: %s", url)
            return OllamaClient(base_url=url, timeout=timeout)

        elif backend == "openai":
            logger.info("Creating OpenAI-compatible client: %s", base_url)
            return OpenAICompatibleClient(base_url=base_url, api_key=api_key, timeout=timeout)

        else:
            logger.warning("Unknown backend '%s', defaulting to llama.cpp", backend)
            return LlamacppClient(base_url=base_url or "http://127.0.0.1:8080", timeout=timeout)
