"""
SAM 2 Vision Lab — 核心包
=========================
基于 Meta SAM 2.1 和 Diffusers 的图像/视频分割工程实验平台。

主要子模块:
  - sam:     SAM 2 预测器封装（loader / image_predictor / auto_mask / video_predictor）
  - mask:    Mask 后处理 / 质量评估 / 可视化 / 几何计算
  - inpaint: SAM2 + Diffusers 图像修复管线
  - api:     FastAPI RESTful 服务（server / routes / schemas）
  - app:     Gradio Web UI
  - utils:   图像 I/O / 清单记录 / 计时器
"""

__version__ = "0.1.0"
