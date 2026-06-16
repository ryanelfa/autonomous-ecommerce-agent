"""Event simulator: generates orders (background noise) and incidents (agent work).

Customer messages are template-based on purpose (no LLM here: cost + latency).
"""
import asyncio
import random
from datetime import timedelta

from sqlmodel import Session, select

from . import config
from .bus import agent_queue, bus, sim_running
from .catalog import find_valid_substitutes
from .db import active_brand, engine, next_id
from .kpi import compute_kpis
from .models import Customer, Incident, Order, Product, utcnow

KINDS_WEIGHTED = [
    ("out_of_stock", 30), ("payment_failed", 25), ("lost_parcel", 20),
    ("vip_complaint", 15), ("return_request", 10),
]

TEMPLATES: dict[str, list[str]] = {
    "out_of_stock": [
        "Bonjour, j'ai commandé {product} et je reçois un mail de rupture de stock ?? J'en ai besoin pour ce week-end.",
        "Votre site m'a laissé payer {product} alors qu'il n'est plus disponible. Que proposez-vous ?",
        "Rupture de stock après commande, sérieusement ? Je veux une solution rapide pour {product}.",
        "Bonjour, commande {order} : article indisponible d'après votre mail. Je fais quoi maintenant ?",
    ],
    "payment_failed": [
        "Mon paiement pour la commande {order} a été refusé alors que ma carte fonctionne ailleurs. Pouvez-vous vérifier ?",
        "Impossible de finaliser le paiement de {product}, ça échoue à chaque fois. C'est agaçant.",
        "Bonjour, échec de paiement sur {order}. Est-ce que ma commande est perdue ?",
        "Le paiement ne passe pas depuis ce matin pour ma commande {order}. Une idée ?",
    ],
    "lost_parcel": [
        "Cela fait plus d'une semaine que ma commande {order} est « expédiée » et toujours rien. Où est mon colis ?",
        "Le suivi de {order} n'a pas bougé depuis 8 jours. Je commence à croire qu'il est perdu.",
        "Bonjour, colis {order} introuvable, le transporteur ne répond pas. J'attends {product} depuis trop longtemps.",
        "Toujours aucune livraison pour {order}. C'était un cadeau, je suis très déçue.",
    ],
    "vip_complaint": [
        "Je suis cliente fidèle depuis des années et l'expérience sur ma dernière commande {order} est indigne de votre maison. J'attends un geste.",
        "Très déçu du service sur {order}. Vu ce que je dépense chez vous chaque année, je m'attendais à mieux.",
        "C'est la troisième fois que j'ai un problème. {order} encore en retard. Je songe sérieusement à aller voir ailleurs.",
        "Votre service client ne répond plus. En tant que cliente VIP, je trouve cela inacceptable. Commande {order}.",
    ],
    "return_request": [
        "Bonjour, je souhaite retourner {product} (commande {order}), la teinte ne me convient pas. Comment procéder ?",
        "L'article {product} est arrivé abîmé, l'emballage était ouvert. Je veux le retourner. Commande {order}.",
        "Puis-je échanger {product} ? Ce n'est pas ce que j'imaginais. Commande {order}.",
        "Quelle est votre politique de retour pour {product} ? Je l'ai reçu il y a 5 jours. Commande {order}.",
    ],
}

SUMMARIES = {
    "out_of_stock": "Rupture de stock sur {product}",
    "payment_failed": "Paiement échoué — {order} ({amount}€)",
    "lost_parcel": "Colis perdu — {order}",
    "vip_complaint": "Cliente VIP mécontente — {customer}",
    "return_request": "Demande de retour — {product}",
}


def _pick_kind(rng: random.Random) -> str:
    kinds, weights = zip(*KINDS_WEIGHTED)
    return rng.choices(kinds, weights=weights, k=1)[0]


def select_out_of_stock_product(products: list[Product], required_quantity: int,
                                rng: random.Random) -> Product:
    """Pick the product that will go out of stock.

    Products are weighted by how many valid same-category substitutes they have, so
    incidents that have a credible alternative occur more often -- but products with
    no alternative can still be picked, keeping refund a genuine possible outcome.
    No product is hardcoded and no substitution is ever guaranteed.
    """
    weights: list[float] = []
    for product in products:
        others = [p for p in products if p.id != product.id]
        valid = find_valid_substitutes(product, others, required_quantity)
        weights.append(1 + 4 * min(len(valid), 3))
    return rng.choices(products, weights=weights, k=1)[0]


