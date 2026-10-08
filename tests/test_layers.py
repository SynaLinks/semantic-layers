"""Reading and verifying layers: names, imports, helpers and recursion."""

import shutil
from pathlib import Path

import synalog
from samples import write
from synalog import checking, runners

from semantic_layers.connect import write_connection
from semantic_layers.layers import check, verify


def test_imports_stay_inside_the_layer(source):
    (source / "support" / "rules" / "Mixed.l").write_text(
        "---\nname: Mixed\n---\nimport tables.Orders.Orders;\n\nMixed(order_id:) :- Orders(order_id:);\n"
    )
    assert any("Mixed" in error for error in verify(source / "support"))
    assert verify(source / "sales") == []


def test_name_is_the_predicate_that_runs(source):
    rules = source / "sales" / "rules"
    helper = (
        "import tables.Orders.Orders;\n\n"
        'Delivered(order_id:, customer_id:) :- Orders(order_id:, customer_id:, status: "delivered");\n'
        '@OrderBy(RepeatBuyer, "customer_id");\n'
        "RepeatBuyer(customer_id:, n? += 1) distinct :- Delivered(customer_id:);\n"
    )
    (rules / "RepeatBuyer.l").write_text(
        "---\nname: RepeatBuyer\ndescription: Delivered orders per customer.\n---\n" + helper
    )
    assert verify(source / "sales") == []
    (rules / "RepeatBuyer.l").write_text("---\nname: Nope\n---\n" + helper)
    assert verify(source / "sales") == [
        "rules/RepeatBuyer.l: [ Error ] Front matter names 'Nope', which this file does not define (Delivered, RepeatBuyer)."
    ]
    (rules / "RepeatBuyer.l").write_text("---\ndescription: x\n---\n" + helper)
    assert "has no name" in verify(source / "sales")[0]


def test_recursive_intermediate_rule(tmp_path):
    layer = write(
        tmp_path / "hr",
        {
            "tables/Employees.l": "---\nname: Employees\n---\nEmployees(employee_id:, manager_id:) :- employees(employee_id:, manager_id:);\n",
            "rules/TeamSize.l": (
                "---\nname: TeamSize\ndescription: People under each manager.\n---\n"
                "import tables.Employees.Employees;\n\n"
                "@Recursive(Manages, 10);\n"
                "Manages(manager_id:, employee_id:) distinct :- Employees(employee_id:, manager_id:);\n"
                "Manages(manager_id:, employee_id:) distinct :-\n"
                "  Manages(manager_id:, employee_id: middle), Employees(employee_id:, manager_id: middle);\n\n"
                '@OrderBy(TeamSize, "team_size", "DESC");\n'
                "TeamSize(manager_id:, team_size? += 1) distinct :- Manages(manager_id:);\n"
            ),
        },
    )
    assert verify(layer) == []
    path = layer / "rules" / "TeamSize.l"
    path.write_text(path.read_text().replace("name: TeamSize", "name: Team"))
    assert verify(layer) == [
        "rules/TeamSize.l: [ Error ] Front matter names 'Team', which this file does not define (Manages, TeamSize)."
    ]


def test_invalid_front_matter_is_reported_not_raised(tmp_path):
    layer = write(tmp_path / "shop", {"rules/X.l": "---\nname: X\ndescription: A thing: broken.\n---\nX(a: 1);\n"})
    assert verify(layer) == [
        "rules/X.l: [ Error ] Invalid front matter YAML: mapping values are not allowed in this context."
    ]


def test_a_functor_defines_its_predicate(tmp_path):
    layer = write(
        tmp_path / "shop",
        {
            "tables/Orders.l": "---\nname: Orders\n---\nOrders(customer_id:, amount:) :- orders(customer_id:, amount:);\n",
            "rules/BigRevenue.l": (
                "---\nname: BigRevenue\ndescription: Revenue of the big orders.\n---\nimport tables.Orders.Orders;\n\n"
                "Segment(customer_id:) distinct :- Orders(customer_id:);\n"
                "Big(customer_id:) distinct :- Orders(customer_id:, amount:), amount > 100;\n"
                "SegmentRevenue(revenue? += amount) distinct :- Segment(customer_id:), Orders(customer_id:, amount:);\n"
                '@OrderBy(BigRevenue, "revenue");\n'
                "BigRevenue := SegmentRevenue(Segment: Big);\n"
            ),
        },
    )
    assert verify(layer) == []


