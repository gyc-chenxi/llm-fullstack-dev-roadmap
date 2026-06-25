"""
环境检查脚本
============

快速验证当前环境的 CUDA/MPS 能力和 PyTorch 配置。
在首次运行生成任务前执行，确保硬件支持就绪。

输出示例：
  Python:     3.11.5
  Platform:   macOS-14.0-arm64-arm-64bit
  PyTorch:   2.3.0
  MPS Built:  True
  MPS Avail:  True
  CUDA Avail: False
  MPS Fallback: 1

运行： python scripts/check_env.py
"""

from diffusers_lab.device import device_report


def main():
    report = device_report()
    print("=" * 40)
    print("Diffusers Lab - Environment Check")
    print("=" * 40)
    for key, value in report.items():
        print(f"  {key}: {value}")
    print("=" * 40)


if __name__ == "__main__":
    main()