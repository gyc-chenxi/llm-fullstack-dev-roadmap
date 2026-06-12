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
    kwargs = {
        "torch_dtype": dtype,
        "local_files_only": True,
    }

    safety_checker = runtime_flag(cfg, "safety_checker", False)
    if not safety_checker:
        kwargs["safety_checker"] = None
        kwargs["requires_safety_checker"] = False

    return kwargs

def _apply_runtime(pipe, cfg: dict):
    if runtime_flag(cfg, "attention_slicing", True):
        pipe.enable_attention_slicing()

    if runtime_flag(cfg, "vae_slicing", True):
        if hasattr(pipe, "vae") and hasattr(pipe.vae, "enable_slicing"):
            pipe.vae.enable_slicing()
        elif hasattr(pipe, "enable_vae_slicing"):
            pipe.enable_vae_slicing()

    return pipe

def build_pipeline(cfg: dict):
    task = cfg["task"]
    device = select_device(cfg.get("device", "auto"))
    dtype = select_dtype(cfg.get("dtype", "auto"), device)

    print(f"[device] selected={device} dtype={dtype}")

    if task == "txt2img":
        model_id = cfg["model_id"]
        pipe = StableDiffusionPipeline.from_pretrained(
            model_id,
            **_common_kwargs(cfg, dtype),
        )

    elif task == "img2img":
        model_id = cfg["model_id"]
        pipe = StableDiffusionImg2ImgPipeline.from_pretrained(
            model_id,
            **_common_kwargs(cfg, dtype),
        )

    elif task == "inpaint":
        model_id = cfg["model_id"]
        pipe = StableDiffusionInpaintPipeline.from_pretrained(
            model_id,
            **_common_kwargs(cfg, dtype),
        )

    elif task == "controlnet_canny":
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
        model_id = cfg["model_id"]
        pipe = StableDiffusionXLPipeline.from_pretrained(
            model_id,
            torch_dtype=dtype,
            local_files_only=True,
        )

    elif task == "lora_txt2img":
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