def test_the_project_name_must_be_the_folder_name(tmp_path):
    layer = write(
        tmp_path / "shop", {"rules/X.l": '---\nname: X\ndescription: One.\n---\n@OrderBy(X, "a");\nX(a: 1);\n'}
    )
    (layer / "layer.toml").write_text('[project]\nname = "store"\ndescription = "A shop."\n')
    assert verify(layer) == ["layer.toml: names the layer 'store', but its folder is 'shop' — they must match"]
    (layer / "layer.toml").write_text('[project]\nname = "shop"\ndescription = "A shop."\n')
    assert verify(layer) == []


def test_a_layer_must_describe_itself(tmp_path):
    layer = write(
        tmp_path / "shop", {"rules/X.l": '---\nname: X\ndescription: One.\n---\n@OrderBy(X, "a");\nX(a: 1);\n'}
    )
    (layer / "layer.toml").write_text('[project]\nname = "shop"\n')
    assert verify(layer) == ["layer.toml: [project] has no description — say what the layer is about"]
    (layer / "layer.toml").unlink()
    assert verify(layer) == ["layer.toml is missing: a layer says what it is in its [project] (name, description)"]


def test_parse_splits_front_matter_and_body():
    from semantic_layers.layers import parse

    meta, body = parse("---\nname: X\ndescription: An x.\n---\nimport tables.T.T;\n\nX(a:) :- T(a:);\n")
    assert meta == {"name": "X", "description": "An x."}
    assert body == "import tables.T.T;\n\nX(a:) :- T(a:);\n"
    assert parse("X(a: 1);\n") == ({}, "X(a: 1);\n")


def test_check_runs_the_assertions_on_the_layers_database(tmp_path, monkeypatch):
    """A connected layer's check runs its @Assert statements on its database:
    a refund counted as a sale makes a country's revenue negative."""
    layer = tmp_path / "sales"
    shutil.copytree(Path(__file__).resolve().parents[1] / "layers" / "sales", layer)
    write_connection(layer, "psql", {"host": "db.example.com", "database": "sales", "user": "analyst"})
    data = {
        "customers": "customer_id,country\n1,FR\n2,DE\n",
        "orders": "order_id,customer_id,status,amount,ordered_at\n"
        "1,1,delivered,30,2026-01-02\n2,2,delivered,-50,2026-01-03\n",
    }
    loads = []
    for table, rows in data.items():
        (tmp_path / f"{table}.csv").write_text(rows)
        loads.append((table, str(tmp_path / f"{table}.csv")))
    # The layer's PostgreSQL stands as an in-memory DuckDB holding the tables
    # above, the assertions compiled for it.
    sessions = []

    def session(engine, connection, _loads=()):
        sessions.append((engine, connection["host"]))
        return runners.session("duckdb", None, loads)

    plan_for = synalog.plan
    monkeypatch.setattr(checking, "session", session)
    monkeypatch.setattr(
        checking._synalog,
        "plan",
        lambda source, predicate, engine=None, **kw: plan_for(source, predicate, engine="duckdb", **kw),
    )

    assert check(layer) == ([], [])  # offline: the assertions wait for data
    assert sessions == []
    errors, warnings = check(layer, assertions=True)
    assert warnings == []
    assert len(errors) == 1
    assert errors[0].startswith("rules/RevenueByCountry.l: Assertion 'RevenueByCountry.positive' is violated")
    assert errors[0].endswith('counterexamples (c): ("DE")')
    assert ("psql", "db.example.com") in sessions  # through the layer's own connection
