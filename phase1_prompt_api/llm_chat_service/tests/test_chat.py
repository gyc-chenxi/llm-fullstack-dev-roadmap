"""聊天接口测试"""

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_chat_non_stream_validation(client: AsyncClient):
    """空 messages 应返回 422"""
    resp = await client.post(
        "/v1/chat/completions",
        json={"messages": [], "stream": False},
    )
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_chat_stream_validation(client: AsyncClient):
    """流式空 messages 应返回 422"""
    resp = await client.post(
        "/v1/chat/completions",
        json={"messages": [], "stream": True},
    )
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_chat_valid_request_format(client: AsyncClient):
    """正常请求格式应被接受（可能因无 API Key 而 502，但不应该是 422）"""
    resp = await client.post(
        "/v1/chat/completions",
        json={
            "messages": [{"role": "user", "content": "Hello"}],
            "max_tokens": 64,
            "temperature": 0.5,
            "stream": False,
        },
    )
    # 无 API Key 时，上游调用会失败，但格式校验应该通过
    # 所以不应该返回 422
    assert resp.status_code != 422


@pytest.mark.anyio
async def test_chat_stream_valid_request_format(client: AsyncClient):
    """流式请求格式应被接受"""
    resp = await client.post(
        "/v1/chat/completions",
        json={
            "messages": [{"role": "user", "content": "Hello"}],
            "stream": True,
        },
    )
    assert resp.status_code != 422
