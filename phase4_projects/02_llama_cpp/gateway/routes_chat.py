from fastapi import APIRouter, Request
from fastapi.responses import ORJSONResponse, StreamingResponse

from gateway.config import settings
from gateway.schemas import ChatCompletionRequest

router = APIRouter(prefix="/v1", tags=["chat"])


@router.post("/chat/completions")
async def chat_completions(req: ChatCompletionRequest, request: Request):
    """
    对外暴露 OpenAI-compatible 路由。
    前端、LangChain、OpenAI SDK 都可以把这里当成本地 base_url。
    """
    client = request.app.state.llamacpp
    payload = req.to_upstream_payload(default_model=settings.default_model)

    if req.stream:
        return StreamingResponse(
            client.stream_chat_completion(payload),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

    data = await client.chat_completion(payload)
    return ORJSONResponse(data)