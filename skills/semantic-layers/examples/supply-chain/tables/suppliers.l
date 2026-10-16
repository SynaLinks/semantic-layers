---
name: Suppliers
description: One row per supplier, with its country.
---
@OrderBy(Suppliers, "supplier_id");
Suppliers(supplier_id:, name:, country:) :- suppliers(supplier_id:, name:, country:);
