---
name: semantic-layers
description: Use whenever a question involves the project's data — counts, rates, rankings, trends, definitions such as "active customer" or "revenue". The project's business definitions are semantic layers in .agents/layers/ (synalog .l files); answer by running them, never by re-deriving a definition or writing ad-hoc SQL.
---

# Semantic layers

This project's business definitions live in semantic layers, in `.agents/layers/`:
one folder per layer, each about one database,
each with the same three folders, one synalog `.l` file per definition.

```
.agents/layers/
  sales/
    tables/     the data — generated from the database, never edited by hand
    concepts/   what the data is about: entities and relationships
    rules/      what people want to know: insights built on concepts
    synalog.toml       the database it runs on
    .env               its password or token (never read it, never commit it)
  support/
    tables/  concepts/  rules/  ...
```

Each file starts with YAML front matter — `name` (the predicate that runs,
and the file's name), `description` (what it holds), `keywords`, `locked` —
then `import` lines for the predicates it builds on, then the synalog
definition: that predicate, and any intermediate rules it is built from.
Always run the `name`, never an intermediate rule. Imports
stay inside the layer: `import tables.Orders.Orders;` is the layer's own
`tables/Orders.l`.

## Answering a question

1. **Search for the definitions.** The layer can hold thousands: never list
   or read them all. Search their front matter (`name`, `keywords`,
   `description`) with a regular expression (case-insensitive) built from
   the question — alternatives for synonyms and word forms — and pick the
   results whose description fits:

   ```shell
   uvx semantic-layers search 'cancel(led|lation)|churn'
   ```

   Each result is a file, `<layer>/<folder>/<Name>.l`, with its description;
   matches in the name come first. No result: widen the pattern (a synonym,
   the entity rather than the measure) before concluding nothing fits.
2. **Read** a file only when you need its definition — to explain it, or to
   build on it.
3. **Run it** from its layer's folder; the answer comes from its rows, never
   from your reading of the definition:

   ```shell
   cd .agents/layers/<layer>
   uvx synalog rules/<Name>.l run <Name> --limit 50
   ```

   synalog finds the layer's `synalog.toml` and its `.env` by itself: the
   engine and the connection come from there. Add `--csv` for
   machine-readable output. A layer whose `synalog.toml` has no
   `[connection]` is not connected yet: tell the user to run
   `uvx semantic-layers connect <layer> <engine> key=value ...`.
4. **Quote** the definition you ran by its name, with the values it returned.

## When no definition fits

Write one, in the same format, inside the layer whose tables it uses, rather
than an ad-hoc query:

- an entity or relationship → `concepts/<Name>.l`; a computation (count, sum,
  rate, ranking, trend) → `rules/<Name>.l`;
- front matter with `name` and a plain-language `description`;
- one `import <folder>.<Name>.<Name>;` line per predicate it uses, from the
  same layer;
- an `@OrderBy` directive, then the rule.

Check it before saving — this validates and compiles without running:

```shell
cd .agents/layers/<layer>
uvx synalog rules/<Name>.l print <Name>
```

Never edit `tables/` (they are regenerated from the database), nor a file whose
front matter says `locked: true`.
