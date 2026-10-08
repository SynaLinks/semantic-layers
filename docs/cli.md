# CLI

`semantic-layers` installs, connects, searches, runs and verifies layers. It is a
Python tool run with [uv](https://docs.astral.sh/uv/):

```shell
uvx semantic-layers <command> [options]
```

Run without a command, it shows the commands; in a terminal, `init`, `add`
and `search` open with the logo — never when a coding agent runs them.

## Commands

| Command | |
|---|---|
| `init [<name>]` | set up a layer project in `./<name>/`, or in the current folder, named after it: `-d` its description (asked in a terminal when not given), `-n` the name as an option, `--force` into a named folder that is not empty |
| `add <source>` | install layers from `owner/repo` on GitHub, a git URL or a folder; `--layer <name>` (repeatable), `--list`, `--force`, `--agent <name>`, `--all` |
| `connect [<engine> key=value ...]` | run in a layer's folder (it has a `layer.toml`): give the layer its database — or use the one in its `layer.toml` — generate its tables, check it |
| `list` | the installed layers and their state: `ok`, `modified`, `local` (yours), `missing` |
| `update` | update installed layers, keeping the ones you modified |
| `search <pattern>` | find definitions whose name, keywords or description match a regular expression (case-insensitive), name matches first; `--limit <n>`, `--tables` |
| `run <definition>` | check a definition, then run it on its layer's database: `<layer>/<Name>`, the path `search` prints, or `<Name>` inside a layer's folder; `--limit`, `--offset`, `--csv`, `--load TABLE=PATH` (in memory, on data files) |
| `check [<layer>]` | verify the installed layers with synalog, or one layer — by name or path (`.`); a connected layer's assertions run on its database; `--offline`, `--load TABLE=PATH` |

Every command takes `--global` (the user's layer, `~/.agents/layers/`) or
`--layers <folder>` (another layers folder).

## Examples

```shell
uvx semantic-layers add SynaLinks/semantic-layers --list            # what a source offers
uvx semantic-layers add SynaLinks/semantic-layers --layer sales     # install one layer
cd .agents/layers/sales
uvx semantic-layers connect psql host=db.example.com database=sales user=analyst password=...
uvx semantic-layers connect                                         # again, from its layer.toml
cd -
uvx semantic-layers search 'revenue|turnover'
uvx semantic-layers run sales/RevenueByCountry --limit 10
uvx semantic-layers check sales
uvx semantic-layers list
uvx semantic-layers update
```

`connect` takes the engine's fields as `key=value`; the secret ones
(`password`, `access_token`, `credentials`) go to the layer's `.env`, the
others to its `layer.toml`. `semantic-layers connect --help` lists every
engine's fields — they are synalog's (`synalog.project.ENGINES`).

## Checking

`check` verifies each layer's structure — front matter, imports, a sound
program, its `layer.toml` — and, for a layer that is connected, runs every
`@Assert` on its database. A violated assertion is a problem, quoting a few
counterexamples; a database that cannot be reached, or an assertion that
cannot be checked on data, is a warning. `--offline` checks the structure
only, without touching any database. `connect` runs the same check right
after generating the tables.

## Exit status

`0` when the command succeeded and everything it checked verifies; `1` when a
definition does not verify, an assertion is violated, a source would not install, or a connection
fails — with the reason on standard error.
