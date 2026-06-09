#!/usr/bin/env python3
"""ReAct Agent Demo — 可直接运行的多工具 Agent

用法：
    export OPENAI_API_KEY=sk-xxx   # 或用 DeepSeek
    python react_agent_demo.py

依赖：pip install openai httpx

这是一个最小但完整可运行的 ReAct Agent。它展示：
- Reasoning + Acting 循环
- 工具注册/调用/结果观察
- 结构化日志输出
- 死循环防护

作者：llm-fullstack-dev-roadmap
"""

import json, os, re, subprocess, time, sys
from typing import Callable
from dataclasses import dataclass, field

# ============================================================
# 配置
# ============================================================
API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
BASE_URL = (
    "https://api.deepseek.com/v1"
    if os.getenv("DEEPSEEK_API_KEY")
    else "https://api.openai.com/v1"
)
MODEL = "deepseek-chat" if os.getenv("DEEPSEEK_API_KEY") else "gpt-4o-mini"
MAX_ITERATIONS = 10


# ============================================================
# 工具定义
# ============================================================
class Tool:
    def __init__(self, name: str, description: str, func: Callable):
        self.name = name
        self.description = description
        self.func = func

    def to_prompt_desc(self) -> str:
        return f"- {self.name}: {self.description}"

    def execute(self, **kwargs) -> str:
        try:
            return str(self.func(**kwargs))
        except Exception as e:
            return f"工具执行出错: {e}"


# --- 真实工具实现 ---
def read_file(path: str) -> str:
    """读取本地文件"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()[:3000]
    except FileNotFoundError:
        return f"文件不存在: {path}"

def search_web(query: str) -> str:
    """模拟网络搜索（不真的联网，返回占位结果）"""
    # 生产环境换成真实搜索 API
    return json.dumps({
        "query": query,
        "results": [
            {"title": f"关于'{query}'的搜索结果", "snippet": f"这是关于{query}的模拟搜索结果..."}
        ]
    }, ensure_ascii=False)

def get_current_time(_: str = "") -> str:
    """获取当前时间"""
    return time.strftime("%Y-%m-%d %H:%M:%S")

def calculate(expression: str) -> str:
    """安全计算数学表达式"""
    allowed = set("0123456789+-*/().% ")
    if not all(c in allowed for c in expression):
        return "错误：表达式中包含不允许的字符"
    try:
        return str(eval(expression))
    except Exception as e:
        return f"计算错误: {e}"

def list_dir(path: str = ".") -> str:
    """列出目录内容"""
    try:
        return "\n".join(os.listdir(path))
    except Exception as e:
        return str(e)


TOOLS = [
    Tool("read_file", "读取文件内容，参数: path=文件路径", read_file),
    Tool("search_web", "搜索互联网信息，参数: query=搜索关键词", search_web),
    Tool("get_current_time", "获取当前日期时间", get_current_time),
    Tool("calculate", "计算数学表达式，参数: expression=表达式(如'3+5*2')", calculate),
    Tool("list_dir", "列出目录内容，参数: path=路径(默认.)", list_dir),
]


# ============================================================
# LLM 调用
# ============================================================
def call_llm(messages: list[dict], stream: bool = False) -> str:
    """调用 OpenAI 兼容 API"""
    import httpx

    if not API_KEY:
        raise RuntimeError("请设置 OPENAI_API_KEY 或 DEEPSEEK_API_KEY 环境变量")

    resp = httpx.post(
        f"{BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json={"model": MODEL, "messages": messages, "temperature": 0, "max_tokens": 1024, "stream": False},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


# ============================================================
# ReAct Agent
# ============================================================
@dataclass
class AgentStep:
    step: int
    thought: str
    action: str | None = None
    observation: str | None = None

@dataclass
class AgentResult:
    answer: str
    steps: list[AgentStep]
    total_tokens: int


def build_system_prompt() -> str:
    tool_desc = "\n".join(t.to_prompt_desc() for t in TOOLS)
    return f"""你是一个 ReAct Agent。你可以使用工具来完成任务。

可用工具：
{tool_desc}

回答格式：
当需要调用工具时：
<thought>你的思考过程</thought>
<tool>工具名</tool>
<params>{{"参数名": "参数值"}}</params>

当任务完成时：
<thought>你的思考过程</thought>
<final_answer>最终答案</final_answer>

