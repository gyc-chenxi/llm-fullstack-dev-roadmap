#!/usr/bin/env python3
"""
SAM 2 Checkpoint 下载脚本
用于自动下载 Meta 官方发布的 SAM 2.1 权重文件。
"""

import argparse
import os
import sys
import urllib.request

# SAM 2.1 官方直链
SAM2_1_URLS = {
    "tiny": "https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_tiny.pt",
    "small": "https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_small.pt",
    "base_plus": "https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_base_plus.pt",
    "large": "https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_large.pt"
}

def download_progress(count, block_size, total_size):
    """终端下载进度条回调函数"""
    if total_size > 0:
        percent = min(100, int(count * block_size * 100 / total_size))
        downloaded_mb = (count * block_size) / (1024 * 1024)
        total_mb = total_size / (1024 * 1024)
        sys.stdout.write(f"\r下载进度: {percent}% [{downloaded_mb:.2f} MB / {total_mb:.2f} MB]")
        sys.stdout.flush()

def main():
    parser = argparse.ArgumentParser(description="下载 SAM 2.1 模型权重文件")
    parser.add_argument(
        "--model-size", 
        type=str, 
        default="tiny", 
        choices=SAM2_1_URLS.keys(), 
        help="指定要下载的模型大小档位"
    )
    parser.add_argument(
        "--output-dir", 
        type=str, 
        default="models/sam2/checkpoints", 
        help="权重文件保存目录"
    )
    args = parser.parse_args()

    url = SAM2_1_URLS[args.model_size]
    filename = url.split("/")[-1]
    output_path = os.path.join(args.output_dir, filename)

    # 确保输出目录存在
    os.makedirs(args.output_dir, exist_ok=True)

    # 检查是否已存在，避免重复下载
    if os.path.exists(output_path):
        print(f"✅ 文件已存在，跳过下载: {output_path}")
        return

    print(f"🚀 开始下载 SAM 2.1 ({args.model_size}) 模型...")
    print(f"🔗 来源: {url}")
    print(f"📁 目标: {output_path}")
    
    try:
        urllib.request.urlretrieve(url, output_path, reporthook=download_progress)
        print(f"\n✅ 成功下载到: {output_path}")
    except Exception as e:
        print(f"\n❌ 下载失败: {e}")
        print("建议检查网络连通性，或使用 runbook 中提供的 curl 命令兜底下载。")
        sys.exit(1)

if __name__ == "__main__":
    main()