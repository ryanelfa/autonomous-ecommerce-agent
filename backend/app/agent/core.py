"""The Agent: receives an incident, reasons with the LLM, calls tools, resolves or escalates.

Every step is published on the event bus so the dashboard shows the agent thinking live.
The loop is written by hand (no agent framework) on purpose: it IS the demonstration.
"""
import asyncio
import json
import time
from pathlib import Path
from typing import Any

from anthropic import AsyncAnthropic
from sqlmodel import Session

from .. import config
from ..bus import EventBus
from ..db import active_brand, engine, next_id
from ..kpi import compute_kpis, saved_amount_for
from ..models import AgentRun, Incident, Order, Ticket, utcnow
from .tools.base import Tool, ToolRegistry
from .tools.crud_tools import CheckStock, GetCustomer, GetOrder, ProposeSubstitute, RefundOrder
from .tools.policy_tools import ApplyVoucher, EscalateToHuman, SearchKB

PROMPT_FILE = Path(__file__).resolve().parent / "prompts" / "system_prompt.md"

# Maps terminal tool -> resolution kind stored on the incident
RESOLUTION_OF = {
    "refund_order": "refund",
    "propose_substitute": "substitute",
    "apply_voucher": "voucher",
    "escalate_to_human": "human",
}


def build_registry() -> ToolRegistry:
    registry = ToolRegistry()
    for tool in (GetOrder(), GetCustomer(), CheckStock(), RefundOrder(),
                 ProposeSubstitute(), ApplyVoucher(), EscalateToHuman(), SearchKB()):
        registry.register(tool)
    return registry


