"""
单元测试：Gateway Pydantic Schema（请求/响应模型）
===================================================

测试范围（不依赖上游或 ASGI 运行时）：
  - ChatMessage：角色类型约束、内容边界
  - ChatCompletionRequest：各字段校验规则、自定义 model_validator、
    to_upstream_payload() 数据转换逻辑
  - HealthResponse：状态枚举和可空字段

数据流（被测试的转换链）：
  客户端 JSON → ChatCompletionRequest (Pydantic 解析+校验)
    → to_upstream_payload(default_model)   ← 重点测试
      → dict（发往上游 llama-server 的完整 payload）

运行： python -m pytest tests/ -v
"""

import pytest
from pydantic import ValidationError

from gateway.schemas import ChatMessage, ChatCompletionRequest, HealthResponse


class TestChatMessage:
    """单条聊天消息模型边界测试。"""

    def test_valid_message(self):
        """标准 user 消息：role + content 正常构造。"""
        m = ChatMessage(role="user", content="hello")
        assert m.role == "user"
        assert m.content == "hello"

    def test_invalid_role(self):
        """
        非法角色值 → ValidationError。
        Role 类型限制为 Literal["system", "user", "assistant", "tool"]，
        非 OpenAI 标准角色（如 "bot"）应被拒绝。
        """
        with pytest.raises(ValidationError):
            ChatMessage(role="invalid_role", content="x")  # type: ignore[arg-type]

    def test_empty_content_allowed(self):
        """
        空 content 合法——对应 tool call 场景中
        assistant 消息可能只有 tool_calls 字段而无文本回复。
        """
        m = ChatMessage(role="assistant", content="")
        assert m.content == ""


class TestChatCompletionRequest:
    """请求体模型校验与数据转换测试。"""

    def test_minimal_valid(self):
        """
        最小合法请求：
        - 仅含必填字段（messages）
        - 验证默认值：model=None（由 default_model 填充）、stream=False、
          temperature=0.2（低温度，确定性强）
        """
        req = ChatCompletionRequest(
            messages=[ChatMessage(role="user", content="hi")],
        )
        assert req.model is None
        assert req.stream is False
        assert req.temperature == 0.2

    def test_no_user_message_rejected(self):
        """
        自定义校验规则：messages 列表必须包含至少一条 user 角色消息。
        纯 system prompt 或纯 assistant 历史的请求应被拒绝。
        """
        with pytest.raises(ValidationError, match="user"):
            ChatCompletionRequest(
                messages=[ChatMessage(role="system", content="system only")],
            )

    def test_empty_messages_rejected(self):
        """空 messages 列表 → Pydantic min_length=1 校验触发拒绝。"""
        with pytest.raises(ValidationError):
            ChatCompletionRequest(messages=[])

    def test_to_upstream_payload_uses_default_model(self):
        """
        model=None 时，to_upstream_payload() 应使用传入的 default_model。
        这是 Gateway 的核心逻辑——未指定模型时走默认模型。
        """
        req = ChatCompletionRequest(
            model=None,
            messages=[ChatMessage(role="user", content="hi")],
        )
        payload = req.to_upstream_payload(default_model="test-model")
        assert payload["model"] == "test-model"

    def test_to_upstream_payload_uses_explicit_model(self):
        """
        显式指定 model 时，应优先于 default_model。
        """
        req = ChatCompletionRequest(
            model="custom-model",
            messages=[ChatMessage(role="user", content="hi")],
        )
        payload = req.to_upstream_payload(default_model="test-model")
        assert payload["model"] == "custom-model"

    def test_extra_body_is_merged(self):
        """
        extra_body 中的字段应合并到 payload 顶层——这是透传上游
        扩展字段（如 grammar 约束、stop 列表）的唯一通道。
        """
        req = ChatCompletionRequest(
            messages=[ChatMessage(role="user", content="hi")],
            extra_body={"grammar": 'root ::= "yes" | "no"'},
        )
        payload = req.to_upstream_payload(default_model="m")
        assert payload["grammar"] == 'root ::= "yes" | "no"'

    def test_temperature_bounds(self):
        """
        temperature 溢出上界（>2.0）→ ValidationError。
        有效范围 [0.0, 2.0]，超出则 Pydantic 的 ge/le 约束触发拒绝。
        """
        with pytest.raises(ValidationError):
            ChatCompletionRequest(
                messages=[ChatMessage(role="user", content="hi")],
                temperature=3.0,
            )

    def test_max_tokens_bounds(self):
        """
        max_tokens 溢出上界（>4096）→ ValidationError。
        Gateway 层设 4096 上限，防止意外设置过长输出打爆显存。
        """
        with pytest.raises(ValidationError):
            ChatCompletionRequest(
                messages=[ChatMessage(role="user", content="hi")],
                max_tokens=99999,
            )


class TestHealthResponse:
    """健康检查响应模型边界测试。"""

    def test_ok(self):
        """正常状态：status="ok" 应正确序列化。"""
        h = HealthResponse(status="ok", upstream="http://x", detail="ready")
        assert h.status == "ok"

    def test_degraded(self):
        """降级状态：status="degraded" 应正确序列化。"""
        h = HealthResponse(status="degraded", upstream="http://x", detail="oops")
        assert h.status == "degraded"

    def test_detail_nullable(self):
        """
        detail 字段可空——当无需额外状态详情时上游可省略该字段。
        验证 Pydantic 默认 None 的正确性。
        """
        h = HealthResponse(status="ok", upstream="http://x")
        assert h.detail is None