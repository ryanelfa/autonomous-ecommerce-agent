"""GraphQL schema (Strawberry). Real-time goes through the WebSocket, not subscriptions."""
import enum

import strawberry
from sqlmodel import Session, select

from .bus import bus, sim_running
from .db import active_brand, engine, load_brands, save_brands, seed_products_for
from .kpi import compute_kpis
from .models import Customer as CustomerModel
from .models import Incident as IncidentModel
from .models import Order as OrderModel
from .models import Product as ProductModel
from .simulator import create_incident, emit_incident


@strawberry.enum
class IncidentKind(enum.Enum):
    OUT_OF_STOCK = "out_of_stock"
    PAYMENT_FAILED = "payment_failed"
    LOST_PARCEL = "lost_parcel"
    VIP_COMPLAINT = "vip_complaint"
    RETURN_REQUEST = "return_request"


@strawberry.enum
class IncidentStatus(enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    ESCALATED = "escalated"


@strawberry.type
class Product:
    id: strawberry.ID
    name: str
    category: str
    price: float
    stock: int


@strawberry.type
class Customer:
    id: strawberry.ID
    name: str
    tier: str
    lifetime_value: float


@strawberry.type
class Order:
    id: strawberry.ID
    amount: float
    quantity: int
    status: str
    created_at: str
    product: Product
    customer: Customer


@strawberry.type
class Incident:
    id: strawberry.ID
    kind: IncidentKind
    severity: str
    summary: str
    customer_message: str
    status: IncidentStatus
    created_at: str
    resolution_kind: str | None
    saved_amount: float
    order: Order


@strawberry.type
class Kpis:
    incidents_resolved: int
    incidents_escalated: int
    saved_revenue: float
    escalation_rate: float
    avg_resolution_seconds: float
    open_incidents: int


@strawberry.type
class BrandColors:
    background: str
    surface: str
    accent: str
    accent_soft: str
    text: str
    muted: str
    danger: str
    success: str


@strawberry.type
class Brand:
    id: strawberry.ID
    name: str
    tagline: str
    logo_svg: str
    colors: BrandColors
    voice: str


def _logo_svg(brand: dict) -> str:
    """Simple generated monogram logo: no real brand assets, ever."""
    initial = brand["name"][0]
    accent = brand["colors"]["accent"]
    text = brand["colors"]["text"]
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" width="48" height="48">'
        f'<circle cx="24" cy="24" r="22" fill="none" stroke="{accent}" stroke-width="2"/>'
        f'<text x="24" y="31" text-anchor="middle" font-family="Georgia,serif" '
        f'font-size="24" fill="{text}">{initial}</text></svg>'
    )


def _brand_to_gql(brand: dict) -> Brand:
    c = brand["colors"]
    return Brand(
        id=strawberry.ID(brand["id"]), name=brand["name"], tagline=brand["tagline"],
        logo_svg=_logo_svg(brand), voice=brand["voice"],
        colors=BrandColors(
            background=c["background"], surface=c["surface"], accent=c["accent"],
            accent_soft=c["accentSoft"], text=c["text"], muted=c["muted"],
            danger=c["danger"], success=c["success"],
        ),
    )


def _incident_to_gql(incident: IncidentModel, session: Session) -> Incident:
    order = session.get(OrderModel, incident.order_id)
    product = session.get(ProductModel, order.product_id)
    customer = session.get(CustomerModel, order.customer_id)
    return Incident(
        id=strawberry.ID(incident.id), kind=IncidentKind(incident.kind),
        severity=incident.severity, summary=incident.summary,
        customer_message=incident.customer_message, status=IncidentStatus(incident.status),
        created_at=incident.created_at.isoformat(),
        resolution_kind=incident.resolution_kind, saved_amount=incident.saved_amount,
        order=Order(
            id=strawberry.ID(order.id), amount=order.amount, quantity=order.quantity,
            status=order.status, created_at=order.created_at.isoformat(),
            product=Product(id=strawberry.ID(product.id), name=product.name,
                            category=product.category, price=product.price, stock=product.stock),
            customer=Customer(id=strawberry.ID(customer.id), name=customer.name,
                              tier=customer.tier, lifetime_value=customer.lifetime_value),
        ),
    )


@strawberry.type
class Query:
    @strawberry.field
    def incidents(self, status: IncidentStatus | None = None, limit: int = 30) -> list[Incident]:
        with Session(engine) as session:
            stmt = select(IncidentModel).order_by(IncidentModel.created_at.desc()).limit(limit)
            if status:
                stmt = select(IncidentModel).where(IncidentModel.status == status.value) \
                    .order_by(IncidentModel.created_at.desc()).limit(limit)
            return [_incident_to_gql(i, session) for i in session.exec(stmt).all()]

    @strawberry.field
    def incident(self, id: strawberry.ID) -> Incident | None:
        with Session(engine) as session:
            incident = session.get(IncidentModel, str(id))
            return _incident_to_gql(incident, session) if incident else None

    @strawberry.field
    def kpis(self) -> Kpis:
        k = compute_kpis()
        return Kpis(
            incidents_resolved=k["incidentsResolved"], incidents_escalated=k["incidentsEscalated"],
            saved_revenue=k["savedRevenue"], escalation_rate=k["escalationRate"],
            avg_resolution_seconds=k["avgResolutionSeconds"], open_incidents=k["openIncidents"],
        )

    @strawberry.field
    def brands(self) -> list[Brand]:
        return [_brand_to_gql(b) for b in load_brands()["brands"]]

    @strawberry.field
    def active_brand(self) -> Brand:
        return _brand_to_gql(active_brand())

    @strawberry.field
    def simulation_running(self) -> bool:
        return sim_running["value"]


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def inject_incident(self, kind: IncidentKind) -> Incident:
        incident = create_incident(kind.value)
        await emit_incident(incident)
        with Session(engine) as session:
            return _incident_to_gql(session.get(IncidentModel, incident.id), session)

    @strawberry.mutation
    async def set_brand(self, brand_id: strawberry.ID) -> Brand:
        data = load_brands()
        if not any(b["id"] == str(brand_id) for b in data["brands"]):
            raise ValueError(f"unknown brand: {brand_id}")
        data["active"] = str(brand_id)
        save_brands(data)
        brand = active_brand()
        with Session(engine) as session:
            seed_products_for(session, brand)
        gql_brand = _brand_to_gql(brand)
        await bus.publish("brand_changed", {
            "id": brand["id"], "name": brand["name"], "tagline": brand["tagline"],
            "logoSvg": _logo_svg(brand), "colors": brand["colors"], "voice": brand["voice"],
        })
        return gql_brand

    @strawberry.mutation
    async def set_simulation(self, running: bool) -> bool:
        sim_running["value"] = running
        await bus.publish("sim_state", {"running": running})
        return running


schema = strawberry.Schema(query=Query, mutation=Mutation)
