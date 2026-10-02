# Synalog, as a layer uses it

Synalog is a logic programming language from the Datalog family. A program is
a set of rules; each predicate compiles to SQL — DuckDB, SQLite, PostgreSQL,
Trino, Presto, Databricks or BigQuery — and runs on the database. In a layer,
every predicate lives in its own `.l` file; the full language reference is at
<https://synalinks.github.io/synalog/>.

## Rules

A rule defines a predicate: the head, `:-`, then the body. A row is in the
head when the body holds.

```
Paid(order_id:, amount:) :- Orders(order_id:, amount:, status: "paid");
```

**Arguments are named.** `Orders(order_id:, amount:)` binds the columns
`order_id` and `amount` to variables of the same name. `Orders(total: amount)`
binds the column `total` to the variable `amount` — the left side is always
the column. A column you don't mention is not constrained.

**A table predicate** is declared once, in `tables/`, mapping the physical
table (lowercase, possibly `schema.table`) to a PascalCase predicate. Every
other file imports it and never names the physical table:

```
Orders(order_id:, customer_id:, status:, amount:) :- orders(order_id:, customer_id:, status:, amount:);
```

## Bodies

- **And** — a comma joins: `Orders(customer_id:), Customers(customer_id:, country:)`.
  Variables shared between atoms are join keys.
- **Or** — `|` unions alternatives (UNION ALL; with `distinct`, deduplicated).
  Defining the same predicate in several rules unions them too.
- **Not** — `~`: `Customers(customer_id:), ~Orders(customer_id:)` keeps the
  customers with no order. Every variable of a negated atom must also appear
  in a positive one.
- **Conditions** — comparisons `== != < > <= >=`, booleans `&& || !`,
  membership `status in ["paid", "shipped"]`.
- **Computed values** — bind a variable with `==`:
  `total == amount * 1.2`, `label == first ++ " " ++ last` (`++` concatenates).
- **Conditional value** — `size == (if amount > 1000 then "large" else "small")`.
- **Nulls** — `x is null`, `x is not null`. Never `x != null`: it is never true, and no error tells you.
- **Default** — `Coalesce(x, 0)`.

## Distinct and aggregation

`distinct` deduplicates the rows of the head — that is how a concept extracts
entities:

```
Customer(customer_id:) distinct :- Orders(customer_id:);
```

Aggregates go in the head, with `distinct`; `?` marks the aggregated column,
the other columns are the grouping key:

```
CustomerRevenue(customer_id:, revenue? += amount, orders? += 1) distinct :-
  Orders(customer_id:, amount:, status: "delivered");
```

| Aggregate | Gives |
|---|---|
| `x? += e` | sum; `n? += 1` counts (never `Count()`) |
| `x? Min= e`, `x? Max= e`, `x? Avg= e` | minimum, maximum, average |
| `x? List= e`, `x? Set= e` | every value, distinct values (arrays) |
| `x? ArgMax= item -> score`, `ArgMin=` | the item with the highest / lowest score |
| `x? TopThree= item -> score` | the top k items, with an alias defined first: `TopThree(x) = ArgMaxK(x, 3);` (`ArgMinK` for the bottom k) |
| `x? StringAgg= e` | values joined into a string |

A condition on an aggregate takes a second rule: aggregate in one predicate,
filter in the next (a helper in the same file is fine).

## Directives

Directives go **before** the rules of the predicate they apply to.

| Directive | Effect |
|---|---|
| `@OrderBy(Name, "column", "DESC")` | row order, compiled to `ORDER BY`; required on every concept and rule |
| `@Limit(Name, 10)` | at most that many rows, compiled to `LIMIT` |
| `@Recursive(Name, 20)` | allows recursion, at most that many steps |

## Functions

- Strings: `++`, `Substr(s, start, length)` (1-based), `Length(s)`, `Upper(s)`,
  `Lower(s)`, `Like(s, "pattern%")`, `Split(s, ",")`, `Join(list, ",")`.
- Numbers: `Abs`, `Round`, `Floor`, `Ceil`, `Sqrt`, `Exp`, `Log`.
- Casts: `ToInt64(x)`, `ToFloat64(x)`, `ToString(x)`. Divide floats for a rate:
  `rate == ToFloat64(late) / ToFloat64(total)`.
- Arrays: `Size(a)`, `Element(a, i)` (0-based), `Range(n)`.

## Dates and times

Never compute on a date or timestamp column directly. Turn it into an ISO
string, cut the part you need, and convert to a number only for arithmetic:

```
month == Substr(ToString(ordered_at), 1, 7)          # "2026-03"
day   == Substr(ToString(ordered_at), 1, 10)         # "2026-03-15"
hour  == ToInt64(Substr(ToString(ordered_at), 12, 2))
```

ISO strings compare in time order: `ToString(ordered_at) >= "2026-01-01"`.
`Today(date:)` ("YYYY-MM-DD") and `Now(timestamp:)` are built in — use them,
never define them.

## Recursion

A recursive predicate needs `@Recursive(Name, depth)` before its rules, a
base case and a recursive case. The depth bounds the path length, so cycles
terminate; the verifier refuses recursion without it, and negation through
recursion.

```
@Recursive(ReportsTo, 20);
ReportsTo(employee_id:, manager_id:) distinct :- Employees(employee_id:, manager_id:);
ReportsTo(employee_id:, manager_id:) distinct :-
  ReportsTo(employee_id:, manager_id: middle), Employees(employee_id: middle, manager_id:);
```

## Functors

`New := Generic(Dependency: Replacement);` makes a copy of `Generic` with one
of the predicates it uses replaced. In a layer, write the generic rule and
its instances **in the same file**: applied to a predicate imported from
another file, a functor has no effect.

## Imports

`import concepts.Customer.Customer;` makes `Customer` from the layer's
`concepts/Customer.l` usable in the file: `<folder>.<File>.<Predicate>`,
resolved from the layer's folder. Directives travel with the imported
predicate. Every import must be used.

## What never to write

- `SqlExpr(...)` — raw SQL; the verifier rejects it.
- A physical table name outside `tables/`.
- A definition of `Today`, `Now` or another built-in.
- A password, a token or a connection string, anywhere in a `.l` file.
