<div align="center">
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="img/semantic-layers-dark.svg">
  <img height="200" alt="Semantic Layers" src="img/semantic-layers-light.svg">
</picture>
</div>

<br>

<div align="center">

![Alpha](https://img.shields.io/badge/Release-Alpha-orange.svg)
[![Tests](https://github.com/synalinks/semantic-layers/actions/workflows/tests.yml/badge.svg)](https://github.com/synalinks/semantic-layers/actions/workflows/tests.yml)
[![Documentation](https://github.com/synalinks/semantic-layers/actions/workflows/docs.yml/badge.svg)](https://synalinks.github.io/semantic-layers/)
[![Discord](https://img.shields.io/discord/1118241178723291219?logo=discord&logoColor=white&label=Discord&cacheSeconds=3600)](https://discord.gg/82nt97uXcM)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-green.svg)](https://opensource.org/license/apache-2-0)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/synalinks/semantic-layers)

</div>

<br>

# Semantic Layers
## A standardized way to give AI agents reasoning and meaning over your data

Semantic Layers are built on [synalog](https://github.com/SynaLinks/synalog), by
[Synalinks](https://github.com/SynaLinks). New here? [Why semantic
layers](https://synalinks.github.io/semantic-layers/why/) makes the case;
[Getting started](https://synalinks.github.io/semantic-layers/getting-started/)
installs one in two commands.

Full documentation: **<https://synalinks.github.io/semantic-layers/>**

## What are Semantic Layers?

Semantic Layers are a lightweight, open format for giving AI agents your
business definitions — *an active customer*, *revenue*, *a late order* — as
verified, composable and executable code instead of prose.

At its core, a semantic layer is a folder holding three folders: `tables/`,
`concepts/` and `rules/`. Each holds one [synalog](https://github.com/SynaLinks/synalog)
`.l` file per definition, with YAML front matter (`name` and `description`,
at minimum) followed by the definition, which compiles to SQL and runs on your
database.

```
my-layer/
├── tables/           # The data: one file per table, generated from the database
├── concepts/         # What the data is about: entities, relationships, clean views
├── rules/            # What you want to know: counts, rates, rankings, trends
├── synalog.toml      # The database it runs on (secrets stay in .env)
└── .env              # The password or token (local, never committed)
```

Here is an example of a predicate, the atomic definition of a semantic layer.

`rules/ActiveCustomer.l`

```
---
name: ActiveCustomer
description: Customers with at least one delivered order.
---
import concepts.Customer.Customer;
import tables.Orders.Orders;

@OrderBy(ActiveCustomer, "customer_id");
ActiveCustomer(customer_id:) distinct :-
  Customer(customer_id:), Orders(customer_id:, status: "delivered");
```

Where an [Agent Skill](https://agentskills.io) is a set of instructions an
agent reads and interprets, a semantic layer is a set of **deterministic,
formally verified** predicates the agent **runs**. A definition is executed,
not paraphrased, so every agent computes the same result from it — and
definitions compose: new ones build on existing ones without losing meaning.

A project's layers live side by side in `.agents/layers/`.

## Powered by synalog

Definitions are written in [synalog](https://github.com/SynaLinks/synalog), a
logic programming language from the Datalog family that compiles to optimized
SQL. A semantic layer is a folder; synalog is what makes the folder *run* —
and it reaches the questions that plain SQL makes hard to get right.

Each example below is shown as a layer's files — path, front matter,
imports — the way a layer stores it; a helper used by one predicate only
stays in that predicate's file.

### Instant knowledge graphs from your tables

A handful of concepts turn relational tables into a knowledge graph — no
ETL, no graph database, no data moved: it compiles to SQL over the tables
you already have, the moment the concepts are written. Nodes are
`distinct` projections of the tables; edges are typed relationships between
nodes, weighted when the data says how much; recursive edges follow them to
any depth; traversals compose them. In a layer, nodes and edges are concepts
and traversals are rules.

Take a supply chain — suppliers, parts, and a bill of materials saying which
assembly contains which component. *If a supplier fails, which of our
assemblies stop?* The answer runs through every level of the bill of
materials: the bolt is in the wheel, the wheel is in the bike.

`concepts/Supplier.l`

```
---
name: Supplier
description: A supplier, as a node.
---
import tables.Suppliers.Suppliers;

@OrderBy(Supplier, "supplier_id");
Supplier(supplier_id:, name:, country:) distinct :- Suppliers(supplier_id:, name:, country:);
```

`concepts/Part.l`

```
---
name: Part
description: A part, bought or assembled in house, as a node.
---
import tables.Parts.Parts;

@OrderBy(Part, "part_id");
Part(part_id:, name:) distinct :- Parts(part_id:, name:);
```

`concepts/Supplies.l`

```
---
name: Supplies
description: The edge from a supplier to each part it supplies.
---
import concepts.Supplier.Supplier;
import concepts.Part.Part;
import tables.Parts.Parts;

@OrderBy(Supplies, "supplier_id", "part_id");
Supplies(supplier_id:, part_id:) distinct :-
  Supplier(supplier_id:), Part(part_id:), Parts(part_id:, supplier_id:);
```

`concepts/Contains.l`

```
---
name: Contains
description: The edge from an assembly to each component it contains, weighted by quantity.
---
import concepts.Part.Part;
import tables.BillOfMaterials.BillOfMaterials;

@OrderBy(Contains, "assembly_id", "component_id");
Contains(assembly_id:, component_id:, quantity:) distinct :-
  Part(part_id: assembly_id), Part(part_id: component_id),
  BillOfMaterials(assembly_id:, component_id:, quantity:);
```

`concepts/Requires.l`

```
---
name: Requires
description: An assembly requires a component, directly or inside a sub-assembly, at any depth.
---
import concepts.Contains.Contains;

@Recursive(Requires, 20);
@OrderBy(Requires, "assembly_id", "component_id");
Requires(assembly_id:, component_id:) distinct :- Contains(assembly_id:, component_id:);
Requires(assembly_id:, component_id:) distinct :-
  Requires(assembly_id:, component_id: middle), Contains(assembly_id: middle, component_id:);
```

`rules/SupplierExposure.l`

```
---
name: SupplierExposure
description: The assemblies that stop if a supplier fails, through every level of the bill of materials.
---
import concepts.Supplies.Supplies;
import concepts.Requires.Requires;

@OrderBy(SupplierExposure, "supplier_id", "assembly_id");
SupplierExposure(supplier_id:, assembly_id:) distinct :-
  Supplies(supplier_id:, part_id: component), Requires(assembly_id:, component_id: component);
```

### Temporal knowledge graphs

Edges can carry the period they were true, so the graph answers *when*, not
just *what*. Source systems usually log changes only: a period lasts until
the next change, and the latest one is still open. From there, what holds
today, what held on any date, and whether two periods overlap are plain
filters — not a bespoke query each time.

`concepts/MemberOf.l`

```
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
@OrderBy(MemberOf, "person_id", "valid_from");
MemberOf(person_id:, team_id:, valid_from:, valid_to:) distinct :-
  Assignments(person_id:, team_id:, changed_at: valid_from),
  NextChange(person_id:, changed_at: valid_from, next: valid_to);
MemberOf(person_id:, team_id:, valid_from:, valid_to:) distinct :-
  Assignments(person_id:, team_id:, changed_at: valid_from),
  ~NextChange(person_id:, changed_at: valid_from), valid_to == "9999-12-31";
```

`rules/MemberToday.l`

```
---
name: MemberToday
description: Who is in which team today.
---
import concepts.MemberOf.MemberOf;

@OrderBy(MemberToday, "person_id");
MemberToday(person_id:, team_id:) distinct :-
  MemberOf(person_id:, team_id:, valid_from:, valid_to:),
  Today(date:), valid_from <= date, date < valid_to;
```

`rules/MemberOn.l`

```
---
name: MemberOn
description: Who was in which team on 15 January 2026.
---
import concepts.MemberOf.MemberOf;

@OrderBy(MemberOn, "person_id");
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

```
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

@OrderBy(ShortestCost, "cost");
ShortestCost(destination:, cost? Min= cost) distinct :- RouteCost(destination:, cost:);
```

### Negation, unions and aggregation

`~` says what is *not* there — customers who never ordered, edges pointing
to nothing, the period still open — checked for safe negation and
stratification. `|` and multiple bodies union alternatives. Aggregations go
beyond sums and counts: `Min=`, `Max=`, `Avg=`, `List=`, `Set=`, `ArgMax=`,
`ArgMin=`, top-k.

`rules/Dormant.l`

```
---
name: Dormant
description: Customers who never ordered.
---
import tables.Customers.Customers;
import tables.Orders.Orders;

@OrderBy(Dormant, "customer_id");
Dormant(customer_id:) :- Customers(customer_id:), ~Orders(customer_id:);
```

`rules/Contactable.l`

```
---
name: Contactable
description: How to reach each customer, by email when there is one, else by phone.
---
import tables.Customers.Customers;

@OrderBy(Contactable, "customer_id");
Contactable(customer_id:, channel:) distinct :-
  Customers(customer_id:, email:), email is not null, channel == "email" |
  Customers(customer_id:, email:, phone:), email is null, phone is not null, channel == "phone";
```

`rules/TopProduct.l`

```
---
name: TopProduct
description: The product with the largest single order.
---
import tables.Orders.Orders;

@OrderBy(TopProduct, "product_id");
TopProduct(product_id? ArgMax= product_id -> amount) distinct :- Orders(product_id:, amount:);
```

### Ordered, bounded results

Results are paginated, so every concept and rule carries `@OrderBy`: without
a stable order, the same page comes back different between calls. `@Limit`
caps a ranking. Both compile into the SQL — `ORDER BY`, `LIMIT` — so the
database sorts and stops, not the agent:

`rules/TopCustomers.l`

```
---
name: TopCustomers
description: The ten customers who spent the most.
---
import tables.Orders.Orders;

@OrderBy(TopCustomers, "spent", "DESC");
@Limit(TopCustomers, 10);
TopCustomers(customer_id:, spent? += amount) distinct :- Orders(customer_id:, amount:);
```

### Composition and reuse

A predicate builds on others by name — `import concepts.Customer.Customer;`
— so knowledge accumulates instead of being re-derived: in the
[`sales` example layer](layers/sales/), `Revenue` builds on `DeliveredOrder`,
which builds on `Orders`. The imports are the layer's
dependency graph: every answer traces back, rule by rule, to the source
tables. A functor instantiates a generic rule for another input: write the
generic rule once — here the revenue of a segment, every customer by
default — and apply it wherever a segment needs it:

`rules/SegmentRevenue.l`

```
---
name: SegmentRevenue
description: Revenue of a segment of customers; every customer unless a functor swaps the segment.
---
import tables.Customers.Customers;
import tables.Orders.Orders;

Segment(customer_id:) distinct :- Customers(customer_id:);

@OrderBy(SegmentRevenue, "revenue");
SegmentRevenue(revenue? += amount) distinct :- Segment(customer_id:), Orders(customer_id:, amount:);
```

`concepts/EnterpriseCustomer.l`

```
---
name: EnterpriseCustomer
description: Customers on the enterprise tier.
---
import tables.Customers.Customers;

@OrderBy(EnterpriseCustomer, "customer_id");
EnterpriseCustomer(customer_id:) distinct :- Customers(customer_id:, tier: "enterprise");
```

`rules/EnterpriseRevenue.l`

```
---
name: EnterpriseRevenue
description: Revenue of enterprise customers.
---
import concepts.EnterpriseCustomer.EnterpriseCustomer;
import rules.SegmentRevenue.SegmentRevenue;

@OrderBy(EnterpriseRevenue, "revenue");
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

## Why Semantic Layers?

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

## How do Semantic Layers work?

Agents load semantic layers through **progressive disclosure**, as with Agent
Skills, in three stages:

1. **Discovery**: Agents search. A semantic layer grows to thousands of
   definitions — too many to list in context, as Agent Skills list theirs —
   so the agent searches the `name`, `keywords` and `description` of every
   definition with a regular expression built from the question
   (`semantic-layers search 'churn|retention'`), and gets back the few that
   fit.

2. **Activation**: When a question matches a definition, the agent reads it —
   and the definitions it imports — into context.

3. **Execution**: The agent runs the definition on the database and answers
   from its rows. When no definition fits, it writes one, verified before it
   is saved.

Only search results reach the context, and definitions only when a question
calls for them, so a layer can hold thousands of them with a small context
footprint.

## Where can I use Semantic Layers?

- **Any coding agent**: `semantic-layers add` installs layers into
  `.agents/layers/` and tells the agent how to use them — a section of
  `AGENTS.md`, and of `CLAUDE.md` for Claude Code — so every coding agent
  searches and runs them with the synalog CLI.
- **[The `semantic-layers` Agent Skill](skills/semantic-layers/)**: teaches a
  coding agent the whole loop — search, read, run, answer, and write the
  definitions that are missing — with the synalog it needs, modelling
  patterns, every error message and a runnable example layer:
  `npx skills add SynaLinks/semantic-layers`.
- **[Lemma](https://github.com/SynaLinks/lemma)**: a workspace is a
  set of semantic layers — its own, plus layers installed from repositories,
  each on its own database — versioned with git, searched and run by its
  analyst and, over MCP and A2A, by any agent.
- **The [synalog](https://github.com/SynaLinks/synalog) CLI**: runs any
  definition from its layer's folder.

## Supported engines

A layer runs on the database its `synalog.toml` names; synalog compiles every
definition to that engine's SQL dialect and runs it there.

| Engine | `engine` | Connection fields | Driver |
|---|---|---|---|
| DuckDB | `duckdb` | none: runs in memory, data files loaded with `--load` | included |
| SQLite | `sqlite` | none: runs in memory, data files loaded with `--load` | standard library |
| PostgreSQL | `psql` | `host`, `port`, `database`, `user`, `password`\*, `sslmode`, `schema` | `psycopg` |
| Trino | `trino` | `host`, `port`, `scheme`, `catalog`, `schema`, `user`, `auth`, `password`\* | `trino` |
| Presto | `presto` | `host`, `port`, `scheme`, `catalog`, `schema`, `user`, `auth`, `password`\* | `presto-python-client` |
| Databricks | `databricks` | `server_hostname`, `http_path`, `access_token`\*, `catalog`, `schema` | `databricks-sql-connector` |
| BigQuery | `bigquery` | `project`, `dataset`, `credentials`\*, `location` | `google-cloud-bigquery` |

\* Secrets never go in `synalog.toml`: `semantic-layers connect` writes them to
the layer's git-ignored `.env`. Run synalog with the engine's driver
alongside, e.g. `uvx --with psycopg synalog rules/Revenue.l run Revenue`.

## Getting started

```shell
uvx semantic-layers add SynaLinks/semantic-layers --layer sales
uvx semantic-layers connect sales psql host=db.example.com database=sales user=analyst password=...
```

This installs the example `sales` layer into `.agents/layers/`, connects it
to your database and generates its tables. Then ask your coding agent about
your sales.

To write your own layer, start a layer project:

```shell
uvx semantic-layers init sales          # tables/, concepts/, rules/, synalog.toml, .gitignore, README, git
cd sales
uvx semantic-layers connect . psql host=db.example.com database=sales user=analyst password=...
```

Write your definitions in `concepts/` and `rules/`, check them with
`semantic-layers check .`, and push the repository: anyone can then install it
with `semantic-layers add <owner>/sales`.

## Documentation

- **[Getting started](docs/getting-started.md)** — Install a layer, connect it, write your own
- **[Specification](docs/specification.md)** — The format, file by file
- **[Sharing](docs/sharing.md)** — Installing, connecting, publishing and updating layers
- **[Agents](docs/agents.md)** — How coding agents are told about the layers
- **[CLI](docs/cli.md)** — Every `semantic-layers` command
- **[Examples](layers/)** — The `sales` and `support` example layers
- **[Agent Skills](https://agentskills.io)** — The format semantic layers are modeled on

## Open development

Semantic Layers were developed by [Synalinks](https://github.com/SynaLinks)
for Lemma, its commercial agent harness, and are released as an open format.

Several questions remain open — merging upstream changes into a modified
layer, binding a shared layer to tables whose names or columns differ, and
letting one layer import another's definitions. They are listed in the
[specification](docs/specification.md#open-questions). Contributions are
welcome: see [Development](docs/development.md) to run the tests, the linter
and the documentation locally.

## License

Apache 2.0 — see [LICENSE](LICENSE).
