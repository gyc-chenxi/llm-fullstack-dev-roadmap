"""
Patch 评估指标
================

从 4 个维度评估 Agent 生成的 patch 质量：

  - patch_size + minimality: patch 行数越少越优（遵循最小化修改原则）
      10 行以内=1.0, <20 行=0.8, <50 行=0.5, >=50 行=0.3
  - regression_pass: 完整测试套件是否仍然通过（确保未引入回归）
  - lint_pass: py_compile 语法检查（基本的 Python 语法验证）
  - has_patch: 是否生成了 patch（有时 LLM 可能只输出描述而无代码）

数据流：state.patch + state.test_output → evaluate_patch() → report dict
"""

from __future__ import annotations

import subprocess

from src.state import SWEAgentState


def evaluate_patch(state: SWEAgentState) -> dict:
    """评估当前 patch 的质量。

    Returns:
        {
            patch_size, minimality, regression_pass, lint_pass,
            has_patch, test_output_snippet, ...
        }
    """
    result = {
        "patch_size": len(state.patch.split("\n")) if state.patch else 0,
        "minimality": 0.0,
        "regression_pass": False,
        "lint_pass": False,
        "has_patch": bool(state.patch),
        "test_output_snippet": state.test_output[:300],
    }

    # 最小化评分：patch 大小与评分成反比
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

    # 回归测试：运行完整测试套件
    try:
        r = subprocess.run(
            ["python", "-m", "pytest", state.working_dir, "--tb=short", "-q"],
            capture_output=True, text=True, timeout=120,
        )
        result["regression_pass"] = (r.returncode == 0)
        result["regression_output"] = (r.stdout + r.stderr)[:500]
    except Exception as e:
        result["regression_error"] = str(e)

    # 语法检查：py_compile 验证 Python 语法
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
    """将评估报告格式化为人类可读文本。"""
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
