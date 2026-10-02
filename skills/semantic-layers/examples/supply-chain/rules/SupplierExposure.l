---
name: SupplierExposure
description: The assemblies that stop if a supplier fails, through every level of the bill of materials.
keywords: [exposure, risk, dependency, failure]
---
import concepts.Supplies.Supplies;
import concepts.Requires.Requires;

@OrderBy(SupplierExposure, "supplier_id", "assembly_id");
SupplierExposure(supplier_id:, assembly_id:) distinct :-
  Supplies(supplier_id:, part_id: component), Requires(assembly_id:, component_id: component);
