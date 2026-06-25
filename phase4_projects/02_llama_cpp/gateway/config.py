"""
统一配置入口
-----------
企业项目不要把上游地址、超时、默认模型写死在 route 里，
否则后续切换 MLX/Ollama/vLLM/云 API 会非常痛苦。

配置覆盖方式（优先级从低到高）：
  1. 默认值（本文件）
  2. .env 文件（同目录，UTF-8 编码）
  3. 环境变量（如 GATEWAY_API_KEY=xxx）

关键参数说明：
  - llamacpp_base_url: 上游 llama-server 地址，Gateway 仅做代理转发
  - max_request_tokens / max_output_tokens: token 上限约束，防止单请求打爆有限显存
  - gateway_api_key: 网关认证密钥，空字符串=关闭认证（开发模式）
  - rate_limit_max_requests: 每 IP 每秒最大请求数，0=关闭限流
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """统一配置入口。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "llamacpp-serving-lab"

    # ── 上游 llama-server 配置 ──
    llamacpp_base_url: str = "http://127.0.0.1:8081"  # llama-server 默认端口
    llamacpp_api_key: str | None = None                # 上游的 API key（如有）
    default_model: str = "local-qwen2.5-7b-q4"         # 请求体中未指定 model 时的默认值

    # ── 上游 HTTP 超时 ──
    # connect: 建立 TCP 连接的超时，本地服务 5 秒绰绰有余
    # read: 读取响应的超时，流式模式下需覆盖为较大值（如 300s）
    upstream_connect_timeout: float = 5.0
    upstream_read_timeout: float = 300.0

    # ── Token 约束 ──
    # max_request_tokens: 输入（prompt）的最大 token 数
    # max_output_tokens: 输出的最大 token 数
    # Qwen2.5-7B 上下文 32768，但在本地推理设 8192 平衡显存与效果
    max_request_tokens: int = 8192
    max_output_tokens: int = Field(default=2048, ge=1, le=8192)

    # ── 网关认证 ──
    # 为空字符串时关闭认证（本地开发）
    # 生产环境应通过环境变量设置，头部为 X-API-Key
    gateway_api_key: str = ""

    # ── 速率限制（进程内滑动窗口） ──
    # 当并发=2 时，~30 req/s 是合理上限
    # 设为 0 可关闭限流；多进程部署时需改为 Redis 实现
    rate_limit_max_requests: int = 30
    rate_limit_window_seconds: float = 1.0


settings = Settings()  # 全局单例，各模块通过 import 引用