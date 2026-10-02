# Semantic Layers

Semantic Layers are a lightweight, open format for giving AI agents your
business definitions — *an active customer*, *revenue*, *a late order* — as
verified, executable code instead of prose, unlocking reasoning and meaning.

At its core, a semantic layer is a folder holding three folders: `tables/`,
`concepts/` and `rules/`. Each holds one [synalog](https://github.com/SynaLinks/synalog)
`.l` file per definition, with YAML front matter (`name` and `description`,
at minimum) followed by the definition, which compiles to SQL and runs on your
database.

```shell
my-layer/
├── tables/           # The data: one file per table, generated from the database
├── concepts/         # What the data is about: entities, relationships, clean views
├── rules/            # What you want to know: counts, rates, rankings, trends
├── synalog.toml      # The database it runs on (secrets stay in .env)
└── .env              # The password or token (local, never committed)
```

Here is an example of a predicate, the atomic structure of a semantic layer.

```prolog
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
reads and follows, a semantic layer is a set of **formally verified** definitions 
the agent **runs**: it never paraphrases a definition, it executes it on your data, 
removing interpretation mistakes and offering error-free composability. A
project's layers sit side by side in `.agents/layers/`.

## How they work

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

## Where to use them

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

## Next

- [Why semantic layers](why.md): the problem they solve.
- [Getting started](getting-started.md): install a layer, connect it, ask.
- [Specification](specification.md): the format, file by file.
