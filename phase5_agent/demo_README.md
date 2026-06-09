# 🤖 Phase 5 可运行 Agent Demo

## 运行方式

```bash
# 1. 安装依赖
pip install openai httpx

# 2. 设置 API Key
export DEEPSEEK_API_KEY=sk-xxx   # 推荐（便宜）
# 或
export OPENAI_API_KEY=sk-xxx

# 3. 运行
cd phase5_agent
python react_agent_demo.py "现在几点？帮我计算再过500分钟是几点几分？"

# 或使用默认演示任务
python react_agent_demo.py
```

## 预期输出

```
============================================================
🤖 ReAct Agent 执行过程
============================================================

📍 Step 1
   💭 我需要先获取当前时间
   🔧 get_current_time({})
   👁️  2026-06-09 15:30:00

📍 Step 2
   💭 现在知道当前时间是 15:30。需要计算 500 分钟后
   🔧 calculate({"expression": "500 // 60"})
   👁️  8

📍 Step 3
   💭 500分钟 = 8小时20分钟。15:30 + 8:20 = 23:50
   → 给出最终答案

============================================================
✅ 最终答案
============================================================
现在是 2026-06-09 15:30:00。再过 500 分钟是 2026-06-09 23:50。
```

## 文件说明

| 文件 | 类型 | 说明 |
|:-----|:---:|:-----|
| `react_agent_demo.py` | 🐍 可运行 | ReAct Agent 完整实现 |
| `01_react_agent.md` | 📝 教程 | ReAct 原理+代码逐行解释 |
| `02_tool_calling.md` | 📝 教程 | 工具定义/注册/并行调用 |
| `03_langgraph_agent.md` | 📝 教程 | LangGraph 多节点 Agent |

## 扩展方向

- 添加真实搜索工具（SerpAPI / DuckDuckGo）
- 添加 SQL 查询工具
- 用 LangGraph 重写为多节点状态机
