# Quickstart

Write your first semantic layer, check it and run it — on a CSV file, no
database needed.

In this tutorial you build `shop`, a layer of one definition: the revenue of
each customer, counting delivered orders only.

## Prerequisites

- [uv](https://docs.astral.sh/uv/)

## Create the layer

```shell
uvx semantic-layers init shop -d "Orders of an online shop: what counts as a sale, revenue."
cd shop
```

Run without arguments, `init` asks for the name and the description. It
created the layer's folders, its `layer.toml` (its name and
description), a `README.md` and a `.gitignore`, and ran `git init`.

## Add the data

A connected layer generates its `tables/` from the database. Without one, a
CSV file stands in for the table:

`data/orders.csv`

```text
order_id,customer_id,status,amount
1,1,delivered,120
2,1,delivered,80
3,2,cancelled,200
4,3,delivered,45
5,2,delivered,60
```

and declare the table, as `connect` would have:

`tables/Orders.l`

```prolog
---
name: Orders
description: One row per order, with its customer, status and amount.
---
@OrderBy(Orders, "order_id");
Orders(order_id:, customer_id:, status:, amount:) :- orders(order_id:, customer_id:, status:, amount:);
```

## Write a definition

Create the file below:

`rules/RevenueByCustomer.l`

```prolog
---
name: RevenueByCustomer
description: Revenue per customer, from delivered orders only, largest first.
keywords: [revenue, sales, turnover, customer, spend]
---
import tables.Orders.Orders;

@Assert(RevenueByCustomer,
        one_row_per_customer: "∀ c r s, RevenueByCustomer c r → RevenueByCustomer c s → r = s",
        positive:             "∀ c, RevenueByCustomer c > 0");
@OrderBy(RevenueByCustomer, "revenue", "DESC");
RevenueByCustomer(customer_id:, revenue? += amount) distinct :-
  Orders(customer_id:, amount:, status: "delivered");
```

Here is what each part does:

- **`name`** — the predicate the file defines and agents run; the file's name.
- **`description`** — what the rows are, in the words people ask with: it is
  what search matches, with the **`keywords`**.
- **`import`** — every definition the file builds on, by folder and name.
- **`@Assert`** — what the rows must satisfy, in first-order logic: one row
  per customer, every revenue positive. It is checked against the data.
- **`@OrderBy`** — a stable order, so every run returns the same page of rows.
- **The rule** — sums the amount of each customer's delivered orders.

## Check it

```shell
uvx semantic-layers check .
```

```text
Everything verifies.
```

`check` verified every file: valid front matter, a `name` the file defines,
imports that resolve, a sound program.

## Run it

```shell
uvx synalog rules/RevenueByCustomer.l run RevenueByCustomer --load orders=data/orders.csv
```

```text
+-------------+---------+
| customer_id | revenue |
+-------------+---------+
| 1           | 200     |
| 2           | 60      |
| 3           | 45      |
+-------------+---------+
```

Customer 2's cancelled order is not revenue. Now check the assertions on the
data:

```shell
uvx synalog rules/RevenueByCustomer.l verify --load orders=data/orders.csv
```

```text
✓ RevenueByCustomer.one_row_per_customer holds
✓ RevenueByCustomer.positive holds
```

Now break the rule: drop `status: "delivered"` from it, add a refund to the
data — a row `6,3,refunded,-45` — and verify again:

```text
✓ RevenueByCustomer.one_row_per_customer holds
✗ RevenueByCustomer.positive is violated: ∀ c, RevenueByCustomer c > 0
  1 counterexample:
+---+
| c |
+---+
| 3 |
+---+
```

The assertion caught a rule that counts refunds as sales, and named the
customer it is wrong for. Put the filter back before going on.

## Use it from your agent

Install the layer into a project, and search it as your agent will:

```shell
cd ~/my-project
uvx semantic-layers add ~/shop
uvx semantic-layers search 'turnover|sales'
```

```text
shop/rules/RevenueByCustomer.l                   Revenue per customer, from delivered orders only, largest first.
```

Connect it to your database (`uvx semantic-layers connect <engine> ...`, in
`.agents/layers/shop/`) and your agent answers *"who are our best
customers?"* by running `RevenueByCustomer`.

## Next steps

- [Best practices](best-practices.md): how to model a layer that stays
  consistent as it grows.
- [Writing findable definitions](findable-definitions.md): names,
  descriptions and keywords that search finds.
- [Evaluating layers](evaluating.md): assertions, and testing the answers.
- [Specification](../specification.md): the complete format.
