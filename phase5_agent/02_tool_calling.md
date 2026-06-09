# 🔧 02 — 工具定义与调用：Tool Registry + 并行执行

> 🎯 **目标**：构建 ToolRegistry 注册中心，实现 5 个真实工具 + OpenAI/Anthropic 格式兼容 + 并行调用。
> ⏱️ 预计时间：2 天

---

## 1️⃣ ToolRegistry 注册中心

```python
import json, asyncio, inspect
from typing import Callable

class Tool:
    def __init__(self, func: Callable, name: str = None, description: str = None):
        self.func = func
        self.name = name or func.__name__
        self.description = description or func.__doc__ or ""
        self._sig = inspect.signature(func)

    def to_openai_spec(self) -> dict:
        """生成 OpenAI Function Calling Schema"""
        props = {}
        for p_name, p in self._sig.parameters.items():
            props[p_name] = {
                'type': 'string',
                'description': f'{p_name} 参数'
            }
        return {
            'type': 'function',
            'function': {
                'name': self.name,
                'description': self.description[:1024],
                'parameters': {
                    'type': 'object',
                    'properties': props,
                    'required': [n for n, p in self._sig.parameters.items() if p.default is inspect.Parameter.empty],
                },
            },
        }

class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, name: str = None, description: str = None):
        """装饰器注册工具"""
        def decorator(func):
            tool = Tool(func, name or func.__name__, description or func.__doc__)
            self._tools[tool.name] = tool
            return func
        return decorator

    def get_specs(self) -> list[dict]:
        return [t.to_openai_spec() for t in self._tools.values()]

    async def execute(self, name: str, **kwargs) -> str:
        tool = self._tools.get(name)
        if not tool:
            return f"未知工具: {name}。可用: {list(self._tools)}"
        try:
            result = tool.func(**kwargs)
            if asyncio.iscoroutine(result):
                result = await result
            return str(result)[:3000]
        except Exception as e:
            return f"工具错误: {e}"

registry = ToolRegistry()

# 注册 5 个真实工具
@registry.register(description="搜索网络信息，返回摘要")
async def search_web(query: str) -> str:
    import httpx
    async with httpx.AsyncClient(timeout=10) as c:
        resp = await c.get('https://html.duckduckgo.com/html/', params={'q': query})
        from bs4 import BeautifulSoup
        results = BeautifulSoup(resp.text, 'html.parser').select('.result__body')[:3]
        return '\n'.join(f"- {r.get_text(strip=True)[:200]}" for r in results) or "无结果"

@registry.register(description="读取本地文件内容")
async def read_file(path: str) -> str:
    with open(path, 'r') as f:
        content = f.read()
    return f"{path} ({len(content)} 字符):\n{content[:2000]}"

@registry.register(description="执行 Python 代码，timeout=10s")
async def execute_python(code: str) -> str:
    import subprocess
    r = subprocess.run(['python3', '-c', code], capture_output=True, text=True, timeout=10)
    return (r.stdout + r.stderr)[:2000] or "(无输出)"

@registry.register(description="查询 SQLite 数据库")
async def query_database(sql: str) -> str:
    import sqlite3
    conn = sqlite3.connect(':memory:')
    cursor = conn.execute(sql)
    rows = cursor.fetchall()[:20]
    cols = [d[0] for d in cursor.description] if cursor.description else []
    conn.close()
    return f"列: {cols}\n" + '\n'.join(str(r) for r in rows) if rows else "(空)"

@registry.register(description="发送 HTTP 请求")
async def send_http_request(method: str, url: str, body: str = "") -> str:
    import httpx
    async with httpx.AsyncClient(timeout=10) as c:
        resp = await c.request(method, url, content=body or None)
        return f"HTTP {resp.status_code}\n{resp.text[:1000]}"
```

---

## 2️⃣ 并行工具调用

```python
async def execute_parallel(tool_calls: list[dict]) -> list[dict]:
    """当 LLM 返回多个 tool_calls 时并发执行"""
    tasks = []
    for tc in tool_calls:
        tasks.append(registry.execute(tc['function']['name'], **json.loads(tc['function']['arguments'])))
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [
        {'tool_call_id': tc['id'], 'name': tc['function']['name'], 'result': str(r)}
        for tc, r in zip(tool_calls, results)
    ]
```

---

## 3️⃣ OpenAI vs Anthropic 工具格式

| 维度 | OpenAI | Anthropic |
|------|--------|-----------|
| 参数名 | `tools` | `tools` |
| Schema | JSON Schema | JSON Schema（略有差异） |
| 返回 | `response.choices[0].message.tool_calls` | `response.content` 中有 `tool_use` 块 |
| 结果回传 | `role: "tool"` message | `tool_result` content block |

```python
# Anthropic 格式转换
def openai_to_anthropic_spec(oa_spec: dict) -> dict:
    return {
        'name': oa_spec['function']['name'],
        'description': oa_spec['function']['description'],
        'input_schema': oa_spec['function']['parameters'],
    }
```

---

## 4️⃣ 工具设计 10 原则

1. **单一职责** — 一个工具只做一件事
2. **描述清晰** — description 决定模型会不会正确调用
3. **参数校验** — 用 Pydantic 自动校验
4. **超时控制** — 任何工具必须在 N 秒内返回
5. **结果截断** — 返回结果限制 3000 字符
6. **错误友好** — 返回结构化错误让 Agent 自我修正
7. **幂等性** — GET 可重试，POST/PUT/DELETE 需确认
8. **沙箱隔离** — 代码执行/文件操作在受限环境
9. **审计日志** — 谁+何时+调了什么+结果
10. **降级策略** — 主工具失败时用备用工具

---

## 🚨 翻车现场

| 现象 | 原因 | 解决 |
|------|------|------|
| 并行调用结果串了 | tool_call_id 没对上 | 严格按 id 匹配结果 |
| 模型一直调错工具 | description 不清晰 | 在 description 里写示例参数 |
| 工具执行死循环 | 工具互相调用 | 禁止工具间相互调用 |

---

## ✅ 产出物 Checklist

- [ ] 实现 ToolRegistry + 5 个真实工具
- [ ] 测试单个工具调用 + 并行多工具调用
- [ ] 对比 OpenAI 和 Anthropic 工具格式
