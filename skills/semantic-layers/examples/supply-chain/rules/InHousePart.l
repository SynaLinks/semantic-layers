---
name: InHousePart
description: Parts no supplier provides, made in house.
keywords: [in house, internal, unsourced]
---
import concepts.Part.Part;
import concepts.Supplies.Supplies;

@OrderBy(InHousePart, "part_id");
InHousePart(part_id:, name:) :- Part(part_id:, name:), ~Supplies(part_id:);
