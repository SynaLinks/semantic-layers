# Semantic Layers

A standardized way to give AI agents reasoning and meaning over of your data.

## What are Semantic Layers?

Semantic Layers are a lightweight, open format for giving AI agents your
business definitions — *an active customer*, *revenue*, *a late order* — as
verified, composable and executable code instead of prose, unlocking reasoning and meaning at scale.

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

```
---
name: ActiveCustomer
description: Customers with at least one delivered order.
---
import concepts.Customer.Customer;
import tables.Orders.Orders;

ActiveCustomer(customer_id:) distinct :-
  Customer(customer_id:), Orders(customer_id:, status: "delivered");
```

Where an [Agent Skill](https://agentskills.io) is a `SKILL.md` the agent
reads and follows (hopefully), a Semantic Layer is a set of 
**deterministic & formally verified** predicates the agent **runs**. 
It **never** make mistakes interpreting them, and can 
**reuses and combines** them over time without any loss. 

A project's layers sit side by side in `.agents/layers/`.

## Powered by synalog

Definitions are written in [synalog](https://github.com/SynaLinks/synalog), a
logic programming language from the Datalog family that compiles to optimized
SQL. A semantic layer is a folder; synalog is what makes the folder *run* —
and it reaches the questions that plain SQL makes hard to get right.

### Instant knowledge graphs from your tables

A handful of concepts turn relational tables into a knowledge graph. Nodes
are entities and categorical values, `distinct` projections of the tables;
edges are relationships between nodes — typed, weighted, symmetric, inverse
— and traversals compose them. In a layer, nodes and edges are concepts and
traversals are rules. The graph is virtual: no ETL, no graph database, no
data moved — it compiles to SQL over the tables you already have, the moment
the concepts are written.

```prolog
# Nodes: entities and categorical values, straight from the tables.
Supplier(supplier_id:, name:) distinct :- Suppliers(supplier_id:, name:);
Product(product_id:, name:) distinct :- Products(product_id:, name:);
Category(category:) distinct :- Products(category:);

# Edges between nodes.
Supplies(supplier_id:, product_id:) distinct :-
  Supplier(supplier_id:), Product(product_id:), Purchases(supplier_id:, product_id:);
InCategory(product_id:, category:) distinct :-
  Product(product_id:), Category(category:), Products(product_id:, category:);

# A traversal: the categories that depend on each supplier, two hops away.
SupplierExposure(supplier_id:, category:) distinct :-
  Supplies(supplier_id:, product_id:), InCategory(product_id:, category:);
```

### Temporal knowledge graphs

Edges can carry the period they were true, so the graph answers *when*, not
just *what*. Source systems usually log changes only: a period lasts until
the next change, and the latest one is still open. From there, what holds
today, what held on any date, and whether two periods overlap are plain
filters — not a bespoke query each time.

```prolog
# Each change lasts until the next one for the same person...
NextChange(person_id:, changed_at:, next? Min= later) distinct :-
  Assignments(person_id:, changed_at:), Assignments(person_id:, changed_at: later),
  later > changed_at;

# ...so the log becomes a temporal edge, the latest period still open.
MemberOf(person_id:, team_id:, valid_from:, valid_to:) distinct :-
  Assignments(person_id:, team_id:, changed_at: valid_from),
  NextChange(person_id:, changed_at: valid_from, next: valid_to);
MemberOf(person_id:, team_id:, valid_from:, valid_to:) distinct :-
  Assignments(person_id:, team_id:, changed_at: valid_from),
  ~NextChange(person_id:, changed_at: valid_from), valid_to == "9999-12-31";

# The graph today, and as it was on any date.
MemberToday(person_id:, team_id:) distinct :-
  MemberOf(person_id:, team_id:, valid_from:, valid_to:),
  Today(date:), valid_from <= date, date < valid_to;
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

```prolog
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

```prolog
Dormant(customer_id:) :- Customers(customer_id:), ~Orders(customer_id:);
Contactable(customer_id:, channel:) distinct :-
  Customers(customer_id:, email:), email is not null, channel == "email" |
  Customers(customer_id:, phone:), phone is not null, channel == "phone";
TopProduct(product_id? ArgMax= product_id -> amount) distinct :- Orders(product_id:, amount:);
```

### Composition and reuse

A predicate builds on others by name — `import concepts.Customer.Customer;`
— so knowledge accumulates instead of being re-derived: `Revenue` builds on
`DeliveredOrder`, which builds on `Orders`. Functors instantiate a generic
rule for another input (`EnterpriseRevenue := SegmentRevenue(Segment:
EnterpriseCustomers)`). The imports are the layer's dependency graph: every
answer traces back, rule by rule, to the source tables.

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
  `.agents/layers/` and tells the agent how to use them — through a companion
  Agent Skill and a section of `AGENTS.md` — so Claude Code, and every agent
  that reads Agent Skills or `AGENTS.md`, runs them with the synalog CLI.
- **[Lemma](https://github.com/SynaLinks/lemma)**: a workspace is a
  set of semantic layers — its own, plus layers installed from repositories,
  each on its own database — versioned with git, searched and run by its
  analyst and, over MCP and A2A, by any agent.
- **The [synalog](https://github.com/SynaLinks/synalog) CLI**: runs any
  definition from its layer's folder.

## Getting started

```shell
uvx semantic-layers add SynaLinks/semantic-layers-examples --layer sales
uvx semantic-layers connect sales psql host=db.example.com database=sales user=analyst password=...
```

Then ask your coding agent about your sales.

To write your own layer, start a layer project:

```shell
uvx semantic-layers init sales          # tables/, concepts/, rules/, synalog.toml, .gitignore, README, git
cd sales
uvx semantic-layers connect . psql host=db.example.com database=sales user=analyst password=...
```

Write your definitions in `concepts/` and `rules/`, check them with
`semantic-layers check .`, and push the repository: it installs with
`semantic-layers add <owner>/sales`.

- **[Specification](docs/specification.md)** — Format details
- **[Sharing](docs/sharing.md)** — Installing, connecting, publishing and updating layers with the `semantic-layers` command
- **[Agent Skills](https://agentskills.io)** — The format semantic layers are modeled on

## Open development

Semantic Layers were developed by [Synalinks](https://github.com/SynaLinks)
for Lemma, its proprietary harness, and are released as an open format. 

Open question, merging pstream changes into a modified layer, binding a 
shared layer to tables whose names or columns differ, letting one layer
import another's definitions are listed in the [specification](docs/specification.md#open-questions);
contributions are welcome.

## License

Apache 2.0.
