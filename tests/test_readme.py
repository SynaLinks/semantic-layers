"""The README's examples are a layer's files: written out with the tables
they use, every one verifies."""

import re
from pathlib import Path

from samples import write

from semantic_layers.layers import verify

ROOT = Path(__file__).resolve().parents[1]
#: "`concepts/X.l`", a blank line, then the file in a code block.
_FILE = re.compile(r"^`((?:concepts|rules|tables)/\w+\.l)`\n\n```prolog\n(.*?)```", re.M | re.S)
TABLES = {
    "tables/Suppliers.l": "Suppliers(supplier_id:, name:) :- suppliers(supplier_id:, name:);",
    "tables/Products.l": "Products(product_id:, name:, category:) :- products(product_id:, name:, category:);",
    "tables/Purchases.l": "Purchases(supplier_id:, product_id:) :- purchases(supplier_id:, product_id:);",
    "tables/Assignments.l": "Assignments(person_id:, team_id:, changed_at:) :- assignments(person_id:, team_id:, changed_at:);",
    "tables/Routes.l": "Routes(origin:, destination:, cost:) :- routes(origin:, destination:, cost:);",
    "tables/Customers.l": "Customers(customer_id:, email:, phone:) :- customers(customer_id:, email:, phone:);",
    "tables/Orders.l": "Orders(customer_id:, product_id:, amount:) :- orders(customer_id:, product_id:, amount:);",
}


def test_readme_examples_verify(tmp_path):
    files = dict(_FILE.findall((ROOT / "README.md").read_text()))
    assert len(files) >= 10, "the README's example files were not found"
    tables = {path: f"---\nname: {Path(path).stem}\n---\n{decl}\n" for path, decl in TABLES.items()}
    layer = write(tmp_path / "readme", {**tables, **files})
    assert verify(layer) == []
