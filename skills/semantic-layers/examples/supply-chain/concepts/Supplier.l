---
name: Supplier
description: A supplier, as a node.
keywords: [supplier, vendor]
---
import tables.Suppliers.Suppliers;

@OrderBy(Supplier, "supplier_id");
Supplier(supplier_id:, name:, country:) distinct :- Suppliers(supplier_id:, name:, country:);
