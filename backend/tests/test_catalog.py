"""Catalog-quality and weighted-selector tests. No Anthropic, no DB, no incidents."""
import json
import random
import unittest
from dataclasses import dataclass
from pathlib import Path

from app.catalog import find_valid_substitutes
from app.simulator import select_out_of_stock_product

BRANDS_FILE = Path(__file__).resolve().parents[1] / "brands.json"
MIN_COVERAGE = 0.70


@dataclass
class FakeProduct:
    """Stand-in product so tests never touch the database."""
    id: str
    brand: str
    category: str
    price: float
    stock: int


def load_products(brand: dict) -> list[FakeProduct]:
    return [
        FakeProduct(id=f"{brand['id']}-{i}", brand=brand["id"],
                    category=p["category"], price=float(p["price"]), stock=int(p["stock"]))
        for i, p in enumerate(brand["products"])
    ]


def coverage(products: list[FakeProduct]) -> tuple[float, list[FakeProduct]]:
    """Share of products that have >=1 valid substitute, plus the ones that have none."""
    uncovered = [
        p for p in products
        if not find_valid_substitutes(p, [o for o in products if o.id != p.id], 1)
    ]
    rate = 1 - len(uncovered) / len(products) if products else 0.0
    return rate, uncovered


class CatalogCoverageTest(unittest.TestCase):
    def test_coverage_per_brand(self) -> None:
        data = json.loads(BRANDS_FILE.read_text(encoding="utf-8"))
        for brand in data["brands"]:
            products = load_products(brand)
            rate, uncovered = coverage(products)
            print(f"\n[{brand['name']}] substitute coverage: {rate:.0%} "
                  f"({len(products) - len(uncovered)}/{len(products)})")
            if uncovered:
                print("  no valid substitute:",
                      ", ".join(brand["products"][int(p.id.split('-')[-1])]["name"] for p in uncovered))
            self.assertGreaterEqual(rate, MIN_COVERAGE,
                                    f"{brand['name']} coverage {rate:.0%} below {MIN_COVERAGE:.0%}")


class WeightedSelectorTest(unittest.TestCase):
    def test_products_with_substitutes_selected_more_often(self) -> None:
        # Two products share a category and price band (each is the other's substitute);
        # a third sits alone in its category (no substitute).
        products = [
            FakeProduct("A", "x", "cat1", 100, 10),
            FakeProduct("B", "x", "cat1", 110, 10),
            FakeProduct("C", "x", "cat2", 100, 10),
        ]
        rng = random.Random(1234)
        counts = {"A": 0, "B": 0, "C": 0}
        for _ in range(6000):
            chosen = select_out_of_stock_product(products, 1, rng)
            counts[chosen.id] += 1
        # A and B have a substitute, C does not -> each of A/B picked more than C,
        # but C is still reachable (never guaranteed away).
        self.assertGreater(counts["A"], counts["C"])
        self.assertGreater(counts["B"], counts["C"])
        self.assertGreater(counts["C"], 0)
        print(f"\n[selector] A={counts['A']} B={counts['B']} C={counts['C']} (C has no substitute)")


if __name__ == "__main__":
    unittest.main(verbosity=2)
