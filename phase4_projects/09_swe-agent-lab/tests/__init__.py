"""Agent 核心循环单元测试。"""
import tempfile

from src.agent import MiniSWEAgent


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
    result = agent._parse_action(
        "<final_answer>这行代码已经修好</final_answer>")
    assert result["type"] == "final_answer"
    assert result["content"] == "这行代码已经修好"


def test_parse_action_tool_call():
    agent = MiniSWEAgent.__new__(MiniSWEAgent)
    result = agent._parse_action(
        '<tool>search_code</tool><args>{"query": "def calculate"}</args>')
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