"""Database models. IDs are short human-readable strings (ORD-1042, INC-0007...)."""
from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Customer(SQLModel, table=True):
    id: str = Field(primary_key=True)          # "CUS-0231"
    name: str
    email: str
    tier: str = "standard"                     # "standard" | "vip"
    lifetime_value: float = 0.0


class Product(SQLModel, table=True):
    id: str = Field(primary_key=True)          # "PRD-0012"
    brand: str                                 # "belleza" | "sportea"
    name: str
    category: str
    price: float
    stock: int


class Order(SQLModel, table=True):
    id: str = Field(primary_key=True)          # "ORD-1042"
    customer_id: str = Field(index=True)
    product_id: str = Field(index=True)
    quantity: int = 1
    amount: float = 0.0
    status: str = "paid"                       # pending|paid|shipped|refunded|replaced
    created_at: datetime = Field(default_factory=utcnow)


class Incident(SQLModel, table=True):
    id: str = Field(primary_key=True)          # "INC-0007"
    order_id: str = Field(index=True)
    kind: str                                  # out_of_stock|payment_failed|lost_parcel|vip_complaint|return_request
    severity: str = "medium"                   # low|medium|high
    summary: str = ""
    customer_message: str = ""
    status: str = "open"                       # open|in_progress|resolved|escalated
    created_at: datetime = Field(default_factory=utcnow)
    resolved_at: datetime | None = None
    resolution_kind: str | None = None         # refund|substitute|voucher|info|human
    saved_amount: float = 0.0


class AgentRun(SQLModel, table=True):
    id: str = Field(primary_key=True)          # "RUN-0007"
    incident_id: str = Field(index=True)
    started_at: datetime = Field(default_factory=utcnow)
    finished_at: datetime | None = None
    outcome: str | None = None
    steps_json: str = "[]"
    tokens_in: int = 0
    tokens_out: int = 0


class Ticket(SQLModel, table=True):
    id: str = Field(primary_key=True)          # "TCK-0003"
    incident_id: str = Field(index=True)
    priority: str = "normal"                   # normal|urgent
    reason: str = ""
    created_at: datetime = Field(default_factory=utcnow)
