# Getting started

Install a semantic layer in your project, connect it to your database, and
let your coding agent answer from it.

## Prerequisites

- [uv](https://docs.astral.sh/uv/): `semantic-layers` and synalog run with
  `uvx`, nothing else to install.
- A database synalog connects to: PostgreSQL, Trino, Presto, Databricks or
  BigQuery. No database at hand? The [Quickstart](creating/quickstart.md)
  runs a layer on a CSV file instead.
- A coding agent that reads `AGENTS.md` or `CLAUDE.md`.

!!! note "Before the first PyPI release"
    Until `semantic-layers` is published, run it from the repository:
    `uvx --from git+https://github.com/SynaLinks/semantic-layers semantic-layers ...`.

## Install a layer

Install the example `sales` layer from this repository:

```shell
uvx semantic-layers add SynaLinks/semantic-layers --layer sales
```

`add` copied the layer into `.agents/layers/sales/`, verified every
definition, recorded it in `semantic-layers-lock.json`, and told your coding
agent about it in a section of `AGENTS.md` (and of `CLAUDE.md` for Claude
Code).

## Connect it

`connect` runs inside the layer's folder:

```shell
cd .agents/layers/sales
uvx semantic-layers connect psql host=db.example.com database=sales user=analyst password=...
```

It wrote the database into the layer's `layer.toml` and the password into
its `.env` — kept out of git — then generated `tables/` from your database
and checked every definition against it: a table or column your database
lacks, or an assertion its data violates, is listed.

## Ask

Ask your agent about your sales — *"which countries bring the most
revenue?"*. It searches the definitions, runs the one that fits and answers
from its rows. Or run one yourself:

```shell
cd .agents/layers/sales
uvx synalog rules/RevenueByCountry.l run RevenueByCountry
```

## How it works

1. **Discovery**: the agent searched the layer with a pattern built from the
   question — `uvx semantic-layers search 'revenue|country'` — and got back
   `sales/rules/RevenueByCountry.l` and its description.
2. **Activation**: it read that file, and the files it imports, to check it
   means what the question means.
3. **Execution**: it ran the definition on your database and answered from
   the rows, naming the definition it ran.

When no definition fits, the agent writes one in the layer, checks it with
`semantic-layers check`, and only then answers from it: the next question
reuses it.

## Next steps

- [Quickstart](creating/quickstart.md): write a layer of your own.
- [Sharing](sharing.md): install from any repository, keep layers up to date.
- [Coding agents](agents.md): what the agent is told, and the Agent Skill.
