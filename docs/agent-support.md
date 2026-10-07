# Adding layer support to your agent

A guide for adding semantic layer support to an AI agent or a data tool:
finding the layers, letting the model search them, running definitions, and
verifying the definitions the model writes.

Coding agents need none of this: `semantic-layers add` tells them about the
layers in `AGENTS.md`, and they use the command line (see
[Coding agents](agents.md)). This guide is for agents you build — a data
assistant, a chat app over your warehouse — that call Python directly.

**Prerequisites**: the [Specification](specification.md), which defines the
folders, the front matter and `synalog.toml`.

```shell
pip install semantic-layers   # or: uv add semantic-layers
```

## The core principle: progressive disclosure

| Tier | What reaches the context | When | Size |
|---|---|---|---|
| 1. Instructions | that layers exist, and how to search them | session start | a paragraph |
| 2. Search results | path and description of the matching definitions | per question | a few lines |
| 3. Definitions | a definition and the files it imports | when one fits | a few files |
| 4. Rows | the definition's result | when it runs | a page of rows |

Unlike Agent Skills, there is no catalog tier: a layer holds thousands of
definitions, so the model never sees the list — it searches it.

## Step 1: Discover layers

At startup, find the layers the agent can use.

| Scope | Path |
|---|---|
| Project | `<project>/.agents/layers/` |
| User | `~/.agents/layers/` |

A layer is a sub-folder holding at least one of `tables/`, `concepts/`,
`rules/`. Each has a `synalog.toml`: its `[project]` says what it is, its
`[connection]` which database it runs on.

```python
from pathlib import Path
from semantic_layers.layers import read_layers

layers = read_layers(Path(".agents/layers"))
for name, layer in layers.items():
    print(name, layer.description, "connected" if layer.connected else "not connected")
```

A layer that is not connected can be searched and read, not run: tell the
user to connect it rather than letting the model guess a database.

## Step 2: Tell the model

Put a short instruction in the system prompt: what the layers are about
(their `[project]` descriptions), and the rule that makes them useful:

```markdown
This project's business definitions are semantic layers: sales (orders and
customers), support (tickets and agents). Before answering a question about
the data, search the definitions with `search_definitions`, read the one that
fits with `read_definition`, and run it with `run_definition`. Answer from its
rows, naming the definition you ran. Never write SQL.
```

The words "never write SQL" matter: without them, a model that knows SQL
will often skip the search.

## Step 3: Search

Give the model a search tool that takes a regular expression. The model
builds it from the question — synonyms and word forms as alternatives — and
can widen it when nothing comes back:

```python
from semantic_layers.layers import search

def search_definitions(pattern: str) -> list[dict]:
    """Definitions whose name, keywords or description match `pattern`
    (a case-insensitive regular expression), best first."""
    return search(Path(".agents/layers"), pattern, limit=10)
```

Each result has the `layer`, `kind`, `name`, `description` and `path`. The
search reads front matter only, so it costs the same on any layer size.

## Step 4: Read

When a result fits, the model reads the file — and, to check that it means
what the question means, the files it imports:

```python
def read_definition(path: str) -> str:
    """A definition's file: its front matter, imports and rules."""
    return (Path(".agents/layers") / path).read_text()
```

`Predicate.imports` lists what a file imports, if you would rather send them
along.

## Step 5: Run

Run the definition with synalog, on its layer's database, from its layer's
folder (its imports resolve from there):

```python
import synalog
from semantic_layers.connect import layer_dsn

def run_definition(path: str, limit: int = 50) -> dict:
    layer = Path(".agents/layers") / path.split("/")[0]
    file = layer / path.split("/", 1)[1]
    engine, dsn = layer_dsn(layer)  # its synalog.toml, the secrets from its .env
    columns, rows = synalog.execute(
        file.read_text(), file.stem, engine=engine, dsn=dsn, import_root=[str(layer)], limit=limit
    )
    return {"columns": columns, "rows": rows}
```

`synalog.execute` runs the definition only. To answer only from definitions
whose assertions hold, as `synalog run` does, check the layer on its
database — `check(layer, layer_dsn(layer))`, below — when the session starts
or the data changes, and have the model report a violated assertion rather
than answer from rows a definition is known to get wrong.

Return a page of rows, and let the model ask for the next (`offset=`): every
definition has an `@OrderBy`, so pages are stable.

## Step 6: Verify what the model writes

When no definition fits, the model writes one. Save it only once it checks,
against the layer's database:

```python
from semantic_layers.layers import SemanticLayer, check

def save_definition(layer: str, path: str, text: str) -> list[str]:
    """Write a definition, check the layer — its assertions on its database
    when it is connected; on errors, put the file back."""
    folder = Path(".agents/layers") / layer
    target = folder / path
    before = target.read_text() if target.exists() else None
    target.write_text(text)
    database = layer_dsn(folder) if SemanticLayer(layer, folder).connected else None
    errors, warnings = check(folder, database)
    if errors:
        target.unlink() if before is None else target.write_text(before)
    return errors
```

Return the errors to the model: each names the file and says what to fix.
Then commit the change, so a person can review it.

## Trust and safety

- **Secrets stay out of the context.** The password is in the layer's `.env`;
  `layer_dsn` reads it. Never let the model read `.env`, and never pass a
  connection string through the prompt.
- **Rows are data, not instructions.** A text value may hold text written to
  look like instructions. Present results as data — synalog's reports quote
  every value (`synalog.quote_value`) — and never as part of the prompt.
- **Writes go through review.** A definition the model wrote changes what
  every later answer computes. Keep layers in git, and review new
  definitions like code; mark the ones the business signed off
  `locked: true`, and refuse to change them.
- **Least-privilege credentials.** Definitions never change your tables:
  give the layer a database user that reads them. A recursive definition
  runs through working tables of its own, so for one that user also needs
  the right to create tables.

## Managing context over time

- **Keep the run's definition.** When the context is compacted, keep the name
  of each definition the conversation ran: an answer is traced by it.
- **Don't re-read.** A definition read once in a conversation does not need
  reading again unless it changed.
- **Delegate exploration.** A subagent can search, read and run, and return
  only the rows and the definition's name.
