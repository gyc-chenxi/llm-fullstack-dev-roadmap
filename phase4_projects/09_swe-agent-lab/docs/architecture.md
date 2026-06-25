# mini-swe-agent 架构文档

## 核心循环

```
┌─────────────────────────────────────────────────────────────┐
│                    SWE Agent 主循环                           │
│                                                              │
│  Issue ──→ LLM 推理 ──→ 解析 Action ──→ 执行工具 ──→ 收集结果 │
│                ↑                                      │      │
│                └────────── 继续循环 ──────────────────┘      │
│                                                              │
│  达到 max_iterations 或 LLM 输出 <final_answer> 时终止        │
└─────────────────────────────────────────────────────────────┘
```

## 工具设计哲学

| 工具 | 输入 | 输出 | 设计意图 |
|------|------|------|---------|
| search_code | query: str | 搜索结果文本 | 定位相关代码文件 |
| open_file | path: str | 带行号的文件内容 | 给 LLM 提供代码上下文 |
| edit_file | old_text, new_text | 修改结果 | 精确替换（防 LLM 幻觉） |
| run_tests | target: str | 测试输出 | 验证修改正确性 |
| git_diff | 无 | patch 文本 | 输出最终 diff |

## 状态机

```
SWEAgentState
├── issue: str           ← 不变的输入
├── working_dir: str     ← 目标仓库
├── current_file: str    ← 当前打开的文件（跨工具共享）
├── patch: str           ← 最终的 git diff
├── test_output: str     ← 最新的 pytest 输出
├── iterations: int      ← 计数器
└── history: list[dict]  ← 完整的行动日志
```

## 关键设计决策

1. **edit_file 使用文本替换而非行号替换**
   - 行号易变：LLM 打开文件后，增删改会让行号过时
   - 文本替换更鲁棒：只要 old_text 精确匹配就能工作
   - 代价：LLM 必须精确复制原文片段

2. **工具结果截断到 3000 字符**
   - 防止上下文窗口被测试输出撑爆
   - Agent 应只读取关键堆栈信息

3. **parse_action 支持两种格式**
   - XML 标签格式（精确可解析）
   - JSON 格式（LLM 更容易生成）