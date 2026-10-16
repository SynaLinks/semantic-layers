---
name: BillOfMaterials
description: Which assembly contains which component, and how many.
---
@OrderBy(BillOfMaterials, "assembly_id");
BillOfMaterials(assembly_id:, component_id:, quantity:) :-
  bill_of_materials(assembly_id:, component_id:, quantity:);
