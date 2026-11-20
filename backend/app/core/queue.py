import asyncio
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass(order=True)
class QueueItem:
    priority: int
    created_at: datetime = field(compare=False)
    run_id: str = field(compare=False)
    payload: Dict[str, Any] = field(compare=False)

class ExecutionQueue:
    """
    In-process asynchronous sequential priority queue.
    Guarantees single-model execution to prevent VRAM / RAM collisions.
    """
    def __init__(self):
        self._queue: asyncio.PriorityQueue[QueueItem] = asyncio.PriorityQueue()
        self._active_run_id: Optional[str] = None
        self._lock = asyncio.Lock()

    async def enqueue(self, run_id: str, payload: Dict[str, Any], priority: int = 10) -> int:
        """Enqueues an evaluation run and returns estimated queue depth."""
        async with self._lock:
            item = QueueItem(
                priority=priority,
                created_at=datetime.utcnow(),
                run_id=run_id,
                payload=payload
            )
            await self._queue.put(item)
            depth = self._queue.qsize()
            logger.info("Enqueued run %s with priority %d. Current queue depth: %d", run_id, priority, depth)
            return depth

    async def dequeue(self) -> QueueItem:
        """Pulls the next priority item from the queue."""
        item = await self._queue.get()
        async with self._lock:
            self._active_run_id = item.run_id
        return item

    async def task_done(self) -> None:
        """Signals completion of the currently dequeued task."""
        async with self._lock:
            self._active_run_id = None
        self._queue.task_done()

    @property
    def active_run_id(self) -> Optional[str]:
        return self._active_run_id

    @property
    def size(self) -> int:
        return self._queue.qsize()

execution_queue = ExecutionQueue()
