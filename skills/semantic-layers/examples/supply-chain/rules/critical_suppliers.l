---
name: CriticalSuppliers
description: The three suppliers whose failure would stop the most assemblies.
keywords: [critical, risk, ranking, top]
---
import concepts.supplier.Supplier;
import rules.supplier_exposure.SupplierExposure;

@OrderBy(CriticalSuppliers, "assemblies", "DESC", "supplier_id");
@Limit(CriticalSuppliers, 3);
CriticalSuppliers(supplier_id:, name:, assemblies? += 1) distinct :-
  Supplier(supplier_id:, name:), SupplierExposure(supplier_id:);
