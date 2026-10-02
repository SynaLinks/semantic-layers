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
                "---\nname: BigRevenue\n---\nimport tables.Orders.Orders;\n\n"
                "Segment(customer_id:) distinct :- Orders(customer_id:);\n"
                "Big(customer_id:) distinct :- Orders(customer_id:, amount:), amount > 100;\n"
                "SegmentRevenue(revenue? += amount) distinct :- Segment(customer_id:), Orders(customer_id:, amount:);\n"
                "BigRevenue := SegmentRevenue(Segment: Big);\n"
            ),
        },
    )
    assert verify(layer) == []


def test_the_project_name_must_be_the_folder_name(tmp_path):
    layer = write(tmp_path / "shop", {"rules/X.l": '---\nname: X\n---\n@OrderBy(X, "a");\nX(a: 1);\n'})
    (layer / "synalog.toml").write_text('[project]\nname = "store"\n')
    assert verify(layer) == ["synalog.toml: names the layer 'store', but its folder is 'shop' — they must match"]
    (layer / "synalog.toml").write_text('[project]\nname = "shop"\n')
    assert verify(layer) == []
