# Specification

The complete format specification for Semantic Layers.

## Directory structure

A semantic layer is a directory containing at least one of `tables/`,
`concepts/` and `rules/`:

```
layer-name/
├── tables/           # The data: one .l file per database table
├── concepts/         # Entities, relationships and clean views, built on tables
├── rules/            # Insights, built on concepts
├── synalog.toml      # Optional: the database it runs on (committed)
├── .env              # Optional: that database's secrets (never committed)
└── .gitignore        # Optional: keeps the credentials out of git
```

The layer's name is its directory's name. It should use lowercase letters,
numbers and hyphens (`sales`, `customer-retention`), as Agent Skills do.

A definition's kind is the folder it is in:

| Folder | Holds |
|---|---|
| `tables/` | the data: one file per database table, generated from the database |
| `concepts/` | what the data is about: entities and relationships extracted from tables, and views that filter tables or rename messy columns |
| `rules/` | what you want to know: insights derived from concepts — counts, rates, rankings, trends |

## `.l` file format

Each definition is one [synalog](https://github.com/SynaLinks/synalog) file,
`<folder>/<Name>.l`, named after the predicate that runs. It contains YAML
front matter, then `import` lines, then the definition: the predicate that
runs and any helper predicates it is built from.

### Front matter

The front matter opens with `---` on the file's first line and closes with a
`---` line. synalog checks that it is valid YAML and otherwise ignores it.

| Field | Required | Constraints |
|-------|----------|-------------|
| `name` | Yes | The predicate that runs, when the file also defines intermediate rules. Must be one of the predicates the file defines. |
| `description` | Recommended | Says what the definition holds, in plain words. Generated tables start without one. |
| `keywords` | No | A list of terms that should lead an agent to the definition. |
| `locked` | No | `true` for a definition that must not change. |
| `protected` | No | Tables only. `true` when the table's structure is fixed: its rows stay editable. |
| `columns` | No | Tables only. The column types of a table on a remote database. |

**Minimal example:**

```
---
name: Customer
description: Every customer who placed an order.
---
```

**Example with optional fields:**

```
---
name: CategoryAvgDiscount
description: Average discount by product category, among discounted items only.
keywords: [discounts, products, categories]
locked: true
---
```

#### `name` field

A predicate sometimes needs intermediate rules — a recursive or transitive
rule above all: a team size counts everyone under a manager, so it needs the
transitive "manages" relation first, a base case plus a recursive one. Other
steps are intermediate too: a staging join, a deduplication, a per-row
computation that only feeds the final aggregate. They are written in the same
file, alongside the predicate they serve — so a file can define several
predicates, and `name` says which one is the definition: the one agents run,
that other files import, and that the `description` describes. The other
predicates are the steps it is built from.

The required `name` field:
- Is the predicate that runs — the one agents run and other definitions
  import — in synalog's convention: `UpperCamelCase` (`ActiveCustomer`,
  `OrdersByStatus`)
- Must be one of the predicates the file defines itself (not an imported one)
- Should be the file's name, without `.l`
- Must be unique within the layer

Here `Manages` is a transitive, recursive intermediate rule and `TeamSize`
the definition:

```
---
name: TeamSize
description: Number of people under each manager, directly or through their reports.
---
import tables.Employees.Employees;

@Recursive(Manages, 10);
Manages(manager_id:, employee_id:) distinct :- Employees(employee_id:, manager_id:);
Manages(manager_id:, employee_id:) distinct :-
  Manages(manager_id:, employee_id: middle), Employees(employee_id:, manager_id: middle);

@OrderBy(TeamSize, "team_size", "DESC");
TeamSize(manager_id:, team_size? += 1) distinct :- Manages(manager_id:);
```

Intermediate rules are private to their file: they are not part of the
layer's catalog, and other files don't import them. A recursive relation
that several definitions traverse — a reporting line, a bill of materials —
is a concept of its own instead. A step worth reusing or
searching for belongs in its own file, with its own `name` and
`description`.

#### `description` field

The `description` field:
- Should say what the definition holds, so an agent can tell whether it
  answers a question
- Should state the exact meaning when a word is ambiguous: *delivered* orders,
  *net of refunds*, *in the last 90 days*
- Is what search matches against: use the words people ask with

**Good example:**
```yaml
description: Customers with at least one delivered order in the last 90 days.
```

**Poor example:**
```yaml
description: Active customers.
```

### Body content

After the front matter come the `import` lines, one per definition the file
builds on, then the synalog definition with its directives:

```
---
name: ActiveCustomer
description: Customers with at least one delivered order.
---
import concepts.Customer.Customer;
import tables.Orders.Orders;

@OrderBy(ActiveCustomer, "customer_id");
ActiveCustomer(customer_id:) distinct :-
  Customer(customer_id:), Orders(customer_id:, status: "delivered");
```

