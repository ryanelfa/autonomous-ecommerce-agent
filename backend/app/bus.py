"""In-process event bus: publishes typed events to all connected WebSocket clients.

Also holds shared runtime state (agent queue, simulation flag) to avoid circular imports.
"""
import asyncio
import json
from datetime import datetime, timezone
from typing import Any

from fastapi import WebSocket


class EventBus:
    def __init__(self) -> None:
        self.connections: set[WebSocket] = set()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self.connections.add(ws)

    def disconnect(self, ws: WebSocket) -> None:
        self.connections.discard(ws)

    async def publish(self, type_: str, payload: dict[str, Any]) -> None:
        message = json.dumps({
            "type": type_,
            "ts": datetime.now(timezone.utc).isoformat(),
            "payload": payload,
        }, ensure_ascii=False, default=str)
        dead: list[WebSocket] = []
        for ws in list(self.connections):
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


bus = EventBus()
agent_queue: "asyncio.Queue[str]" = asyncio.Queue()  # incident ids, FIFO
sim_running: dict[str, bool] = {"value": True}        # mutable flag shared across modules
