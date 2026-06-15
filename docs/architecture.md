# Architecture

## Overview

Agent War Room is a single-machine, two-process application:

- a **Python/FastAPI backend** that simulates an e-commerce operation, runs an autonomous
  agent, and exposes both a GraphQL API and a WebSocket stream;
- a **React/TypeScript frontend** that bootstraps over GraphQL and then renders the live
  agent activity received over the WebSocket.

There is no database server, no message broker and no cloud dependency. State lives in a
local SQLite file (`backend/warroom.db`), recreated and seeded on first start.

## Backend modules

| Module | Responsibility |
|---|---|
| `app/main.py` | FastAPI app; on startup launches the simulator loop and the agent worker |
| `app/config.py` | Settings (env vars, simulation speed, agent limits) |
| `app/models.py` | SQLModel tables (Customer, Product, Order, Incident, AgentRun, Ticket) |
| `app/db.py` | Engine, ID generation, seeding, brand catalog loading |
| `app/simulator.py` | asyncio loop generating orders and incidents; French message templates |
| `app/bus.py` | EventBus (WebSocket broadcast) + shared runtime state (agent queue, sim flag) |
| `app/kpi.py` | KPI computation and the "saved revenue" rule |
| `app/graphql_schema.py` | Strawberry schema: queries + mutations |
| `app/ws.py` | WebSocket endpoint |
| `app/agent/core.py` | The Agent class: hand-written tool-use loop + error fallback |
| `app/agent/tools/` | The 8 tools (OOP: `Tool` base class + `ToolRegistry`) |
| `app/agent/prompts/` | The system prompt |
| `app/agent/kb/` | Knowledge base markdown files (returns, shipping, VIP) |

## Data flow

1. The **simulator** ticks every `TICK_SECONDS`. With probability `INCIDENT_RATIO` it
   creates an incident; otherwise a normal paid order (background noise for the KPIs).
2. A new incident is published on the bus (`incident_created`) and pushed onto the
   `agent_queue` (FIFO — one incident handled at a time, so the trace stays readable).
3. The **agent worker** pops the incident and runs `Agent.handle_incident`:
   - it calls the Anthropic API with the system prompt and the tool definitions;
   - each text block becomes an `agent_thinking` event;
   - each tool-use block becomes a `tool_call` → execution → `tool_result` event;
   - a successful terminal tool ends the loop;
   - a final, tool-free turn produces the customer reply (`customer_reply`).
4. The incident is closed (`resolved` or `escalated`), `saved_amount` is computed, and
   `agent_finished` + `kpi_update` are published.
5. The **frontend** updates its three columns and animates the saved-revenue counter.

## WebSocket protocol

All messages: `{ "type": string, "ts": ISO8601, "payload": object }`.

| `type` | payload |
|---|---|
| `order_created` | `{ orderId, customerName, productName, amount }` |
| `incident_created` | full incident (id, kind, severity, summary, customerMessage, status, createdAt, order{…}) |
| `agent_started` | `{ runId, incidentId }` |
| `agent_thinking` | `{ runId, incidentId, text }` |
| `tool_call` | `{ runId, incidentId, tool, args }` |
| `tool_result` | `{ runId, incidentId, tool, ok, resultSummary }` |
| `customer_reply` | `{ runId, incidentId, text }` |
| `agent_finished` | `{ runId, incidentId, outcome, savedAmount, durationSeconds }` |
| `kpi_update` | full Kpis object |
| `brand_changed` | full Brand object |
| `sim_state` | `{ running: bool }` |

## GraphQL surface

Queries: `incidents`, `incident(id)`, `kpis`, `brands`, `activeBrand`, `simulationRunning`.
Mutations: `injectIncident(kind)`, `setBrand(brandId)`, `setSimulation(running)`.

Real-time updates do **not** use GraphQL subscriptions; the WebSocket carries them.
GraphQL is used for the initial bootstrap and for the three mutations the UI triggers.

## Incident taxonomy (weighted)

| kind | weight | generation |
|---|---|---|
| `out_of_stock` | 30% | product stock forced to 0, order pending |
| `payment_failed` | 25% | order pending |
| `lost_parcel` | 20% | order shipped > 7 simulated days ago |
| `vip_complaint` | 15% | VIP customer guaranteed |
| `return_request` | 10% | order shipped, random reason |

## Error handling

The agent must never crash the server. Any exception inside the loop (API error, tool
failure, max iterations reached) triggers an automatic urgent escalation: a ticket is
created, a neutral customer reply is sent, and the run is closed with outcome `human`.
