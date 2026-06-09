# 📊 07 — Agent 评估体系

> 🎯 **目标**：建立 Agent 评估框架，知道任务完成率/工具准确率/步数效率怎么量化。
> ⏱️ 预计时间：1 天

---

## 📋 六大评估维度

| 维度 | 指标 | 计算方式 |
|------|------|---------|
| **任务完成率** | Success Rate | 完成数 / 总任务数 |
| **工具准确率** | Tool Accuracy | 调对工具的步数 / 总工具调用步数 |
| **步数效率** | Step Efficiency | 最优步数 / 实际步数 |
| **Token 效率** | Token/任务 | 平均 Token 消耗 |
| **安全性** | Safety Score | 危险操作被拦截的比例 |
| **鲁棒性** | Recovery Rate | 异常后自恢复的比例 |

---

## 评估脚本框架

```python
test_suite = [
    {"task": "查北京天气，下雨提醒带伞", "expected_tools": ["search_web"], "max_steps": 5},
    {"task": "读取 README.md 并总结", "expected_tools": ["read_file"], "max_steps": 3},
    # ... 20 条测试
]

def evaluate_agent(agent, test_suite):
    results = []
    for tc in test_suite:
        start = time.time()
        result = asyncio.run(agent.run(tc['task']))
        elapsed = time.time() - start
        results.append({
            'task': tc['task'], 'success': tc['check'](result),
            'steps': agent.iteration, 'tokens': agent.total_tokens,
            'latency': elapsed,
        })
    return {
        'success_rate': sum(r['success'] for r in results) / len(results),
        'avg_steps': sum(r['steps'] for r in results) / len(results),
        'avg_tokens': sum(r['tokens'] for r in results) / len(results),
    }
```

---

## 可观测性：LangFuse 接入

```python
import langfuse
langfuse_client = langfuse.Langfuse(public_key="pk-xxx", secret_key="sk-xxx")

trace = langfuse_client.trace(name="agent-run", input={"task": task})
for step in agent_steps:
    trace.span(name=step['tool'] or 'thought', input=step, output=step['observation'])
trace.update(output=final_answer)
```

---

## ✅ 产出物 Checklist

- [ ] 构建 20 条 Agent 测试集
- [ ] 跑评估 + 输出 6 项指标
- [ ] 接入 LangFuse 看 Trace
