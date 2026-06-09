# 🚀 04 — Agent 服务化 API

> 🎯 **目标**：将 Agent 封装为生产级 API，含任务队列、持久化、SSE 实时推送、安全沙箱。
> ⏱️ 预计时间：2 天

---

## 📋 系统架构

```mermaid
graph TB
    subgraph "🎨 前端"
        A[Vue3 Dashboard<br/>Agent 执行过程可视化]
    end
    subgraph "⚡ API Gateway"
        B[POST /v1/agent/run<br/>提交任务]
        C[GET /v1/agent/tasks/{id}<br/>查询状态]
        D[GET /v1/agent/tasks/{id}/events<br/>SSE 事件流]
    end
    subgraph "🔧 后台"
        E[Redis Queue<br/>任务队列]
        F[Agent Worker<br/>异步执行]
        G[LLM + Tools<br/>Agent 运行时]
    end
    subgraph "🗄️ 存储"
        H[(PostgreSQL<br/>任务状态)]
        I[(Redis<br/>事件缓存)]
    end

    A -.->|SSE| D
    B --> E --> F --> G
    F --> H
    F --> I
```

---

## 1️⃣ 任务状态流转

```
PENDING → QUEUED → RUNNING → SUCCESS
                          ↘ FAILED → RETRYING → RUNNING
                          ↘ CANCELLED
```

---

## 2️⃣ 完整 FastAPI 实现

```python
# app/main.py
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uuid, json, asyncio, time
from enum import Enum

app = FastAPI(title="🤖 Agent API", version="3.0.0")

class TaskStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"

class AgentRunRequest(BaseModel):
    task: str
    tools: list[str] = ["search_web", "read_file", "execute_python"]
    max_iterations: int = 10
    max_tokens: int = 4096

class AgentTask:
    def __init__(self, task_id: str, req: AgentRunRequest):
        self.task_id = task_id
        self.task = req.task
        self.tools = req.tools
        self.max_iterations = req.max_iterations
        self.status = TaskStatus.PENDING
        self.result = None
        self.error = None
        self.created_at = time.time()
        self.finished_at = None
        self.steps: list[dict] = []       # Agent 执行步骤
        self.total_tokens = 0
        self.events = asyncio.Queue()     # SSE 事件队列

# 生产环境用 Redis + PostgreSQL，演示用内存
tasks: dict[str, AgentTask] = {}

async def _execute_agent(task: AgentTask):
    task.status = TaskStatus.RUNNING
    await task.events.put({
        "type": "agent_start",
        "task_id": task.task_id,
        "message": f"开始执行: {task.task}"
    })
    
    try:
        agent = ReactAgent(llm_client, tools_registry.get_tools(task.tools))
        
        async for event in agent.astream_events(task.task, max_iterations=task.max_iterations):
            task.events.put_nowait(event)
            
            if event["type"] == "tool_call_end":
                task.steps.append(event)
            elif event["type"] == "thought":
                task.steps.append(event)
        
        task.status = TaskStatus.SUCCESS
        task.finished_at = time.time()
        await task.events.put({
            "type": "task_complete",
            "result": task.result,
            "steps": len(task.steps),
            "latency_sec": task.finished_at - task.created_at,
        })
    
    except asyncio.CancelledError:
        task.status = TaskStatus.CANCELLED
        await task.events.put({"type": "task_cancelled", "message": "任务被取消"})
    
    except Exception as e:
        task.status = TaskStatus.FAILED
        task.error = str(e)
        await task.events.put({"type": "task_failed", "error": str(e)})

@app.post("/v1/agent/run", response_model=dict)
async def submit_task(req: AgentRunRequest):
    task_id = uuid.uuid4().hex[:12]
    task = AgentTask(task_id, req)
    tasks[task_id] = task
    
    # 异步执行
    asyncio.create_task(_execute_agent(task))
    
    return {"task_id": task_id, "status": task.status.value}

@app.get("/v1/agent/tasks/{task_id}")
async def get_task(task_id: str):
    t = tasks.get(task_id)
    if not t: raise HTTPException(404, "任务不存在")
    return {
        "task_id": t.task_id,
        "status": t.status.value,
        "task": t.task,
        "steps": len(t.steps),
        "total_tokens": t.total_tokens,
        "result": t.result,
        "error": t.error,
        "created_at": t.created_at,
        "finished_at": t.finished_at,
    }

@app.get("/v1/agent/tasks/{task_id}/events")
async def stream_events(task_id: str):
    t = tasks.get(task_id)
    if not t: raise HTTPException(404, "任务不存在")
    
    async def event_generator():
        while True:
            event = await t.events.get()
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            if event["type"] in ("task_complete", "task_failed", "task_cancelled"):
                break
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

@app.delete("/v1/agent/tasks/{task_id}")
async def cancel_task(task_id: str):
    t = tasks.get(task_id)
    if not t: raise HTTPException(404)
    t.status = TaskStatus.CANCELLED
    return {"task_id": task_id, "status": "cancelled"}
```

