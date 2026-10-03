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
and it reaches the questions plain SQL makes hard to get right:

- **Composition** — a definition builds on others by name, through its
  imports; every answer traces back, rule by rule, to the source tables.
- **[Knowledge graphs](https://synalinks.github.io/synalog/knowledge-graphs/)** — entities and
  relationships modelled over the tables you already have: no ETL, no graph
  database, no data moved.
- **[Temporal knowledge graphs](https://synalinks.github.io/synalog/knowledge-graphs/#temporal-graphs)** —
  edges that carry when they were true: what holds today, what held on any date.
- **[Recursion](https://synalinks.github.io/synalog/language/recursion/)** — transitive closures, paths,
  shortest paths, cycles, with termination guaranteed.
- **[Negation, unions](https://synalinks.github.io/synalog/language/syntax/), [aggregation](https://synalinks.github.io/synalog/language/aggregation/)
  and [functors](https://synalinks.github.io/synalog/language/functors/)** — what is *not* there, alternatives,
  top-k, and generic rules instantiated for each input.
- **[Verified before it runs](https://synalinks.github.io/synalog/verification/)** — safety, negation,
  aggregation, stratification, arity, recursion and unknown references are
  checked before any SQL is generated: this is what *formally verified* means
  here.
- **[Every warehouse](https://synalinks.github.io/synalog/engines/), [in milliseconds](https://synalinks.github.io/synalog/benchmark/)** —
  one definition compiles to each engine's dialect, by a Rust engine fast
  enough for an agent to check every rule it writes.

Each is shown as layer files — front matter, imports, `@OrderBy` — in the
[modelling patterns](skills/semantic-layers/references/patterns.md) and the
[example layers](layers/).

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
- **The [synalog](https://github.com/SynaLinks/synalog) CLI**: runs any
  definition from its layer's folder.

## Supported engines

DuckDB, SQLite, PostgreSQL, Trino, Presto, Databricks and BigQuery — every
engine [synalog supports](https://synalinks.github.io/synalog/engines/), with
the drivers it needs. A layer's `synalog.toml` names its engine;
`semantic-layers connect --help` lists each engine's connection fields, and
the secret ones go to the layer's git-ignored `.env`.

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
uvx semantic-layers init sales --description "Orders and customers"   # tables/, concepts/, rules/, synalog.toml, README, git
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
and are released as an open format.

Several questions remain open — merging upstream changes into a modified
layer, binding a shared layer to tables whose names or columns differ, and
letting one layer import another's definitions. They are listed in the
[specification](docs/specification.md#open-questions). Contributions are
welcome: see [Development](docs/development.md) to run the tests, the linter
and the documentation locally.

## License

Apache 2.0 — see [LICENSE](LICENSE).
