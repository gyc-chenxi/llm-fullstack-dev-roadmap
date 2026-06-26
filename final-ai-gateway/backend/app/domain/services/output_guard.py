"""
Output guard — detects garbled output, repetition, invisible characters, and other anomalies.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from ..entities.fault_event import FaultEvent, FaultType


@dataclass
class OutputGuard:
    max_repeat_ngram: int = 5
    max_repeat_window: int = 50
    min_visible_ratio: float = 0.3
    generation_buffer: str = ""
    repeat_buffer: list[str] = field(default_factory=list)

    def check(self, new_text: str) -> Optional[FaultEvent]:
        self.generation_buffer += new_text
        self.repeat_buffer.append(new_text)

        if fault := self._check_repetition():
            return fault
        if fault := self._check_invisible_chars(new_text):
            return fault
        if fault := self._check_garbled(new_text):
            return fault
        return None

    def _check_repetition(self) -> Optional[FaultEvent]:
        if len(self.repeat_buffer) < self.max_repeat_ngram * 2:
            return None
        recent = self.repeat_buffer[-self.max_repeat_window:]
        for n in range(3, self.max_repeat_ngram + 1):
            for i in range(len(recent) - n * 2 + 1):
                window = recent[i:i + n]
                if recent[i + n:i + n * 2] == window:
                    return FaultEvent(
                        fault_type=FaultType.REPETITION,
                        message=f"detected {n}-gram repetition",
                        detail={"ngram_size": n, "pattern": "".join(window)},
                    )
        return None

    def _check_invisible_chars(self, text: str) -> Optional[FaultEvent]:
        if not text:
            return None
        visible = len(re.sub(r'[\x00-\x1f\x7f-\x9f​-‏ - ﻿]', '', text))
        if visible / max(len(text), 1) < self.min_visible_ratio:
            return FaultEvent(
                fault_type=FaultType.INVISIBLE_CHARS,
                message="too many invisible characters",
                detail={"visible_ratio": visible / max(len(text), 1)},
            )
        return None

    def _check_garbled(self, text: str) -> Optional[FaultEvent]:
        if not text.strip():
            return None
        if len(text) < 3:
            return None
        unicode_blocks = len(set(text)) / max(len(text), 1)
        if unicode_blocks > 0.8:
            return FaultEvent(
                fault_type=FaultType.GARBLED_OUTPUT,
                message="high unicode entropy — possible garbled output",
                detail={"unicode_ratio": unicode_blocks},
            )
        return None

    def reset(self):
        self.generation_buffer = ""
        self.repeat_buffer.clear()