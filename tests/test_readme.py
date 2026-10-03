"""The examples of the README and the docs are a layer's files: written out
with the tables they use, every one verifies."""

import re
from pathlib import Path

import pytest
from samples import write

from semantic_layers.layers import verify

ROOT = Path(__file__).resolve().parents[1]
#: "`concepts/X.l`", a blank line, then the file in a code block.
_FILE = re.compile(r"^`((?:concepts|rules|tables)/\w+\.l)`\n\n```(?:prolog)?\n(.*?)```", re.M | re.S)
#: What the examples build on without showing it.
SUPPORT = {
    "tables/Suppliers.l": "Suppliers(supplier_id:, name:, country:) :- suppliers(supplier_id:, name:, country:);",
    "tables/Parts.l": "Parts(part_id:, name:, supplier_id:) :- parts(part_id:, name:, supplier_id:);",
    "tables/BillOfMaterials.l": (
        "BillOfMaterials(assembly_id:, component_id:, quantity:) :- bill_of_materials(assembly_id:, component_id:, quantity:);"
    ),
    "tables/Assignments.l": "Assignments(person_id:, team_id:, changed_at:) :- assignments(person_id:, team_id:, changed_at:);",
    "tables/Routes.l": "Routes(origin:, destination:, cost:) :- routes(origin:, destination:, cost:);",
    "tables/Customers.l": "Customers(customer_id:, email:, phone:, tier:) :- customers(customer_id:, email:, phone:, tier:);",
    "tables/Orders.l": "Orders(customer_id:, product_id:, amount:, status:) :- orders(customer_id:, product_id:, amount:, status:);",
    "tables/Employees.l": "Employees(employee_id:, manager_id:) :- employees(employee_id:, manager_id:);",
    "concepts/Customer.l": (
        "import tables.Orders.Orders;\n\n"
        '@OrderBy(Customer, "customer_id");\nCustomer(customer_id:) distinct :- Orders(customer_id:);'
    ),
}
PAGES = ["README.md", "docs/index.md", "docs/specification.md"]


@pytest.mark.parametrize("page", PAGES)
def test_examples_verify(page, tmp_path):
    files = dict(_FILE.findall((ROOT / page).read_text()))
    assert files, f"no example file found in {page}"
    support = {
        path: f"---\nname: {Path(path).stem}\ndescription: Support.\n---\n{text}\n" for path, text in SUPPORT.items()
    }
    layer = write(tmp_path / "examples", {**support, **files})
    assert verify(layer) == []


def test_every_example_is_a_file():
    """No synalog example without its path and front matter."""
    for page in [*PAGES, "docs/getting-started.md"]:
        text = (ROOT / page).read_text()
        for block in re.finditer(r"```(\w*)\n(.*?)```", text, re.S):
            if block.group(1) not in ("", "prolog") or ":-" not in block.group(2) and "--8<--" not in block.group(2):
                continue  # not a synalog example
            caption = text[: block.start()].rstrip().splitlines()[-1]
            assert re.fullmatch(r"`[\w/]+\.l`", caption), f"{page}: an example has no file path above it"
            assert block.group(2).startswith(("---\n", "--8<--")), f"{page}: an example has no front matter"


def test_every_concept_and_rule_is_ordered():
    """Results are paginated: every example concept and rule has its @OrderBy."""
    examples = [(page, path, text) for page in PAGES for path, text in _FILE.findall((ROOT / page).read_text())]
    examples += [("layers", str(p), p.read_text()) for p in (ROOT / "layers").glob("*/*/*.l")]
    for page, path, text in examples:
        if "tables/" in path:
            continue
        name = re.search(r"^name: (\w+)", text, re.M).group(1)
        assert f"@OrderBy({name}," in text, f"{page}: {path} has no @OrderBy"
