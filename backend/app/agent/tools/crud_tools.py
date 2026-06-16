"""Read tools (investigation) and action tools (terminal) operating on the SQLite db."""
import random
import string
from typing import Any

from sqlmodel import Session, select

from ...models import Customer, Incident, Order, Product, Ticket, utcnow
from ...db import next_id
from ...catalog import find_valid_substitutes
from .base import Tool


def _strict(props: dict, required: list[str]) -> dict:
    return {"type": "object", "properties": props, "required": required, "additionalProperties": False}


class GetOrder(Tool):
    name = "get_order"
    description = "Fetch full details of an order: amount, quantity, status, product and customer ids."
    input_schema = _strict({"order_id": {"type": "string"}}, ["order_id"])

    async def execute(self, db: Session, order_id: str) -> dict[str, Any]:
        order = db.get(Order, order_id)
        if not order:
            return {"ok": False, "error": "order_not_found"}
        product = db.get(Product, order.product_id)
        return {
            "ok": True, "order_id": order.id, "status": order.status,
            "amount": order.amount, "quantity": order.quantity,
            "customer_id": order.customer_id,
            "product": {"product_id": product.id, "name": product.name,
                        "category": product.category, "price": product.price} if product else None,
            "created_at": order.created_at.isoformat(),
        }


class GetCustomer(Tool):
    name = "get_customer"
    description = "Fetch a customer's profile: name, tier (standard/vip) and lifetime value in euros."
    input_schema = _strict({"customer_id": {"type": "string"}}, ["customer_id"])

    async def execute(self, db: Session, customer_id: str) -> dict[str, Any]:
        customer = db.get(Customer, customer_id)
        if not customer:
            return {"ok": False, "error": "customer_not_found"}
        return {"ok": True, "name": customer.name, "tier": customer.tier,
                "lifetime_value": customer.lifetime_value}


class CheckStock(Tool):
    name = "check_stock"
    description = ("Check current stock for a product and list up to 3 valid same-category "
                   "alternatives within +/-30% of its price. Pass required_quantity with the "
                   "order quantity from get_order so only alternatives with enough stock are "
                   "returned (defaults to 1 if omitted).")
    input_schema = _strict({
        "product_id": {"type": "string"},
        "required_quantity": {"type": "integer", "minimum": 1},
    }, ["product_id"])

    async def execute(self, db: Session, product_id: str,
                      required_quantity: int = 1) -> dict[str, Any]:
        product = db.get(Product, product_id)
        if not product:
            return {"ok": False, "error": "product_not_found"}
        qty = max(1, int(required_quantity))
        candidates = db.exec(
            select(Product).where(
                Product.brand == product.brand,
                Product.category == product.category,
                Product.id != product.id,
            )
        ).all()
        alts = find_valid_substitutes(product, candidates, qty)[:3]
        return {
            "ok": True, "product_id": product.id, "stock": product.stock,
            "alternatives": [
                {"product_id": a.id, "name": a.name, "price": a.price, "stock": a.stock}
                for a in alts
            ],
        }


class RefundOrder(Tool):
    name = "refund_order"
    description = ("TERMINAL ACTION. Refund an order in full. Hard policy: never use for amounts "
                   "above 200 euros (escalate instead). Provide a short reason.")
    input_schema = _strict({"order_id": {"type": "string"}, "reason": {"type": "string"}},
                           ["order_id", "reason"])
    terminal = True

    async def execute(self, db: Session, order_id: str, reason: str) -> dict[str, Any]:
        order = db.get(Order, order_id)
        if not order:
            return {"ok": False, "error": "order_not_found"}
        if order.amount > 200:
            return {"ok": False, "error": "amount_exceeds_refund_policy_200eur"}
        order.status = "refunded"
        db.add(order)
        db.commit()
        return {"ok": True, "refunded_amount": order.amount}


class ProposeSubstitute(Tool):
    name = "propose_substitute"
    description = ("TERMINAL ACTION. Replace the ordered product by an in-stock substitute "
                   "(use check_stock first to find one). Price difference up to 15 euros is "
                   "offered to the customer; above that the customer pays the difference.")
    input_schema = _strict({
        "order_id": {"type": "string"},
        "substitute_product_id": {"type": "string"},
        "reason": {"type": "string"},
    }, ["order_id", "substitute_product_id", "reason"])
    terminal = True

    async def execute(self, db: Session, order_id: str, substitute_product_id: str,
                      reason: str) -> dict[str, Any]:
        order = db.get(Order, order_id)
        substitute = db.get(Product, substitute_product_id)
        if not order or not substitute:
            return {"ok": False, "error": "order_or_product_not_found"}
        if substitute.stock < order.quantity:
            return {"ok": False, "error": "substitute_out_of_stock"}
        old_amount = order.amount
        diff = round(substitute.price * order.quantity - old_amount, 2)
        order.product_id = substitute.id
        order.status = "replaced"
        substitute.stock -= order.quantity
        db.add(order)
        db.add(substitute)
        db.commit()
        return {
            "ok": True, "new_product_name": substitute.name,
            "price_difference": diff,
            "price_difference_offered": diff if 0 < diff <= 15 else 0.0,
        }
