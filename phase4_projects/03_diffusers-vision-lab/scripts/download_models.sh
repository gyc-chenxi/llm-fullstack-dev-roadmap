#!/usr/bin/env bash
set -euo pipefail

export HF_HOME="${HF_HOME:-$PWD/.cache/huggingface}"
export HF_HUB_CACHE="${HF_HUB_CACHE:-$HF_HOME/hub}"
export HF_XET_CACHE="${HF_XET_CACHE:-$HF_HOME/xet}"
export HF_XET_HIGH_PERFORMANCE=1
export HF_HUB_DOWNLOAD_TIMEOUT=60
export HF_HUB_ETAG_TIMEOUT=30

mkdir -p \
  models/sd15 \
  models/sd15-inpaint \
  models/sdxl-base \
  models/controlnet-canny \
  models/lora

echo "==> HF auth status"
hf auth whoami

echo "==> Download SD 1.5 Diffusers format"
hf download runwayml/stable-diffusion-v1-5 \
  --local-dir models/sd15 \
  --include "model_index.json" \
  --include "scheduler/**" \
  --include "tokenizer/**" \
  --include "text_encoder/**" \
  --include "unet/**" \
  --include "vae/**" \
  --include "feature_extractor/**" \
  --include "safety_checker/**"

echo "==> Download SD 1.5 Inpainting Diffusers format"
hf download runwayml/stable-diffusion-inpainting \
  --local-dir models/sd15-inpaint \
  --include "model_index.json" \
  --include "scheduler/**" \
  --include "tokenizer/**" \
  --include "text_encoder/**" \
  --include "unet/**" \
  --include "vae/**" \
  --include "feature_extractor/**" \
  --include "safety_checker/**"

echo "==> Download SDXL Base Diffusers format"
hf download stabilityai/stable-diffusion-xl-base-1.0 \
  --local-dir models/sdxl-base \
  --include "model_index.json" \
  --include "scheduler/**" \
  --include "tokenizer/**" \
  --include "tokenizer_2/**" \
  --include "text_encoder/**" \
  --include "text_encoder_2/**" \
  --include "unet/**" \
  --include "vae/**"

echo "==> Download ControlNet Canny"
hf download lllyasviel/sd-controlnet-canny \
  --local-dir models/controlnet-canny \
  --include "config.json" \
  --include "diffusion_pytorch_model.safetensors" \
  --include "diffusion_pytorch_model.bin"

echo "✅ Model download complete"
