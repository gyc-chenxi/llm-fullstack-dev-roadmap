"""
单元测试：运行 ID 生成
======================

测试范围：
  - new_run_id() 的格式正确性
  - 验证生成的 ID 包含 task 名和 seed 信息

测试策略：
  字符串包含断言，确保 ID 对人类可读。
"""

from diffusers_lab.manifest import new_run_id


def test_new_run_id_contains_task_and_seed():
    """
    验证 new_run_id 格式：{task}_{timestamp}_seed{seed}_{random}.
    应同时包含 task 类型 "txt2img" 和 "seed42" 标记。
    """
    rid = new_run_id("txt2img", 42)
    assert "txt2img" in rid
    assert "seed42" in rid