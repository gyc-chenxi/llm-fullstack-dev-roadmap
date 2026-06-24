"""
应用配置管理
-----------
所有配置项可通过环境变量覆盖，开发时直接使用默认值即可。
路径使用 pathlib 基于本文件位置计算，无论从哪个目录启动都正确。

关键参数说明：
  - MODEL_PATH / ADAPTER_PATH：模型加载路径，由 LLMEngine.__init__ 消费
  - DATABASE_URL：SQLite 数据库连接串，由 database.create_engine 消费
  - CONTEXT_WINDOW_TOKENS：滑动窗口 token 上限，由 LLMEngine.truncate_messages 消费
  - MAX_TOKENS_DEFAULT / TEMPERATURE_DEFAULT：推理默认参数，前端初始化时参考
"""

import os
from pathlib import Path

# 项目根目录（server/ 的上级目录，即 01_mlx_lm/）
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# --- 模型配置 ---
# 基础模型路径（MLX 格式的 4-bit 量化模型）
# Qwen2.5-7B-Instruct-4bit：4-bit 量化版本，推理只需约 4GB 显存（统一内存模式
# 下 M 系列芯片共享 CPU+GPU 内存）
MODEL_PATH = os.getenv(
    "MODEL_PATH",
    str(PROJECT_ROOT / "models" / "Qwen2.5-7B-Instruct-4bit"),
)

# LoRA 适配器路径（微调后的增量权重，与基础模型叠加推理）
ADAPTER_PATH = os.getenv(
    "ADAPTER_PATH",
    str(PROJECT_ROOT / "adapters" / "identity_lora"),
)

# --- 数据库配置 ---
# SQLite 数据库文件路径（存储在项目根目录，初次自动创建）
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{PROJECT_ROOT / 'chat.db'}",
)

# --- 推理默认参数 ---
# 最大生成 token 数（默认值，前端可覆盖）
MAX_TOKENS_DEFAULT = int(os.getenv("MAX_TOKENS_DEFAULT", "512"))
# 采样温度（默认值，0.7 兼顾创意与确定性）
TEMPERATURE_DEFAULT = float(os.getenv("TEMPERATURE_DEFAULT", "0.7"))

# --- 上下文窗口配置 ---
# 滑动窗口的 token 上限（prompt 部分的 token 数不会超过此值）
# Qwen2.5-7B 最大上下文 32768，此处设为 4096 的原因：
#   - 对 7B 模型安全（过长上下文会显著增加首 token 延迟）
#   - 4-bit 量化下 KV cache 占用约 4GB，4096 window 确保多轮对话不 OOM
CONTEXT_WINDOW_TOKENS = int(os.getenv("CONTEXT_WINDOW_TOKENS", "4096"))

# --- 服务器配置 ---
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8001"))
