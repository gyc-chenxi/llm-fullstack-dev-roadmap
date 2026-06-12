from fastapi.testclient import TestClient

from sam2_lab.api.server import app

# 使用 FastAPI 自带的测试客户端，不需要真的启动服务就能测试路由
client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    
    # 验证接口返回值是否符合预期契约
    assert data["status"] == "ok"
    assert data["model"] == "sam2.1_hiera_tiny"
    assert "device" in data