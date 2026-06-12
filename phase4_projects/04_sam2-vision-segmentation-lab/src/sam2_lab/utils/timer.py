"""
计时器工具
---------
提供简单的上下文管理器和装饰器，用于测量代码块执行耗时。
"""
from __future__ import annotations

import time
from contextlib import contextmanager


@contextmanager
def timer(label: str = "操作"):
    """上下文管理器：进入时记录开始时间，退出时打印耗时。

    用法:
        with timer("SAM2 推理"):
            masks = predictor.predict(...)
        # 输出: [timer] SAM2 推理: 1.23s
    """
    start = time.perf_counter()
    yield
    elapsed = time.perf_counter() - start
    if elapsed < 0.1:
        print(f"[timer] {label}: {elapsed * 1000:.1f}ms")
    else:
        print(f"[timer] {label}: {elapsed:.2f}s")


class Timer:
    """可复用的计时器，支持 start/stop/reset/elapsed。

    用法:
        t = Timer()
        t.start()
        # ... do work ...
        t.stop()
        print(f"耗时: {t.elapsed:.2f}s")
    """

    def __init__(self):
        self._start: float | None = None
        self._end: float | None = None

    def start(self) -> None:
        self._start = time.perf_counter()
        self._end = None

    def stop(self) -> float:
        self._end = time.perf_counter()
        return self.elapsed

    def reset(self) -> None:
        self._start = None
        self._end = None

    @property
    def elapsed(self) -> float:
        if self._start is None:
            return 0.0
        end = self._end if self._end is not None else time.perf_counter()
        return end - self._start
