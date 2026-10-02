---
name: ActiveCustomer
description: Customers with at least one delivered order.
keywords: [active, engaged, retained]
---
import concepts.Customer.Customer;
import concepts.DeliveredOrder.DeliveredOrder;

@OrderBy(ActiveCustomer, "customer_id");
ActiveCustomer(customer_id:) distinct :-
  Customer(customer_id:), DeliveredOrder(customer_id:);
