"""
SWE Agent 工具函数
====================

6 个核心工具，统一签名为 (state: SWEAgentState, **kwargs) → str。

工具设计原则：
  - 文本替换而非行号替换（edit_file）：行号在多轮编辑间会漂移
  - 结果截断至 ~3000 字符（search_code, run_tests）：防止撑爆 LLM 上下文
  - 先 open_file 再 edit_file：通过 state.current_file 强制文件上下文确认
  - grep 而非 codemodel：简单可靠，无需额外依赖

工具注册：
  get_available_tools() 返回 dict[str, Callable]，Agent 通过名称查找。
"""

from __future__ import annotations

import os
import subprocess
from typing import Callable

from src.state import SWEAgentState


def search_code(state: SWEAgentState, query: str) -> str:
    """用 grep 在仓库中搜索 .py 文件，返回匹配的文件名和行号。

    结果截断至 3000 字符，防止 LLM 上下文溢出。
    无匹配时提示尝试更宽泛的关键词（而非直接放弃）。
    """
    result = subprocess.run(
        ["grep", "-rn", "--include=*.py", query, state.working_dir],
        capture_output=True, text=True, timeout=10,
    )
    output = result.stdout[:3000]
    if not output:
        return f"未找到 '{query}' 的匹配项。尝试更宽泛的关键词。"
    return output


def open_file(state: SWEAgentState, path: str) -> str:
    """打开文件，返回带行号的内容。

    path 是相对于 state.working_dir 的相对路径。
    成功后更新 state.current_file —— 后续 edit_file 基于此值确认操作目标。
    """
    full_path = os.path.join(state.working_dir, path)
    if not os.path.exists(full_path):
        return f"文件不存在: {path}"

    with open(full_path) as f:
        lines = f.readlines()

    state.current_file = path
    return "\n".join(f"{i+1:4d}| {line.rstrip()}" for i, line in enumerate(lines))


def edit_file(state: SWEAgentState, old_text: str, new_text: str) -> str:
    """修改文件：将 old_text 替换为 new_text（只替换首次匹配）。

    约束：
      - 必须先调用 open_file（state.current_file 非空）
      - old_text 必须精确匹配文件内容（逐字符），否则返回错误
      - 使用 str.replace(old, new, 1) 而非行号替换（避免多轮编辑间行号漂移）
    """
    if not state.current_file:
        return "错误：没有打开的文件。请先 open_file。"

    full_path = os.path.join(state.working_dir, state.current_file)
    with open(full_path) as f:
        content = f.read()

    if old_text not in content:
        return (
            f"错误：在 {state.current_file} 中找不到精确匹配的 old_text。"
            f"请先 open_file 确认内容。"
        )

    new_content = content.replace(old_text, new_text, 1)
    with open(full_path, "w") as f:
        f.write(new_content)

    return f"✅ 已修改 {state.current_file}（替换了 {len(old_text)} 字符）"


def run_tests(state: SWEAgentState, target: str = "") -> str:
    """运行 pytest 测试。

    参数：
      target: 可选，指定测试文件或目录；为空则运行整个工作目录
    选项：
      -x: 首次失败即停止（节省 LLM 上下文）
      --tb=short: 简洁回溯格式
      -q: 减少打印输出

    输出截断至 3000 字符，同时写入 state.test_output 供 evaluator 使用。
    """
    test_path = os.path.join(state.working_dir, target) if target else state.working_dir
    result = subprocess.run(
        ["python", "-m", "pytest", test_path, "-x", "--tb=short", "--no-header", "-q"],
        capture_output=True, text=True, timeout=60,
    )
    output = (result.stdout + result.stderr)[:3000]
    state.test_output = output
    return output


def git_diff(state: SWEAgentState) -> str:
    """获取工作区 vs 暂存区的 unified diff。

    结果写入 state.patch（供 final_answer 和 evaluate_patch 使用）。
    无修改时返回提示。
    """
    result = subprocess.run(
        ["git", "-C", state.working_dir, "diff"],
        capture_output=True, text=True, timeout=10,
    )
    patch = result.stdout
    state.patch = patch
    return patch if patch else "没有未暂存的修改。"


def git_apply_patch(state: SWEAgentState, patch_content: str) -> str:
    """通过 stdin 将 patch 文本应用到 git 仓库。"""
    result = subprocess.run(
        ["git", "-C", state.working_dir, "apply"],
        input=patch_content,
        capture_output=True, text=True, timeout=10,
    )
    if result.returncode == 0:
        return "✅ Patch 应用成功"
    return f"Patch 应用失败:\n{result.stderr[:1000]}"


def get_available_tools() -> dict[str, Callable]:
    """注册并返回所有可用工具（key=工具名, value=工具函数）。

    Agent 主循环通过 tool_name in self.tools 查找并调用。
    工具名与系统提示词中的命名保持一致。
    """
    return {
        "search_code": search_code,
        "open_file": open_file,
        "edit_file": edit_file,
        "run_tests": run_tests,
        "git_diff": git_diff,
        "git_apply_patch": git_apply_patch,
    }
