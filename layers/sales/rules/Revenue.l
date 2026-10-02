---
name: Revenue
description: Total amount of delivered orders.
keywords: [revenue, sales, turnover, income]
---
import concepts.DeliveredOrder.DeliveredOrder;

Revenue(revenue? += amount) distinct :- DeliveredOrder(amount:);
