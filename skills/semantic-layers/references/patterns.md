# Modeling patterns

How common questions become layer files. Every example is a complete file of
a layer whose tables are `Orders(order_id, customer_id, product_id, status,
amount, ordered_at)`, `Customers(customer_id, country, tier, email, phone)`,
`Products(product_id, name, category)`, `Employees(employee_id, manager_id)`,
`Routes(origin, destination, cost)` and `Assignments(person_id, team_id,
changed_at)` — they all verify together.

## Entities: concepts first

Extract each entity as a `distinct` projection of its table, keyed by its
identifier first. Rules then build on the entity, not on the raw table.

`concepts/Customer.l`

```
---
name: Customer
description: A customer, with their country and tier.
keywords: [customer, client, account]
---
import tables.Customers.Customers;

@OrderBy(Customer, "customer_id");
Customer(customer_id:, country:, tier:) distinct :- Customers(customer_id:, country:, tier:);
```

`concepts/Product.l`

```
---
name: Product
description: A product of the catalog, with its category.
keywords: [product, item, sku]
---
import tables.Products.Products;

@OrderBy(Product, "product_id");
Product(product_id:, name:, category:) distinct :- Products(product_id:, name:, category:);
```

## Categorical values: a node of their own

`status`, `tier`, `category`, `country` are entities in disguise. Extract the
distinct values first: the vocabulary becomes searchable, and every rule
agrees on it.

`concepts/OrderStatus.l`

```
---
name: OrderStatus
description: The statuses an order can have.
keywords: [status, state, stage]
---
import tables.Orders.Orders;

@OrderBy(OrderStatus, "status");
OrderStatus(status:) distinct :- Orders(status:);
```

## A clean view: say once what counts

When "an order" really means "a delivered order", write that once, as a
concept, and build every revenue rule on it.

`concepts/DeliveredOrder.l`

```
---
name: DeliveredOrder
description: Orders that reached the customer, the ones that count as sales.
keywords: [delivered, completed, fulfilled, sale]
---
import tables.Orders.Orders;

@OrderBy(DeliveredOrder, "order_id");
DeliveredOrder(order_id:, customer_id:, product_id:, amount:, ordered_at:) :-
  Orders(order_id:, customer_id:, product_id:, amount:, ordered_at:, status: "delivered");
```

## Edges, through their nodes

An edge joins two nodes. Going through the node concepts — not the raw
tables — means a node filter applies to every edge.

`concepts/Bought.l`

```
---
name: Bought
description: The edge from a customer to each product they received.
keywords: [bought, purchased, customer product]
---
import concepts.Customer.Customer;
import concepts.Product.Product;
import concepts.DeliveredOrder.DeliveredOrder;

@OrderBy(Bought, "customer_id", "product_id");
Bought(customer_id:, product_id:) distinct :-
  Customer(customer_id:), Product(product_id:), DeliveredOrder(customer_id:, product_id:);
```

## Traversals: questions over the graph

Two hops: customers who bought the same product. A symmetric edge, built by
joining the edge with itself.

`rules/SharedProduct.l`

```
---
name: SharedProduct
description: Pairs of customers who bought at least one same product.
keywords: [similar customers, co-purchase, lookalike]
---
import concepts.Bought.Bought;

@OrderBy(SharedProduct, "customer_a", "customer_b");
SharedProduct(customer_a:, customer_b:) distinct :-
  Bought(customer_id: customer_a, product_id:), Bought(customer_id: customer_b, product_id:),
  customer_a != customer_b;
```

## Recursion: any number of hops

A base case, a recursive case, `@Recursive` with a depth. The relation is a
concept: other definitions traverse it.

`concepts/ReportsTo.l`

```
---
name: ReportsTo
description: An employee reports to a manager, directly or through other managers.
keywords: [hierarchy, org chart, reporting line, manager]
---
import tables.Employees.Employees;

@Recursive(ReportsTo, 20);
@OrderBy(ReportsTo, "employee_id", "manager_id");
ReportsTo(employee_id:, manager_id:) distinct :- Employees(employee_id:, manager_id:);
ReportsTo(employee_id:, manager_id:) distinct :-
  ReportsTo(employee_id:, manager_id: middle), Employees(employee_id: middle, manager_id:);
```

`rules/TeamSize.l`

```
---
name: TeamSize
description: How many people work under each manager, directly or not.
keywords: [team size, headcount, span of control]
---
import concepts.ReportsTo.ReportsTo;

@OrderBy(TeamSize, "people", "DESC");
TeamSize(manager_id:, people? += 1) distinct :- ReportsTo(manager_id:);
```

## Shortest paths

Enumerate the path costs recursively (a helper), then keep the minimum per
destination.

`rules/CheapestRoute.l`

```
---
name: CheapestRoute
description: The cheapest cost from the warehouse to each destination.
keywords: [shortest path, cheapest, route, shipping cost]
---
import tables.Routes.Routes;

@Recursive(RouteCost, 10);
RouteCost(destination:, cost:) :- Routes(origin: "warehouse", destination:, cost:);
RouteCost(destination:, cost: total) :-
  RouteCost(destination: hub, cost: hub_cost), Routes(origin: hub, destination:, cost:),
  total == hub_cost + cost;

@OrderBy(CheapestRoute, "cost");
CheapestRoute(destination:, cost? Min= cost) distinct :- RouteCost(destination:, cost:);
```

## Temporal edges: what held when

