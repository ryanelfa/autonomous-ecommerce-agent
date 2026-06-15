"""Database engine, ID generation and seeding."""
import json
import random

from sqlmodel import Session, SQLModel, create_engine, func, select

from . import config
from .models import Customer, Order, Product

engine = create_engine(f"sqlite:///{config.DB_FILE}", connect_args={"check_same_thread": False})

_FIRST = ["Camille", "Léa", "Chloé", "Manon", "Inès", "Jade", "Louise", "Emma", "Sarah", "Zoé",
          "Lucas", "Hugo", "Nathan", "Tom", "Sofiane", "Adam", "Rayan", "Paul", "Mehdi", "Noah"]
_LAST = ["Moreau", "Bernard", "Petit", "Durand", "Leroy", "Lefèvre", "Roux", "Fontaine",
         "Chevalier", "Garnier", "Benali", "Nguyen", "Diallo", "Martins", "Costa", "Klein"]


def next_id(session: Session, model: type[SQLModel], prefix: str, start: int = 1000) -> str:
    count = session.exec(select(func.count()).select_from(model)).one()
    return f"{prefix}-{start + count + 1}"


def load_brands() -> dict:
    return json.loads(config.BRANDS_FILE.read_text(encoding="utf-8"))


def save_brands(data: dict) -> None:
    config.BRANDS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def active_brand() -> dict:
    data = load_brands()
    return next(b for b in data["brands"] if b["id"] == data["active"])


def seed_products_for(session: Session, brand: dict) -> None:
    """Create the brand's catalog if not present yet."""
    existing = session.exec(select(Product).where(Product.brand == brand["id"])).all()
    if existing:
        return
    for p in brand["products"]:
        session.add(Product(
            id=next_id(session, Product, "PRD", 0),
            brand=brand["id"], name=p["name"], category=p["category"],
            price=float(p["price"]), stock=int(p["stock"]),
        ))
        session.commit()


def init_db() -> None:
    SQLModel.metadata.create_all(engine)
    rng = random.Random(42)
    with Session(engine) as session:
        if session.exec(select(func.count()).select_from(Customer)).one() > 0:
            return  # already seeded
        # Customers: 60, of which 8 VIP
        for i in range(60):
            vip = i < 8
            name = f"{rng.choice(_FIRST)} {rng.choice(_LAST)}"
            session.add(Customer(
                id=f"CUS-{200 + i}",
                name=name,
                email=name.lower().replace(" ", ".") + "@example.com",
                tier="vip" if vip else "standard",
                lifetime_value=round(rng.uniform(800, 5000) if vip else rng.uniform(30, 600), 2),
            ))
        session.commit()
        # Products for the active brand
        seed_products_for(session, active_brand())
        # 40 historical paid orders for KPI volume
        customers = session.exec(select(Customer)).all()
        products = session.exec(select(Product)).all()
        for _ in range(40):
            c, p = rng.choice(customers), rng.choice(products)
            qty = rng.randint(1, 3)
            session.add(Order(
                id=next_id(session, Order, "ORD"),
                customer_id=c.id, product_id=p.id, quantity=qty,
                amount=round(p.price * qty, 2), status=rng.choice(["paid", "shipped", "shipped"]),
            ))
            session.commit()
