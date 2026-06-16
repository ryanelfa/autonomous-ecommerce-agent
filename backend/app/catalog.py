"""Shared catalog logic: the single source of truth for substitute eligibility.

Both the incident simulator and the check_stock tool import find_valid_substitutes,
so they can never drift apart on what counts as a valid alternative.
"""
from typing import Protocol

# Same-category alternatives must stay within this relative price band.
PRICE_BAND = 0.30


class ProductLike(Protocol):
    """Minimal shape we need from a product (SQLModel rows satisfy this)."""
    id: str
    brand: str
    category: str
    price: float
    stock: int


def is_valid_substitute(source: ProductLike, candidate: ProductLike,
                        required_quantity: int) -> bool:
    """True when candidate can replace source: same brand, same category,
    different product, enough stock for the ordered quantity, and a unit
    price within +/-30% of the source price.
    """
    if candidate.id == source.id:
        return False
    if candidate.brand != source.brand:
        return False
    if candidate.category != source.category:
        return False
    if candidate.stock < required_quantity:
        return False
    lo = source.price * (1 - PRICE_BAND)
    hi = source.price * (1 + PRICE_BAND)
    return lo <= candidate.price <= hi


def find_valid_substitutes(source: ProductLike, candidates: list[ProductLike],
                           required_quantity: int) -> list[ProductLike]:
    """Return every candidate that is a valid substitute for the source product."""
    return [c for c in candidates if is_valid_substitute(source, c, required_quantity)]
