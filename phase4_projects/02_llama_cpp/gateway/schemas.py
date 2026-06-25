"""
Pydantic 请求/响应模型
---------------------
定义 Gateway 的 API 契约。与 OpenAI Chat Completions API 兼容，
使 LangChain、OpenAI SDK 等工具可以直接将 Gateway 当作 base_url。

数据流向：
  客户端 JSON → ChatCompletionRequest (Pydantic 校验)
    → to_upstream_payload()          ← 重组为上游 llama-server 接受的格式
      ├── model         ← 未指定时使用 default_model 填充
      ├── messages      ← 透传
      ├── temperature   ← 默认 0.2（企业场景优先确定性）
      ├── top_p         ← 默认 0.9
      ├── max_tokens    ← 默认 512
      ├── stream        ← 根据端点选择
      └── extra_body    ← 合并到 payload 顶层（透传上游支持的扩展字段）
"""

from typing import Literal, Any
from pydantic import BaseModel, Field, model_validator

# 角色类型字面量（OpenAI 标准）
Role = Literal["system", "user", "assistant", "tool"]


class ChatMessage(BaseModel):
    """单条聊天消息"""
    role: Role
    content: str


class ChatCompletionRequest(BaseModel):
    """
    OpenAI Chat Completions 的最小兼容子集。
    不追求一次性覆盖全部字段，先保证最常用 serving 链路稳定。
    后续可逐步扩展 frequency_penalty、stop、logprobs 等。
    """

    model: str | None = None                          # 未指定则用 settings.default_model
    messages: list[ChatMessage] = Field(min_length=1)  # 至少 1 条消息

    # 采样参数（默认值偏保守，适合结构化输出场景）
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)  # 0.2 低温度 → 确定性强
    top_p: float = Field(default=0.9, ge=0.0, le=1.0)        # 核采样，保留 90% 概率质量
    max_tokens: int = Field(default=512, ge=1, le=4096)       # 单次回复上限
    stream: bool = False  # 是否启用 SSE 流式

    # 额外字段透传（如 grammar、stop、frequency_penalty 等上游支持但本 schema 未建模的字段）
    extra_body: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_messages(self):
        """
        校验规则：messages 列表中至少要有一条 user 消息。
        防止开发者误传纯 system prompt 导致模型无输入。
        """
        if not any(m.role == "user" for m in self.messages):
            raise ValueError("messages 至少需要包含一条 user 消息")
        return self

    def to_upstream_payload(self, default_model: str) -> dict[str, Any]:
        """
        将 Gateway 层的请求体转换为发往上游 llama-server 的 payload。

        参数：
          default_model: 当 self.model 为 None 时使用的默认模型名

        返回：
          与上游 llama-server API 兼容的 dict
        """
        # 构造上游 payload 基础结构
        # 输出格式：{"model": str, "messages": list[{"role": str, "content": str}],
        #            "temperature": float, "top_p": float, "max_tokens": int, "stream": bool}
        payload = {
            "model": self.model or default_model,
            "messages": [m.model_dump() for m in self.messages],
            "temperature": self.temperature,    # 控制输出随机性，0.0=确定，1.0=平衡，2.0=高随机
            "top_p": self.top_p,                # 核采样阈值，top_p=0.9 保留概率质量最高的 90%
            "max_tokens": self.max_tokens,      # 单次回复最大 token 数，防止无限生成耗尽资源
            "stream": self.stream,              # SSE 流式开关，true 时逐 token 返回
        }
        # extra_body 中的字段合并到 payload 顶层（如 grammar 约束等）
        payload.update(self.extra_body)
        return payload


class HealthResponse(BaseModel):
    """健康检查响应（/healthz, /readyz）"""
    status: Literal["ok", "degraded"]   # degraded 表示上游不可用但 Gateway 自身正常
    upstream: str                        # 上游 llama-server 的地址
    detail: str | None = None             # 附加状态详情