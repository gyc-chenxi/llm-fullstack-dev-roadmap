# 🧪 08 — LLM 调用测试指南

> 🎯 **目标**：学会为 LLM 调用写测试，不花钱反复调 API。
> ⏱️ 预计时间：0.5 天

---

## 📋 为什么 LLM 调用也要写测试？

| 不写测试 | 写测试 |
|---------|--------|
| 改了一行 Prompt，不知道有没有破坏功能 | 跑一遍 Prompt 评估集看分数变化 |
| 每次调试都花真金白银调 API | mock 掉 API，免费测 |
| 重构客户端后不敢上线 | 测试覆盖所有 Provider |
| 面试时说"我会写测试"但没有 LLM 相关例子 | 实实在在的 LLM 测试代码 |

---

## 1️⃣ pytest + pytest-asyncio 基础

```bash
pip install pytest pytest-asyncio httpx
```

```python
# tests/conftest.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app  # FastAPI 应用

@pytest.fixture
async def client():
    """异步测试客户端（走 ASGI transport，不需要启动真实服务器）"""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c
```

---

## 2️⃣ Mock LLM API 响应（用 respx）

```bash
pip install respx  # httpx 专用 mock 工具
```

```python
import respx
import httpx

@respx.mock
async def test_chat_with_mock():
    """Mock 掉 OpenAI API，避免真花钱"""
    # 注册 mock 响应
    mock_route = respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json={
            "id": "chatcmpl-mock-001",
            "object": "chat.completion",
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": "你好！我是 Mock 回复。"},
                "finish_reason": "stop",
            }],
            "usage": {"prompt_tokens": 10, "completion_tokens": 8, "total_tokens": 18},
        })
    )

    client = OpenAIClient(api_key="fake-key", model="gpt-4o-mini")
    response = await client.chat([{"role": "user", "content": "你好"}])

    assert response.content == "你好！我是 Mock 回复。"
    assert response.usage["total_tokens"] == 18
    assert mock_route.called  # 确认真的调了
```

### 📌 Mock 多种响应场景

```python
# 模拟流式响应
async def mock_stream():
    for token in ["你", "好", "！"]:
        yield f'data: {{"choices":[{{"delta":{{"content":"{token}"}}}}]}}\n\n'
    yield "data: [DONE]\n\n"

# 模拟 API 错误
respx.post("https://api.openai.com/v1/chat/completions").mock(
    return_value=httpx.Response(429, json={
        "error": {"message": "Rate limit exceeded", "type": "rate_limit_error"}
    })
)

# 模拟超时
respx.post("https://api.openai.com/v1/chat/completions").mock(
    side_effect=httpx.TimeoutException("Connection timed out")
)
```

---

## 3️⃣ unittest.mock 方式

```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_chat_with_unittest_mock():
    """不需要 respx，直接 mock 客户端方法"""
    with patch.object(OpenAIClient, 'chat', new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = LLMResponse(
            content="Mock 回复",
            model="gpt-4o-mini",
            usage={"total_tokens": 15},
        )

        # 用 mock 客户端测试路由
        response = await client.post("/v1/chat/completions", json={
            "messages": [{"role": "user", "content": "你好"}],
        })

        assert response.status_code == 200
        assert "Mock 回复" in response.json()["choices"][0]["message"]["content"]
```

---

## 4️⃣ Monkey-patch 环境变量

```python
@pytest.mark.asyncio
async def test_with_env_override(monkeypatch):
    """测试时临时修改环境变量"""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-fake-key")
    monkeypatch.setenv("GATEWAY_API_KEY", "test-secret")

    # 这里 Key 已经被替换为测试值
    response = await client.post("/v1/chat/completions", json={
        "messages": [{"role": "user", "content": "hi"}],
    }, headers={"X-API-Key": "test-secret"})

    assert response.status_code != 401  # 鉴权应该通过
```

---

## 5️⃣ 测试类型与边界

| 测试类型 | 测什么 | 是否调真实 API | 工具 |
|----------|--------|--------------|------|
| **单元测试** | 单个函数逻辑（如 TokenCounter.count） | ❌ | pytest |
| **集成测试** | 客户端 + API 交互 | ❌ (mock) | pytest + respx |
| **端到端测试** | 完整请求链路 | ✅ (偶尔) | curl / 手动 |
| **Prompt Eval** | Prompt 效果评估 | ✅ (批量) | Python 脚本 |

### 📌 测试覆盖率目标

```
核心客户端代码: 80%+ 覆盖率
路由处理逻辑: 70%+ 覆盖率
中间件: 60%+ 覆盖率
```

---

## 6️⃣ VCR 模式（vcrpy）：录制+回放

> 💡 VCR = 第一次调真实 API 录下来，之后测试直接播放录像，不花钱。

```bash
pip install vcrpy
```

```python
import vcr

@vcr.use_cassette("tests/cassettes/openai_hello.yaml")
async def test_openai_with_vcr():
    """第一次运行调真实 API 并录制，之后直接回放"""
    client = OpenAIClient(api_key=os.getenv("OPENAI_API_KEY"))
    response = await client.chat([{"role": "user", "content": "你好"}])

    assert len(response.content) > 0
    # 第一次：真调 API（花钱）
    # 第 N 次：播放录像（免费 + 瞬间完成）
```

### 📌 VCR 使用建议

```
✅ 适合：Prompt 评估、集成测试
❌ 不适合：CI/CD 中测试（录像文件可能过时）
⚠️ 注意：vcrpy 录像文件包含真实 API Key！务必 .gitignore cassettes/
```

---

## 7️⃣ 测试 Prompt 评估

```python
import json, asyncio

async def evaluate_prompt(prompt_template: str, test_cases: list[dict]) -> dict:
    """评估一个 Prompt 在测试集上的表现"""
    client = LLMClientFactory.create("openai", api_key="...")
    results = []

    for tc in test_cases:
        prompt = prompt_template.replace("{{query}}", tc["query"])
        try:
            response = await client.chat([{"role": "user", "content": prompt}])
            passed = tc["check"](response.content)  # 自定义检查函数
            results.append({"id": tc["id"], "passed": passed, "response": response.content[:200]})
        except Exception as e:
            results.append({"id": tc["id"], "passed": False, "error": str(e)})

    accuracy = sum(1 for r in results if r["passed"]) / len(results)
    return {"accuracy": accuracy, "total": len(test_cases), "results": results}
```

---

## 🚨 翻车现场

| 现象 | 原因 | 解决 |
|------|------|------|
| mock 不生效 | respx 没加 `@respx.mock` | 函数上加装饰器或在 `with respx.mock:` 中 |
| ASGI transport 不走中间件 | 测试客户端没配 transport | `ASGITransport(app=app)` |
| vcrpy 录像泄露 Key | 录像文件包含 Key | `.gitignore` 加 `tests/cassettes/` |
| monkeypatch 影响其他测试 | 忘了隔离 scope | 用 `pytest fixtures` 的 `autouse=False` |
| CI 里 VCR 测试失败 | 录像文件没 commit | 要么 commit 录像，要么 CI 里跳过 VCR 测试 |

---

## ✅ 产出物 Checklist

- [ ] 用 respx mock OpenAI API，写 1 个单元测试
- [ ] 用 `ASGITransport` 写 1 个 FastAPI 集成测试
- [ ] 用 `monkeypatch` 覆盖环境变量
- [ ] 了解 vcrpy 的基本用法（可选）
- [ ] 跑 `pytest -v`，至少 5 个测试全部通过
