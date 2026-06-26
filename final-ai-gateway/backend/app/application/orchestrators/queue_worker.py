"""
Queue worker — background consumer that dequeues requests and assigns slots.
"""

from __future__ import annotations

import asyncio
import logging

from app.application.use_cases.dequeue_request_use_case import DequeueRequestUseCase

logger = logging.getLogger(__name__)


class QueueWorker:
    def __init__(
        self,
        dequeue_use_case: DequeueRequestUseCase,
        poll_interval_sec: float = 0.5,
    ):
        self.dequeue_use_case = dequeue_use_case
        self.poll_interval_sec = poll_interval_sec
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self):
        self._running = True
        self._task = asyncio.create_task(self._run())
        logger.info("Queue worker started (interval=%.1fs)", self.poll_interval_sec)

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Queue worker stopped")

    async def _run(self):
        while self._running:
            try:
                result = await self.dequeue_use_case.execute()
                if result:
                    logger.info("Dequeued: %s → slot %s", result["request_id"], result.get("slot_id"))
            except Exception as e:
                logger.error("Queue worker error: %s", e)
            await asyncio.sleep(self.poll_interval_sec)
