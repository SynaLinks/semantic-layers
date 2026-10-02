# Getting started

You need [uv](https://docs.astral.sh/uv/) — `semantic-layers` and synalog run
with `uvx`, nothing else to install.

## Use a layer

Install the example `sales` layer into your project, then connect it to your
database:

```shell
uvx semantic-layers add SynaLinks/semantic-layers --layer sales
uvx semantic-layers connect sales psql host=db.example.com database=sales user=analyst password=...
```

`add` copied the layer into `.agents/layers/sales/`, verified it, and told
your coding agent about it (a companion skill and a section of `AGENTS.md`).
`connect` wrote the layer's `synalog.toml` — the database, as plain fields —
and its `.env` — the password, kept out of git — then generated `tables/`
from your database and checked every definition against it.

Ask your agent about your sales: it searches the definitions, runs the one
that fits and answers from its rows. Or run one yourself:

```shell
cd .agents/layers/sales
uvx synalog rules/RevenueByCountry.l run RevenueByCountry
```

## Write your own

```shell
uvx semantic-layers init sales          # tables/, concepts/, rules/, synalog.toml, .gitignore, README, git
cd sales
uvx semantic-layers connect . psql host=db.example.com database=sales user=analyst password=...
```

Write each definition as one `.l` file — concepts in `concepts/`, rules in
`rules/` — with front matter naming the predicate that runs:

```prolog
--8<-- "layers/sales/rules/RevenueByCountry.l"
```

Check everything, then push the repository:

```shell
uvx semantic-layers check .
git add -A && git commit -m "Revenue by country" && git push
```

Anyone installs it with `uvx semantic-layers add <owner>/sales`.
