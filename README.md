# Agent War Room — Belleza Ops

> An autonomous AI agent that triages and resolves e-commerce incidents **live**,
> during a sales peak. Watch it think, call tools, and act — in real time.
>
> Un agent IA autonome qui triage et résout les incidents e-commerce **en direct**,
> pendant un pic de ventes. On le voit raisonner, appeler ses outils et agir, en temps réel.

Built as a portfolio project for the **Salesforce "AI Builder"** role: it uses the
exact stack from the job description — React, TypeScript, GraphQL, Python, OOP,
real-time (WebSocket), an LLM with tool calling, and prompt engineering.

---

## The pitch (FR)

Pendant les pics e-commerce (Noël, ventes privées), une marque beauté reçoit des
milliers d'incidents : ruptures de stock, paiements échoués, colis perdus, clientes
VIP mécontentes. **Belleza Ops** est un agent IA autonome qui :

- **triage** chaque incident dès qu'il arrive,
- **enquête** avec ses outils (commande, profil client, stock, base de connaissances),
- **agit** réellement (remboursement, produit de substitution, geste commercial),
- **sait s'arrêter** : il escalade à un humain les cas sensibles (clientes VIP, montants élevés).

Le chiffre d'affaires sauvé s'affiche en direct. Tout le comportement est piloté par
un *system prompt* et des règles métier — pas de framework d'agent, la boucle est
écrite à la main (c'est le cœur de la démonstration).

---

## Architecture

```
┌─────────────┐   WebSocket (live trace, KPIs)   ┌──────────────────────┐
│   Frontend  │ <───────────────────────────────  │       Backend        │
│ React + TS  │                                    │      FastAPI         │
│ Apollo      │   GraphQL (bootstrap, mutations)   │                      │
│ Tailwind    │  ───────────────────────────────> │  ┌────────────────┐  │
└─────────────┘                                    │  │  Simulator     │  │
                                                   │  │  (asyncio)     │  │
                                                   │  └───────┬────────┘  │
                                                   │          │ incident  │
                                                   │          v           │
                                                   │  ┌────────────────┐  │
                                                   │  │  Agent loop    │  │
                                                   │  │  (hand-written)│  │
                                                   │  │  Anthropic API │  │
                                                   │  └───────┬────────┘  │
                                                   │          │ tools     │
                                                   │          v           │
                                                   │  ┌────────────────┐  │
                                                   │  │ 8 Tools (OOP)  │  │
                                                   │  │ SQLite (SQLModel)│ │
                                                   │  │ Knowledge base │  │
                                                   │  └────────────────┘  │
                                                   └──────────────────────┘
```

Detailed diagram and data contracts: see [`docs/architecture.md`](docs/architecture.md).

---

## How the agent thinks

The agent receives an incident with minimal context (kind, customer message, order id).
It must **investigate before acting**: it fetches the order and customer profile, checks
stock or the knowledge base, then takes exactly **one terminal action**. Every step is
streamed to the dashboard over the WebSocket, so you literally watch it reason.

The behaviour is entirely driven by the system prompt
([`backend/app/agent/prompts/system_prompt.md`](backend/app/agent/prompts/system_prompt.md)),
which encodes the business rules, for example:

- VIP complaints are **always** escalated to a human (priority urgent) — the agent
  gathers context first, but never resolves them itself.
- Refunds are capped at €200, vouchers at €30 (also enforced in the tools themselves).
- Out of stock → propose a same-category substitute within ±30% of price; refund if none.

The loop is in [`backend/app/agent/core.py`](backend/app/agent/core.py). No LangChain,
no agent framework: a plain `while` loop over the Anthropic tool-use protocol.

### The 8 tools

| Tool | Role | Terminal |
|---|---|---|
| `get_order` | fetch order + product | no |
| `get_customer` | fetch profile (tier, lifetime value) | no |
| `check_stock` | stock + same-category alternatives | no |
| `search_kb` | mini-RAG over the policy markdown files | no |
| `refund_order` | full refund (≤ €200) | yes |
| `propose_substitute` | replace product, offer price diff ≤ €15 | yes |
| `apply_voucher` | goodwill voucher (≤ €30) | yes |
| `escalate_to_human` | create a ticket for an operator | yes |

---

## "Saved revenue" — an honest metric

The headline counter is deliberately conservative and fully explainable:

| Resolution | Saved amount |
|---|---|
| `substitute` (sale preserved) | 100% of order amount |
| `voucher` (sale likely recovered) | 50% of order amount |
| `info` (return handled without refund) | 30% of order amount |
| `refund` | €0 (incident resolved, but at cost) |
| `human` (escalation) | €0 |

---

## Run it locally

**Prerequisites:** Python ≥ 3.12, Node ≥ 20, [`uv`](https://docs.astral.sh/uv/), and an
Anthropic API key. A full from-scratch setup guide (macOS) is in `SETUP_MAC.md`.

```bash
# 1. Set your API key
cp .env.example .env
#    then edit .env and paste your ANTHROPIC_API_KEY

# 2. Backend  (terminal 1)
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8000

# 3. Frontend (terminal 2)
cd frontend
npm install
npm run dev          # open http://localhost:5173
```

The simulation starts automatically. Use the buttons at the bottom to **inject an
incident on demand** — this is the demo moment: break your own production and let the
agent fix it.

---

## White-label in 30 seconds

The whole UI (palette, logo, product catalog, brand voice) is driven by
[`backend/brands.json`](backend/brands.json). Switch from **Belleza** (beauty) to
**Sportéa** (sports) live from the top bar: colors, logo and the agent's tone all change
without a page reload. Same agent, any client.

> All brands, customers and products are **fictional**. Logos are generated SVG
> monograms — no real brand assets are used.

---

## Design decisions

- **No agent framework** (LangChain etc.): the tool-use loop is hand-written on purpose,
  to demonstrate understanding of how agents actually work.
- **Simulated customer messages use templates, not the LLM** — the LLM is reserved for
  the agent's reasoning, keeping cost and latency low.
- **Real-time via WebSocket, not GraphQL subscriptions** — simpler and more robust for a
  live demo; GraphQL handles bootstrap + mutations.
- **SQLite, no auth, no Docker** — this is a local demo, optimised to run in under
  5 minutes on a clean machine.
- The agent **never crashes the server**: any failure falls back to an automatic urgent
  escalation.

## Tech stack

Backend: Python 3.12, FastAPI, Strawberry GraphQL, SQLModel/SQLite, Anthropic SDK.
Frontend: Vite, React 18, TypeScript (strict), Tailwind CSS, Apollo Client.
