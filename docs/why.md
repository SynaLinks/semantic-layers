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
  stratification, unknown references — before it is saved, and runs its
  assertions against the data; a definition that doesn't check never lands.
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
- **[Assertions](https://synalinks.github.io/synalog/assertions/)** — what a
  definition must satisfy, stated in first-order logic (one row per customer,
  a share between 0 and 1, every order tied to a known customer) and checked
  against the data: a counterexample names the rows a rule gets wrong.
- **[Every warehouse](https://synalinks.github.io/synalog/engines/), [in milliseconds](https://synalinks.github.io/synalog/benchmark/)** —
  one definition compiles to each engine's dialect, by a Rust engine fast
  enough for an agent to check every rule it writes.

Each is shown as layer files — front matter, imports, `@OrderBy` — in the
[modelling patterns](https://github.com/SynaLinks/semantic-layers/blob/main/skills/semantic-layers/references/patterns.md) and the
[example layers](examples.md).

