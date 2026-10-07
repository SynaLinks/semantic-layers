---
name: RevenueByCountry
description: Delivered revenue per customer country, largest first.
keywords: [revenue, country, geography, market]
---
import concepts.DeliveredOrder.DeliveredOrder;
import tables.Customers.Customers;

@Assert(RevenueByCountry,
        one_row_per_country: "∀ c r s, RevenueByCountry c r → RevenueByCountry c s → r = s",
        positive:            "∀ c, RevenueByCountry c > 0");
@OrderBy(RevenueByCountry, "revenue", "DESC");
RevenueByCountry(country:, revenue? += amount) distinct :-
  DeliveredOrder(customer_id:, amount:), Customers(customer_id:, country:);
