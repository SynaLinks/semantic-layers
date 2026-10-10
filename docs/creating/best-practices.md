# Best practices for layer authors

How to write layers whose definitions mean one thing, stay consistent as they
grow, and are found when a question needs them.

## Start from real definitions

A layer is worth what its definitions encode that an agent could not guess:
which orders count as sales, when a customer stops being active, which
column holds the real amount. Asking an agent to "model the sales domain"
from the tables alone produces plausible definitions — the same ones it would
improvise at question time, which is what a layer is meant to replace.

Ground each definition in a decision your business already made:

- **Existing SQL**: the queries behind dashboards and reports, dbt models,
  the views analysts maintain. Each is a definition someone signed off.
- **Metric documents**: KPI glossaries, board-pack footnotes, data contracts.
- **Corrections**: every time an answer was wrong — a refund counted as a
  sale, a test account in the totals — the fix is a definition.
- **The people who own the numbers**: one question to finance about what
  "revenue" excludes is worth a hundred guessed filters.

Then run the definition and compare its rows with the number the business
already reports. A definition that disagrees with the dashboard is either
wrong or has found a bug in the dashboard: find out which before it lands.

## One definition per file, small, built on others

Each file holds one definition that answers one question. A larger
definition is built from smaller ones through imports, never by copying
their logic:

```synalog
# rules/RevenueByCountry.l — built on what a sale is, not on raw orders
import concepts.DeliveredOrder.DeliveredOrder;
import tables.Customers.Customers;
```

When "delivered" changes meaning, one file changes, and every definition
built on it follows. Small definitions are also easier to find, to read
and to check.

### Concepts hold meaning, rules hold questions

| Put it in | When it is |
|---|---|
| `concepts/` | **what the data is about**: an entity (`Customer`), a relationship (`Manages`), a clean view that filters or renames a table (`DeliveredOrder`) |
| `rules/` | **what someone wants to know**: a count, a sum, a rate, a ranking, a trend, a yes/no test (`RevenueByCountry`, `RepeatBuyer`) |

Build rules on concepts rather than on tables. The filters that make data
mean something — `status: "delivered"`, `deleted_at is null`, `is_test ==
false` — belong in one concept, so no rule can forget them.

### Helpers stay private

A file may define intermediate predicates its definition needs — a
recursive relation, a staging join — and `name` says which one runs.
Helpers are not searched and not imported. A helper that a second
definition needs is a definition: move it to its own file, with its own
`name` and `description`.

## State exactly what a definition means

The words of a business are ambiguous; a definition is not. Its
`description` says which reading it chose:

| Ambiguous | Exact |
|---|---|
| Active customers. | Customers with at least one delivered order in the last 90 days. |
| Revenue. | Sum of delivered order amounts, net of refunds, in the order's currency. |
| Late orders. | Orders delivered after their promised date, or still open past it. |

When two readings are both in use, write both, with names that say the
difference (`GrossRevenue`, `NetRevenue`) — never one definition that
silently picks.

## Assert what a rule could get wrong

Write the properties a definition must satisfy as `@Assert` statements — in
first-order logic, a different notation from the rule, so a mistake in one
is unlikely to be repeated in the other:

```synalog
@Assert(RevenueByCountry,
        one_row_per_country: "∀ c r s, RevenueByCountry c r → RevenueByCountry c s → r = s",
        positive:            "∀ c, RevenueByCountry c > 0");
```

Assert keys, references, bounds and totals: the properties a join that
duplicates rows, a filter applied on one side, or an integer division breaks
without any error. Writing the assertion first, then the rule, is the
fastest way to get the rule right. [Evaluating layers](evaluating.md) lists
what to assert.

## Calibrate the order and the size of results

- Every definition has an `@OrderBy`: results are paginated, and a stable
  order makes every page the same on every run. Order by what the question
  ranks — `"revenue", "DESC"` — or by the key.
- A ranking has an `@Limit`: *the top 10 products* is a definition; *all
  products by sales* is another.
- Return the columns the answer needs, named in the business's words
  (`revenue`, not `sum_amt`).

## Keep tables generated

Never edit the declarations in `tables/`: `connect` regenerates them from the
database. Their front matter is yours — write a real `description` and
`keywords` for every table a concept builds on; `connect` keeps them.

## Review definitions as code

A layer is a git repository, and every change to a definition is a commit:
who changed it, what changed, a way back.

- Review new definitions — the agent's included — as pull requests, and run
  `semantic-layers check` in CI.
- Mark a definition the business signed off with `locked: true`: agents
  read it and build on it, and the skill tells them never to change it.
- When a definition changes meaning, change its `description` in the same
  commit.

## Gotchas

- **One layer, one database.** A layer imports only its own files, and its
  tables come from one connection. Data from two databases is two layers.
- **Imports are used.** synalog refuses an import the file never uses.
- **A description is required.** `check` refuses a file without one —
  generated tables start with one made from the table's name; replace it.
- **Front matter is YAML.** A value holding `: ` must be quoted:
  `description: "Revenue: delivered orders only."`
- **Assertions are checked, not proven.** One that holds has no
  counterexample *in this data*: run them on representative data.

## Next steps

- [Writing findable definitions](findable-definitions.md): make search find
  the right definition.
- [Evaluating layers](evaluating.md): assertions, and testing the answers.
