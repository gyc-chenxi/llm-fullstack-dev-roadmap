"""
SWE Agent 核心循环
====================

Think-Act-Observe 循环的完整实现。

数据流（单次迭代）：
  1. LLM.invoke(messages_history) → response
  2. _parse_action(response)
     ├── type="tool_call"  → state.tools[tool_name](state, **args) → result
     │    → messages.append("工具结果: {result}")
     └── type="final_answer" → return state.patch
  3. state.iterations++ → if exhausted: break

系统提示词设计：
  包含可用工具签名、工作目录、迭代上限、输出格式和核心流程指引。
  温度 0.2：代码修复需要低温度确保确定性（避免随机重命名/重构）。

Action 解析格式：
  <tool>tool_name</tool><args>{"param": "value"}</args>
  <final_answer>patch content</final_answer>
  {"tool": "name", "args": {...}}  (JSON 备用格式)
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import yaml
from rich.console import Console
from rich.panel import Panel

from src.llm import LLMClient
from src.state import SWEAgentState
from src.tools import get_available_tools

console = Console()


def _build_system_prompt(state: SWEAgentState, tool_names: list[str]) -> str:
    """构建系统提示词，明确列出工具签名和输出格式。

    关键设计：
      - 明确参数名和类型（如 query: str, path: str），引导 LLM 生成正确 JSON
      - 设定 6 步核心流程：搜索→打开→编辑→测试→读错误→输出 patch
      - 强调最小化修改原则（只改必要的行，不重构风格）
    """
    return f"""你是一个代码修复 Agent。你的任务是根据 Issue 描述修复代码中的 bug。

工作目录: {state.working_dir}
最大迭代次数: {state.max_iterations}

## 可用工具及参数

search_code(query: str) — 用关键词搜索代码，返回匹配文件名和行号
open_file(path: str) — 打开文件查看内容（path 是相对于工作目录的路径）
edit_file(old_text: str, new_text: str) — 修改文件：将 old_text 替换为 new_text（只替换首次匹配）
run_tests(target: str = "") — 运行 pytest，target 可选（文件路径或目录）
git_diff() — 查看当前 git diff
git_apply_patch(patch_content: str) — 将 patch 应用到仓库

## 核心流程
1. 用 search_code(query=...) 在仓库中定位相关的代码文件
2. 用 open_file(path=...) 打开文件理解逻辑上下文
3. 用 edit_file(old_text=..., new_text=...) 做最小修改（只改必要的行）
4. 用 run_tests(target=...) 运行测试验证修改
5. 如果测试失败，读取错误输出 → 分析原因 → 调整修改 → 重试
6. 测试通过后，用 git_diff() 输出最终 patch

## 输出格式
- 调用工具: <tool>tool_name</tool><args>{{"param": "value"}}</args>
- 提交最终答案: <final_answer>patch 内容或分析结论</final_answer>

