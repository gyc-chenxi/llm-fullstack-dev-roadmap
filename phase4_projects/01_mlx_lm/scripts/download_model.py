import os

# 1. 强制在代码级别清空任何可能的代理残留
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)
os.environ.pop("all_proxy", None)

# 2. 强制指定 Hugging Face 国内镜像站
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

from huggingface_hub import snapshot_download

print("🚀 代理干扰已屏蔽。正在通过 hf-mirror 国内镜像直连下载...")

snapshot_download(
    repo_id="mlx-community/Qwen2.5-7B-Instruct-4bit",
    local_dir="./models/Qwen2.5-7B-Instruct-4bit",
    local_dir_use_symlinks=False, 
    max_workers=4
)

print("\n🎉 下载彻底完成！去跑 python scripts/infer.py 吧！")