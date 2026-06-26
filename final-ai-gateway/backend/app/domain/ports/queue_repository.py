"""
Queue Repository port — abstract interface for priority queue storage.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from ..entities.queue_ticket import QueueTicket


class QueueRepositoryPort(ABC):
    @abstractmethod
    async def enqueue(self, ticket: QueueTicket) -> None:
        ...

    @abstractmethod
    async def dequeue(self) -> Optional[QueueTicket]:
        ...

    @abstractmethod
    async def peek(self) -> Optional[QueueTicket]:
        ...

    @abstractmethod
    async def remove(self, request_id: str) -> bool:
        ...

    @abstractmethod
    async def size(self) -> int:
        ...
