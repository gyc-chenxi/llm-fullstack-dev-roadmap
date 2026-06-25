"""
SAM 2 Checkpoint 下载脚本
==========================

从 Meta 官方直链下载 SAM 2.1 模型权重文件。
支持四种模型规格：tiny / small / base_plus / large。

数据流：
  脚本参数 --model-size=tiny → 拼接官方 URL
    → urllib.request.urlretrieve() → 下载到 models/sam2/checkpoints/
    → sam2.1_hiera_tiny.pt（约 77 MB）

可选模型规格与文件大小：
  - tiny:      ~77 MB   (Hiera-Tiny)    ← 推荐，平衡速度与质量
  - small:     ~230 MB  (Hiera-Small)
  - base_plus: ~350 MB  (Hiera-Base+)
  - large:     ~700 MB  (Hiera-Large)

使用方式：
  python scripts/01_download_sam2.py --model-size tiny
  # 或 make download-sam2
"""

import argparse
import os
import sys
import urllib.request

# SAM 2.1 官方直链（Meta FAIR 官方发布）
# 如果链接失效，请参考 https://github.com/facebookresearch/sam2
SAM2_1_URLS = {
    "tiny": "https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_tiny.pt",
    "small": "https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_small.pt",
    "base_plus": "https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_base_plus.pt",
    "large": "https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_large.pt"
}


def download_progress(count, block_size, total_size):
    """
    终端下载进度条回调。

    由 urllib.request.urlretrieve 的 reporthook 参数调用，
    每次下载一个 block 时触发。
    """
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
        help="指定要下载的模型大小档位: tiny/small/base_plus/large",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="models/sam2/checkpoints",
        help="权重文件保存目录",
    )
    args = parser.parse_args()

    url = SAM2_1_URLS[args.model_size]
    filename = url.split("/")[-1]
    output_path = os.path.join(args.output_dir, filename)

    os.makedirs(args.output_dir, exist_ok=True)

    # 已下载则跳过，支持断点续下（不重复下载相同文件）
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