Source systems usually log changes only. Close each period with the next
change, and the latest one with negation; then "now" and "on a date" are
filters on a half-open interval `[valid_from, valid_to)`.

`concepts/MemberOf.l`

```
---
name: MemberOf
description: A person belongs to a team from valid_from until valid_to (9999-12-31 while it lasts).
keywords: [team, membership, history, assignment]
---
import tables.Assignments.Assignments;

NextChange(person_id:, changed_at:, next? Min= later) distinct :-
  Assignments(person_id:, changed_at:), Assignments(person_id:, changed_at: later),
  later > changed_at;

@OrderBy(MemberOf, "person_id", "valid_from");
MemberOf(person_id:, team_id:, valid_from:, valid_to:) distinct :-
  Assignments(person_id:, team_id:, changed_at: valid_from),
  NextChange(person_id:, changed_at: valid_from, next: valid_to);
MemberOf(person_id:, team_id:, valid_from:, valid_to:) distinct :-
  Assignments(person_id:, team_id:, changed_at: valid_from),
  ~NextChange(person_id:, changed_at: valid_from), valid_to == "9999-12-31";
```

`rules/MemberToday.l`

```
---
name: MemberToday
description: Who is in which team today.
keywords: [current team, now, today]
---
import concepts.MemberOf.MemberOf;

@OrderBy(MemberToday, "person_id");
MemberToday(person_id:, team_id:) distinct :-
  MemberOf(person_id:, team_id:, valid_from:, valid_to:),
  Today(date:), valid_from <= date, date < valid_to;
```

Two periods `[s1, e1)` and `[s2, e2)` overlap when `s1 < e2 && s2 < e1`.

## Absence: negation

`rules/Dormant.l`

```
---
name: Dormant
description: Customers who never received an order.
keywords: [dormant, inactive, never ordered, lapsed]
---
import concepts.Customer.Customer;
import concepts.DeliveredOrder.DeliveredOrder;

@OrderBy(Dormant, "customer_id");
Dormant(customer_id:) :- Customer(customer_id:), ~DeliveredOrder(customer_id:);
```

## Rankings: the top N, and the top k per group

`rules/TopCustomers.l`

```
---
name: TopCustomers
description: The ten customers who spent the most.
keywords: [top, best, biggest, ranking]
---
import concepts.DeliveredOrder.DeliveredOrder;

@OrderBy(TopCustomers, "spent", "DESC");
@Limit(TopCustomers, 10);
TopCustomers(customer_id:, spent? += amount) distinct :- DeliveredOrder(customer_id:, amount:);
```

`rules/TopProductsByCountry.l`

```
---
name: TopProductsByCountry
description: The three best-selling products of each country.
keywords: [best sellers, top products, country]
---
import concepts.Customer.Customer;
import concepts.DeliveredOrder.DeliveredOrder;

TopThree(x) = ArgMaxK(x, 3);

Sales(country:, product_id:, sold? += amount) distinct :-
  Customer(customer_id:, country:), DeliveredOrder(customer_id:, product_id:, amount:);

@OrderBy(TopProductsByCountry, "country");
TopProductsByCountry(country:, products? TopThree= product_id -> sold) distinct :- Sales(country:, product_id:, sold:);
```

## Rates and trends

`rules/CancellationRate.l`

```
---
name: CancellationRate
description: The share of orders that were cancelled, between 0 and 1.
keywords: [cancellation, churn, rate, ratio]
---
import tables.Orders.Orders;

Counts(cancelled? += (if status == "cancelled" then 1 else 0), total? += 1) distinct :- Orders(status:);

@OrderBy(CancellationRate, "rate");
CancellationRate(rate:) :- Counts(cancelled:, total:), rate == ToFloat64(cancelled) / ToFloat64(total);
```

`rules/MonthlyRevenue.l`

```
---
name: MonthlyRevenue
description: Delivered revenue per month.
keywords: [revenue, monthly, trend, over time]
---
import concepts.DeliveredOrder.DeliveredOrder;

@OrderBy(MonthlyRevenue, "month");
MonthlyRevenue(month:, revenue? += amount) distinct :-
  DeliveredOrder(amount:, ordered_at:), month == Substr(ToString(ordered_at), 1, 7);
```

## Reuse: one generic rule, several instances

Build on what exists — `MonthlyRevenue` above builds on `DeliveredOrder`
instead of filtering `Orders` again. For the same computation over different
inputs, write the generic rule once, with a default input, and instantiate it
with a functor wherever it is needed:

`rules/SegmentRevenue.l`

```
---
name: SegmentRevenue
description: Delivered revenue of a segment of customers; every customer unless a functor swaps the segment.
keywords: [segment, revenue, cohort]
---
import concepts.Customer.Customer;
import concepts.DeliveredOrder.DeliveredOrder;

Segment(customer_id:) distinct :- Customer(customer_id:);

@OrderBy(SegmentRevenue, "revenue");
SegmentRevenue(revenue? += amount) distinct :- Segment(customer_id:), DeliveredOrder(customer_id:, amount:);
```

`rules/EnterpriseRevenue.l`

```
---
name: EnterpriseRevenue
description: Delivered revenue of enterprise customers.
keywords: [enterprise, segment, revenue]
---
import concepts.Customer.Customer;
import rules.SegmentRevenue.SegmentRevenue;

Enterprise(customer_id:) distinct :- Customer(customer_id:, tier: "enterprise");

@OrderBy(EnterpriseRevenue, "revenue");
EnterpriseRevenue := SegmentRevenue(Segment: Enterprise);
```
