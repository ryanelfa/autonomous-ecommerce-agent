"""Remaining tools: voucher (policy-capped), escalation (creates a Ticket) and KB search (mini-RAG)."""
import math
import random
import re
import string
from collections import Counter
from pathlib import Path
from typing import Any

from sqlmodel import Session

from ...db import next_id
from ...models import Customer, Ticket
from .base import Tool

KB_DIR = Path(__file__).resolve().parents[1] / "kb"


def _strict(props: dict, required: list[str]) -> dict:
    return {"type": "object", "properties": props, "required": required, "additionalProperties": False}


class ApplyVoucher(Tool):
    name = "apply_voucher"
    description = ("TERMINAL ACTION. Issue a goodwill voucher to a customer. "
                   "Hard policy cap: 30 euros maximum (enforced by the tool).")
    input_schema = _strict({
        "customer_id": {"type": "string"},
        "amount": {"type": "number"},
        "reason": {"type": "string"},
    }, ["customer_id", "amount", "reason"])
    terminal = True

    async def execute(self, db: Session, customer_id: str, amount: float, reason: str) -> dict[str, Any]:
        if amount > 30:
            return {"ok": False, "error": "amount_exceeds_policy_30eur"}
        if not db.get(Customer, customer_id):
            return {"ok": False, "error": "customer_not_found"}
        code = "BELZ-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
        return {"ok": True, "voucher_code": code, "amount": round(float(amount), 2)}


class EscalateToHuman(Tool):
    name = "escalate_to_human"
    description = ("TERMINAL ACTION. Hand the incident to a human operator by creating a ticket. "
                   "Use priority 'urgent' for VIP customers or high amounts. "
                   "The reason must summarize the situation and what you already checked.")
    input_schema = _strict({
        "incident_id": {"type": "string"},
        "priority": {"type": "string", "enum": ["normal", "urgent"]},
        "reason": {"type": "string"},
    }, ["incident_id", "priority", "reason"])
    terminal = True

    async def execute(self, db: Session, incident_id: str, priority: str, reason: str) -> dict[str, Any]:
        ticket = Ticket(
            id=next_id(db, Ticket, "TCK", 0),
            incident_id=incident_id, priority=priority, reason=reason,
        )
        db.add(ticket)
        db.commit()
        return {"ok": True, "ticket_id": ticket.id}


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zàâçéèêëîïôûùüÿñæœ0-9]+", text.lower())


class SearchKB(Tool):
    name = "search_kb"
    description = ("Search the brand knowledge base (returns policy, shipping FAQ, VIP program). "
                   "Returns the 2 most relevant sections. Always consult it before answering "
                   "policy questions (returns, delivery delays, lost parcels).")
    input_schema = _strict({"query": {"type": "string"}}, ["query"])

    def __init__(self) -> None:
        # Index sections once: split each markdown file on '## ' headings, TF scoring with IDF.
        self.sections: list[dict[str, str]] = []
        for file in sorted(KB_DIR.glob("*.md")):
            raw = file.read_text(encoding="utf-8")
            parts = re.split(r"^## ", raw, flags=re.MULTILINE)
            for part in parts[1:]:
                heading, _, body = part.partition("\n")
                self.sections.append({"source": file.name, "heading": heading.strip(),
                                      "content": body.strip()[:600]})
        self.docs_tokens = [_tokenize(s["heading"] + " " + s["content"]) for s in self.sections]
        df: Counter[str] = Counter()
        for tokens in self.docs_tokens:
            df.update(set(tokens))
        n_docs = max(len(self.docs_tokens), 1)
        self.idf = {tok: math.log((n_docs + 1) / (count + 1)) + 1 for tok, count in df.items()}

    async def execute(self, db: Session, query: str) -> dict[str, Any]:
        q_tokens = _tokenize(query)
        scores: list[float] = []
        for tokens in self.docs_tokens:
            tf = Counter(tokens)
            score = sum(tf[t] * self.idf.get(t, 1.0) for t in q_tokens)
            scores.append(score / (len(tokens) ** 0.5 + 1))
        ranked = sorted(zip(scores, self.sections), key=lambda x: x[0], reverse=True)[:2]
        results = [s for score, s in ranked if score > 0]
        return {"ok": True, "results": results or [{"source": "none", "heading": "no_match",
                                                    "content": "No relevant policy found."}]}