def create_incident(kind: str, rng: random.Random | None = None) -> Incident:
    """Creates an order + incident of the given kind. Sync (called from async via to_thread or directly)."""
    rng = rng or random.Random()
    with Session(engine) as session:
        brand_id = active_brand()["id"]
        brand_products = session.exec(
            select(Product).where(Product.brand == brand_id, Product.stock > 0)
        ).all()
        customers = session.exec(select(Customer)).all()
        if kind == "vip_complaint":
            customers = [c for c in customers if c.tier == "vip"]
        customer = rng.choice(customers)
        qty = rng.randint(1, 2)
        if kind == "out_of_stock":
            product = select_out_of_stock_product(brand_products, qty, rng)
        else:
            product = rng.choice(brand_products)
        amount = round(product.price * qty, 2)

        status = {"out_of_stock": "pending", "payment_failed": "pending"}.get(kind, "shipped")
        order = Order(
            id=next_id(session, Order, "ORD"),
            customer_id=customer.id, product_id=product.id, quantity=qty,
            amount=amount, status=status,
        )
        if kind == "lost_parcel":
            order.created_at = utcnow() - timedelta(days=rng.randint(8, 14))
        if kind == "out_of_stock":
            product.stock = 0
            session.add(product)
        session.add(order)
        session.commit()

        severity = "high" if customer.tier == "vip" or amount > 200 else rng.choice(["low", "medium", "medium"])
        fmt = {"product": product.name, "order": order.id, "amount": amount, "customer": customer.name}
        incident = Incident(
            id=next_id(session, Incident, "INC", 0),
            order_id=order.id, kind=kind, severity=severity,
            summary=SUMMARIES[kind].format(**fmt),
            customer_message=rng.choice(TEMPLATES[kind]).format(**fmt),
        )
        session.add(incident)
        session.commit()
        session.refresh(incident)
        return incident


def incident_payload(incident: Incident) -> dict:
    """Serializes an incident (+ order context) for the WebSocket."""
    with Session(engine) as session:
        order = session.get(Order, incident.order_id)
        customer = session.get(Customer, order.customer_id) if order else None
        product = session.get(Product, order.product_id) if order else None
    return {
        "id": incident.id, "kind": incident.kind, "severity": incident.severity,
        "summary": incident.summary, "customerMessage": incident.customer_message,
        "status": incident.status, "createdAt": incident.created_at.isoformat(),
        "resolutionKind": incident.resolution_kind, "savedAmount": incident.saved_amount,
        "order": {
            "id": order.id, "amount": order.amount, "status": order.status,
            "productName": product.name if product else "?",
            "customerName": customer.name if customer else "?",
            "customerTier": customer.tier if customer else "standard",
        } if order else None,
    }


async def emit_incident(incident: Incident) -> None:
    """Publish + enqueue for the agent. Shared by simulator and the GraphQL inject mutation."""
    await bus.publish("incident_created", incident_payload(incident))
    await agent_queue.put(incident.id)


async def simulator_loop() -> None:
    rng = random.Random()
    sim_running["value"] = config.SIM_AUTOSTART
    while True:
        await asyncio.sleep(config.TICK_SECONDS)
        if not sim_running["value"]:
            continue
        try:
            if rng.random() < config.INCIDENT_RATIO:
                incident = create_incident(_pick_kind(rng), rng)
                await emit_incident(incident)
            else:
                with Session(engine) as session:
                    customer = rng.choice(session.exec(select(Customer)).all())
                    products = [p for p in session.exec(select(Product)).all() if p.stock > 0]
                    if not products:
                        continue
                    product = rng.choice(products)
                    qty = rng.randint(1, 3)
                    order = Order(
                        id=next_id(session, Order, "ORD"),
                        customer_id=customer.id, product_id=product.id, quantity=qty,
                        amount=round(product.price * qty, 2), status="paid",
                    )
                    product.stock -= qty
                    session.add(order)
                    session.add(product)
                    session.commit()
                    payload = {
                        "orderId": order.id, "customerName": customer.name,
                        "productName": product.name, "amount": order.amount,
                    }
                await bus.publish("order_created", payload)
                await bus.publish("kpi_update", compute_kpis())
        except Exception as exc:  # the simulator must never die
            print(f"[simulator] error: {exc}")
