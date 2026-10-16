---
name: Parts
description: One row per part; supplier_id is empty for a part assembled in house.
---
@OrderBy(Parts, "part_id");
Parts(part_id:, name:, supplier_id:) :- parts(part_id:, name:, supplier_id:);
