---
name: Requires
description: An assembly requires a component, directly or inside a sub-assembly, at any depth.
keywords: [depends, requires]
---
import concepts.Contains.Contains;

@Recursive(Requires, 20);
@OrderBy(Requires, "assembly_id", "component_id");
Requires(assembly_id:, component_id:) distinct :- Contains(assembly_id:, component_id:);
Requires(assembly_id:, component_id:) distinct :-
  Requires(assembly_id:, component_id: middle), Contains(assembly_id: middle, component_id:);
