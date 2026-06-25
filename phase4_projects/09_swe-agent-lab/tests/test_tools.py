"""
工具函数单元测试
==================

验证 search_code / open_file / edit_file / git_diff 四个核心工具
的正确行为。每个测试使用 tempfile 创建独立的工作仓库。
"""

import os
import tempfile

from src.state import SWEAgentState
from src.tools import edit_file, git_diff, open_file, search_code


def _make_state(tmpdir: str) -> SWEAgentState:
    """创建指向临时目录的最小化测试状态。"""
    return SWEAgentState(issue="test", working_dir=tmpdir)


def test_search_code_finds_match():
    """search_code 应返回包含匹配的文件名和行内容。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "main.py"), "w") as f:
            f.write("def hello():\n    print('world')\n")
        state = _make_state(tmpdir)
        result = search_code(state, "hello")
        assert "main.py" in result
        assert "def hello" in result


def test_search_code_no_match():
    """无匹配时返回友好的提示文本。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        state = _make_state(tmpdir)
        result = search_code(state, "nosuchfunction")
        assert "未找到" in result


def test_open_file():
    """open_file 返回带行号内容，并设置 state.current_file。"""
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
    """不存在的文件返回错误提示。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        state = _make_state(tmpdir)
        result = open_file(state, "nope.py")
        assert "不存在" in result


def test_edit_file():
    """edit_file 将 old_text 替换为 new_text（首次匹配）。"""
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
    """未 open_file 时 edit_file 应拒绝操作。"""
    state = _make_state("/tmp")
    result = edit_file(state, "old", "new")
    assert "没有打开的文件" in result


def test_git_diff_clean_repo():
    """干净仓库无 diff 时返回提示。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.system(
            f"cd {tmpdir} && git init -q "
            f"&& git config user.email t@t.com && git config user.name t")
        with open(os.path.join(tmpdir, "f.py"), "w") as f:
            f.write("v1\n")
        os.system(f"cd {tmpdir} && git add . && git commit -qm 'init'")
        state = _make_state(tmpdir)
        result = git_diff(state)
        assert "没有" in result


def test_git_diff_dirty_repo():
    """有未暂存修改时返回 diff 并更新 state.patch。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.system(
            f"cd {tmpdir} && git init -q "
            f"&& git config user.email t@t.com && git config user.name t")
        with open(os.path.join(tmpdir, "f.py"), "w") as f:
            f.write("v1\n")
        os.system(f"cd {tmpdir} && git add . && git commit -qm 'init'")
        with open(os.path.join(tmpdir, "f.py"), "w") as f:
            f.write("v2\n")
        state = _make_state(tmpdir)
        result = git_diff(state)
        assert "v2" in result
        assert state.patch
