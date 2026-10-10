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
├── layer.toml        # Required: its name, description and database (committed)
├── .env              # Optional: that database's secrets (never committed)
├── .gitignore        # Optional: keeps the credentials out of git
└── README.md         # Optional: what the layer is for, for people
```

Other files — a `README.md`, sample data in `data/` — are allowed and
ignored by the tools: only `.l` files in the three folders are definitions.

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
| `name` | Yes | Must be a predicate the file defines (not an imported one), ordered by an `@OrderBy`. Should be `UpperCamelCase` and the file's name without `.l`. |
| `description` | Yes | Non-empty text: what the definition's rows are, in plain words. Generated tables get one made from the table's name. |
| `keywords` | No | A list of strings: other words that should find the definition. |
| `locked` | No | A boolean. `true` for a definition that must not change. |
| `protected` | No | Tables only. A boolean: `true` when the table's structure is fixed; its rows stay editable. |
| `columns` | No | Tables only. The column types of a table on a remote database. |

Other keys are allowed, and ignored.

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

`rules/TeamSize.l`

```synalog
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

#### `keywords` field

The optional `keywords` field:

- Lists the words that should find the definition but are not in its name
  or description: synonyms, the business's own terms and acronyms, the
  team's other languages
- Ranks between the `name` and the `description` in search

```yaml
keywords: [revenue, sales, turnover, income, GMV]
```

#### `locked` field

The optional `locked` field marks a definition the business signed off:
agents read it and build on it, and are told never to change it. A change
goes through the people who own the definition.

### Body content

After the front matter come the `import` lines, one per definition the file
builds on, then the synalog definition with its directives:

`rules/ActiveCustomer.l`

```synalog
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

Directives shape how a definition runs and what it promises:

| Directive | Effect |
|---|---|
| `@OrderBy(Name, "column", "DESC")` | the order of its rows, compiled to `ORDER BY`. Every definition must have one — synalog refuses a file whose named predicate has none: results are paginated, and without a stable order a page differs between calls. |
| `@Limit(Name, 10)` | at most that many rows, compiled to `LIMIT` — the top of a ranking. A caller's own limit can only lower it. |
| `@Recursive(Name, 10)` | allows `Name` to be recursive, at most that many steps deep; the verifier refuses recursion without it. |
| `@Assert(Name, key: "statement", ...)` | what the rows must satisfy, in first-order logic, one named statement per property; checked against the data (see [Assertions](#assertions)). It does not change the SQL. |

The [synalog directives](https://synalinks.github.io/synalog/language/directives/)
lists the others.

The file is a standalone synalog module: run from the layer's folder, it
checks, compiles and runs on its own. See the
[synalog language reference](https://github.com/SynaLinks/synalog) for the
definitions themselves.

## Assertions

An `@Assert` states what a definition's rows must satisfy, as named
statements in first-order logic. It is part of the definition: written in
its file, before or after its rules, and checked against the data.

```synalog
@Assert(RevenueByCountry,
        one_row_per_country: "∀ c r s, RevenueByCountry c r → RevenueByCountry c s → r = s",
        positive:            "∀ c, RevenueByCountry c > 0");
```

- Each statement has a name, unique for its predicate, that reports use
  (`RevenueByCountry.positive`).
- Predicates are applied by position, in the order their rule declares
  their columns. A statement may use any predicate the file defines or
  imports.
- A statement holds when the data has no counterexample to it. It is
  checked when the layer is checked on its database (see
  [Validation](#validation)), not when it is installed.

The statement language is synalog's: see
[Assertions](https://synalinks.github.io/synalog/assertions/).
[Evaluating layers](creating/evaluating.md) lists the properties worth
asserting.

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

`tables/PublicOrders.l`

```synalog
---
name: PublicOrders
description: One row per order.
---
@OrderBy(PublicOrders, "order_id");
PublicOrders(order_id:, customer_id:, status:, amount:) :- public.orders(order_id:, customer_id:, status:, amount:);
```

The declaration maps the predicate onto the physical table, ordered by its
first column — usually its key — since synalog wants the predicate a file
names ordered. A new table's `description` comes from its name
(`public.order_items` reads "Order items.") until someone writes a better one — synalog
wants every file described. Connecting again regenerates the declarations
and keeps the `description` and `keywords` written by hand. A shared layer's tables say which data its concepts and
rules expect; connecting it to another database replaces them with that
database's.

## Connection

A layer's `layer.toml`, at its root and committed with it, says what the
layer is and which database it runs on.

```toml
[project]
name = "sales"
description = "Orders and customers: revenue, active customers, countries."

[connection]
engine = "psql"
host = "db.example.com"
database = "sales"
user = "analyst"
```

| Key | Required | Constraints |
|---|---|---|
| `[project] name` | No | The layer's name; when given, must be its folder's name. |
| `[project] description` | Yes | Non-empty: what the layer is about, shown by `list` and `add --list`. A layer without one does not check, and does not install. |
| `[connection] engine` | To run | `psql`, `trino`, `presto`, `databricks` or `bigquery`. |
| `[connection]` other keys | Per engine | The engine's non-secret fields (`host`, `port`, `database`, `user`, `schema`, ...): `semantic-layers connect --help` lists them. Never a secret. |

- `[connection]` is synalog's [project file](https://github.com/SynaLinks/synalog#projects-layertoml):
  the engine and its fields, the secrets in the git-ignored `.env`, found by
  synalog run anywhere in the layer. `semantic-layers connect` writes both
  through synalog.

A layer published with a `[connection]` says which database it was written
for: whoever installs it only adds the secrets — or connects it to another
database. A layer meant for anyone's data is published without one.

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
[Writing findable definitions](creating/findable-definitions.md) shows how,
and how to test it.

## Validation

Every file must check with synalog, its imports resolved from the layer's
folder:

```shell
cd my-layer
uvx semantic-layers check .                  # the whole layer
uvx semantic-layers run ActiveCustomer       # one definition: checked, then run
```

The check has two levels:

| Level | Checks | Runs |
|---|---|---|
| **Structure** | The front matter is valid YAML, with a `name` the file defines and orders, and a `description`; the definition parses, its imports resolve, and the program is sound — safety, arity, stratification, recursion, unknown references; `layer.toml` describes the layer | Always: `add`, `check`, `connect` |
| **Data** | Every `@Assert` holds on the layer's database: each violated one is reported with a few counterexamples | When the layer is connected: `check` (unless `--offline`) and `connect` |

A layer is installed only if its structure checks. Its assertions run once
it has a database.

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
