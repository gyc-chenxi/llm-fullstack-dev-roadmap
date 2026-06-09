from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    统一配置入口。
    企业项目不要把上游地址、超时、默认模型写死在 route 里，
    否则后续切换 MLX/Ollama/vLLM/云 API 会非常痛苦。
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "llamacpp-serving-lab"

    llamacpp_base_url: str = "http://127.0.0.1:8081"
    llamacpp_api_key: str | None = None
    default_model: str = "local-qwen2.5-7b-q4"

    upstream_connect_timeout: float = 5.0
    upstream_read_timeout: float = 300.0

    max_request_tokens: int = 8192
    max_output_tokens: int = Field(default=2048, ge=1, le=8192)

    # ── Gateway security ──
    # When set, every request (except /healthz, /readyz) must carry
    # `X-API-Key: <this value>`.  Leave empty to disable auth (local dev).
    gateway_api_key: str = ""

    # ── Rate limiting (in-process sliding window) ──
    # Set to 0 to disable.  For local dev with parallel=2 slots,
    # a reasonable ceiling is ~30 req/s per IP.
    rate_limit_max_requests: int = 30
    rate_limit_window_seconds: float = 1.0


settings = Settings()