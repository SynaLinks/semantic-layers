# Reading errors

`uvx semantic-layers check .` (in a layer's folder) lists every problem of the
layer at once, one line per file (`rules/X.l: …`): fix them all in one pass,
then check again. Nothing is saved or installed while a problem remains.

## The layer's own

| Message | Fix |
|---|---|
| `synalog.toml is missing: a layer says what it is …` | create it with `[project]`: `name` and `description` |
| `synalog.toml: [project] has no description — say what the layer is about` | add a `description` to `[project]` |
| `synalog.toml: names the layer 'store', but its folder is 'shop' …` | change `[project] name` to the folder's name |
| `connect runs inside a layer, and … has no synalog.toml` | `cd` into the layer's folder first |
| `… is not connected: run 'semantic-layers connect <engine> key=value ...'` | the layer has no `[connection]`: ask the user for the database details |

The other messages are synalog's.

