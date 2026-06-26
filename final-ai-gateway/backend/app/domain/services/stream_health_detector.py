"""
Stream health detector — monitors SSE stream for anomalies.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class StreamHealthDetector:
    heartbeat_interval_sec: float = 15.0
    max_silence_sec: float = 60.0
    last_event_time: float = field(default_factory=time.monotonic)
    event_count: int = 0

    def record_event(self):
        self.last_event_time = time.monotonic()
        self.event_count += 1

    @property
    def is_stale(self) -> bool:
        return (time.monotonic() - self.last_event_time) > self.max_silence_sec

    @property
    def needs_heartbeat(self) -> bool:
        return (time.monotonic() - self.last_event_time) > self.heartbeat_interval_sec