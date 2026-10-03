"""Sample layers and helpers shared by the tests."""

from pathlib import Path

from semantic_layers import connect
from semantic_layers.connect import ordered
from semantic_layers.install import Scope

ORDERS = "Orders(order_id:, customer_id:, status:, amount:) :- orders(order_id:, customer_id:, status:, amount:);"
CUSTOMERS = "Customers(customer_id:, country:) :- customers(customer_id:, country:);"

SALES = {
    "tables/Orders.l": f"---\nname: Orders\ndescription: One row per order.\n---\n{ORDERS}\n",
    "tables/Customers.l": f"---\nname: Customers\n---\n{CUSTOMERS}\n",
    "concepts/Customer.l": (
        "---\nname: Customer\ndescription: Every customer who ordered.\n---\n"
        "import tables.Orders.Orders;\n\n"
        '@OrderBy(Customer, "customer_id");\n'
        "Customer(customer_id:) distinct :- Orders(customer_id:);\n"
    ),
    "rules/ActiveCustomer.l": (
        "---\nname: ActiveCustomer\ndescription: Customers with a delivered order.\n---\n"
        "import concepts.Customer.Customer;\nimport tables.Orders.Orders;\n\n"
        '@OrderBy(ActiveCustomer, "customer_id");\n'
        'ActiveCustomer(customer_id:) distinct :- Customer(customer_id:), Orders(customer_id:, status: "delivered");\n'
    ),
    "rules/OrdersByStatus.l": (
        "---\nname: OrdersByStatus\ndescription: Orders per status.\n---\n"
        "import tables.Orders.Orders;\n\n"
        '@OrderBy(OrdersByStatus, "status");\n'
        "OrdersByStatus(status:, n? += 1) distinct :- Orders(status:);\n"
    ),
}
SUPPORT = {
    "tables/Tickets.l": "---\nname: Tickets\n---\nTickets(ticket_id:, status:) :- tickets(ticket_id:, status:);\n",
    "rules/OpenTickets.l": (
        "---\nname: OpenTickets\ndescription: Tickets still open.\n---\n"
        "import tables.Tickets.Tickets;\n\n"
        '@OrderBy(OpenTickets, "ticket_id");\n'
        'OpenTickets(ticket_id:) distinct :- Tickets(ticket_id:, status: "open");\n'
    ),
}


def _ordered_table(text: str) -> str:
    """A table file with its declaration ordered, as `connect` writes it."""
    if text.startswith("---\n"):
        end = text.index("\n---\n", 4) + 5
        return text[:end] + ordered(text[end:])
    return ordered(text)


def write(root: Path, files: dict[str, str]) -> Path:
    """Write ``files`` under ``root``. A layer (files under tables/, concepts/
    or rules/) gets the synalog.toml every layer has, unless one is given,
    and its table files the @OrderBy `connect` writes, unless they have one."""
    if any(k.split("/")[0] in ("tables", "concepts", "rules") for k in files) and "synalog.toml" not in files:
        files = {**files, "synalog.toml": f'[project]\nname = "{root.name}"\ndescription = "A test layer."\n'}
    files = {k: _ordered_table(v) if k.startswith("tables/") and "@OrderBy" not in v else v for k, v in files.items()}
    for relative, text in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    return root


def scope(project):
    return Scope.resolve(project)


def layer(project):
    return project / ".agents" / "layers"


PG = {"host": "h", "database": "db", "user": "u", "password": "p"}


def connected_sales(project, orders=ORDERS):
    """The sales layer as `connect` leaves it: your tables and connection."""
    folder = layer(project) / "sales"
    write(folder, {"tables/Orders.l": f"---\nname: Orders\ndescription: Mine.\n---\n{orders}\n"})
    connect.write_connection(folder, "psql", PG)
    return folder
