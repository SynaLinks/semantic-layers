---
name: Supplies
description: The edge from a supplier to each part it supplies.
keywords: [supplies, sourcing]
---
import concepts.Supplier.Supplier;
import concepts.Part.Part;
import tables.Parts.Parts;

@OrderBy(Supplies, "supplier_id", "part_id");
Supplies(supplier_id:, part_id:) distinct :-
  Supplier(supplier_id:), Part(part_id:), Parts(part_id:, supplier_id:);
