# P9: SWE-agent 代码修复 Agent（Day 72-75，4天）

> 核心价值：理解最接近生产力的 Agent 形态——自动修 Bug

---

## 学习目标

- SWE-agent 核心循环：读 Issue → 搜代码 → 打开文件 → 修改 → 跑测试 → 根据反馈重试
- 代码工具设计：search、open_file、edit_file、run_tests、git_diff
- mini-swe-agent 源码阅读（轻量实现，适合学习）
- 评估：resolve rate、patch minimality、regression

## SWE-agent 循环

```
用户提 Issue
    ↓
Agent 搜代码 → 定位文件 → 打开文件 → 理解逻辑
    ↓
生成 patch → 跑测试
    ↓
[测试失败] → 根据错误信息调整 → 重新修改 → 再测试
    ↓
[测试通过] → git diff → 提交 patch
```

## 技术栈

```
mini-swe-agent / docker (沙箱) / pytest
```

## 产出物

- [ ] `code_agent_runbook.md`
- [ ] 至少成功修复 1 个 bug 的完整 trace
- [ ] 失败案例分析（为什么某些 bug 修不了？）

## 参考资料

- SWE-agent: https://github.com/princeton-nlp/SWE-agent
- mini-swe-agent（轻量学习版）
- 项目路线详见 `phase4_projects/PROJECTS_SUMMARY.md`
