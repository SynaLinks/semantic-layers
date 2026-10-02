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

