---
name: Contains
description: The edge from an assembly to each component it contains, weighted by quantity.
keywords: [bill of materials, bom]
---
import concepts.Part.Part;
import tables.BillOfMaterials.BillOfMaterials;

@OrderBy(Contains, "assembly_id", "component_id");
Contains(assembly_id:, component_id:, quantity:) distinct :-
  Part(part_id: assembly_id), Part(part_id: component_id),
  BillOfMaterials(assembly_id:, component_id:, quantity:);
