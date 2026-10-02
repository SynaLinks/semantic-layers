"""Reading and verifying layers: names, imports, helpers and recursion."""

from samples import write

from semantic_layers.layers import verify


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
        "RepeatBuyer(customer_id:, n? += 1) distinct :- Delivered(customer_id:);\n"
    )
    (rules / "RepeatBuyer.l").write_text(
        "---\nname: RepeatBuyer\ndescription: Delivered orders per customer.\n---\n" + helper
    )
    assert verify(source / "sales") == []
    (rules / "RepeatBuyer.l").write_text("---\nname: Nope\n---\n" + helper)
    assert verify(source / "sales") == [
        "rules/RepeatBuyer.l: its front matter names 'Nope', which it does not define (Delivered, RepeatBuyer)"
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
        "rules/TeamSize.l: its front matter names 'Team', which it does not define (Manages, TeamSize)"
    ]
