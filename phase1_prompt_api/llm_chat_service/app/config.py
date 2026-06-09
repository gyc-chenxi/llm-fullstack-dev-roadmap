"""应用配置 — 基于 pydantic-settings，从 .env 加载"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 服务配置
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # API 鉴权
    api_key: str = ""
    auth_enabled: bool = False

    # 默认 LLM Provider
    default_provider: str = "openai"
    default_model: str = "gpt-4o-mini"

    # 各 Provider 配置
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"

    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com/v1"

    anthropic_api_key: str = ""

    # 本地模型
    ollama_base_url: str = "http://localhost:11434/v1"
    llamacpp_base_url: str = "http://localhost:8081/v1"

    # 限流（内存版）
    rate_limit_enabled: bool = True
    rate_limit_max_requests: int = 30
    rate_limit_window_seconds: int = 60

    # 请求超时
    request_timeout: int = 60
    max_retries: int = 3

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


settings = Settings()
