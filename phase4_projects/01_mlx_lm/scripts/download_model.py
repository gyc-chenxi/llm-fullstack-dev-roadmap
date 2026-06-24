"""
模型下载脚本
----------
通过 Hugging Face 国内镜像站 (hf-mirror.com) 下载 MLX 格式的 Qwen2.5 量化模型。

设计要点：
  1. 强制清除代理环境变量，避免代理干扰国内镜像直连
  2. 设置 HF_ENDPOINT 为 hf-mirror.com，走国内 CDN 加速
  3. 使用 snapshot_download 下载完整模型仓库（含 config.json, tokenizer.json, .safetensors）

下载目标：
  mlx-community/Qwen2.5-7B-Instruct-4bit
  → ./models/Qwen2.5-7B-Instruct-4bit   (约 4GB，4-bit 量化)
"""

import os

# 1. 强制清除任何可能的代理残留，确保直连国内镜像
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)
os.environ.pop("all_proxy", None)

# 2. 强制指定 Hugging Face 国内镜像站（绕过网络限制）
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

from huggingface_hub import snapshot_download

print("代理干扰已屏蔽。正在通过 hf-mirror 国内镜像直连下载...")

# snapshot_download 参数说明：
#   - repo_id: Hugging Face 仓库 ID
#   - local_dir: 本地保存路径（相对于项目根目录）
#   - local_dir_use_symlinks=False: 直接下载文件（不缓存 symlink）
#   - max_workers=4: 4 线程并发下载，平衡速度与网络稳定性
snapshot_download(
    repo_id="mlx-community/Qwen2.5-7B-Instruct-4bit",
    local_dir="./models/Qwen2.5-7B-Instruct-4bit",
    local_dir_use_symlinks=False,
    max_workers=4
)

print("\n下载完成！去运行 python scripts/infer.py 测试推理吧！")