规则：
1. 每次只调用一个工具
2. 根据工具返回的结果决定下一步
3. 如果工具出错，尝试换个方式或换个工具
4. 完成任务后立即给出 final_answer"""


def parse_action(response: str) -> dict | None:
    """解析 Agent 响应"""
    # 提取 thought
    thought = re.search(r"<thought>(.*?)</thought>", response, re.DOTALL)
    thought_text = thought.group(1).strip() if thought else ""

    # 提取 final_answer
    final = re.search(r"<final_answer>(.*?)</final_answer>", response, re.DOTALL)
    if final:
        return {"type": "final_answer", "content": final.group(1).strip(), "thought": thought_text}

    # 提取 tool + params
    tool = re.search(r"<tool>(.*?)</tool>", response, re.DOTALL)
    params = re.search(r"<params>(.*?)</params>", response, re.DOTALL)

    if tool and params:
        try:
            parsed_params = json.loads(params.group(1).strip())
        except json.JSONDecodeError:
            parsed_params = {}
        return {"type": "tool_call", "tool": tool.group(1).strip(), "params": parsed_params, "thought": thought_text}

    # 解析失败——当作思考
    return {"type": "unknown", "content": response, "thought": thought_text}


def run_agent(task: str) -> AgentResult:
    """运行 ReAct Agent"""
    if not API_KEY:
        print("❌ 错误：请先设置 API Key")
        print("   export OPENAI_API_KEY=sk-xxx")
        print("   或 export DEEPSEEK_API_KEY=sk-xxx")
        sys.exit(1)

    messages = [
        {"role": "system", "content": build_system_prompt()},
        {"role": "user", "content": task},
    ]

    steps: list[AgentStep] = []

    for i in range(MAX_ITERATIONS):
        # 调用 LLM
        response = call_llm(messages)
        parsed = parse_action(response)

        step = AgentStep(step=i + 1, thought=parsed.get("thought", ""))

        if parsed["type"] == "final_answer":
            step.action = "→ 给出最终答案"
            steps.append(step)
            return AgentResult(answer=parsed["content"], steps=steps, total_tokens=0)

        elif parsed["type"] == "tool_call":
            tool_name = parsed["tool"]
            tool_params = parsed["params"]
            step.action = f"🔧 {tool_name}({json.dumps(tool_params, ensure_ascii=False)})"

            # 查找并执行工具
            tool = next((t for t in TOOLS if t.name == tool_name), None)
            if tool:
                result = tool.execute(**tool_params)
                step.observation = result
            else:
                step.observation = f"未知工具: {tool_name}。可用: {[t.name for t in TOOLS]}"

            steps.append(step)

            # 把结果追加到对话历史
            messages.append({"role": "assistant", "content": response})
            messages.append({"role": "user", "content": f"工具返回：{step.observation}"})

        else:
            step.action = "⚠️ 无法解析的动作"
            step.observation = parsed.get("content", "")
            steps.append(step)
            messages.append({"role": "assistant", "content": response})
            messages.append({"role": "user", "content": "请按格式回复：<thought>...</thought> <tool>...</tool> <params>...</params>"})

    return AgentResult(answer="达到最大迭代次数", steps=steps, total_tokens=0)


# ============================================================
# 演示
# ============================================================
def print_steps(result: AgentResult):
    """格式化输出 Agent 执行过程"""
    print("\n" + "=" * 60)
    print("🤖 ReAct Agent 执行过程")
    print("=" * 60)

    for s in result.steps:
        print(f"\n📍 Step {s.step}")
        print(f"   💭 {s.thought[:200]}")
        if s.action:
            print(f"   {s.action}")
        if s.observation:
            obs = s.observation[:300].replace("\n", "\n   ")
            print(f"   👁️  {obs}")

    print("\n" + "=" * 60)
    print("✅ 最终答案")
    print("=" * 60)
    print(result.answer)
    print(f"\n总步数: {len(result.steps)}")


if __name__ == "__main__":
    TASKS = [
        "现在几点？帮我计算如果现在是下午3点，再过500分钟是几点几分？",
        "读取项目根目录的 README.md 文件，用一句话告诉我这个项目是做什么的",
    ]

    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
    else:
        print("🎯 没有指定任务，使用默认演示任务：")
        for i, t in enumerate(TASKS):
            print(f"  [{i+1}] {t[:80]}")
        print(f"\n用法：python react_agent_demo.py '你的任务描述'")
        print(f"示例：python react_agent_demo.py '现在几点？'\n")
        task = TASKS[0]

    result = run_agent(task)
    print_steps(result)
