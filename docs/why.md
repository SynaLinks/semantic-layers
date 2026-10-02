# Why semantic layers

Ask three agents for "active customers" and you get three SQL queries, each
plausible, each different. Written guidance — a prompt, a wiki page, an Agent
Skill — can describe the right definition, but each agent still re-derives it
in its own words, **every time**. Semantic layers package the definitions
themselves into portable, version-controlled folders. This gives agents:

- **One meaning, everywhere**: Every agent that uses a definition computes the
  same thing, on any database synalog targets — DuckDB, SQLite, PostgreSQL,
  Trino, Presto, Databricks, BigQuery.
- **Verified knowledge**: synalog checks every definition formally — arity, safety,
  stratification, unknown references — before it is saved; a definition that
  doesn't check never lands.
- **A layer that grows with use**: When a question needs a definition that
  doesn't exist, the agent writes it, building on the ones already there —
  and every change is a git commit: who made it, what changed, a way back.
- **Cross-project reuse**: Build a layer once, share it as a folder in a git
  repository, and install it in any project — connected to that project's
  own database.

## What synalog enables

Definitions are written in [synalog](https://github.com/SynaLinks/synalog), a
logic programming language from the Datalog family that compiles to optimized
SQL. A semantic layer is a folder; synalog is what makes the folder *run* —
and it reaches the questions that plain SQL makes hard to get right.

Each example below is shown as a layer's files — path, front matter,
imports — the way a layer stores it; a helper used by one predicate only
stays in that predicate's file.

### Instant knowledge graphs from your tables

A handful of concepts turn relational tables into a knowledge graph. Nodes
are entities and categorical values, `distinct` projections of the tables;
edges are relationships between nodes — typed, weighted, symmetric, inverse
— and traversals compose them. In a layer, nodes and edges are concepts and
traversals are rules. The graph is virtual: no ETL, no graph database, no
data moved — it compiles to SQL over the tables you already have, the moment
the concepts are written.

`concepts/Supplier.l`

```prolog
---
name: Supplier
description: A supplier, as a node.
---
import tables.Suppliers.Suppliers;

Supplier(supplier_id:, name:) distinct :- Suppliers(supplier_id:, name:);
```

`concepts/Product.l`

```prolog
---
name: Product
description: A product, as a node.
---
import tables.Products.Products;

Product(product_id:, name:) distinct :- Products(product_id:, name:);
```

`concepts/Category.l`

```prolog
---
name: Category
description: A product category, a categorical column turned into a node.
---
import tables.Products.Products;

Category(category:) distinct :- Products(category:);
```

`concepts/Supplies.l`

```prolog
---
name: Supplies
description: The edge from a supplier to each product it supplies.
---
import concepts.Supplier.Supplier;
import concepts.Product.Product;
import tables.Purchases.Purchases;

Supplies(supplier_id:, product_id:) distinct :-
  Supplier(supplier_id:), Product(product_id:), Purchases(supplier_id:, product_id:);
```

`concepts/InCategory.l`

```prolog
---
name: InCategory
description: The edge from a product to its category.
---
import concepts.Product.Product;
import concepts.Category.Category;
import tables.Products.Products;

InCategory(product_id:, category:) distinct :-
  Product(product_id:), Category(category:), Products(product_id:, category:);
```

`rules/SupplierExposure.l`

```prolog
---
name: SupplierExposure
description: The categories that depend on each supplier, two hops away.
---
import concepts.Supplies.Supplies;
import concepts.InCategory.InCategory;

SupplierExposure(supplier_id:, category:) distinct :-
  Supplies(supplier_id:, product_id:), InCategory(product_id:, category:);
```

### Temporal knowledge graphs

Edges can carry the period they were true, so the graph answers *when*, not
just *what*. Source systems usually log changes only: a period lasts until
the next change, and the latest one is still open. From there, what holds
today, what held on any date, and whether two periods overlap are plain
filters — not a bespoke query each time.

`concepts/MemberOf.l`

```prolog
---
name: MemberOf
description: The edge from a person to their team, valid from valid_from until valid_to (9999-12-31 while it lasts).
---
import tables.Assignments.Assignments;

# Each change lasts until the next one for the same person...
NextChange(person_id:, changed_at:, next? Min= later) distinct :-
  Assignments(person_id:, changed_at:), Assignments(person_id:, changed_at: later),
  later > changed_at;

# ...and the latest one is still open.
MemberOf(person_id:, team_id:, valid_from:, valid_to:) distinct :-
  Assignments(person_id:, team_id:, changed_at: valid_from),
  NextChange(person_id:, changed_at: valid_from, next: valid_to);
MemberOf(person_id:, team_id:, valid_from:, valid_to:) distinct :-
  Assignments(person_id:, team_id:, changed_at: valid_from),
  ~NextChange(person_id:, changed_at: valid_from), valid_to == "9999-12-31";
```

`rules/MemberToday.l`

```prolog
---
name: MemberToday
description: Who is in which team today.
---
import concepts.MemberOf.MemberOf;

MemberToday(person_id:, team_id:) distinct :-
  MemberOf(person_id:, team_id:, valid_from:, valid_to:),
  Today(date:), valid_from <= date, date < valid_to;
```

`rules/MemberOn.l`

```prolog
---
name: MemberOn
description: Who was in which team on 15 January 2026.
---
import concepts.MemberOf.MemberOf;

MemberOn(person_id:, team_id:, date:) distinct :-
  MemberOf(person_id:, team_id:, valid_from:, valid_to:),
  date == "2026-01-15", valid_from <= date, date < valid_to;
```

### Recursion: transitive closure, paths, shortest paths, cycles

A base case and a recursive case give the transitive closure — org charts,
taxonomies, bills of materials, referral and approval chains — and, from
there, the route itself, the cheapest path (`Min=`), or the cycles in a
hierarchy. `@Recursive` bounds the depth, and the verifier guarantees
termination.

`rules/ShortestCost.l`

```prolog
---
name: ShortestCost
description: The cheapest shipping cost from the warehouse to each destination.
---
import tables.Routes.Routes;

# Every route cost from the warehouse, hop by hop (up to 10 hops).
@Recursive(RouteCost, 10);
RouteCost(destination:, cost:) :- Routes(origin: "warehouse", destination:, cost:);
RouteCost(destination:, cost: total) :-
  RouteCost(destination: hub, cost: hub_cost), Routes(origin: hub, destination:, cost:),
  total == hub_cost + cost;

ShortestCost(destination:, cost? Min= cost) distinct :- RouteCost(destination:, cost:);
```

### Negation, unions and aggregation

`~` says what is *not* there — customers who never ordered, edges pointing
to nothing, the period still open — checked for safe negation and
stratification. `|` and multiple bodies union alternatives. Aggregations go
beyond sums and counts: `Min=`, `Max=`, `Avg=`, `List=`, `Set=`, `ArgMax=`,
`ArgMin=`, top-k.

`rules/Dormant.l`

```prolog
---
name: Dormant
description: Customers who never ordered.
---
import tables.Customers.Customers;
import tables.Orders.Orders;

Dormant(customer_id:) :- Customers(customer_id:), ~Orders(customer_id:);
```

`rules/Contactable.l`

```prolog
---
name: Contactable
description: How to reach each customer, by email when there is one, else by phone.
---
import tables.Customers.Customers;

Contactable(customer_id:, channel:) distinct :-
  Customers(customer_id:, email:), email is not null, channel == "email" |
  Customers(customer_id:, phone:), phone is not null, channel == "phone";
```

`rules/TopProduct.l`

```prolog
---
name: TopProduct
description: The product with the largest single order.
---
import tables.Orders.Orders;

TopProduct(product_id? ArgMax= product_id -> amount) distinct :- Orders(product_id:, amount:);
```

### Composition and reuse

A predicate builds on others by name — `import concepts.Customer.Customer;`
— so knowledge accumulates instead of being re-derived: `Revenue` builds on
`DeliveredOrder`, which builds on `Orders`. The imports are the layer's
dependency graph: every answer traces back, rule by rule, to the source
tables. Within a file, a functor instantiates a generic rule for another
input — here the revenue of a segment, applied to enterprise customers:

`concepts/EnterpriseCustomer.l`

```prolog
---
name: EnterpriseCustomer
description: Customers on the enterprise tier.
---
import tables.Customers.Customers;

EnterpriseCustomer(customer_id:) distinct :- Customers(customer_id:, tier: "enterprise");
```

`rules/EnterpriseRevenue.l`

```prolog
---
name: EnterpriseRevenue
description: Revenue of enterprise customers.
---
import concepts.EnterpriseCustomer.EnterpriseCustomer;
import tables.Customers.Customers;
import tables.Orders.Orders;

# A generic rule: the revenue of a segment, every customer by default...
Segment(customer_id:) distinct :- Customers(customer_id:);
SegmentRevenue(revenue? += amount) distinct :- Segment(customer_id:), Orders(customer_id:, amount:);

# ...instantiated for one segment.
EnterpriseRevenue := SegmentRevenue(Segment: EnterpriseCustomer);
```

### Verified before it runs

synalog checks every definition before any SQL is generated — this is what
*formally verified* means here. A definition an agent writes that parses but
is wrong is rejected up front, never discovered in a board meeting:

| Check | Rejects |
|---|---|
| Safety | a result variable bound by nothing |
| Safe negation and aggregation | a negated or aggregated variable with no positive occurrence |
| Stratification | negation through recursion |
| Arity | a predicate used with inconsistent arguments |
| Recursion | a missing base case, a trivial loop, unbounded recursion |
| Unknown references | a predicate or table that does not exist |

### One definition, every warehouse — in milliseconds

The same `.l` file compiles to the dialect of DuckDB, SQLite, PostgreSQL,
Trino, Presto, Databricks or BigQuery and runs where the data is, at
warehouse scale: a layer written against one database installs on another.
The engine is written in Rust — checking and compiling take milliseconds —
so an agent can validate every rule it writes, at every step.

The [synalog documentation](https://synalinks.github.io/synalog/) covers each in depth: [knowledge graphs](https://synalinks.github.io/synalog/knowledge-graphs/), [recursion](https://synalinks.github.io/synalog/language/recursion/), [temporal data](https://synalinks.github.io/synalog/language/temporal/), [verification](https://synalinks.github.io/synalog/verification/), [supported engines](https://synalinks.github.io/synalog/engines/).