## 重要原则
- 先理解再修改：不要只改了症状没改病因
- 最小化修改：只改出问题的行，不要重构代码风格
- 每次只做一步：不要一次修改多个文件
- 认真读测试输出：测试失败的堆栈信息里包含了 bug 的精确位置"""


class MiniSWEAgent:
    """轻量级 SWE Agent。

    核心循环：
    while not state.is_exhausted():
        1. LLM 推理 → 2. 解析 Action → 3. 执行工具 / 返回最终答案 → 4. 反馈结果
    """

    def __init__(self, llm: LLMClient | None = None,
                 config_path: str = "configs/agent_config.yaml"):
        self.llm = llm or LLMClient.from_config(config_path)
        self.tools = get_available_tools()
        self.tool_names = list(self.tools.keys())
        with open(config_path) as f:
            self.config = yaml.safe_load(f)

    def run(self, issue: str, repo_path: str) -> str:
        """运行 Agent 主循环。

        Args:
            issue: GitHub Issue 描述文本
            repo_path: 目标 Git 仓库的本地路径

        Returns:
            生成的 git diff patch 字符串，失败时返回空字符串
        """
        max_iter = self.config["agent"]["max_iterations"]
        state = SWEAgentState(
            issue=issue,
            working_dir=str(Path(repo_path).resolve()),
            max_iterations=max_iter,
        )

        system_prompt = _build_system_prompt(state, self.tool_names)

        messages: list[dict] = [
            {"role": "system", "content": system_prompt},
            {"role": "user",
             "content": f"# Issue 描述\n\n{issue}\n\n请修复这个 bug。"},
        ]

        console.print(Panel(
            f"[bold cyan]SWE Agent 启动[/]\nIssue: {issue[:80]}...\n仓库: {repo_path}",
            title="Agent"))

        while not state.is_exhausted():
            state.iterations += 1
            console.print(
                f"[bold yellow]── Iteration {state.iterations}/{state.max_iterations} ──[/]"
            )

            # 1. LLM 推理
            response = self.llm.invoke(messages)
            messages.append({"role": "assistant", "content": response})

            # 2. 解析 action
            action = self._parse_action(response)

            if action["type"] == "final_answer":
                final = action["content"]
                console.print(Panel(final, title="[green]Final Answer[/]"))
                state.patch = final
                return state.patch

            elif action["type"] == "tool_call":
                tool_name = action["tool"]
                tool_args = action["args"]
                console.print(
                    f"  [blue]🔧 {tool_name}[/] 参数: {tool_args}")

                # 3. 执行工具：异常捕获后反馈给 LLM（不作为致命错误）
                if tool_name in self.tools:
                    try:
                        result = self.tools[tool_name](state, **tool_args)
                    except Exception as e:
                        result = f"工具执行异常: {e}"
                else:
                    result = f"未知工具: {tool_name}。可用: {self.tool_names}"

                console.print(
                    f"  [dim]结果 ({len(result)} 字符): {result[:200]}...[/]")
                state.add_to_history(
                    f"{tool_name}({tool_args})", result)

                # 4. 反馈：结果作为 user 消息追加
                messages.append(
                    {"role": "user",
                     "content": f"工具 '{tool_name}' 执行结果:\n{result}"})

            else:
                # LLM 输出了无法解析的文本 → 告知格式并重试
                console.print(f"  [red]⚠ 无法解析 action，重试[/]")
                messages.append(
                    {"role": "user",
                     "content": "请使用 <tool>...</tool><args>...</args> 或 <final_answer>...</final_answer> 格式。"})

        console.print("[red]达到最大迭代次数，修复失败。[/]")
        return state.patch

    def _parse_action(self, response: str) -> dict:
        """解析 LLM 输出，提取 action。

        匹配优先级：
          1. <final_answer>...</final_answer> → 修复完成
          2. <tool>name</tool><args>{JSON}</args> → 工具调用
          3. {"tool": "...", "args": {...}} → JSON 备用格式
          4. 都不匹配 → type="unknown"（触发格式修正提示）
        """
        # 1. final_answer
        final_match = re.search(
            r'<final_answer>(.*?)</final_answer>', response, re.DOTALL)
        if final_match:
            return {"type": "final_answer",
                    "content": final_match.group(1).strip()}

        # 2. tool_call
        tool_match = re.search(
            r'<tool>(.*?)</tool>\s*<args>(.*?)</args>', response, re.DOTALL)
        if tool_match:
            try:
                args = json.loads(tool_match.group(2).strip())
            except json.JSONDecodeError:
                args = {"raw": tool_match.group(2).strip()}
            return {
                "type": "tool_call",
                "tool": tool_match.group(1).strip(),
                "args": args,
            }

        # 3. 纯 JSON 备用格式
        try:
            parsed = json.loads(response.strip())
            if "tool" in parsed:
                return {"type": "tool_call",
                        "tool": parsed["tool"],
                        "args": parsed.get("args", {})}
        except json.JSONDecodeError:
            pass

        return {"type": "unknown", "content": response}


def main():
    """CLI 入口 — python -m src.agent --issue "..." --repo ./sample_repo"""
    import argparse

    parser = argparse.ArgumentParser(
        description="mini-swe-agent: 代码修复 Agent")
    parser.add_argument("--issue", required=True, help="GitHub Issue 描述")
    parser.add_argument("--repo", required=True, help="目标代码仓库路径")
    parser.add_argument("--config", default="configs/agent_config.yaml",
                        help="配置文件路径")
    args = parser.parse_args()

    agent = MiniSWEAgent(config_path=args.config)
    patch = agent.run(issue=args.issue, repo_path=args.repo)

    if patch:
        print("\n" + "=" * 60)
        print("生成的 Patch:")
        print(patch)
    else:
        print("Agent 未能生成修复方案。")


if __name__ == "__main__":
    main()
