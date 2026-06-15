"""WebSocket endpoint: clients receive every bus event. Server->client only."""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from .bus import bus
from .kpi import compute_kpis

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket) -> None:
    await bus.connect(ws)
    try:
        # Send a KPI snapshot on connect so the UI is populated immediately.
        await bus.publish("kpi_update", compute_kpis())
        while True:
            await ws.receive_text()  # ignore client messages, keep the socket alive
    except WebSocketDisconnect:
        bus.disconnect(ws)
    except Exception:
        bus.disconnect(ws)
