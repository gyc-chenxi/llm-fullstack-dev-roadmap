"""
SSE Event Store — generates event IDs and manages SSE I/O helpers.
"""

from __future__ import annotations

import json
import time
from typing import AsyncIterator


class EventIdGenerator:
    def __init__(self, start: int = 1):
        self._counter = start - 1

    def next(self) -> int:
        self._counter += 1
        return self._counter

    def current(self) -> int:
        return self._counter


class SseEventStore:
    def __init__(self):
        self._event_generators: dict[str, EventIdGenerator] = {}

    def generator_for(self, request_id: str) -> EventIdGenerator:
        if request_id not in self._event_generators:
            self._event_generators[request_id] = EventIdGenerator()
        return self._event_generators[request_id]

    def remove(self, request_id: str):
        self._event_generators.pop(request_id, None)


def format_sse_event(event_id: int, request_id: str, event_type: str, data: dict,
                      run_id: str = "", span_id: str = "") -> str:
    payload = {
        "event_id": event_id,
        "request_id": request_id,
        "type": event_type,
        **data,
        "created_at": int(time.time()),
    }
    if run_id:
        payload["run_id"] = run_id
    if span_id:
        payload["span_id"] = span_id
    return f"data: {json.dumps(payload)}\n\n"


async def sse_heartbeat_generator(interval_sec: float = 15.0) -> AsyncIterator[str]:
    while True:
        yield ": heartbeat\n\n"
        import asyncio
        await asyncio.sleep(interval_sec)
