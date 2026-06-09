"""pytest fixtures"""

import pytest
from httpx import AsyncClient, ASGITransport
import sys
import os

# 确保项目根在 sys.path 中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.config import settings


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    """异步测试客户端"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
