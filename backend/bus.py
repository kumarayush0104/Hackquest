from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Dict, List

from .models import Event


class EventBus:
    def __init__(self) -> None:
        self._subscribers: Dict[str, List[asyncio.Queue[Event]]] = defaultdict(list)
        self._history: List[Event] = []

    def subscribe(self, topic: str) -> asyncio.Queue[Event]:
        queue: asyncio.Queue[Event] = asyncio.Queue()
        self._subscribers[topic].append(queue)
        return queue

    async def publish(self, event: Event) -> None:
        self._history.append(event)
        if len(self._history) > 200:
            self._history = self._history[-200:]
        targets = list(self._subscribers.get(event.topic, []))
        targets += list(self._subscribers.get("*", []))
        for queue in targets:
            await queue.put(event)

    def recent(self, limit: int = 50) -> List[Event]:
        return self._history[-limit:]
