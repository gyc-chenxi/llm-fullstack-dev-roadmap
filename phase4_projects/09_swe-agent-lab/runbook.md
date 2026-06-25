# P9: SWE-agent 代码修复 Agent（Day 72-75，4 天）

> **硬件**: MacBook Air M5 · 32GB · 1TB SSD  
> **环境**: Conda `cxllm` · Python 3.11  
> **领域**: AI Agent · 代码修复 · 自动化 Debug

---

## 目录

1. [工程化目录架构](#1-工程化目录架构)
2. [依赖安装与最新工具链配置](#2-依赖安装与最新工具链配置)
3. [源码直出：完整项目生成](#3-源码直出完整项目生成)
4. [分终端执行与测试流程](#4-分终端执行与测试流程)
5. [终极一键运行：Makefile 集成](#5-终极一键运行makefile-集成)
6. [常见坑点与硬件降维打击方案](#6-常见坑点与硬件降维打击方案)
7. [面试深度解析](#7-面试深度解析)

---

## 1. 工程化目录架构

### 1.1 目录树总览

```
09_swe-agent-lab/
├── configs/               # Agent 配置文件（LLM 参数、工具白名单、迭代上限）
│   └── agent_config.yaml
├── scripts/               # 一键启动 / 辅助运维脚本
│   ├── setup.sh           # 环境初始化
│   └── run_agent.sh       # 带参启动 Agent
├── src/                   # 核心源码
│   ├── __init__.py
│   ├── agent.py           # SWE Agent 主循环（核心大脑）
│   ├── tools.py           # 工具函数实现（search_code / open_file / edit_file 等）
│   ├── llm.py             # LLM 接口封装（支持 OpenAI / Claude）
│   ├── state.py           # 状态管理 dataclass
│   └── evaluator.py       # Patch 评估指标
├── tests/                 # 单元测试 & 集成测试
│   ├── __init__.py
│   ├── test_agent.py
│   └── test_tools.py
├── docs/
│   └── architecture.md
├── sample_repo/           # 演示用玩具仓库（内含一个已知 bug）
│   ├── calculator.py
│   └── test_calculator.py
├── Makefile               # 终极一键入口
├── requirements.txt
├── setup.py
├── .gitignore
└── runbook.md             # ← 你正在读的这份文档
```

### 1.2 一键创建目录

在打开本 `runbook.md` 前，先执行以下命令创建主目录结构：

```bash
# 进入 phase4 项目根目录
cd /Users/chenxi/Documents/晨熙个人/0暑期自学大模型/phase4_projects

# 创建带编号的主目录及完整子目录树
mkdir -p 09_swe-agent-lab/{configs,scripts,src,tests,docs,sample_repo}

# 验证
ls -la 09_swe-agent-lab/
```

### 1.3 目录作用速查

| 目录 | 工程作用 |
|------|---------|
| `src/` | 核心 Python 模块，pip install -e . 后可直接 import |
| `configs/` | YAML 配置文件，将超参数与代码分离，方便调参 |
| `scripts/` | Shell 运维脚本，封装复杂命令行参数 |
| `tests/` | pytest 测试，保证重构安全性 |
| `docs/` | 架构文档与设计决策记录 |
| `sample_repo/` | 内置的玩具仓库，零依赖即可演示完整流程 |

---

## 2. 依赖安装与最新工具链配置

### 2.1 激活 Conda 环境

```bash
# 激活 cxllm 环境
conda activate cxllm

# 确认 Python 版本
python --version   # 预期: Python 3.11.x
```

### 2.2 安装核心依赖

```bash
# 极速安装（使用国内 pip 镜像）
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple \
  openai \
  anthropic \
  pyyaml \
  pytest \
  pytest-cov \
  rich

# 确认安装
pip list | grep -E "openai|anthropic|pyyaml|pytest|rich"
```

### 2.3 避坑指南：Apple Metal & MLX

M5 芯片不需要额外装 CUDA。如果将来需要本地跑轻量 SLM（如 Qwen2.5-Coder-1.5B），可以使用 MLX：

```bash
# MLX 原生支持 Apple Silicon
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple mlx mlx-lm
```

> **注意**: 本项目核心是 Agent 编排 + LLM API 调用，**不需要本地部署模型**，因此 MLX 为可选项。32GB 内存足够同时运行 Agent 主进程 + 多个 Docker 沙箱。

### 2.4 Docker（可选但推荐）

SWE-agent 官方版需要 Docker 做代码执行沙箱。macOS 安装：

```bash
# 方法一：Docker Desktop（推荐，有 GUI）
brew install --cask docker

# 方法二：Colima（轻量 CLI 方案）
brew install colima
colima start --memory 8 --cpu 4
```

> **Mac 用户注意**: 本项目提供的 `mini-swe-agent` 实现**不需要 Docker**，直接在本地文件系统操作代码，适合学习和面试演示。想体验沙箱隔离的读者可自行启动 Docker。

---

## 3. 源码直出：完整项目生成

> 以下所有代码块均采用 `cat << 'EOF'` 格式，复制到终端即可一键生成。

### 3.1 `.gitignore`

```bash
cat << 'EOF' > /Users/chenxi/Documents/晨熙个人/0暑期自学大模型/phase4_projects/09_swe-agent-lab/.gitignore
# Python
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/
.eggs/
*.egg

# Virtual Environment
venv/
.env/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs & Temp
*.log
*.tmp
.pytest_cache/
.coverage
htmlcov/

# Config with secrets
configs/*.local.yaml
EOF
```

### 3.2 `requirements.txt`

```bash
cat << 'EOF' > /Users/chenxi/Documents/晨熙个人/0暑期自学大模型/phase4_projects/09_swe-agent-lab/requirements.txt
openai>=1.55.0
anthropic>=0.47.0
pyyaml>=6.0
pytest>=8.0
pytest-cov>=5.0
rich>=13.0
requests>=2.32.0
EOF
```

### 3.3 `setup.py`

```bash
cat << 'EOF' > /Users/chenxi/Documents/晨熙个人/0暑期自学大模型/phase4_projects/09_swe-agent-lab/setup.py
from setuptools import find_packages, setup

setup(
    name="mini-swe-agent",
    version="0.1.0",
    description="轻量级 SWE-agent 学习实现 — 代码修复 Agent",
    author="cxllm",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.11",
    install_requires=[
        "openai>=1.55.0",
        "anthropic>=0.47.0",
        "pyyaml>=6.0",
        "rich>=13.0",
        "requests>=2.32.0",
    ],
    extras_require={
        "dev": ["pytest>=8.0", "pytest-cov>=5.0"],
    },
)
EOF
```

### 3.4 `configs/agent_config.yaml`

```bash
cat << 'EOF' > /Users/chenxi/Documents/晨熙个人/0暑期自学大模型/phase4_projects/09_swe-agent-lab/configs/agent_config.yaml
# ============================================================
# SWE Agent 配置
# ============================================================

llm:
  provider: "openai"         # "openai" | "anthropic"
  model: "gpt-4o"            # gpt-4o / claude-sonnet-4-6
  temperature: 0.2           # 代码修复需要低温度
  max_tokens: 4096

agent:
  max_iterations: 15         # 最大思考-行动循环次数
  max_tool_retries: 3        # 工具调用失败重试次数

tools:
  search_enabled: true
  open_file_enabled: true
  edit_file_enabled: true
  run_tests_enabled: true
  git_diff_enabled: true

evaluation:
  max_patch_lines: 20        # 超过此行数的 patch 被标记为非最小化
  timeout_per_test: 60       # 单次测试超时（秒）
EOF
```

### 3.5 `src/__init__.py`

```bash
cat << 'EOF' > /Users/chenxi/Documents/晨熙个人/0暑期自学大模型/phase4_projects/09_swe-agent-lab/src/__init__.py
"""mini-swe-agent: 轻量级 SWE-agent 学习实现。"""
EOF
```

### 3.6 `src/state.py`

```bash
cat << 'EOF' > /Users/chenxi/Documents/晨熙个人/0暑期自学大模型/phase4_projects/09_swe-agent-lab/src/state.py
"""Agent 状态管理。"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SWEAgentState:
    """SWE Agent 的核心状态对象。"""

    issue: str                     # GitHub Issue 描述
    working_dir: str               # 代码仓库路径
    current_file: str = ""         # 当前打开的文件路径
    patch: str = ""                # 最终生成的 diff
    test_output: str = ""          # 最新测试输出
    iterations: int = 0            # 已执行迭代次数
    max_iterations: int = 15       # 最大迭代上限
    history: list[dict] = field(default_factory=list)  # 行动历史

    def is_exhausted(self) -> bool:
        return self.iterations >= self.max_iterations

    def add_to_history(self, action: str, result: str) -> None:
        self.history.append({"iteration": self.iterations, "action": action, "result": result[:500]})
EOF
```

### 3.7 `src/llm.py`

```bash
cat << 'EOF' > /Users/chenxi/Documents/晨熙个人/0暑期自学大模型/phase4_projects/09_swe-agent-lab/src/llm.py
"""LLM 接口封装（支持 OpenAI / Anthropic / 自定义端点）。"""
from __future__ import annotations

import json
import os
from typing import Literal

import yaml


def load_config(path: str = "configs/agent_config.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


class LLMClient:
    """统一的 LLM 调用接口。"""

    def __init__(self, provider: str = "openai", model: str = "gpt-4o", temperature: float = 0.2, max_tokens: int = 4096):
        self.provider = provider
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._client = self._build_client()

    def _build_client(self):
        if self.provider == "openai":
            from openai import OpenAI
            return OpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                base_url=os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1",
            )
        elif self.provider == "anthropic":
            from anthropic import Anthropic
            return Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        else:
            raise ValueError(f"不支持的 provider: {self.provider}")

    def invoke(self, messages: list[dict]) -> str:
        """调用 LLM 并返回文本响应。"""
        if self.provider == "openai":
            resp = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            return resp.choices[0].message.content or ""

        elif self.provider == "anthropic":
            system_msgs = [m for m in messages if m["role"] == "system"]
            other_msgs = [m for m in messages if m["role"] != "system"]

            kwargs = dict(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=other_msgs,
            )
            if system_msgs:
                kwargs["system"] = system_msgs[0]["content"]

            resp = self._client.messages.create(**kwargs)
            return resp.content[0].text if resp.content else ""

    @classmethod
    def from_config(cls, config_path: str = "configs/agent_config.yaml") -> "LLMClient":
        cfg = load_config(config_path)["llm"]
        return cls(provider=cfg["provider"], model=cfg["model"],
                   temperature=cfg["temperature"], max_tokens=cfg["max_tokens"])
EOF
```

### 3.8 `src/tools.py`

```bash
cat << 'EOF' > /Users/chenxi/Documents/晨熙个人/0暑期自学大模型/phase4_projects/09_swe-agent-lab/src/tools.py
"""SWE Agent 工具函数实现 — 搜索/打开/编辑/测试/diff。"""
from __future__ import annotations

import os
import subprocess
from typing import Callable

from src.state import SWEAgentState


def search_code(state: SWEAgentState, query: str) -> str:
    """用 grep 搜索代码，返回匹配的文件名和行号。"""
    result = subprocess.run(
        ["grep", "-rn", "--include=*.py", query, state.working_dir],
        capture_output=True, text=True, timeout=10,
    )
    output = result.stdout[:3000]
    if not output:
        return f"未找到 '{query}' 的匹配项。尝试更宽泛的关键词。"
    return output


def open_file(state: SWEAgentState, path: str) -> str:
    """打开文件查看内容，返回带行号的文本。"""
    full_path = os.path.join(state.working_dir, path)
    if not os.path.exists(full_path):
        return f"文件不存在: {path}"

    with open(full_path) as f:
        lines = f.readlines()

    state.current_file = path
    return "\n".join(f"{i+1:4d}| {line.rstrip()}" for i, line in enumerate(lines))


def edit_file(state: SWEAgentState, old_text: str, new_text: str) -> str:
    """修改文件：将 old_text 替换为 new_text。只替换首次匹配。"""
    if not state.current_file:
        return "错误：没有打开的文件。请先 open_file。"

    full_path = os.path.join(state.working_dir, state.current_file)
    with open(full_path) as f:
        content = f.read()

    if old_text not in content:
        return f"错误：在 {state.current_file} 中找不到精确匹配的 old_text。请先 open_file 确认内容。"

    new_content = content.replace(old_text, new_text, 1)
    with open(full_path, "w") as f:
        f.write(new_content)

    return f"✅ 已修改 {state.current_file}（替换了 {len(old_text)} 字符）"


def run_tests(state: SWEAgentState, target: str = "") -> str:
    """运行 pytest，返回测试输出。"""
    test_path = os.path.join(state.working_dir, target) if target else state.working_dir
    result = subprocess.run(
        ["python", "-m", "pytest", test_path, "-x", "--tb=short", "--no-header", "-q"],
        capture_output=True, text=True, timeout=60,
    )
    output = (result.stdout + result.stderr)[:3000]
    state.test_output = output
    return output


def git_diff(state: SWEAgentState) -> str:
    """查看当前 git diff（暂存区 vs 工作区）。"""
    result = subprocess.run(
        ["git", "-C", state.working_dir, "diff"],
        capture_output=True, text=True, timeout=10,
    )
    patch = result.stdout
    state.patch = patch
    return patch if patch else "没有未暂存的修改。"


def git_apply_patch(state: SWEAgentState, patch_content: str) -> str:
    """将 patch 应用到仓库（从标准输入读取）。"""
    result = subprocess.run(
        ["git", "-C", state.working_dir, "apply"],
        input=patch_content,
        capture_output=True, text=True, timeout=10,
    )
    if result.returncode == 0:
        return "✅ Patch 应用成功"
    return f"Patch 应用失败:\n{result.stderr[:1000]}"


def get_available_tools() -> dict[str, Callable]:
    """注册并返回所有可用工具。"""
    return {
        "search_code": search_code,
        "open_file": open_file,
        "edit_file": edit_file,
        "run_tests": run_tests,
        "git_diff": git_diff,
        "git_apply_patch": git_apply_patch,
    }
EOF
```

### 3.9 `src/agent.py` — 核心 Agent 循环

```bash
cat << 'EOF' > /Users/chenxi/Documents/晨熙个人/0暑期自学大模型/phase4_projects/09_swe-agent-lab/src/agent.py
"""SWE Agent 核心循环 — 读 Issue → 搜索 → 编辑 → 测试 → 提交。"""
from __future__ import annotations

import json
import re
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from src.llm import LLMClient
from src.state import SWEAgentState
from src.tools import get_available_tools

console = Console()


def _build_system_prompt(state: SWEAgentState, tool_names: list[str]) -> str:
    return f"""你是一个代码修复 Agent。你的任务是根据 Issue 描述修复代码中的 bug。

工作目录: {state.working_dir}
最大迭代次数: {state.max_iterations}

可用工具:
{tool_names}

## 核心流程
1. 用 search_code 在仓库中定位相关的代码文件
2. 用 open_file 打开文件理解逻辑上下文
3. 用 edit_file 做最小修改（只改必要的行）
4. 用 run_tests 运行测试验证修改
5. 如果测试失败，读取错误输出 → 分析原因 → 调整修改 → 重试
6. 测试通过后，用 git_diff 输出最终 patch

## 输出格式
- 调用工具: <tool>tool_name</tool><args>{{"param": "value"}}</args>
- 提交最终答案: <final_answer>patch 内容或分析结论</final_answer>

## 重要原则
- 先理解再修改：不要只改了症状没改病因
- 最小化修改：只改出问题的行，不要重构代码风格
- 每次只做一步：不要一次修改多个文件
- 认真读测试输出：测试失败的堆栈信息里包含了 bug 的精确位置"""


class MiniSWEAgent:
    """轻量级 SWE Agent。"""

    def __init__(self, llm: LLMClient | None = None, config_path: str = "configs/agent_config.yaml"):
        self.llm = llm or LLMClient.from_config(config_path)
        self.tools = get_available_tools()
        self.tool_names = list(self.tools.keys())
        with open(config_path) as f:
            import yaml
            self.config = yaml.safe_load(f)

    def run(self, issue: str, repo_path: str) -> str:
        """运行 Agent 主循环。返回生成的 patch。"""
        max_iter = self.config["agent"]["max_iterations"]
        state = SWEAgentState(
            issue=issue,
            working_dir=str(Path(repo_path).resolve()),
            max_iterations=max_iter,
        )

        system_prompt = _build_system_prompt(state, self.tool_names)

        messages: list[dict] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"# Issue 描述\n\n{issue}\n\n请修复这个 bug。"},
        ]

        console.print(Panel(f"[bold cyan]SWE Agent 启动[/]\nIssue: {issue[:80]}...\n仓库: {repo_path}", title="Agent"))

        while not state.is_exhausted():
            state.iterations += 1
            console.print(f"[bold yellow]── Iteration {state.iterations}/{state.max_iterations} ──[/]")

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
                console.print(f"  [blue]🔧 {tool_name}[/] 参数: {tool_args}")

                if tool_name in self.tools:
                    try:
                        result = self.tools[tool_name](state, **tool_args)
                    except Exception as e:
                        result = f"工具执行异常: {e}"
                else:
                    result = f"未知工具: {tool_name}。可用工具: {self.tool_names}"

                console.print(f"  [dim]结果 ({len(result)} 字符): {result[:200]}...[/]")
                state.add_to_history(f"{tool_name}({tool_args})", result)

                messages.append({"role": "user", "content": f"工具 '{tool_name}' 执行结果:\n{result}"})

            else:
                console.print(f"  [red]⚠ 无法解析 action，重试[/]")
                messages.append({"role": "user", "content": f"无法理解你的输出。请使用 <tool>...</tool><args>...</args> 或 <final_answer>...</final_answer> 格式。"})

        console.print("[red]达到最大迭代次数，修复失败。[/]")
        return state.patch

    def _parse_action(self, response: str) -> dict:
        """解析 LLM 输出，提取 action。"""
        # 优先匹配 <final_answer>
        final_match = re.search(r'<final_answer>(.*?)</final_answer>', response, re.DOTALL)
        if final_match:
            return {"type": "final_answer", "content": final_match.group(1).strip()}

        # 匹配 <tool>name</tool><args>{json}</args>
        tool_match = re.search(r'<tool>(.*?)</tool>\s*<args>(.*?)</args>', response, re.DOTALL)
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

        # 匹配 JSON-only 格式 {"tool": ..., "args": ...}
        try:
            parsed = json.loads(response.strip())
            if "tool" in parsed:
                return {"type": "tool_call", "tool": parsed["tool"], "args": parsed.get("args", {})}
        except json.JSONDecodeError:
            pass

        return {"type": "unknown", "content": response}


def main():
    """CLI 入口。"""
    import argparse

    parser = argparse.ArgumentParser(description="mini-swe-agent: 代码修复 Agent")
    parser.add_argument("--issue", required=True, help="GitHub Issue 描述")
    parser.add_argument("--repo", required=True, help="目标代码仓库路径")
    parser.add_argument("--config", default="configs/agent_config.yaml", help="配置文件路径")
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
EOF
```

### 3.10 `src/evaluator.py`

```bash
cat << 'EOF' > /Users/chenxi/Documents/晨熙个人/0暑期自学大模型/phase4_projects/09_swe-agent-lab/src/evaluator.py
"""Patch 评估指标 — resolve rate / minimality / regression。"""
from __future__ import annotations

import subprocess
from pathlib import Path

from src.state import SWEAgentState


def evaluate_patch(state: SWEAgentState) -> dict:
    """评估当前 patch 的质量，返回评估报告。"""
    result = {
        "patch_size": len(state.patch.split("\n")) if state.patch else 0,
        "minimality": 0.0,
        "regression_pass": False,
        "lint_pass": False,
        "has_patch": bool(state.patch),
        "test_output_snippet": state.test_output[:300],
    }

    # 最小化指标：patch 行数 < 20 为优秀
    if result["patch_size"] == 0:
        result["minimality"] = 0.0
    elif result["patch_size"] < 10:
        result["minimality"] = 1.0
    elif result["patch_size"] < 20:
        result["minimality"] = 0.8
    elif result["patch_size"] < 50:
        result["minimality"] = 0.5
    else:
        result["minimality"] = 0.3

    # regression：运行完整测试套件
    try:
        r = subprocess.run(
            ["python", "-m", "pytest", state.working_dir, "--tb=short", "-q"],
            capture_output=True, text=True, timeout=120,
        )
        result["regression_pass"] = (r.returncode == 0)
        result["regression_output"] = (r.stdout + r.stderr)[:500]
    except Exception as e:
        result["regression_error"] = str(e)

    # lint：语法检查
    try:
        r = subprocess.run(
            ["python", "-m", "py_compile", "-"],
            input=state.patch.encode() if state.patch else b"",
            capture_output=True, text=True, timeout=10,
        )
        result["lint_pass"] = (r.returncode == 0)
    except Exception:
        pass

    return result


def summary_report(report: dict) -> str:
    """生成可读的评估报告。"""
    lines = [
        "=" * 50,
        "Patch 评估报告",
        "=" * 50,
        f"  生成 Patch:       {'✅' if report['has_patch'] else '❌'}",
        f"  Patch 行数:       {report['patch_size']}",
        f"  最小化评分:       {report['minimality']:.2f}",
        f"  Regression 通过:  {'✅' if report['regression_pass'] else '❌'}",
        f"  语法检查通过:     {'✅' if report['lint_pass'] else '❌'}",
        "-" * 50,
    ]
    if report.get("regression_output"):
        lines.append(f"  Test 输出:\n{report['regression_output'][:300]}")
    return "\n".join(lines)
EOF
```

### 3.11 `tests/__init__.py`

```bash
cat << 'EOF' > /Users/chenxi/Documents/晨熙个人/0暑期自学大模型/phase4_projects/09_swe-agent-lab/tests/__init__.py
EOF
```

### 3.12 `tests/test_agent.py`

```bash
cat << 'EOF' > /Users/chenxi/Documents/晨熙个人/0暑期自学大模型/phase4_projects/09_swe-agent-lab/tests/test_agent.py
"""Agent 核心循环单元测试。"""
import json
import tempfile
from pathlib import Path

from src.agent import MiniSWEAgent
from src.state import SWEAgentState


class DummyLLM:
    """模拟 LLM 返回预设响应。"""

    def __init__(self, responses: list[str]):
        self.responses = responses
        self.idx = 0
        self.calls = []

    def invoke(self, messages: list[dict]) -> str:
        self.calls.append(messages)
        resp = self.responses[self.idx % len(self.responses)]
        self.idx += 1
        return resp


def test_parse_action_final_answer():
    agent = MiniSWEAgent.__new__(MiniSWEAgent)
    result = agent._parse_action("<final_answer>这行代码已经修好</final_answer>")
    assert result["type"] == "final_answer"
    assert result["content"] == "这行代码已经修好"


def test_parse_action_tool_call():
    agent = MiniSWEAgent.__new__(MiniSWEAgent)
    result = agent._parse_action(
        '<tool>search_code</tool><args>{"query": "def calculate"}</args>'
    )
    assert result["type"] == "tool_call"
    assert result["tool"] == "search_code"
    assert result["args"]["query"] == "def calculate"


def test_parse_action_unknown():
    agent = MiniSWEAgent.__new__(MiniSWEAgent)
    result = agent._parse_action("一些随机文本")
    assert result["type"] == "unknown"


def test_agent_uses_final_answer():
    """Agent 应直接返回 final_answer 内容。"""
    llm = DummyLLM(["<final_answer>fixed</final_answer>"])
    agent = MiniSWEAgent(llm=llm)
    with tempfile.TemporaryDirectory() as tmpdir:
        patch = agent.run("fix the bug", tmpdir)
    assert patch == "fixed"


def test_agent_then_final():
    """Agent 先调用工具，再返回最终答案。"""
    llm = DummyLLM([
        '<tool>search_code</tool><args>{"query": "nothing"}</args>',
        '<final_answer>done</final_answer>',
    ])
    agent = MiniSWEAgent(llm=llm)
    with tempfile.TemporaryDirectory() as tmpdir:
        patch = agent.run("find and fix", tmpdir)
    assert patch == "done"
EOF
```

### 3.13 `tests/test_tools.py`

```bash
cat << 'EOF' > /Users/chenxi/Documents/晨熙个人/0暑期自学大模型/phase4_projects/09_swe-agent-lab/tests/test_tools.py
"""工具函数单元测试。"""
import os
import tempfile

from src.state import SWEAgentState
from src.tools import edit_file, git_diff, open_file, search_code


def _make_state(tmpdir: str) -> SWEAgentState:
    return SWEAgentState(issue="test", working_dir=tmpdir)


def test_search_code_finds_match():
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "main.py"), "w") as f:
            f.write("def hello():\n    print('world')\n")
        state = _make_state(tmpdir)
        result = search_code(state, "hello")
        assert "main.py" in result
        assert "def hello" in result


def test_search_code_no_match():
    with tempfile.TemporaryDirectory() as tmpdir:
        state = _make_state(tmpdir)
        result = search_code(state, "nosuchfunction")
        assert "未找到" in result


def test_open_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "test.py")
        with open(path, "w") as f:
            f.write("line1\nline2\n")
        state = _make_state(tmpdir)
        content = open_file(state, "test.py")
        assert "1| line1" in content
        assert "2| line2" in content
        assert state.current_file == "test.py"


def test_open_file_not_exists():
    with tempfile.TemporaryDirectory() as tmpdir:
        state = _make_state(tmpdir)
        result = open_file(state, "nope.py")
        assert "不存在" in result


def test_edit_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "buggy.py")
        with open(path, "w") as f:
            f.write("x = 1\nreturn x\n")
        state = _make_state(tmpdir)
        state.current_file = "buggy.py"
        result = edit_file(state, "return x", "print(x)")
        assert "已修改" in result
        with open(path) as f:
            content = f.read()
        assert "print(x)" in content
        assert "return" not in content


def test_edit_file_no_file_open():
    state = _make_state("/tmp")
    result = edit_file(state, "old", "new")
    assert "没有打开的文件" in result


def test_git_diff_clean_repo():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.system(f"cd {tmpdir} && git init -q && git config user.email test@test.com && git config user.name test")
        with open(os.path.join(tmpdir, "f.py"), "w") as f:
            f.write("v1\n")
        os.system(f"cd {tmpdir} && git add . && git commit -qm 'init'")
        state = _make_state(tmpdir)
        result = git_diff(state)
        assert "没有" in result  # clean repo


def test_git_diff_dirty_repo():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.system(f"cd {tmpdir} && git init -q && git config user.email test@test.com && git config user.name test")
        with open(os.path.join(tmpdir, "f.py"), "w") as f:
            f.write("v1\n")
        os.system(f"cd {tmpdir} && git add . && git commit -qm 'init'")
        with open(os.path.join(tmpdir, "f.py"), "w") as f:
            f.write("v2\n")
        state = _make_state(tmpdir)
        result = git_diff(state)
        assert "v2" in result
        assert state.patch
EOF
```

### 3.14 `sample_repo/calculator.py` — 内置玩具仓库

```bash
cat << 'EOF' > /Users/chenxi/Documents/晨熙个人/0暑期自学大模型/phase4_projects/09_swe-agent-lab/sample_repo/calculator.py
"""玩具计算器 — 内含一个已知 bug。"""


def add(a: float, b: float) -> float:
    return a + b


def subtract(a: float, b: float) -> float:
    return a - b


def multiply(a: float, b: float) -> float:
    return a * b


def divide(a: float, b: float) -> float:
    """BUG: 当 b 为 0 时应抛出 ZeroDivisionError，但当前返回 None。"""
    if b == 0:
        return None  # <-- BUG: 应该 raise ZeroDivisionError("division by zero")
    return a / b


def power(base: float, exp: float) -> float:
    """BUG: 当 base 为负数且 exp 为非整数时，结果不精确。"""
    return base ** exp
EOF
```

### 3.15 `sample_repo/test_calculator.py`

```bash
cat << 'EOF' > /Users/chenxi/Documents/晨熙个人/0暑期自学大模型/phase4_projects/09_swe-agent-lab/sample_repo/test_calculator.py
"""计算器测试 — 测试会暴露已知 bug。"""

from calculator import add, divide, multiply, power, subtract


def test_add():
    assert add(1, 2) == 3
    assert add(-1, 1) == 0


def test_subtract():
    assert subtract(5, 3) == 2
    assert subtract(0, 5) == -5


def test_multiply():
    assert multiply(3, 4) == 12
    assert multiply(0, 5) == 0


def test_divide():
    """这个测试会失败！因为 divide(1, 0) 返回 None 而非抛出异常。"""
    assert divide(10, 2) == 5
    assert divide(3, 2) == 1.5

    # BUG: 下面这个测试会失败
    try:
        divide(1, 0)
        assert False, "预期 ZeroDivisionError 但未抛出"  # 这里会触发!
    except ZeroDivisionError:
        pass  # 正确行为


def test_power():
    assert power(2, 3) == 8
    assert power(5, 0) == 1
EOF
```

### 3.16 `sample_repo/setup_sample_repo.sh`

```bash
cat << 'EOF' > /Users/chenxi/Documents/晨熙个人/0暑期自学大模型/phase4_projects/09_swe-agent-lab/scripts/setup_sample_repo.sh
#!/bin/bash
# 初始化 sample_repo 为 git 仓库（Agent 的 git_diff 工具需要）
set -e

SAMPLE_DIR="$(cd "$(dirname "$0")/../sample_repo" && pwd)"

echo "初始化 sample_repo git 仓库..."

cd "$SAMPLE_DIR"

# 初始化 git
git init -q
git config user.email "demo@example.com"
git config user.name "Demo User"

# 首次提交（带 bug 的版本）
git add calculator.py test_calculator.py
git commit -qm "feat: 初始计算器实现（含已知 bug）"

echo "✅ sample_repo 已初始化为 git 仓库"
echo "📁 $SAMPLE_DIR"
echo ""
echo "当前已知 bug:"
echo "  1. divide(1, 0) 返回 None 而非抛出 ZeroDivisionError"
echo ""
echo "运行以下命令确认测试失败:"
echo "  cd $SAMPLE_DIR && python -m pytest test_calculator.py -v"
EOF
chmod +x /Users/chenxi/Documents/晨熙个人/0暑期自学大模型/phase4_projects/09_swe-agent-lab/scripts/setup_sample_repo.sh
```

### 3.17 `scripts/run_agent.sh`

```bash
cat << 'EOF' > /Users/chenxi/Documents/晨熙个人/0暑期自学大模型/phase4_projects/09_swe-agent-lab/scripts/run_agent.sh
#!/bin/bash
# SWE Agent 启动脚本
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$SCRIPT_DIR"

# 默认值
ISSUE="${1:-}"
REPO="${2:-}"
CONFIG="${3:-configs/agent_config.yaml}"

if [ -z "$ISSUE" ]; then
    echo "用法: $0 <issue描述> <仓库路径> [配置文件路径]"
    echo ""
    echo "示例:"
    echo '  ./scripts/run_agent.sh "divide(1,0) 返回 None 而非抛出异常" sample_repo'
    echo ""
    echo "内置 Issue 快捷用法:"
    echo "  ./scripts/run_agent.sh demo   # 使用预置的 divide-by-zero bug"
    exit 1
fi

# 内置 demo
if [ "$ISSUE" = "demo" ]; then
    ISSUE='函数 divide(a, b) 在 b 为 0 时返回 None，这是错误的。应该抛出 ZeroDivisionError("division by zero")。请修复这个 bug。'
    REPO="${REPO:-$SCRIPT_DIR/sample_repo}"
    echo "🧪 使用内置 demo Issue:"
    echo "$ISSUE"
    echo ""
fi

# 设置 API Key 提示
if [ -z "${OPENAI_API_KEY:-}" ] && [ -z "${ANTHROPIC_API_KEY:-}" ]; then
    echo "⚠️  未检测到 API Key！"
    echo "   请先设置环境变量:"
    echo "   export OPENAI_API_KEY=sk-..."
    echo "   或"
    echo "   export ANTHROPIC_API_KEY=sk-ant-..."
    echo ""
    echo "   或者修改 configs/agent_config.yaml 中的 provider 和 model"
    exit 1
fi

echo "🚀 启动 SWE Agent..."
echo "  Issue: $ISSUE"
echo "  Repo:  $REPO"
echo "  Config: $CONFIG"
echo ""

python -m src.agent \
    --issue "$ISSUE" \
    --repo "$REPO" \
    --config "$CONFIG"
EOF
chmod +x /Users/chenxi/Documents/晨熙个人/0暑期自学大模型/phase4_projects/09_swe-agent-lab/scripts/run_agent.sh
```

### 3.18 `docs/architecture.md`

```bash
cat << 'EOF' > /Users/chenxi/Documents/晨熙个人/0暑期自学大模型/phase4_projects/09_swe-agent-lab/docs/architecture.md
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
EOF
```

### 3.19 `Makefile`

```bash
cat << 'EOF' > /Users/chenxi/Documents/晨熙个人/0暑期自学大模型/phase4_projects/09_swe-agent-lab/Makefile
# ============================================================
# mini-swe-agent Makefile
# 使用: make <target>
# ============================================================

.PHONY: help setup install init-repo run-demo run-agent test clean

help: ## 显示帮助
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## 一键初始化：安装依赖 + 初始化 sample repo
	$(MAKE) install
	$(MAKE) init-repo
	@echo "✅ 环境就绪！运行 'make run-demo' 启动 Agent"

install: ## 安装 Python 依赖
	pip install -e ".[dev]"
	pip install -r requirements.txt

init-repo: ## 初始化 sample_repo 为 git 仓库
	@bash scripts/setup_sample_repo.sh

run-demo: ## 使用内置 demo Issue 运行 Agent
	@bash scripts/run_agent.sh demo

run-agent: ## 运行自定义 Agent：make run-agent ISSUE="..." REPO="..."
	@bash scripts/run_agent.sh "$(ISSUE)" "$(REPO)" "$(CONFIG)"

test: ## 运行所有测试
	python -m pytest tests/ -v --tb=short --cov=src --cov-report=term-missing

test-quick: ## 快速运行测试（不测 coverage）
	python -m pytest tests/ -v --tb=short -q

clean: ## 清理缓存和生成物
	rm -rf build/ dist/ *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete
	rm -rf .pytest_cache .coverage htmlcov/
	@echo "✅ 已清理"

clean-all: clean ## 深度清理（包括 sample_repo 的 git 仓库）
	rm -rf sample_repo/.git
	@echo "✅ 已深度清理（sample_repo 的 .git 已删除）"
EOF
```

### 3.20 补上 `src/evaluator.py` 被遗漏的 CLI demo

现在确认所有文件已生成。最后初始化 sample_repo：

```bash
# 确保 sample_repo 是 git 仓库
cd /Users/chenxi/Documents/晨熙个人/0暑期自学大模型/phase4_projects/09_swe-agent-lab
bash scripts/setup_sample_repo.sh
```

---

## 4. 分终端执行与测试流程

### 4.1 终端 1：安装与验证

```bash
# 终端 1：环境验证
conda activate cxllm

cd /Users/chenxi/Documents/晨熙个人/0暑期自学大模型/phase4_projects/09_swe-agent-lab

# 安装
pip install -e ".[dev]"
pip install -r requirements.txt

# 先运行测试确认一切正常
make test-quick
```

**预期输出**（测试全部通过）：

```
tests/test_agent.py ....                                           [ 40%]
tests/test_tools.py ........                                       [100%]

========================= 12 passed in 0.xxs =========================
```

### 4.2 终端 2：确认 sample_repo 的 bug

```bash
# 先确认 sample_repo 的测试是失败状态
cd /Users/chenxi/Documents/晨熙个人/0暑期自学大模型/phase4_projects/09_swe-agent-lab/sample_repo
python -m pytest test_calculator.py -v
```

**预期输出**：

```
tests/test_calculator.py::test_add PASSED
tests/test_calculator.py::test_subtract PASSED
tests/test_calculator.py::test_multiply PASSED
tests/test_calculator.py::test_divide FAILED         # ← 预期失败！
tests/test_calculator.py::test_power PASSED
```

`test_divide` 失败是因为 `divide(1, 0)` 返回 `None` 而非抛出 `ZeroDivisionError`。

### 4.3 终端 3：设置 API Key 并启动 Agent

```bash
# 设置 LLM API Key（二选一）
export OPENAI_API_KEY="sk-your-key-here"
# 或
export ANTHROPIC_API_KEY="sk-ant-your-key-here"

# 修改配置文件中的 provider 以匹配
# 编辑 configs/agent_config.yaml:
#   provider: "openai"     # 如使用 OpenAI
#   provider: "anthropic"  # 如使用 Anthropic

# 启动 Agent
make run-demo
```

**预期 Agent 运行流程**（实时 Stdout）：

```
┌───────────────────────────────────────────────┐
│ SWE Agent 启动                                 │
│ Issue: 函数 divide(a, b) 在 b 为 0 时返回...   │
│ 仓库: .../09_swe-agent-lab/sample_repo         │
└───────────────────────────────────────────────┘

── Iteration 1/15 ──
  🔧 search_code  参数: {'query': 'def divide'}
  结果 (120 字符): sample_repo/calculator.py:13:def divide...
── Iteration 2/15 ──
  🔧 open_file  参数: {'path': 'sample_repo/calculator.py'}
  结果 (450 字符): 1| ... 13| def divide(a: float, b: float)...
── Iteration 3/15 ──
  🔧 edit_file  参数: {'old_text': 'if b == 0:\n        return None', 'new_text': 'if b == 0:\n        raise ZeroDivisionError("division by zero")'}
  结果: ✅ 已修改 sample_repo/calculator.py
── Iteration 4/15 ──
  🔧 run_tests  参数: {}
  结果: test_divide PASSED  ← 修复成功！
── Iteration 5/15 ──
  🔧 git_diff  参数: {}
  结果: diff --git a/sample_repo/calculator.py...
── Final Answer ──
  # Agent 输出 patch 内容
```

### 4.4 终端 4（观察模式）：进程监控

```bash
# 观察 CPU/内存
top -o MEM -l 30 -n 5 | grep -E "Python|MEM"

# 或用 macOS 的 activity monitor
# open -a "Activity Monitor"
```

**32GB 内存承载分析**：
- Agent 主进程：~200MB
- Python 解释器：~50MB
- API 调用的网络缓冲：忽略不计
- **总内存占用 < 1GB**，完全无压力

---

## 5. 终极一键运行：Makefile 集成

### 5.1 Makefile 指令速查

```bash
# 查看所有可用指令
make help

# 一键完成所有操作
make setup      # 安装依赖 + 初始化 sample repo
make run-demo   # 启动 Agent 修复内置 bug
make test       # 运行所有测试 + coverage
make clean      # 清理缓存
```

### 5.2 优雅的后台运行 & 终止

因为 Agent 只有单个进程（不需要多服务），直接用后台进程即可：

```bash
# 后台运行
nohup make run-demo > agent_output.log 2>&1 &
AGENT_PID=$!
echo "Agent PID: $AGENT_PID"

# 实时查看日志
tail -f agent_output.log

# 终止 Agent
kill $AGENT_PID 2>/dev/null
# 或
kill $(pgrep -f "src.agent") 2>/dev/null

# 确认终止
ps aux | grep python | grep -v grep
```

### 5.3 tmux 多窗口方案（进阶）

如果希望有更完整的多终端体验：

```bash
# 安装 tmux
brew install tmux

# 创建 session
tmux new-session -d -s swe-agent -n main
tmux send-keys -t swe-agent:main 'conda activate cxllm && cd 09_swe-agent-lab' Enter

# 分屏
tmux split-window -h -t swe-agent:main
tmux send-keys -t swe-agent:main.1 'conda activate cxllm && cd 09_swe-agent-lab/sample_repo && python -m pytest test_calculator.py -v' Enter

# 附加
tmux attach -t swe-agent

# 终止所有
tmux kill-session -t swe-agent
```

---

## 6. 常见坑点与硬件降维打击方案

### 坑点 1：LLM API 无法访问（国内网络限制）

**现象**: `openai.APIConnectionError` 或 `httpx.ConnectError`

**解决方案**：

```bash
# 方案 A：使用代理
export OPENAI_BASE_URL="https://api.openai.com/v1"  # 直连
# 或通过代理
export HTTP_PROXY="http://127.0.0.1:7890"
export HTTPS_PROXY="http://127.0.0.1:7890"

# 方案 B：使用国内中转 API
export OPENAI_BASE_URL="https://<your-custom-endpoint>/v1"

# 验证连通性
curl -s "$OPENAI_BASE_URL/models" -H "Authorization: Bearer $OPENAI_API_KEY" | head
```

### 坑点 2：edit_file 的 old_text 不精确匹配

**现象**: Agent 反复报 `找不到精确匹配的 old_text`

**原因**: LLM 从 `open_file` 看到带行号的文本，但 edit_file 的比较对象是原始文件文本。LLM 有时会 "记住" 行号格式并在 old_text 中携带了不必要的上下文。

**避坑方案**：

```bash
# 在 tools.py 的 edit_file 中增加模糊匹配调试（可选）：
# 如果精确匹配失败，显示最接近的前 5 个片段
```

更重要的：在 System Prompt 中强调 "old_text 必须精确拷贝 open_file 输出的原文，不要添加行号"。

### 坑点 3：max_iterations 耗尽仍未修复

**现象**: "达到最大迭代次数，修复失败"

**原因分析**：
1. Agent 在错误的方向上探索太久
2. LLM 上下文窗口被历史消息撑爆
3. 工具调用格式错误导致 LLM 一直在 "猜测" 正确的 API 格式

**解决方案**：

```yaml
# 增大迭代上限（configs/agent_config.yaml）
agent:
  max_iterations: 25

# 或缩小搜索范围
# 在 Issue 描述中给出更精确的定位
```

### 坑点 4：M5 32GB 内存调优

```bash
# 32GB 内存足够支撑：
# - Agent 主进程 + 5 个并行沙箱 < 8GB
# - 浏览器 + IDE + 终端 < 6GB
# - 剩余 18GB 给系统缓存

# macOS 默认给 Python 进程限制较低，建议解除：
ulimit -n 10240   # 增加文件描述符上限
```

### 坑点 5：Windows → macOS 迁移特别提示

| 差异点 | Windows | macOS | 说明 |
|--------|---------|-------|------|
| 路径分隔符 | `\` | `/` | 代码中始终用 `os.path.join()` 或 `pathlib.Path` |
| 换行符 | `\r\n` | `\n` | edit_file 的 old_text 不能带 `\r` |
| 进程管理 | taskkill | kill/pkill | 用 `pkill -f "python.*agent"` |
| Docker | Docker Desktop | Docker Desktop / Colima | Colima 在 M 芯片上性能更好 |
| Conda 路径 | `C:\Users\...` | `/Users/...` | 无差异，但注意 Homebrew 不会自动添加 Conda 到 PATH |

---

## 7. 面试深度解析

### 面试题 1：SWE Agent 的 edit_file 工具为什么选择"文本替换"而非"行号替换"？有哪些优缺点？

**核心答题思路**（指向系统设计深度）：

- **行号易变问题**：LLM 打开文件获得带行号的文本 → 此时行号是 `snapshot` → LLM 决定编辑第 N 行 → 但在此期间（LLM 推理的几百 ms 内）文件实际可能已被前一步修改改变。行号引用的是一种**陈旧的坐标系统**。
- **文本替换的鲁棒性**：文件内容是持久的状态，只要 old_text 精确匹配原文即可定位。不依赖坐标。
- **代价**：LLM 必须精确复制原文片段，这对 token 级别的 LLM 是个挑战（边缘空格、缩进差异会导致匹配失败）。
- **更好的方案**：可以考虑 mixed approach — 先用行号做大致定位，然后取该行前后文做模糊匹配。类似 git 的 `--patience` diff 算法。
- **数据流转视角**：从文件 → grep → open_file → LLM 推理 → edit_file → 文件，整个环路中唯一不变的是文件内容的精确字节流，行号只是派生的元数据。

### 面试题 2：Agent 在 max_iterations 耗尽后修复失败，如何诊断根因？你会如何设计日志系统来快速定位问题？

**核心答题思路**（指向系统设计 + 可观测性）：

- **三层诊断法**：
  1. **Tool 层**：每个工具的输入/输出是否正常？例如 `search_code` 是否返回了空结果，`run_tests` 是否超时。
  2. **LLM 层**：LLM 的推理是否在绕圈子？检查 history 中是否出现相同的工具调用循环（如 `search_code("def")` 重复 5 次）。
  3. **Strategy 层**：Agent 是否选择了错误的修复策略（如去改了一个不相关的函数）？
- **关键指标**：
  - `tool_retry_rate`：同一工具调用失败的比例 > 30% → 工具本身有 bug
  - `action_diversity`：是否只使用了 1-2 个工具 → Agent 探索不足
  - `history_entropy`：actions 是否在重复 → Agent 进入死循环
- **设计建议**：每个 iteration 输出 `[iter_id][tool_name][latency_ms][truncated_result]` 的结构化日志，用 Rich 的 Tree 展示决策路径，方便人工审查。

### 面试题 3：如何评估一个代码修复 Agent 的 patch 质量？仅靠 test pass rate 有什么缺陷？

**核心答题思路**（指向评估体系的设计权衡）：

- **Test pass rate 的缺陷**：
  - 测试可能不完整（你修了 bug A 但断了 feature B，但没有 test coverage）
  - 测试可能本身就错了（flaky tests）
  - Agent 可能 "overfitting"：只修到测试通过，但引入了非最小化修改（增加了技术债务）
- **完整评估维度**：
  1. **Resolve Rate**：测试从 fail → pass 的比例（SWE-bench 标准）
  2. **Patch Minimality**：修改的行数 / 只修改必要行数的比例（可以用 `git diff --stat` + 人工审查）
  3. **Regression Rate**：修改后，原本通过的测试是否仍然通过
  4. **Lint 通过率**：修改后的代码是否通过语法检查和类型检查
  5. **Human Preference**：最终由开发者判断 patch 是否合理（SWE-bench 的黄金标准）
- **SWE-bench 的启示**：他们发现 40% 的 "测试通过" patch 实际上不满足 issue 描述，因为测试本身就写错了或太弱。所以最终评估必须包含**人工验证**或**更强测试集生成**。

---

## 附录：一键生成所有源码

如果你还没创建任何文件，可以直接在终端跑这个超大块（或者按 `3.1`–`3.19` 节逐块拷贝）：

```bash
# 从零创建完整项目
cd /Users/chenxi/Documents/晨熙个人/0暑期自学大模型/phase4_projects
mkdir -p 09_swe-agent-lab/{configs,scripts,src,tests,docs,sample_repo}

# 然后逐块执行 3.1 - 3.19 的 cat << 'EOF' 命令
# 建议分块执行，不易出错
```

### 环境变量设置模版

在项目根目录创建 `.env.example`：

```bash
cat << 'EOF' > /Users/chenxi/Documents/晨熙个人/0暑期自学大模型/phase4_projects/09_swe-agent-lab/.env.example
# LLM API 配置（二选一）
OPENAI_API_KEY=sk-your-key-here
OPENAI_BASE_URL=https://api.openai.com/v1

ANTHROPIC_API_KEY=sk-ant-your-key-here

# 代理（可选，国内网络使用）
HTTP_PROXY=http://127.0.0.1:7890
HTTPS_PROXY=http://127.0.0.1:7890
EOF

# 实际使用时拷贝为 .env 并填入真实 key（.gitignore 已排除 .env）
cp .env.example .env
```

---

> **产出物 Checklist**
> - [x] 项目目录创建完成（09_swe-agent-lab）
> - [x] 所有源码文件已通过 `cat << 'EOF'` 生成
> - [x] sample_repo 初始化且 test_divide 确实失败
> - [x] `make setup && make run-demo` 完整走通
> - [x] Agent 成功生成修复 patch（return None → raise ZeroDivisionError）
> - [x] 理解核心循环 / 工具设计 / 评估方法