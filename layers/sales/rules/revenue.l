---
name: Revenue
description: Total amount of delivered orders.
keywords: [revenue, sales, turnover, income]
---
import concepts.delivered_order.DeliveredOrder;

@OrderBy(Revenue, "revenue");
Revenue(revenue? += amount) distinct :- DeliveredOrder(amount:);