class Agent:
    def __init__(self, registry: ToolRegistry, bus: EventBus,
                 model: str = config.AGENT_MODEL,
                 max_iterations: int = config.MAX_AGENT_ITERATIONS) -> None:
        self.registry = registry
        self.bus = bus
        self.model = model
        self.max_iterations = max_iterations
        self.client = AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)

    # ---------- prompt building ----------

    def system_prompt(self) -> str:
        brand = active_brand()
        descriptor = {
            "belleza": "a luxury beauty e-commerce brand",
            "sportea": "a sports equipment e-commerce brand",
        }.get(brand["id"], "an e-commerce brand")
        return PROMPT_FILE.read_text(encoding="utf-8").format(
            brand_name=brand["name"], brand_descriptor=descriptor, brand_voice=brand["voice"],
        )

    def initial_message(self, incident: Incident, db: Session) -> str:
        order = db.get(Order, incident.order_id)
        payload = {
            "incident": {
                "id": incident.id, "kind": incident.kind, "severity": incident.severity,
                "summary": incident.summary, "customer_message": incident.customer_message,
            },
            "order": {"order_id": order.id, "amount": order.amount, "status": order.status,
                      "customer_id": order.customer_id, "product_id": order.product_id},
        }
        return ("New incident to resolve. Investigate with your tools, then take exactly one "
                "terminal action (or answer from the knowledge base for informational requests).\n"
                + json.dumps(payload, ensure_ascii=False))

    # ---------- main loop ----------

    async def handle_incident(self, incident_id: str) -> None:
        started = time.monotonic()
        steps: list[dict[str, Any]] = []
        tokens_in = tokens_out = 0
        outcome: str | None = None
        customer_reply: str | None = None

        with Session(engine) as db:
            incident = db.get(Incident, incident_id)
            if incident is None:
                return
            incident.status = "in_progress"
            db.add(incident)
            db.commit()
            run = AgentRun(id=next_id(db, AgentRun, "RUN", 0), incident_id=incident.id)
            db.add(run)
            db.commit()
            run_id = run.id
            order_amount = (db.get(Order, incident.order_id) or Order(amount=0.0)).amount
            first_message = self.initial_message(incident, db)

        await self.bus.publish("agent_started", {"runId": run_id, "incidentId": incident_id})

        messages: list[dict[str, Any]] = [{"role": "user", "content": first_message}]
        kb_used = False

        try:
            for _ in range(self.max_iterations):
                response = await self.client.messages.create(
                    model=self.model,
                    max_tokens=config.MAX_TOKENS_PER_CALL,
                    system=self.system_prompt(),
                    messages=messages,
                    tools=self.registry.to_anthropic_tools(),
                )
                tokens_in += response.usage.input_tokens
                tokens_out += response.usage.output_tokens

                tool_uses = [b for b in response.content if b.type == "tool_use"]
                for block in response.content:
                    if block.type == "text" and block.text.strip():
                        steps.append({"type": "thinking", "text": block.text.strip()})
                        await self.bus.publish("agent_thinking", {
                            "runId": run_id, "incidentId": incident_id, "text": block.text.strip(),
                        })

                if not tool_uses:
                    # Model stopped without a terminal tool -> informational resolution
                    # (legitimate for return_request answered from the KB).
                    if response.content and response.content[-1].type == "text":
                        customer_reply = response.content[-1].text.strip()
                    outcome = "info" if kb_used else "human"
                    break

                messages.append({"role": "assistant", "content": response.content})
                tool_results: list[dict[str, Any]] = []
                terminal_called: str | None = None

                for tool_use in tool_uses:
                    args = dict(tool_use.input or {})
                    if tool_use.name == "search_kb":
                        kb_used = True
                    steps.append({"type": "tool_call", "tool": tool_use.name, "args": args})
                    await self.bus.publish("tool_call", {
                        "runId": run_id, "incidentId": incident_id,
                        "tool": tool_use.name, "args": args,
                    })
                    with Session(engine) as db:
                        result = await self.registry.dispatch(tool_use.name, args, db)
                    summary = json.dumps(result, ensure_ascii=False)[:140]
                    steps.append({"type": "tool_result", "tool": tool_use.name,
                                  "ok": bool(result.get("ok")), "result": result})
                    await self.bus.publish("tool_result", {
                        "runId": run_id, "incidentId": incident_id, "tool": tool_use.name,
                        "ok": bool(result.get("ok")), "resultSummary": summary,
                    })
                    tool_results.append({
                        "type": "tool_result", "tool_use_id": tool_use.id,
                        "content": json.dumps(result, ensure_ascii=False),
                    })
                    if result.get("ok") and self.registry.is_terminal(tool_use.name):
                        terminal_called = tool_use.name

                messages.append({"role": "user", "content": tool_results})

                if terminal_called:
                    outcome = RESOLUTION_OF[terminal_called]
                    customer_reply = await self._final_reply(messages)
                    break
            else:
                outcome = None  # max iterations reached

            if outcome is None:
                raise RuntimeError("max_iterations_reached")

        except Exception as exc:
            # The agent must NEVER crash the server: automatic escalation fallback.
            outcome = "human"
            customer_reply = ("Votre demande a été transmise en priorité à un conseiller, "
                              "qui revient vers vous très rapidement.")
            steps.append({"type": "error", "text": str(exc)})
            with Session(engine) as db:
                db.add(Ticket(id=next_id(db, Ticket, "TCK", 0), incident_id=incident_id,
                              priority="urgent", reason=f"agent_error: {exc}"))
                db.commit()

        # ---------- close the run ----------
        duration = round(time.monotonic() - started, 1)
        if customer_reply:
            steps.append({"type": "customer_reply", "text": customer_reply})
            await self.bus.publish("customer_reply", {
                "runId": run_id, "incidentId": incident_id, "text": customer_reply,
            })

        with Session(engine) as db:
            incident = db.get(Incident, incident_id)
            incident.status = "escalated" if outcome == "human" else "resolved"
            incident.resolved_at = utcnow()
            incident.resolution_kind = outcome
            incident.saved_amount = saved_amount_for(outcome, order_amount)
            db.add(incident)
            run = db.get(AgentRun, run_id)
            run.finished_at = utcnow()
            run.outcome = outcome
            run.steps_json = json.dumps(steps, ensure_ascii=False, default=str)
            run.tokens_in, run.tokens_out = tokens_in, tokens_out
            db.add(run)
            db.commit()
            saved = incident.saved_amount

        await self.bus.publish("agent_finished", {
            "runId": run_id, "incidentId": incident_id, "outcome": outcome,
            "savedAmount": saved, "durationSeconds": duration,
        })
        await self.bus.publish("kpi_update", compute_kpis())

    async def _final_reply(self, messages: list[dict[str, Any]]) -> str:
        """One last turn, no tools: write the customer-facing message."""
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=config.MAX_TOKENS_PER_CALL,
            system=self.system_prompt(),
            messages=messages + [{
                "role": "user",
                "content": ("Terminal action done. Now write ONLY the final customer reply "
                            "in French (2-4 sentences), nothing else."),
            }],
        )
        texts = [b.text for b in response.content if b.type == "text"]
        return " ".join(texts).strip() or "Votre demande a bien été traitée."


async def agent_worker(agent: Agent, queue: "asyncio.Queue[str]") -> None:
    """FIFO worker: one incident at a time, so the dashboard trace stays readable."""
    while True:
        incident_id = await queue.get()
        try:
            await agent.handle_incident(incident_id)
        except Exception as exc:
            print(f"[agent_worker] unexpected error on {incident_id}: {exc}")
        finally:
            queue.task_done()
