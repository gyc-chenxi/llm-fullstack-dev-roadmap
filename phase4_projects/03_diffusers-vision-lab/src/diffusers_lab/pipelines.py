"""
Diffusers Pipeline 工厂
=======================

支持 6 种文生图/图生图任务：
  1. txt2img           — 文本 → 图像（StableDiffusionPipeline）
  2. img2img           — 图像 + 文本 → 新图像（StableDiffusionImg2ImgPipeline）
  3. inpaint           — 图像 + 遮罩 + 文本 → 修复区域（StableDiffusionInpaintPipeline）
  4. controlnet_canny  — Canny 边缘图 + 文本 → 受控生成（StableDiffusionControlNetPipeline）
  5. sdxl_txt2img      — SDXL 文本 → 图像（StableDiffusionXLPipeline）
  6. lora_txt2img      — 文本 → 图像 + LoRA 权重融合

数据流：
  YAML config → build_pipeline(cfg)
    → select_device() / select_dtype()  ← 确定设备和精度
    → from_pretrained() ← 加载模型权重
    → pipe.to(device)   ← 模型移动到目标设备
    → _apply_runtime()  ← 启用显存优化
    → (pipe, device, dtype) 返回给 generate.py

张量流（以 txt2img 为例）：
  prompt → text_encoder → text_embeddings [1, 77, 768]
    ↓
  random noise → UNet (step × 25) → denoised latent [1, 4, 64, 64]
    ↓
  VAE decoder → RGB image [512, 512, 3]
"""

from pathlib import Path
import torch

from diffusers import (
    StableDiffusionPipeline,
    StableDiffusionImg2ImgPipeline,
    StableDiffusionInpaintPipeline,
    StableDiffusionControlNetPipeline,
    StableDiffusionXLPipeline,
    ControlNetModel,
)

from .config import runtime_flag
from .device import select_device, select_dtype


def _common_kwargs(cfg: dict, dtype):
    """
    构造公共 from_pretrained 参数。

    参数：
      cfg: 完整配置字典
      dtype: torch.dtype（float32/float16）

    返回：
      dict — 包含 torch_dtype、local_files_only 等参数

    设计说明：
      safety_checker 在本地实验场景中不需要，关闭可减少
      不必要的计算和模型加载量。生产环境需重新评估。
    """
    kwargs = {
        "torch_dtype": dtype,
        "local_files_only": True,  # 仅从本地加载，不联网下载
    }

    safety_checker = runtime_flag(cfg, "safety_checker", False)
    if not safety_checker:
        kwargs["safety_checker"] = None
        kwargs["requires_safety_checker"] = False

    return kwargs


def _apply_runtime(pipe, cfg: dict):
    """
    应用运行时优化配置。

    显存优化策略（在有限显存上运行大模型的关键技巧）：
    - attention_slicing：将注意力计算切分为多个步骤，
      减少峰值显存占用（时间换空间）
    - vae_slicing：VAE 解码时分 batch 处理，
      避免大分辨率图像解码时显存溢出
    """
    if runtime_flag(cfg, "attention_slicing", True):
        pipe.enable_attention_slicing()

    if runtime_flag(cfg, "vae_slicing", True):
        if hasattr(pipe, "vae") and hasattr(pipe.vae, "enable_slicing"):
            pipe.vae.enable_slicing()
        elif hasattr(pipe, "enable_vae_slicing"):
            pipe.enable_vae_slicing()

    return pipe


def build_pipeline(cfg: dict):
    """
    根据配置构建指定的 Diffusers Pipeline。

    参数：
      cfg: 配置字典（必须包含 task 字段）

    返回：
      (pipe, device, dtype)
      - pipe: diffusers pipeline 实例
      - device: 计算设备名（str）
      - dtype: torch 数据类型

    支持的任务类型（cfg["task"]）：
      txt2img, img2img, inpaint, controlnet_canny, sdxl_txt2img, lora_txt2img
    """
    task = cfg["task"]
    device = select_device(cfg.get("device", "auto"))
    dtype = select_dtype(cfg.get("dtype", "auto"), device)

    print(f"[device] selected={device} dtype={dtype}")

    if task == "txt2img":
        # SD1.5 基础文生图
        # 输入: text prompt
        # 输出: 512×512 RGB 图像
        model_id = cfg["model_id"]
        pipe = StableDiffusionPipeline.from_pretrained(
            model_id,
            **_common_kwargs(cfg, dtype),
        )

    elif task == "img2img":
        # SD1.5 图生图
        # 输入: text prompt + 初始图像
        # 输出: 基于输入图像风格修改后的 512×512 图像
        model_id = cfg["model_id"]
        pipe = StableDiffusionImg2ImgPipeline.from_pretrained(
            model_id,
            **_common_kwargs(cfg, dtype),
        )

    elif task == "inpaint":
        # SD1.5 图像修复
        # 输入: text prompt + 原始图像 + 遮罩（白=修复区域）
        # 输出: 仅遮罩区域被重新生成，其余保持原样
        model_id = cfg["model_id"]
        pipe = StableDiffusionInpaintPipeline.from_pretrained(
            model_id,
            **_common_kwargs(cfg, dtype),
        )

    elif task == "controlnet_canny":
        # ControlNet + Canny 边缘控制生成
        # 输入: text prompt + Canny 边缘图
        # 输出: 严格遵循边缘轮廓的 512×512 图像
        base_model_id = cfg["base_model_id"]
        controlnet_model_id = cfg["controlnet_model_id"]

        controlnet = ControlNetModel.from_pretrained(
            controlnet_model_id,
            torch_dtype=dtype,
            local_files_only=True,
        )

        pipe = StableDiffusionControlNetPipeline.from_pretrained(
            base_model_id,
            controlnet=controlnet,
            **_common_kwargs(cfg, dtype),
        )

    elif task == "sdxl_txt2img":
        # SDXL 高质量文生图
        # 差异：双文本编码器（CLIP-L + OpenCLIP-G）
        # 输入维度: 77×768 + 77×1280
        # 默认输出: 1024×1024（也可配置为 512）
        model_id = cfg["model_id"]
        pipe = StableDiffusionXLPipeline.from_pretrained(
            model_id,
            torch_dtype=dtype,
            local_files_only=True,
        )

    elif task == "lora_txt2img":
        # SD1.5 + LoRA 微调权重融合
        # 加载基础模型 → 加载 LoRA 权重 → fuse_lora() 融合到原始权重
        # LoRA scale 控制影响强度（1.0 = 完全应用）
        model_id = cfg["model_id"]
        pipe = StableDiffusionPipeline.from_pretrained(
            model_id,
            **_common_kwargs(cfg, dtype),
        )

        lora = cfg.get("lora") or {}
        lora_path = Path(lora.get("path", ""))
        weight_name = lora.get("weight_name")
        scale = float(lora.get("scale", 1.0))

        if not lora_path.exists():
            raise FileNotFoundError(f"LoRA path not found: {lora_path}")

        if not weight_name:
            raise ValueError("LoRA weight_name is required")

        weight_file = lora_path / weight_name
        if not weight_file.exists():
            raise FileNotFoundError(f"LoRA weight file not found: {weight_file}")

        pipe.load_lora_weights(str(lora_path), weight_name=weight_name)
        pipe.fuse_lora(lora_scale=scale)

    else:
        raise ValueError(f"Unsupported task: {task}")

    pipe = pipe.to(device)
    pipe = _apply_runtime(pipe, cfg)

    return pipe, device, dtype