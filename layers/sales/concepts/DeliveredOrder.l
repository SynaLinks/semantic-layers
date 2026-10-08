---
name: DeliveredOrder
description: Orders that reached the customer, the ones that count as sales.
keywords: [delivered, completed, fulfilled, sale]
---
import tables.Orders.Orders;

@OrderBy(DeliveredOrder, "order_id");
DeliveredOrder(order_id:, customer_id:, amount:) :-
  Orders(order_id:, customer_id:, amount:, status: "delivered");
