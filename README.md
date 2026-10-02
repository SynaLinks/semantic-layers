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

```synalog
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
and what makes it worth more than a set of saved queries:

- **Definitions compose.** A predicate builds on other predicates by name
  (`import concepts.Customer.Customer;`), so knowledge accumulates instead of
  being re-derived: `Revenue` builds on `DeliveredOrder`, which builds on
  `Orders`. A complex question becomes a few small named predicates an agent
  can read, reuse and combine — and the imports are the layer's dependency
  graph, so every answer traces back, rule by rule, to the source tables.
- **Recursion is a base case and a recursive case.** Org charts, taxonomies,
  bills of materials, referral chains, approval paths — the questions that
  are notoriously wrong in hand-written SQL — are a few lines, and synalog
  guarantees they terminate:

  ```prolog
  @Recursive(Manages, 10);
  Manages(manager_id:, employee_id:) distinct :- Employees(employee_id:, manager_id:);
  Manages(manager_id:, employee_id:) distinct :-
    Manages(manager_id:, employee_id: middle), Employees(employee_id:, manager_id: middle);

  TeamSize(manager_id:, team_size? += 1) distinct :- Manages(manager_id:);
  ```

- **Your tables become a knowledge graph — without moving them.** A few
  concepts for entities and relationships (`Supplies`, `ReportsTo`,
  `WorksIn`) turn relational tables into a graph an agent traverses —
  composition, inverse, recursive chains — with no ETL and no graph database:
  the graph compiles to SQL over the tables you already have.
- **Time is first-class.** Validity windows, "active today", overlaps and
  point-in-time joins answer *what did this look like in March* — the
  reasoning that is most error-prone to express directly in SQL.
- **Nothing unsound runs.** synalog's verifier checks every definition
  before any SQL is generated — arity, safety, stratification, unknown
  references, termination — so a definition an agent writes that parses but
  is wrong is rejected up front, never discovered in a board meeting. This is
  what *formally verified* means here.
- **One definition, every warehouse.** The same `.l` file compiles to the
  dialect of DuckDB, SQLite, PostgreSQL, Trino, Presto, Databricks or
  BigQuery and runs where the data is, at warehouse scale: a layer written
  against one database installs on another.
- **Fast enough for the agent's inner loop.** synalog's engine is written in
  Rust: checking and compiling a definition takes milliseconds, so an agent
  can validate every rule it writes, every step.

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
