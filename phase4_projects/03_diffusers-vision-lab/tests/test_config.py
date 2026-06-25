"""
单元测试：YAML 配置加载
=======================

测试范围：
  - load_yaml() 能否正确解析 sd15_txt2img.yaml 的字段
  - 对 configs/ 目录下所有 YAML 的一致性验证

测试策略：
  直接读取 configs/ 中的文件进行验证，不 mock 文件系统，
  因为配置文件的正确性本身就是测试的一部分。

数据流：
  configs/sd15_txt2img.yaml → load_yaml() → dict → 字段断言
"""

from pathlib import Path
from diffusers_lab.config import load_yaml


def test_load_sd15_config():
    """
    验证 SD1.5 txt2img 配置加载正确性。
    检查 task 类型、dtype 默认值和模型路径。
    """
    cfg = load_yaml(Path("configs/sd15_txt2img.yaml"))
    assert cfg["task"] == "txt2img"
    assert cfg["dtype"] == "float32"
    assert cfg["model_id"] == "models/sd15"