"""KPI computation. The 'saved revenue' rule is deliberately conservative and documented:
- substitute  -> 100% of order amount (sale preserved)
- voucher     -> 50% of order amount (sale likely recovered, conservative)
- info        -> 30% of order amount (relationship preserved, return avoided in part)
- refund/human-> 0
The per-incident value is stored at resolution time in Incident.saved_amount.
"""
from sqlmodel import Session, func, select

from .db import engine
from .models import Incident

SAVED_RATE = {"substitute": 1.0, "voucher": 0.5, "info": 0.3, "refund": 0.0, "human": 0.0}


def saved_amount_for(resolution_kind: str, order_amount: float) -> float:
    return round(order_amount * SAVED_RATE.get(resolution_kind, 0.0), 2)


def compute_kpis() -> dict:
    with Session(engine) as s:
        resolved = s.exec(select(func.count()).select_from(Incident)
                          .where(Incident.status == "resolved")).one()
        escalated = s.exec(select(func.count()).select_from(Incident)
                           .where(Incident.status == "escalated")).one()
        open_count = s.exec(select(func.count()).select_from(Incident)
                            .where(Incident.status.in_(["open", "in_progress"]))).one()
        saved = s.exec(select(func.coalesce(func.sum(Incident.saved_amount), 0.0))).one()
        durations = s.exec(
            select(Incident.created_at, Incident.resolved_at)
            .where(Incident.resolved_at.is_not(None))
        ).all()
    total_done = resolved + escalated
    avg_seconds = (
        sum((b - a).total_seconds() for a, b in durations) / len(durations) if durations else 0.0
    )
    return {
        "incidentsResolved": resolved,
        "incidentsEscalated": escalated,
        "savedRevenue": round(float(saved), 2),
        "escalationRate": round(escalated / total_done, 3) if total_done else 0.0,
        "avgResolutionSeconds": round(avg_seconds, 1),
        "openIncidents": open_count,
    }
