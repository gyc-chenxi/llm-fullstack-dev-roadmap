"""
Agent 状态管理
================

SWEAgentState 是贯穿 Agent 主循环的唯一状态对象，所有工具函数共享
同一个实例。使用 dataclass 简化状态定义和默认值管理。

数据流（状态在各节点间的传递）：
  state.working_dir → search_code/open_file/edit_file (文件系统操作)
  state.current_file → edit_file (确认当前编辑目标)
  state.test_output ← run_tests (测试输出，供评估使用)
  state.patch ← git_diff (diff 文本，供 final_answer 和 evaluate_patch)
  state.iterations → is_exhausted() (循环终止条件)
  state.history ← add_to_history() (工具调用审计日志)
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SWEAgentState:
    """SWE Agent 的核心状态对象。

    使用 dataclass 的 field(default_factory=list) 避免所有实例共享
    同一个可变默认 list（Python 经典陷阱）。
    """

    issue: str
    working_dir: str
    current_file: str = ""          # 当前通过 open_file 打开的文件（相对路径）
    patch: str = ""                 # 最终 git diff 文本
    test_output: str = ""           # 最新 run_tests 的原始输出
    iterations: int = 0             # 已执行的迭代次数
    max_iterations: int = 15        # 最大迭代次数（由配置覆盖）
    history: list[dict] = field(default_factory=list)  # [{iteration, action, result}]

    def is_exhausted(self) -> bool:
        """主循环终止条件：iterations >= max_iterations。"""
        return self.iterations >= self.max_iterations

    def add_to_history(self, action: str, result: str) -> None:
        """记录工具调用到历史，结果截断至 500 字符防止内存膨胀。"""
        self.history.append({
            "iteration": self.iterations,
            "action": action,
            "result": result[:500],
        })
