---
name: CriticalSuppliers
description: The three suppliers whose failure would stop the most assemblies.
keywords: [critical, risk, ranking, top]
---
import concepts.Supplier.Supplier;
import rules.SupplierExposure.SupplierExposure;

@OrderBy(CriticalSuppliers, "assemblies", "DESC");
@Limit(CriticalSuppliers, 3);
CriticalSuppliers(supplier_id:, name:, assemblies? += 1) distinct :-
  Supplier(supplier_id:, name:), SupplierExposure(supplier_id:);
