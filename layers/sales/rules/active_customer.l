---
name: ActiveCustomer
description: Customers with at least one delivered order.
keywords: [active, engaged, retained]
---
import concepts.customer.Customer;
import concepts.delivered_order.DeliveredOrder;

@OrderBy(ActiveCustomer, "customer_id");
ActiveCustomer(customer_id:) distinct :-
  Customer(customer_id:), DeliveredOrder(customer_id:);
