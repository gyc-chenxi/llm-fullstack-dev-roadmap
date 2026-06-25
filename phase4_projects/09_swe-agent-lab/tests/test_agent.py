"""
Agent 核心循环单元测试
========================

使用 DummyLLM 模拟 LLM 响应，隔离测试 Agent 的 action 解析和主循环逻辑。

测试策略：
  - DummyLLM 按顺序返回预设响应列表，无需真实 API 调用
  - 测试覆盖三种 action 类型：final_answer、tool_call、unknown
  - 测试 Agent 的单步直接完成和多步工具调用流程
"""

import tempfile

from src.agent import MiniSWEAgent


class DummyLLM:
    """模拟 LLM：按顺序返回预设响应，无需真实 API 调用。

    calls 属性记录所有 invoke 的 messages 参数，用于验证 Agent 的对话构建逻辑。
    """

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
    """<final_answer> 标签应被正确解析为 type=final_answer。"""
    agent = MiniSWEAgent.__new__(MiniSWEAgent)
    result = agent._parse_action(
        "<final_answer>这行代码已经修好</final_answer>")
    assert result["type"] == "final_answer"
    assert result["content"] == "这行代码已经修好"


def test_parse_action_tool_call():
    """<tool> + <args> JSON 格式应正确解析工具名和参数。"""
    agent = MiniSWEAgent.__new__(MiniSWEAgent)
    result = agent._parse_action(
        '<tool>search_code</tool><args>{"query": "def calculate"}</args>')
    assert result["type"] == "tool_call"
    assert result["tool"] == "search_code"
    assert result["args"]["query"] == "def calculate"


def test_parse_action_unknown():
    """无格式匹配时应返回 type=unknown（触发 Agent 的格式修正提示）。"""
    agent = MiniSWEAgent.__new__(MiniSWEAgent)
    result = agent._parse_action("一些随机文本")
    assert result["type"] == "unknown"


def test_agent_uses_final_answer():
    """Agent 收到 final_answer 后应直接返回，无需调用任何工具。"""
    llm = DummyLLM(["<final_answer>fixed</final_answer>"])
    agent = MiniSWEAgent(llm=llm)
    with tempfile.TemporaryDirectory() as tmpdir:
        patch = agent.run("fix the bug", tmpdir)
    assert patch == "fixed"


def test_agent_then_final():
    """Agent 先调用工具获得结果，再返回最终答案的完整流程。"""
    llm = DummyLLM([
        '<tool>search_code</tool><args>{"query": "nothing"}</args>',
        '<final_answer>done</final_answer>',
    ])
    agent = MiniSWEAgent(llm=llm)
    with tempfile.TemporaryDirectory() as tmpdir:
        patch = agent.run("find and fix", tmpdir)
    assert patch == "done"
