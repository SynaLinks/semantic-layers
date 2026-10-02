---
name: RevenueByCountry
description: Delivered revenue per customer country, largest first.
keywords: [revenue, country, geography, market]
---
import concepts.DeliveredOrder.DeliveredOrder;
import tables.Customers.Customers;

@OrderBy(RevenueByCountry, "revenue", "DESC");
RevenueByCountry(country:, revenue? += amount) distinct :-
  DeliveredOrder(customer_id:, amount:), Customers(customer_id:, country:);
