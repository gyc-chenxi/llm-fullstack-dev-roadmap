"""
应用配置管理
-----------
所有配置项可通过环境变量覆盖，开发时直接使用默认值即可。
路径使用 pathlib 基于本文件位置计算，无论从哪个目录启动都正确。
"""

import os
from pathlib import Path

# 项目根目录（server/ 的上级目录）
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# --- 模型配置 ---
# 基础模型路径（MLX 格式的 4-bit 量化模型）
MODEL_PATH = os.getenv(
    "MODEL_PATH",
    str(PROJECT_ROOT / "models" / "Qwen2.5-7B-Instruct-4bit"),
)

# LoRA 适配器路径（微调后的权重）
ADAPTER_PATH = os.getenv(
    "ADAPTER_PATH",
    str(PROJECT_ROOT / "adapters" / "identity_lora"),
)

# --- 数据库配置 ---
# SQLite 数据库文件路径（存储在项目根目录）
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{PROJECT_ROOT / 'chat.db'}",
)

# --- 推理默认参数 ---
MAX_TOKENS_DEFAULT = int(os.getenv("MAX_TOKENS_DEFAULT", "512"))
TEMPERATURE_DEFAULT = float(os.getenv("TEMPERATURE_DEFAULT", "0.7"))

# --- 上下文窗口配置 ---
# 滑动窗口的 token 上限（prompt 部分的 token 数不会超过此值）
# Qwen2.5-7B 最大支持 32768，这里设 4096 对 7B 模型安全且充足
CONTEXT_WINDOW_TOKENS = int(os.getenv("CONTEXT_WINDOW_TOKENS", "4096"))

# --- 服务器配置 ---
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8001"))
