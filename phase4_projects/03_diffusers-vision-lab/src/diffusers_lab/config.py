"""
配置加载工具
============

用途：从 YAML 配置文件中读取 pipeline 参数，覆盖顺序：
  1. YAML 文件中的默认值（本函数）
  2. API 请求体中的字段覆盖（见 api.py）

数据流：
  YAML 文件（configs/*.yaml） → load_yaml() → dict[str, Any]
    ↓
  generate_from_config() 逐字段读取用于构建 pipeline 和推理参数

YAML 配置示例结构（sd15_txt2img.yaml）：
  task: txt2img                      ← pipeline 类型（6种可选）
  model_id: models/sd15              ← 本地模型路径
  prompt: "a cat wearing a wizard hat"
  negative_prompt: "blurry, low quality"
  seed: 42                           ← 随机种子（可复现）
  num_inference_steps: 25            ← 推理步数
  guidance_scale: 7.5                ← CFG 引导强度（越高越贴近 prompt）
  width: 512                         ← 输出宽度（像素）
  height: 512                        ← 输出高度（像素）
  device: auto                       ← 设备选择策略
  dtype: float32                     ← 精度（float32/float16）
  runtime:                           ← 运行时优化标志
    attention_slicing: true          ← 切片注意力（节省显存）
    vae_slicing: true                ← VAE 切片（节省显存）
    safety_checker: false            ← 关闭安全过滤器
"""

from pathlib import Path
from typing import Any
import yaml


def load_yaml(path: str | Path) -> dict[str, Any]:
    """
    加载 YAML 配置文件并验证为 dict 类型。

    参数：
      path: YAML 配置文件路径（来自 configs/ 目录）

    返回：
      配置字典，包含 task、model_id、prompt 等字段

    异常：
      FileNotFoundError: 配置文件不存在
      ValueError: YAML 内容不是 mapping 类型
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Config not found: {p}")

    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Config must be a mapping: {p}")

    return data


def runtime_flag(cfg: dict, key: str, default: bool = False) -> bool:
    """
    从配置的 runtime 节读取布尔标志。

    参数：
      cfg: 完整配置字典
      key: 标志名（如 "attention_slicing"、"vae_slicing"）
      default: 默认值

    返回：
      bool — 标志值（不存在时为 default）
    """
    runtime = cfg.get("runtime") or {}
    return bool(runtime.get(key, default))