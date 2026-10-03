---
name: Orders
description: One row per order, with its customer, status and amount.
keywords: [order, purchase, sale]
---
@OrderBy(Orders, "order_id");
Orders(order_id:, customer_id:, status:, amount:, ordered_at:) :-
  orders(order_id:, customer_id:, status:, amount:, ordered_at:);
