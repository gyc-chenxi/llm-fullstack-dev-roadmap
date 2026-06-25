"""
mini-swe-agent — 轻量级 SWE Agent 学习实现
============================================

核心架构：
  Issue 描述 → Agent 主循环（Think-Act-Observe）→ 代码 Patch
    │                │
    │  ┌─────────────┼─────────────┐
    │  │  LLM 推理  │  工具执行    │
    │  │  (GPT-4o/  │  (search/   │
    │  │   Claude)  │   edit/test)│
    │  └─────────────┴─────────────┘
    │                │
    ▼                ▼
  evaluate_patch ← git_diff(patch)
    ├── patch_size + minimality (最小化评分)
    ├── regression_pass (原有测试仍然通过)
    └── lint_pass (语法检查)

6 个工具函数：
  search_code → grep 搜索代码
  open_file  → 打开文件查看内容
  edit_file  → 文本替换修改文件
  run_tests  → 运行 pytest
  git_diff   → 查看 diff
  git_apply_patch → 应用 patch

数据流：
  SWE Agent = LLMClient + ToolRegistry + SWEAgentState
  Messages history = [system_prompt, issue, tool_results, ...]
  Loop: LLM → parse(tool|final) → execute → feedback → LLM → ...
"""
