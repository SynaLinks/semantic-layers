"""The Agent Skill in skills/semantic-layers: well formed, its examples
verify, its example layer runs, its links resolve."""

import re
import subprocess
import sys
from pathlib import Path

import yaml
from samples import write

from semantic_layers.layers import verify

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "semantic-layers"
_FILE = re.compile(r"^`((?:concepts|rules|tables)/\w+\.l)`\n\n```(?:prolog)?\n(.*?)```", re.M | re.S)
TABLES = {
    "Orders": "Orders(order_id:, customer_id:, product_id:, status:, amount:, ordered_at:) :- "
    "orders(order_id:, customer_id:, product_id:, status:, amount:, ordered_at:);",
    "Customers": "Customers(customer_id:, country:, tier:, email:, phone:) :- "
    "customers(customer_id:, country:, tier:, email:, phone:);",
    "Products": "Products(product_id:, name:, category:) :- products(product_id:, name:, category:);",
    "Employees": "Employees(employee_id:, manager_id:) :- employees(employee_id:, manager_id:);",
    "Routes": "Routes(origin:, destination:, cost:) :- routes(origin:, destination:, cost:);",
    "Assignments": "Assignments(person_id:, team_id:, changed_at:) :- assignments(person_id:, team_id:, changed_at:);",
}


def test_skill_front_matter():
    text = (SKILL / "SKILL.md").read_text()
    meta = yaml.safe_load(text.split("---")[1])
    assert meta["name"] == SKILL.name and re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", meta["name"])
    assert 0 < len(meta["description"]) <= 1024


def test_skill_examples_verify(tmp_path):
    """Every file shown in the skill, written into one layer with the tables
    the patterns use, verifies."""
    files = {}
    for page in [SKILL / "SKILL.md", *sorted((SKILL / "references").glob("*.md"))]:
        files.update(_FILE.findall(page.read_text()))
    assert len(files) > 15
    tables = {f"tables/{n}.l": f"---\nname: {n}\n---\n{d}\n" for n, d in TABLES.items()}
    assert verify(write(tmp_path / "skill", {**tables, **files})) == []


def test_example_layer_runs():
    layer = SKILL / "examples" / "supply-chain"
    assert verify(layer) == []
    loads = [f"--load={t}=data/{t}.csv" for t in ("suppliers", "parts", "bill_of_materials")]
    run = subprocess.run(
        [sys.executable, "-m", "synalog.cli", "rules/CriticalSuppliers.l", "run", "CriticalSuppliers", "--csv", *loads],
        cwd=layer,
        capture_output=True,
        text=True,
    )
    assert run.returncode == 0, run.stderr
    assert run.stdout.splitlines() == [
        "supplier_id,name,assemblies",
        "1,Acme Bolts,3",
        "3,Steelworks,2",
        "2,Rubber Co,2",
    ]


def test_links_resolve():
    for page in SKILL.rglob("*.md"):
        for target in re.findall(r"\]\(([^)#:]+)(?:#[^)]*)?\)", page.read_text()):
            assert (page.parent / target).exists(), f"{page.relative_to(ROOT)} links to missing {target}"
