"""
通用工具函数
============

提供图像处理的辅助功能：
  - ensure_dir: 自动创建目录
  - load_rgb: 加载 RGB 图像并可选缩放
  - load_mask: 加载灰度遮罩图像并可选缩放
  - image_stats: 在保存前快速检查图像是否异常（全黑、过曝等）

数据流：
  图像文件路径 → load_rgb() / load_mask()
    → PIL.Image (RGB/L mode, 缩放至指定尺寸)
    → pipe(**kwargs) 作为输入
"""

from pathlib import Path
from PIL import Image
import numpy as np


def ensure_dir(path: str | Path) -> Path:
    """
    确保目录存在，不存在则创建。

    参数：
      path: 目录路径

    返回：
      Path — 规范化后的目录路径
    """
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def load_rgb(path: str | Path, size: tuple[int, int] | None = None) -> Image.Image:
    """
    加载 RGB 图像，可选缩放到目标尺寸。

    参数：
      path: 图像文件路径
      size: (width, height) — 缩放目标尺寸（可选）

    返回：
      PIL.Image — RGB 模式图像
    """
    img = Image.open(path).convert("RGB")
    if size is not None:
        img = img.resize(size)
    return img


def load_mask(path: str | Path, size: tuple[int, int] | None = None) -> Image.Image:
    """
    加载灰度遮罩图像，可选缩放到目标尺寸。

    遮罩约定（与 Diffusers Inpaint 一致）：
      - 白色 (255) = 需要修复/重绘的区域
      - 黑色 (0) = 保留原始像素的区域

    参数：
      path: 遮罩文件路径
      size: (width, height) — 缩放目标尺寸（可选）

    返回：
      PIL.Image — 灰度 (L) 模式遮罩图像
    """
    img = Image.open(path).convert("L")
    if size is not None:
        img = img.resize(size)
    return img


def image_stats(image: Image.Image) -> dict:
    """
    计算图像基本统计量，用于快速质量检查。

    参数：
      image: PIL.Image 对象

    返回：
      {min, max, mean, black_image}
      black_image=True 提示输出全黑，可能是有问题的生成结果

    典型值（正常图像）：
      min=0, max=255, mean≈117~128, black_image=False
    """
    arr = np.array(image.convert("RGB"))
    return {
        "min": int(arr.min()),
        "max": int(arr.max()),
        "mean": round(float(arr.mean()), 3),
        "black_image": bool(arr.max() == 0),  # 全黑 → 生成失败
    }