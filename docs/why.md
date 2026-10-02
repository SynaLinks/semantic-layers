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

The [synalog documentation](https://synalinks.github.io/synalog/) covers each in depth: [knowledge graphs](https://synalinks.github.io/synalog/knowledge-graphs/), [recursion](https://synalinks.github.io/synalog/language/recursion/), [temporal data](https://synalinks.github.io/synalog/language/temporal/), [verification](https://synalinks.github.io/synalog/verification/), [supported engines](https://synalinks.github.io/synalog/engines/).
