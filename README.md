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
## The Agent Skills of formally verified reasoning and knowledge work

Semantic Layers are built on [synalog](https://github.com/SynaLinks/synalog), by
[Synalinks](https://github.com/SynaLinks). Full documentation:
**<https://synalinks.github.io/semantic-layers/>**

## The Problem

Ask three agents for your number of "active customers" and you get three SQL
queries, each plausible, each different:

| Agent   | Decides an active customer is…                       | Answer |
| ------- | ---------------------------------------------------- | -----: |
| First   | anyone with an order in the last 90 days             |  4,812 |
| Second  | anyone with an order, cancelled ones included        |  6,307 |
| Third   | a row of `customers` whose `status` is `'active'`    |  5,140 |

None of them errs on the SQL. Each guessed a meaning your business already
settled — which orders count, which period, which column holds the truth —
and nothing tells you which guess you got. The same question asked tomorrow
may get another one.

Writing the meaning down does not fix it. A prompt, a wiki page, an Agent
Skill can *describe* the right definition, but the agent still re-derives it
in its own words, **every time**: a filter dropped, a join that duplicates
rows, a refund counted as a sale. And what one session learns — a correction,
a new metric — is gone at the next.

The questions that matter most are often shaped like a graph: *which
suppliers does this product depend on, through its whole bill of materials?*
*Who reports, directly or not, to this manager?* *How is this account
connected to that one?* SQL makes them hard to get right — a recursive query
per engine, a traversal that stops one level short, a cycle that never ends.
The usual answer is a knowledge graph in a graph database: an ETL pipeline
to copy the tables, a second store to keep in sync and secure, a second query
language — and agents that reason over a copy already out of date.

A semantic layer holds the definition itself, as code the agent **runs**:
checked before it runs, asserted against the data, and the same result from
every agent, every time. Entities and relationships are definitions too: the
knowledge graph is built over the tables you already have, traversed by
recursive rules compiled to SQL and run where the data lives — no data
moved, no graph database to maintain.

## What are Semantic Layers?

[Agent Skills](https://agentskills.io) gave agents an open format for
*procedures*: a folder of instructions an agent loads when a task calls for
it. Semantic Layers are the same idea for *knowledge*: a folder of
definitions — *an active customer*, *revenue*, *a late order* — and of the
rules that reason over them, loaded when a question calls for them.

Instructions suit procedures, which an agent adapts to the task at hand. They
do not suit definitions, which must mean the same thing every time. So where a
skill is read, a layer is run:

|                | Agent Skill                        | Semantic Layer                                          |
| -------------- | ---------------------------------- | ------------------------------------------------------- |
| **Packages**   | Procedures: how to do a task       | Knowledge: what things mean, and what follows from them |
| **Written as** | Instructions, in Markdown          | Predicates, in synalog                                  |
| **The agent**  | Reads and interprets it            | **Runs** it                                             |
| **The result** | Depends on the agent that reads it | **Deterministic**: the same from every agent            |
| **Checked**    | By review                          | **Formally**: before it runs, and against the data      |

The two work together: the [`semantic-layers` skill](skills/semantic-layers/)
teaches an agent how to use a layer, and the layer holds the knowledge it
reasons with.

A semantic layer is a folder holding three folders, with one
[synalog](https://github.com/SynaLinks/synalog) `.l` file per definition:

```
my-layer/
├── tables/           # The data: one file per table, generated from the database
├── concepts/         # What the data is about: entities, relationships, clean views
├── rules/            # What you want to know: counts, rates, rankings, trends
├── synalog.toml      # The database it runs on (secrets stay in .env)
└── .env              # The password or token (local, never committed)
```

A project's layers live in `.agents/layers/`, side by side with its skills in
`.agents/skills/`:

```
.agents/
├── skills/           # How to do things: Agent Skills, read by the agent
└── layers/           # What things mean: semantic layers, run by the agent
    ├── sales/
    └── support/
```

## From a question to an answer

A definition is a predicate: YAML front matter (`name` and `description`, at
minimum), what it builds on, what it must satisfy, and the rule itself.

`rules/ActiveCustomer.l`

```
---
name: ActiveCustomer
description: Customers with at least one delivered order.
keywords: [active, engaged, retained]
---
import concepts.Customer.Customer;
import concepts.DeliveredOrder.DeliveredOrder;

# Assertions (new in synalog 2.0): what the result must satisfy, whatever the
# rule below says. Each is a statement of first-order logic written as a Lean
# proposition: ∀ "for all", ∃ "there is", → "implies". synalog searches the
# data for counterexamples, and refuses to run the definition if it finds one.
@Assert(ActiveCustomer,
      # Every active customer is a customer.
      is_customer:  "∀ c, ActiveCustomer c → Customer c",
      # Every active customer has a delivered order o, of some amount a.
      has_delivery: "∀ c, ActiveCustomer c → ∃ o a, DeliveredOrder o c a");

# The rule: how the result is computed.
@OrderBy(ActiveCustomer, "customer_id");
ActiveCustomer(customer_id:) distinct :-
  Customer(customer_id:), DeliveredOrder(customer_id:);
```

Asked *"who are our active customers?"*, an agent does not write SQL. It
searches the layers for a definition that fits:

```
$ uvx semantic-layers search 'active|customer'
sales/rules/ActiveCustomer.l       Customers with at least one delivered order.
sales/concepts/Customer.l          Every customer who placed at least one order.
sales/concepts/DeliveredOrder.l    Orders that reached the customer — the ones that count as sales.
sales/rules/RevenueByCountry.l     Delivered revenue per customer country, largest first.
```

reads it, and runs it on the database:

```
$ uvx synalog rules/ActiveCustomer.l run ActiveCustomer
+-------------+
| customer_id |
+-------------+
| 10          |
| 11          |
+-------------+
2 rows
```

The answer comes from those rows. The definition was executed, not
paraphrased, so the next agent asked the same question gets the same
customers — and when no definition fits, the agent writes one, building on
the ones already there.

## What "formally verified" means

Two things are checked, neither by a model.

**The definition, before it runs.** synalog
[verifies](https://synalinks.github.io/synalog/verification/) every definition
before any SQL is generated: safety, negation, aggregation, stratification,
arity, recursion and unknown references. A definition that does not check is
never saved, and never run.

**Its result, against the data.** A rule says *how* to compute a predicate. An
assertion says *what the result must satisfy*, independently of the rule: a
customer appears once, a revenue is positive, shares add up to one, a
relationship is transitive.

Assertions are new in synalog 2.0, and are not written in synalog. They are
statements of first-order logic, written as [Lean](https://lean-lang.org/)
propositions — the notation of the Lean theorem prover, with the same operator
precedence, and an ASCII spelling for every symbol (`forall`, `exists`, `->`).
A predicate takes its arguments by position, as in Lean: with
`DeliveredOrder(order_id:, customer_id:, amount:)`, `DeliveredOrder o c a`
holds when order `o` of customer `c`, of amount `a`, was delivered. So

```
∀ c, ActiveCustomer c → ∃ o a, DeliveredOrder o c a
```

reads *for every `c`, if `c` is an active customer, then there is an order `o`
and an amount `a` such that `o` is a delivered order of `c`.*

synalog does not hand the statement to a model, nor to Lean. It compiles a
search for counterexamples to SQL and runs it on the database, like any
predicate. The assertion holds when the search returns no row:

```
$ uvx synalog rules/ActiveCustomer.l verify
✓ ActiveCustomer.is_customer holds
✓ ActiveCustomer.has_delivery holds
```

Had the rule forgotten the delivered-order condition, `has_delivery` would be
violated, and synalog would name the customer that breaks it. `run` checks a
definition's assertions before it prints anything, and refuses one that is
violated.

This matters most for definitions an agent writes. A rule and its assertion
state the same intent in two notations, so a mistake made in one is unlikely
to be repeated in the other: the assertion is the contract, stated first, and
the rule is written — and checked — against it.

Two limits, stated plainly. An assertion that holds has no counterexample *in
the data it ran on*: it is a check, not a proof, and says nothing about data
it has not seen. And neither check says a definition is the one your business
means — that is still yours to decide, once, in a file everyone can read.

## How do Semantic Layers work?

Agents load semantic layers through **progressive disclosure**, in three
stages:

1. **Discovery**: Agents search. A semantic layer grows to thousands of
   definitions — too many to list in context — so the agent searches the
   `name`, `keywords` and `description` of every definition with a regular
   expression built from the question
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

## Getting started

> Until `semantic-layers` is published on PyPI, run it from the repository:
> `uvx --from git+https://github.com/SynaLinks/semantic-layers semantic-layers ...`.

```shell
uvx semantic-layers add SynaLinks/semantic-layers --layer sales
cd .agents/layers/sales
uvx semantic-layers connect psql host=db.example.com database=sales user=analyst password=...
```

This installs the example `sales` layer into `.agents/layers/`, connects it
to your database and generates its tables. Then ask your coding agent about
your sales.

To write your own layer, start a layer project:

```shell
uvx semantic-layers init sales --description "Orders and customers"   # tables/, concepts/, rules/, synalog.toml, README, git
cd sales
uvx semantic-layers connect psql host=db.example.com database=sales user=analyst password=...
```

Write your definitions in `concepts/` and `rules/`, check them with
`semantic-layers check .` — their structure, and their assertions on your
database — and push the repository: anyone can then install it with
`semantic-layers add <owner>/sales`. The [Quickstart](docs/creating/quickstart.md)
walks through a first layer on a CSV file.

## Why Semantic Layers?

Semantic layers package definitions into portable, version-controlled
folders. This gives agents:

- **One meaning, everywhere**: Every agent that uses a definition computes the
  same thing, on any database synalog targets.
- **Verified knowledge**: Every definition is checked before it is saved, and
  its assertions against the data; a definition that doesn't check never
  lands.
- **A layer that grows with use**: When a question needs a definition that
  doesn't exist, the agent writes it, building on the ones already there —
  and every change is a git commit: who made it, what changed, a way back.
- **Cross-project reuse**: Build a layer once, share it as a folder in a git
  repository, and install it in any project — connected to that project's
  own database.

## Powered by synalog

Definitions are written in [synalog](https://github.com/SynaLinks/synalog), a
logic programming language from the Datalog family that compiles to optimized
SQL. A semantic layer is a folder; synalog is what makes the folder *run* —
and what lets a layer reason, not only count. This concept, from the
[supply-chain example](skills/semantic-layers/examples/supply-chain/), follows
a bill of materials to any depth:

`concepts/Requires.l`

```
---
name: Requires
description: An assembly requires a component, directly or inside a sub-assembly, at any depth.
keywords: [depends, requires]
---
import concepts.Contains.Contains;

@Recursive(Requires, 20);
@OrderBy(Requires, "assembly_id", "component_id");
Requires(assembly_id:, component_id:) distinct :- Contains(assembly_id:, component_id:);
Requires(assembly_id:, component_id:) distinct :-
  Requires(assembly_id:, component_id: middle), Contains(assembly_id: middle, component_id:);
```

A rule built on it answers *which assemblies stop if this supplier fails?* —
a question plain SQL makes hard to get right. synalog reaches the others like
it:

- **Composition** — a definition builds on others by name, through its
  imports; every answer traces back, rule by rule, to the source tables.
- **[Knowledge graphs](https://synalinks.github.io/synalog/knowledge-graphs/)** — entities and
  relationships modelled over the tables you already have, and
  [edges that carry when they were true](https://synalinks.github.io/synalog/knowledge-graphs/#temporal-graphs):
  no ETL, no graph database, no data moved.
- **[Recursion](https://synalinks.github.io/synalog/language/recursion/)** — transitive closures, paths,
  shortest paths, cycles, with termination guaranteed.
- **[Negation, unions](https://synalinks.github.io/synalog/language/syntax/), [aggregation](https://synalinks.github.io/synalog/language/aggregation/)
  and [functors](https://synalinks.github.io/synalog/language/functors/)** — what is *not* there, alternatives,
  top-k, and generic rules instantiated for each input.
- **[In milliseconds](https://synalinks.github.io/synalog/benchmark/)** — a Rust engine fast enough for an
  agent to check every rule it writes.

Each is shown as layer files — front matter, imports, `@OrderBy` — in the
[modelling patterns](skills/semantic-layers/references/patterns.md) and the
[example layers](layers/).

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
the drivers it needs. One definition compiles to each engine's dialect. A
layer's `synalog.toml` names its engine; `semantic-layers connect --help`
lists each engine's connection fields, and the secret ones go to the layer's
git-ignored `.env`.

## Documentation

- **[Getting started](docs/getting-started.md)** — Install a layer, connect it, ask
- **[Quickstart](docs/creating/quickstart.md)** — Write, check and run your first layer, no database needed
- **[Specification](docs/specification.md)** — The format, file by file
- **[Best practices](docs/creating/best-practices.md)** — Definitions that mean one thing and stay consistent
- **[Writing findable definitions](docs/creating/findable-definitions.md)** — Front matter that search finds, and how to test it
- **[Evaluating layers](docs/creating/evaluating.md)** — Assertions, and testing the answers
- **[Sharing](docs/sharing.md)** — Installing, connecting, publishing and updating layers
- **[Coding agents](docs/agents.md)** — How coding agents are told about the layers
- **[Adding layer support to your agent](docs/agent-support.md)** — Discovery, search, execution and verification, step by step
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
