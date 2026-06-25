"""
单元测试：API 契约
===================

测试范围：
  - FastAPI /health 端点返回正确的状态和设备信息
  - 验证 API 契约是否与 Pydantic schema 一致

测试策略：
  使用 FastAPI TestClient（不启动 uvicorn，in-process 测试），
  实际的模型加载由 server.py 的 lifespan 管理，TestClient 默认
  不触发 lifespan，因此测试仅验证路由注册和 schema 契约。

运行： python -m pytest tests/test_api_contract.py -v
"""

from fastapi.testclient import TestClient

from sam2_lab.api.server import app

client = TestClient(app)


def test_health_check():
    """
    验证 /health 端点的响应结构：
    - status=ok
    - model 值为预期模型名
    - device 字段存在
    """
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "ok"
    assert data["model"] == "sam2.1_hiera_tiny"
    assert "device" in data