# CLI

`semantic-layers` installs, connects, searches and verifies layers. It is a
Python tool run with [uv](https://docs.astral.sh/uv/):

```shell
uvx semantic-layers <command> [options]
```

Run without a command, it shows the commands; in a terminal, `init`, `add`
and `search` open with the logo — never when a coding agent runs them.

## Commands

| Command | |
|---|---|
| `init [<name>]` | set up a layer project: `./<name>/`, or the current folder |
| `add <source>` | install layers from `owner/repo` on GitHub, a git URL or a folder; `--layer <name>` (repeatable), `--list`, `--force`, `--agent <name>`, `--all` |
| `connect <layer> [<engine> key=value ...]` | give a layer its database (or use the one in its `synalog.toml`), generate its tables, check it; `<layer>` is an installed layer's name or a folder's path (`.`) |
| `list` | the installed layers and their state: `ok`, `modified`, `local` (yours), `missing` |
| `update` | update installed layers, keeping the ones you modified |
| `search <pattern>` | find definitions whose name, keywords or description match a regular expression (case-insensitive), name matches first; `--limit <n>`, `--tables` |
| `check [<layer>]` | verify the installed layers with synalog, or one layer — by name or path (`.`) |

Every command takes `--global` (the user's layer, `~/.agents/layers/`) or
`--layers <folder>` (another layers folder).

## Examples

```shell
uvx semantic-layers add SynaLinks/semantic-layers --list            # what a source offers
uvx semantic-layers add SynaLinks/semantic-layers --layer sales     # install one layer
uvx semantic-layers connect sales psql host=db.example.com database=sales user=analyst password=...
uvx semantic-layers connect sales                                   # again, from its synalog.toml
uvx semantic-layers search 'revenue|turnover'
uvx semantic-layers check sales
uvx semantic-layers list
uvx semantic-layers update
```

`connect` takes the engine's fields as `key=value`; the secret ones
(`password`, `access_token`) go to the layer's `.env`, the others to its
`synalog.toml`. The fields of each engine:

| Engine | Fields (secret in bold) |
|---|---|
| `psql` | `host`, `port` (5432), `database`, `user`, **`password`**, `sslmode` (prefer), `schema` (public) |
| `trino` | `host`, `port` (8080), `scheme` (http), `catalog`, `schema`, `user`, `auth` (none, password, jwt), **`password`** |
| `presto` | `host`, `port` (8080), `scheme` (http), `catalog`, `schema`, `user`, `auth` (none, password), **`password`** |
| `databricks` | `server_hostname`, `http_path`, **`access_token`**, `catalog` (main), `schema` |
| `bigquery` | `project`, `dataset`, **`credentials`** (`GOOGLE_APPLICATION_CREDENTIALS`, a key file's path), `location` |

## Exit status

`0` when the command succeeded and everything it checked verifies; `1` when a
definition does not verify, a source would not install, or a connection
fails — with the reason on standard error.