---

## 3️⃣ 生产级任务队列（Redis + ARQ）

```python
# worker.py — 用 ARQ 替代 asyncio.create_task
from arq import create_pool
from arq.connections import RedisSettings

async def execute_agent_task(ctx, task_id: str, task_input: str, tools: list[str]):
    """ARQ Worker 函数"""
    agent = ReactAgent(llm_client, tools_registry.get_tools(tools))
    result = await agent.run(task_input)
    # 结果存入 PostgreSQL
    await db.save_result(task_id, result)
    return result

# 启动 Worker
# arq worker.WorkerSettings --queue agent_tasks

# 提交任务
redis = await create_pool(RedisSettings())
job = await redis.enqueue_job('execute_agent_task', task_id, task_input, tools)
```

---

## 4️⃣ SSE 事件类型详解

| 事件类型 | 触发时机 | 前端展示 | 携带数据 |
|:--------|:--------|:--------|:--------|
| `agent_start` | 任务开始执行 | "Agent 开始思考..." | task_id, message |
| `thought` | Agent 输出思考 | 灰色引用块 | thought 文本 |
| `tool_call_start` | 开始调用工具 | 🔧 工具名+参数卡片 | tool_name, params |
| `tool_call_end` | 工具返回 | 结果折叠区 | tool_name, result, latency |
| `answer_token` | 流式输出 token | token 逐字渲染 | token |
| `task_complete` | 成功完成 | ✅ 最终答案 | result, steps, latency |
| `task_failed` | 失败 | ❌ 错误信息 | error |
| `task_cancelled` | 被取消 | ⚠️ 已取消 | message |

---

## 5️⃣ Agent 安全沙箱

```python
import subprocess, tempfile, os

class SafeExecutor:
    """Agent 工具执行沙箱"""
    ALLOWED_PATHS = ["/tmp/agent_workspace/", "./data/"]
    BLOCKED_IMPORTS = {"os", "subprocess", "shutil", "socket", "ctypes"}
    
    @staticmethod
    def execute_python(code: str, timeout: int = 10) -> str:
        """在隔离环境中执行 Python 代码"""
        # 检查危险导入
        for blocked in SafeExecutor.BLOCKED_IMPORTS:
            if f"import {blocked}" in code or f"from {blocked}" in code:
                return f"❌ 禁止导入模块: {blocked}"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            try:
                r = subprocess.run(
                    ["python3", "-c", code],
                    capture_output=True, text=True, timeout=timeout,
                    env={"PATH": os.environ.get("PATH", ""), "HOME": tmpdir},
                )
                return (r.stdout + r.stderr)[:2000]
            except subprocess.TimeoutExpired:
                return "⏰ 代码执行超时"
    
    @staticmethod
    def read_file(path: str) -> str:
        """路径白名单校验"""
        abs_path = os.path.abspath(path)
        allowed = any(
            abs_path.startswith(os.path.abspath(p)) 
            for p in SafeExecutor.ALLOWED_PATHS
        )
        if not allowed:
            return f"❌ 权限拒绝: 不允许读取 {path}"
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()[:3000]
        except FileNotFoundError:
            return f"❌ 文件不存在: {path}"
```

---

## 🚨 翻车现场

| 现象 | 原因 | 解决 |
|:-----|:-----|:-----|
| SSE 事件漏收 | asyncio.Queue 满了 | 设 `maxsize=100` + 丢弃旧事件 |
| 任务状态丢失 | `tasks: dict = {}` 重启就丢 | 用 PostgreSQL 持久化 |
| 并发任务互相阻塞 | 单 Worker | 部署多 Worker + Redis Queue |
| 工具调用超时 | 外部 API 响应慢 | 设 timeout + 重试 + 降级 |

---

## ✅ 产出物 Checklist

- [ ] FastAPI Agent API 跑通（提交→轮询→SSE）
- [ ] 支持任务取消
- [ ] 配置工具白名单 + 沙箱执行
- [ ] 审计日志记录每次工具调用
- [ ] （可选）Redis + PostgreSQL 持久化
