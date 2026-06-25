"""
Pytest 配置：共享 fixtures、自动标记 async 测试、集成测试标记
================================================================

测试策略说明：
  - 单元测试：直接测试 Pydantic 模型（test_gateway_schema.py），无需上游
  - 集成测试（lite）：使用 httpx.ASGITransport + AsyncMock 模拟上游，
    验证中间件栈和路由层的逻辑（test_gateway_health.py），不启动 uvicorn。
  - 完整集成测试：需实际运行 llama-server 和 Gateway（未在此目录中，
    使用 scripts/bench_concurrency.py 作为替代端到端验证）。

数据流：
  pytest 执行 → 自动标记 async 函数 → conftest 注入 fixtures
    → ASGITransport 创建 in-process FastAPI 实例 → 请求经由全部中间件栈
    → 路由处理 → 返回响应
"""

import pytest


# 自动为 async 测试函数添加 @pytest.mark.asyncio，无需手动标注。
def pytest_collection_modifyitems(items):
    for item in items:
        if item.get_closest_marker("asyncio") is None and hasattr(item.obj, "__call__"):
            import inspect
            if inspect.iscoroutinefunction(item.obj):
                item.add_marker(pytest.mark.asyncio)


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "integration: mark test as requiring a running upstream (llama-server)",
    )