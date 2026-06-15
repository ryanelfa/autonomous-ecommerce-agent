import { useEffect, useRef, useState } from "react";
import type { WsMessage } from "./types";

const WS_URL = "ws://localhost:8000/ws";
const MAX_RETRIES = 10;

/** WebSocket hook with auto-reconnect (1s/2s/4s... backoff, max 10 attempts). */
export function useWarRoomSocket(onMessage: (msg: WsMessage) => void): { connected: boolean } {
  const [connected, setConnected] = useState(false);
  const handler = useRef(onMessage);
  handler.current = onMessage;

  useEffect(() => {
    let ws: WebSocket | null = null;
    let retries = 0;
    let closed = false;
    let timer: ReturnType<typeof setTimeout>;

    const connect = () => {
      ws = new WebSocket(WS_URL);
      ws.onopen = () => {
        retries = 0;
        setConnected(true);
      };
      ws.onmessage = (event) => {
        try {
          handler.current(JSON.parse(event.data) as WsMessage);
        } catch {
          /* ignore malformed frames */
        }
      };
      ws.onclose = () => {
        setConnected(false);
        if (!closed && retries < MAX_RETRIES) {
          timer = setTimeout(connect, Math.min(1000 * 2 ** retries, 8000));
          retries += 1;
        }
      };
      ws.onerror = () => ws?.close();
    };

    connect();
    return () => {
      closed = true;
      clearTimeout(timer);
      ws?.close();
    };
  }, []);

  return { connected };
}
