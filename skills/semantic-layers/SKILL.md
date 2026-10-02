---
name: semantic-layers
description: Answer questions about a project's data from its semantic layers, and write the business definitions they lack. Use whenever a question involves the data — counts, rates, rankings, trends, "active customer", "revenue" — or when asked to define, model or fix a business concept. A semantic layer is a folder of synalog .l files (tables/, concepts/, rules/) under .agents/layers/, with a synalog.toml naming its database.
---

# Semantic layers

A semantic layer holds a project's business definitions as **verified,
executable code**: each definition is a [synalog](https://github.com/SynaLinks/synalog)
predicate that compiles to SQL and runs on the project's database. You answer
from the definitions — you never re-derive one, and you never write ad-hoc SQL.

```
.agents/layers/
  sales/
    synalog.toml   [project] name + description; [connection] the database
    tables/        one file per database table — generated, never edited by hand
    concepts/      what the data is about: entities, relationships, clean views
    rules/         what people want to know: counts, rates, rankings, trends
    .env           the database password — never read it, never commit it
  support/
    ...
```

Each `.l` file is one definition: YAML front matter (`name`, `description`,
`keywords`), the `import` lines of the definitions it builds on, then synalog.
The predicate it defines has the file's name. A layer is self-contained: it
imports only its own files, and layers cannot be joined in one definition.

## Answering a question

1. **Find.** Search the definitions with a regular expression built from the
   question — synonyms and word forms as alternatives, case-insensitive:

   ```shell
   uvx semantic-layers search 'cancel(led|lation)|churn|attrition'
   uvx semantic-layers search 'order' --tables      # include the tables
   ```

   Each result is a file path (`sales/rules/Revenue.l`) and its description.
   No result? Widen the pattern (a synonym, the entity rather than the
   measure) before concluding nothing fits. Searching is cheap; listing a
   whole layer is not — layers grow to thousands of definitions.

2. **Read** the definition that fits, and the files it imports. Check that it
   means what the question means: a "customer" who ordered once is not an
   "active customer".

3. **Run** it from its layer's folder. The folder's `synalog.toml` names the
   engine and the database; the password comes from `.env` by itself:

   ```shell
   cd .agents/layers/sales
   uvx synalog rules/RevenueByCountry.l run RevenueByCountry --limit 50
   uvx synalog rules/RevenueByCountry.l run RevenueByCountry --csv   # to read the values
   ```

4. **Answer** from the rows, naming the definition you ran
   (`sales.RevenueByCountry`) and the values it returned. Never round a
   definition into prose of your own.

If the layer's `synalog.toml` has no `[connection]`, it is not connected yet:
tell the user to run, in that folder,
`uvx semantic-layers connect <engine> key=value ...`
(see [Connecting](#connecting-a-layer)).

## Writing a definition the layer lacks

When no definition fits, write one — inside the layer whose tables it uses,
building on the definitions already there. It becomes part of the layer: the
next question reuses it.

- An entity, a relationship or a clean view → `concepts/<Name>.l`.
- A computation — count, sum, rate, ranking, trend, a yes/no test → `rules/<Name>.l`.
- `<Name>` is PascalCase, plain, no suffix: `ActiveCustomer`, not
  `ActiveCustomerRule` or `active_customers`.

`rules/RepeatBuyer.l`

```
---
name: RepeatBuyer
description: Customers with at least two delivered orders.
keywords: [repeat, loyal, returning, retention]
---
import concepts.DeliveredOrder.DeliveredOrder;

# A helper: delivered orders per customer.
DeliveredCount(customer_id:, orders? += 1) distinct :- DeliveredOrder(customer_id:);

@OrderBy(RepeatBuyer, "orders", "DESC");
RepeatBuyer(customer_id:, orders:) :- DeliveredCount(customer_id:, orders:), orders > 1;
```

The rules of the format — `semantic-layers check` enforces them:

- **`name`** is the predicate that runs, and the file's name. A file may also
  define helper predicates its definition needs (a recursive relation, a
  staging step); `name` says which one runs. A helper worth reusing gets a
  file of its own.
- **`description`** says what the rows are, in the words a user would search
  for. **`keywords`** list other words that should find it.
- **Imports**: one `import <folder>.<Name>.<Name>;` per predicate the file
  uses — `import concepts.Customer.Customer;`, `import tables.Orders.Orders;`.
  Every import must be used. Import concepts and rules rather than going
  back to the raw tables: that is how the layer stays consistent.
- **`@OrderBy`** on every concept and rule: results are paginated, and
  without a stable order the same page differs between calls. Add `@Limit`
  for the top of a ranking.
- **No secrets, no SQL**: never write `SqlExpr`; never put a password in a file.

Then check it, run it, and only then answer from it:

```shell
cd .agents/layers/sales
uvx semantic-layers check .                                   # every file of the layer
uvx synalog rules/RepeatBuyer.l run RepeatBuyer --limit 20     # does it return what you expect?
```

`check` reports every problem at once, one line per file. Fix them all and
check again; [references/errors.md](references/errors.md) explains each
message. A definition that does not check must not be left in the layer.

## Changing a definition

Read it and everything it imports first. Other definitions may build on it:
find them with `grep -rl 'import <folder>.<Name>.<Name>' .agents/layers/<layer>`,
and check the whole layer after the change. A file with `locked: true` in its
front matter must not change — say so instead. Never edit `tables/`: those
files are regenerated from the database (their `description` and `keywords`
are kept).

## Connecting a layer

`connect` runs inside a layer's folder — the one with its `synalog.toml`:

```shell
cd .agents/layers/sales
uvx semantic-layers connect psql host=db.example.com database=sales user=analyst password=...
uvx semantic-layers connect          # again, from the connection already in synalog.toml
```

It writes the connection into `synalog.toml` (`[connection]`), the secret
fields into `.env` (git-ignored), then generates `tables/` from the
database and checks every definition against it. `uvx semantic-layers connect --help`
lists each engine's fields. The user
gives the credentials — never guess or invent them.

## Writing synalog

[references/synalog.md](references/synalog.md) is the language as a layer
uses it — read it before writing anything non-trivial. The rules that matter
most:

- Arguments are **named**: `Orders(customer_id:, amount:)`. In
  `Orders(total: amount)`, `total` is the column and `amount` your variable.
- Aggregate in the head, with `distinct`: `Revenue(revenue? += amount) distinct :- ...`.
  Count with `n? += 1`, never `Count()`.
- Null tests are `x is null` / `x is not null`, never `x != null`.
- Negation is `~`: `Customers(customer_id:), ~Orders(customer_id:)`.
- Dates: compare ISO strings; for parts of a date use `Substr(ToString(d), 1, 7)`
  (month), never date arithmetic on the column itself.
- Recursion needs `@Recursive(Name, depth)` before its rules, and a base case.

[references/patterns.md](references/patterns.md) shows how to model common
questions as layer files: entities and categorical values, edges and
traversals (a knowledge graph), recursion and shortest paths, temporal
edges, absence, rankings and reuse.

## Try it

[examples/supply-chain/](examples/supply-chain/) is a complete layer — a
knowledge graph of suppliers, parts and a bill of materials — that runs
without a database, on the CSV files in its `data/`:

```shell
cd examples/supply-chain
uvx synalog rules/CriticalSuppliers.l run CriticalSuppliers \
  --load suppliers=data/suppliers.csv --load parts=data/parts.csv \
  --load bill_of_materials=data/bill_of_materials.csv
```
