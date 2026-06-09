"""GET /v1/models — 列出可用模型"""

from fastapi import APIRouter

router = APIRouter(prefix="/v1", tags=["Models"])


AVAILABLE_MODELS = [
    {"id": "gpt-4o", "object": "model", "owned_by": "openai"},
    {"id": "gpt-4o-mini", "object": "model", "owned_by": "openai"},
    {"id": "deepseek-chat", "object": "model", "owned_by": "deepseek"},
    {"id": "deepseek-reasoner", "object": "model", "owned_by": "deepseek"},
    {"id": "claude-3-5-sonnet", "object": "model", "owned_by": "anthropic"},
    {"id": "qwen-max", "object": "model", "owned_by": "alibaba"},
    {"id": "local-llama", "object": "model", "owned_by": "local"},
]


@router.get("/models")
async def list_models():
    return {
        "object": "list",
        "data": AVAILABLE_MODELS,
    }