The file is a standalone synalog module: run from the layer's folder, it
checks, compiles and runs on its own. See the
[synalog language reference](https://github.com/SynaLinks/synalog) for the
definitions themselves.

## Imports

An import names a definition by its folder, its file and its predicate:
`import <folder>.<Name>.<Name>;`. Imports are resolved from the layer's
folder: `import tables.Orders.Orders;` is the layer's own `tables/Orders.l`.

A layer is therefore self-contained: everything its definitions import is
inside it, its tables included. The imports are the layer's dependency graph —
what each definition builds on, and so what a change affects.

## Tables

Table files are not written by hand: they are generated from the database's
schema when the layer is connected, one per table, named schema + table
(`synalog introspect`):

```
---
name: PublicOrders
description: One row per order.
---
PublicOrders(order_id:, customer_id:, status:, amount:) :- public.orders(order_id:, customer_id:, status:, amount:);
```

The declaration maps the predicate onto the physical table. Connecting again
regenerates the declarations and keeps the `description` and `keywords`
written by hand. A shared layer's tables say which data its concepts and
rules expect; connecting it to another database replaces them with that
database's.

## Connection

A layer's database is synalog's project file, `synalog.toml`, at the layer's
root: the engine and its connection details as plain fields, committed with
the layer.

```toml
[connection]
engine = "psql"
host = "db.example.com"
port = 5432
database = "sales"
user = "analyst"
schema = "public"
```

Secrets are never in it — synalog refuses a secret field there. They live in
the layer's `.env`, owner-readable only and listed in its `.gitignore`, as
`SYNALOG_<ENGINE>_<FIELD>`: `SYNALOG_PSQL_PASSWORD`,
`SYNALOG_DATABRICKS_ACCESS_TOKEN`, or `GOOGLE_APPLICATION_CREDENTIALS` (a
path to BigQuery's key file). synalog run anywhere inside the layer finds
`synalog.toml`, loads the `.env` and targets that database — no `--engine`,
no connection string. The fields of each engine are synalog's
(`synalog.project.ENGINES`). `SYNALOG_<ENGINE>_DSN` (e.g. `SYNALOG_PSQL_DSN`)
takes precedence, for CI.

A layer published with its `synalog.toml` says which database it was written
for: whoever installs it only adds the secrets — or connects it to another
database. A layer meant for anyone's data is published without one.

Engines with a connection: `psql`, `trino`, `presto`, `databricks`,
`bigquery`. DuckDB and SQLite have none: synalog runs them in memory, loading
files with `--load`.

## Layers folder

A project's layers sit side by side in `.agents/layers/`
(`~/.agents/layers/` for the user's):

```
.agents/layers/
├── sales/
└── support/
```

## Progressive disclosure

Agents load definitions *progressively*, pulling in more only as a question
calls for it. Layers should be written to take advantage of this:

1. **Search**: The `name`, `keywords` and `description` of the concepts and
   rules are searched with a regular expression built from the question
   (case-insensitive: `cancel(led|lation)|churn`), and only the matches reach
   the context — a match in the name first, then in the keywords, then in
   the description. A layer holds thousands of definitions: listing them
   all, as Agent Skills list their skills, does not scale
2. **Definitions**: A definition, and what it imports, is read when the agent
   needs to explain it or build on it
3. **Rows**: The definition is run, and the answer comes from its rows —
   never from the agent's reading of the definition

Search is what makes a definition findable, so its front matter is written
for it: a `name` that says what it holds, a `description` in the words people
ask with, and `keywords` for the other words they use (synonyms, the
business's own terms, the other language of the team).

Keep each definition small, and build larger ones on top through imports:
small definitions are easier to find, to reuse and to check.

## Validation

Every file must check with synalog, its imports resolved from the layer's
folder:

```shell
cd my-layer
uvx synalog rules/ActiveCustomer.l print ActiveCustomer   # one definition
uvx semantic-layers check .                               # the whole layer
```

This checks that the front matter is valid YAML and its `name` is a predicate
the file defines, and that the definition parses, its imports resolve and the
whole program is sound.

## Open questions

- **Local changes**: `update` keeps a layer modified locally; whether it
  should offer to merge the upstream change.
- **Binding**: A shared layer's concepts and rules use its tables by name;
  connected to another database, the tables are regenerated from it — how to
  map tables whose names or columns differ.
- **Layers building on layers**: A layer is self-contained, since synalog
  resolves imports from one root; whether one layer should be able to import
  another's definitions (a shared `customers` layer used by `sales` and
  `support`).
