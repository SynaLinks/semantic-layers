# Semantic Layers

A simple, open format for giving AI agents your business definitions as
verified, executable code.

## What are semantic layers?

A semantic layer is a folder of business definitions — *an active customer*,
*revenue*, *a late order* — each written as a
[synalog](https://github.com/SynaLinks/synalog) predicate that compiles to SQL
and runs on your database. Every definition is one `.l` file: YAML front
matter (`name` and `description`) followed by the definition.

```shell
sales/
├── tables/           # The data: one file per table, generated from the database
├── concepts/         # What the data is about: entities, relationships, clean views
├── rules/            # What you want to know: counts, rates, rankings, trends
├── layer.toml        # What the layer is, and the database it runs on
└── .env              # The password or token (local, never committed)
```

`rules/ActiveCustomer.l`

```prolog
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
formally verified** predicates the agent **runs**.

## Why semantic layers?

Ask three agents for "active customers" and you get three SQL queries, each
plausible, each different. Written guidance can describe the right definition,
but each agent still re-derives it in its own words, every time. A semantic
layer packages the definitions themselves:

- **One meaning, everywhere**: every agent that runs a definition computes the
  same rows, on any database synalog targets.
- **Verified knowledge**: every definition is checked before it is saved,
  and its `@Assert` statements are checked against the data.
- **A layer that grows with use**: a missing definition is written by the
  agent, on top of the ones already there, and reviewed like code.
- **Portable**: a layer is a folder in a git repository, installed in any
  project with one command and connected to that project's database.

[Why semantic layers](why.md) tells the longer story.

## How do semantic layers work?

Agents load semantic layers through **progressive disclosure**, in three
stages:

1. **Discovery**: a layer grows to thousands of definitions — too many to list
   in the agent's context — so the agent **searches** their `name`,
   `keywords` and `description` with a regular expression built from the
   question (`semantic-layers search 'churn|retention'`), and gets back the
   few that fit.
2. **Activation**: when a definition fits, the agent reads it — and the
   definitions it imports — into context.
3. **Execution**: the agent runs the definition on the database and answers
   from its rows. When none fits, it writes one, verified before it is saved.

Only search results reach the context, and definitions only when a question
calls for them, so a layer of thousands of definitions costs a few lines of
context.

## Where can I use semantic layers?

- **Any coding agent**: `semantic-layers add` installs layers into
  `.agents/layers/` and tells the agent how to use them, in `AGENTS.md` (and
  `CLAUDE.md` for Claude Code). See [Coding agents](agents.md).
- **Agents that support [Agent Skills](https://agentskills.io)**: the
  `semantic-layers` skill teaches searching, running and writing definitions.
- **Your own agent**: [Adding layer support](agent-support.md) walks through
  discovery, search, execution and verification, step by step.
- **The command line**: `uvx semantic-layers run sales/Revenue` runs any
  definition from its layer's folder.

## Open development

The format, the `semantic-layers` command and the example layers are
developed in the open, under the Apache 2.0 license, at
[github.com/SynaLinks/semantic-layers](https://github.com/SynaLinks/semantic-layers).
Contributions — layers, fixes, ideas — are welcome as issues and pull
requests.

## Get started

- [Getting started](getting-started.md): install a layer, connect it, ask.
- [Quickstart](creating/quickstart.md): write your first layer in five minutes,
  no database needed.
- [Specification](specification.md): the format, file by file.
- [Examples](examples.md): two layers to read and install.
