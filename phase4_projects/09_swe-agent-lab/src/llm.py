"""
LLM 接口封装
==============

统一 OpenAI 与 Anthropic SDK 的差异，使 Agent 主循环无需关心底层 provider。

数据流：
  messages: [{role, content}] → LLMClient.invoke()
    ├── OpenAI: client.chat.completions.create(model, messages, temperature, max_tokens)
    │     → resp.choices[0].message.content → str
    └── Anthropic: client.messages.create(model, messages, temperature, max_tokens)
          (system 消息独立传入 system 参数)
          → resp.content[0].text → str

provider 切换：
  - 修改 configs/agent_config.yaml 中的 llm.provider 和 llm.model
  - 自动从环境变量读取对应 API Key
  - OpenAI 模式下支持 OPENAI_BASE_URL 自定义端点（中转/代理/本地 LLM）
"""

from __future__ import annotations

import os

import yaml


def load_config(path: str = "configs/agent_config.yaml") -> dict:
    """从 YAML 配置文件加载 LLM 超参数。"""
    with open(path) as f:
        return yaml.safe_load(f)


class LLMClient:
    """统一的 LLM 调用接口。

    延迟导入 SDK（用到时才 import），避免同时依赖 OpenAI 和 Anthropic。
    """

    def __init__(self, provider: str = "openai", model: str = "gpt-4o",
                 temperature: float = 0.2, max_tokens: int = 4096):
        self.provider = provider
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._client = self._build_client()

    def _build_client(self):
        """根据 provider 构建对应的 SDK Client。

        OpenAI: 支持 OPENAI_BASE_URL 自定义端点（如本地 llama.cpp 或中转服务）
        Anthropic: 通过 ANTHROPIC_API_KEY 环境变量认证
        """
        if self.provider == "openai":
            from openai import OpenAI
            return OpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                base_url=os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1",
            )
        elif self.provider == "anthropic":
            from anthropic import Anthropic
            return Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        else:
            raise ValueError(f"不支持的 provider: {self.provider}")

    def invoke(self, messages: list[dict]) -> str:
        """调用 LLM 并返回文本响应。

        Args:
            messages: [{role: "system"|"user"|"assistant", content: str}]

        Returns:
            LLM 响应的文本内容

        Anthropic 特殊处理：
          从 messages 中分离 system 消息，通过独立的 system 参数传入
          （Anthropic API 不支持 messages 中的 system role）。
        """
        if self.provider == "openai":
            resp = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            return resp.choices[0].message.content or ""

        elif self.provider == "anthropic":
            system_msgs = [m for m in messages if m["role"] == "system"]
            other_msgs = [m for m in messages if m["role"] != "system"]

            kwargs = dict(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=other_msgs,
            )
            if system_msgs:
                kwargs["system"] = system_msgs[0]["content"]

            resp = self._client.messages.create(**kwargs)
            return resp.content[0].text if resp.content else ""

    @classmethod
    def from_config(cls, config_path: str = "configs/agent_config.yaml") -> "LLMClient":
        """从 YAML 配置文件中的 llm 段构造 LLMClient。"""
        cfg = load_config(config_path)["llm"]
        return cls(provider=cfg["provider"], model=cfg["model"],
                   temperature=cfg["temperature"], max_tokens=cfg["max_tokens"])
