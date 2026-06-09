"""Pytest configuration — shared fixtures, markers, and asyncio mode."""

import pytest


# Auto-detect async test functions (no explicit @pytest.mark.asyncio needed).
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
