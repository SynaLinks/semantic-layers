<!-- semantic-layers:start -->
## Semantic layers

This project's business definitions are semantic layers in `.agents/layers/`: one
folder per layer, each with `tables/`, `concepts/` and `rules/` — one synalog
`.l` file per predicate, described by its front matter (`name`,
`description`).

- **Answer from them.** Before answering a question about the data, search
  the definitions that fit (`uvx semantic-layers search '<regex from the
  question>'`), read them, and run them from their layer's folder
  (`uvx synalog rules/<Name>.l run <Name>`: the folder's `layer.toml`
  names the database). Never re-derive a definition or write ad-hoc SQL.
- **Write what is missing.** An entity or relationship goes in
  `concepts/<Name>.l`, a computation in `rules/<Name>.l`, inside the layer
  whose tables it uses: front matter with `name` (the predicate that runs)
  and `description`, one `import <folder>.<Name>.<Name>;` per predicate it
  uses, an `@OrderBy` (and `@Limit` for a ranking), then the rule.
- **Check before saving**: `uvx semantic-layers check <layer>`.
<!-- semantic-layers:end -->
