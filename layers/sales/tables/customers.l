---
name: Customers
description: One row per customer, with their country.
keywords: [customer, client, account]
---
@OrderBy(Customers, "customer_id");
Customers(customer_id:, country:) :- customers(customer_id:, country:);
