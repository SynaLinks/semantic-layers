---
name: Part
description: A part, bought or assembled in house, as a node.
keywords: [part, component, assembly]
---
import tables.Parts.Parts;

@OrderBy(Part, "part_id");
Part(part_id:, name:) distinct :- Parts(part_id:, name:);
