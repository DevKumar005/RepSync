import asyncio
import json
from datetime import datetime, timezone
from typing import AsyncGenerator, Dict, List, Optional


class EventBroadcaster:
    """Manages active SSE connections per outlet sync job with event replay buffering."""

    def __init__(self) -> None:
        self._listeners: Dict[str, List[asyncio.Queue]] = {}
        self._event_buffer: Dict[str, List[dict]] = {}

    def subscribe(self, outlet_id: str) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue()
        if outlet_id not in self._listeners:
            self._listeners[outlet_id] = []
        self._listeners[outlet_id].append(queue)

        # Replay past events if client connected after pipeline started or completed
        for past_event in self._event_buffer.get(outlet_id, []):
            queue.put_nowait(past_event)

        return queue

    def unsubscribe(self, outlet_id: str, queue: asyncio.Queue) -> None:
        if outlet_id in self._listeners:
            if queue in self._listeners[outlet_id]:
                self._listeners[outlet_id].remove(queue)
            if not self._listeners[outlet_id]:
                del self._listeners[outlet_id]

    def clear_buffer(self, outlet_id: str) -> None:
        self._event_buffer.pop(outlet_id, None)

    async def emit(
        self,
        outlet_id: str,
        event_type: str,
        source: Optional[str] = None,
        status: Optional[str] = None,
        message: Optional[str] = None,
        extra: Optional[dict] = None,
    ) -> None:
        payload = {
            "type": event_type,
            "source": source,
            "status": status,
            "message": message,
            "ts": datetime.now(timezone.utc).isoformat(),
        }
        if extra:
            payload.update(extra)

        # Buffer recent events for this outlet so late subscribers receive them
        if outlet_id not in self._event_buffer:
            self._event_buffer[outlet_id] = []
        self._event_buffer[outlet_id].append(payload)
        if len(self._event_buffer[outlet_id]) > 30:
            self._event_buffer[outlet_id].pop(0)

        if outlet_id in self._listeners:
            for q in list(self._listeners[outlet_id]):
                await q.put(payload)


broadcaster = EventBroadcaster()


async def event_generator(outlet_id: str) -> AsyncGenerator[str, None]:
    """Yields Server-Sent Events formatted data to connected clients."""
    queue = broadcaster.subscribe(outlet_id)
    try:
        # Initial ping to establish connection
        init_payload = {
            "type": "connected",
            "message": f"Connected to sync stream for outlet {outlet_id}",
            "ts": datetime.now(timezone.utc).isoformat(),
        }
        yield f"data: {json.dumps(init_payload)}\n\n"

        while True:
            # Wait for event or ping keepalive every 15s
            try:
                event = await asyncio.wait_for(queue.get(), timeout=15.0)
                yield f"data: {json.dumps(event)}\n\n"
                if event.get("type") == "done":
                    # Allow client 1.5s to receive the done event, call es.close(), and invalidate queries
                    await asyncio.sleep(1.5)
                    break
            except asyncio.TimeoutError:
                # Keep-alive heartbeat
                ping = {"type": "ping", "ts": datetime.now(timezone.utc).isoformat()}
                yield f"data: {json.dumps(ping)}\n\n"
    finally:
        broadcaster.unsubscribe(outlet_id, queue)
