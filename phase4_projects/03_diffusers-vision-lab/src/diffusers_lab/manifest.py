"""
生成记录清单（Manifest）管理
============================

为每次生成图像创建一个唯一 run_id，并将完整的生成元数据
以 JSONL 格式追加写入 manifest 文件，供后续比较实验时查阅。

JSONL 格式优势：
  - 每行一条独立的 JSON 记录，可用 grep/jq 直接查询
  - 支持流式追加，无需加锁或维护索引
  - 易于导入 Pandas/Spark 做批量分析

数据流：
  generate_from_config() → new_run_id() + append_manifest()
    → 写入 outputs/manifests/generation_manifest.jsonl
    → 每行格式:
      {"run_id":"txt2img_20240610_143022_seed42_a1b2c3",
       "task":"txt2img","model_id":"models/sd15",...}
"""

from pathlib import Path
import json
import time
import uuid


def new_run_id(task: str, seed: int) -> str:
    """
    生成唯一运行 ID，格式：{task}_{时间戳}_seed{种子}_{6位随机}.

    参数：
      task: 任务类型（如 "txt2img"、"inpaint"）
      seed: 随机种子

    返回：
      str — 唯一运行 ID，用作输出文件名前缀
    """
    ts = time.strftime("%Y%m%d_%H%M%S")
    short = uuid.uuid4().hex[:6]
    return f"{task}_{ts}_seed{seed}_{short}"


def append_manifest(path: str | Path, record: dict) -> None:
    """
    将一次生成记录追加写入 JSONL manifest 文件。

    参数：
      path: manifest 文件路径（不存在则自动创建）
      record: 生成记录字典（含 run_id、task、latency 等）

    写入格式：
      每行一个完整 JSON 对象，末尾换行符分隔
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")