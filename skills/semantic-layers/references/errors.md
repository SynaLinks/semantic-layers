# Reading errors

`uvx semantic-layers check .` (in a layer's folder) and `uvx synalog <file> run|print <Name>`
report problems on standard error and exit with status 1 — status 2 is a
mistake in the command itself. Nothing runs and nothing is written while a
problem remains. `check` lists every problem of the layer at once, one line
per file (`rules/X.l: …`): fix them all in one pass, then check again.

## Syntax errors

The parser stops at the first one and quotes the statement, with `<EMPTY>`
where something was expected:

```
Parsing:
A(x) :- x ==<EMPTY>

[ Error ] Could not parse expression of a value.
```

Fix the quoted statement and check again: later syntax errors only show once
the earlier ones are fixed. Usual causes: a missing `;`, a missing `:` after
an argument name (`Orders(amount)` instead of `Orders(amount:)`), an
unbalanced parenthesis or quote.

## Verification errors

Found after parsing, before any SQL is generated — all of them at once.

| Message | Means | Fix |
|---|---|---|
| `Unbound variable 'y' in head of rule: …` | a column of the head gets no value from the body | bind it in the body (`Orders(amount: y)`) or drop it from the head |
| `Unsafe negation: variable 'x' only appears negated in: …` | a negated atom introduces a variable | bind `x` in a positive atom first: `Customer(customer_id: x), ~Orders(customer_id: x)` |
| `Undefined predicate 'Nope': not defined and not a built-in` | a misspelt name, or a missing import | import it (`import concepts.Nope.Nope;`) or fix the name |
| `Unknown column 'y' for predicate 'A'` | a column the predicate does not have | use the predicate's own column names — read its file |
| `Recursive predicate 'R' missing @Recursive annotation` | recursion without a depth | add `@Recursive(R, 20);` before its rules |
| `Trivial infinite loop: 'R' calls itself with same arguments` | the recursive case adds nothing | join the recursive atom with another table on a *different* variable |
| `Negative recursion cycle detected: P` | `P` depends on `~P`, through recursion | negate a predicate computed beforehand, not the recursive one |
| `Unsafe SqlExpr in rule 'A': …` | raw SQL | write it with synalog functions instead |
| `[ Error ] Predicate imported but not used.` | an `import` no rule uses | remove the import |
| `[ Error ] Invalid front matter YAML: …` | the front matter is not valid YAML | quote a value that holds `: ` — `description: "A thing: details"` — or reword it |

## Format errors (`semantic-layers check`)

| Message | Fix |
|---|---|
| `its front matter has no name: the predicate that runs, one of A, B` | add `name:` with the predicate that answers — usually the file's name |
| `its front matter names 'X', which it does not define (Helper)` | the file must define `X`: rename the predicate or the `name`, and the file |
| `synalog.toml: names the layer 'store', but its folder is 'shop' — they must match` | change `[project] name` to the folder's name |

## Compile errors

`Compile error: No rules are defining 'Missing', but compilation was requested.`
— the predicate given to `run` or `print` is not defined in the file. Check
the spelling, and run an imported predicate from its own file
(`uvx synalog concepts/Customer.l run Customer`), not from a file that imports it.

## Connection errors

| Message | Fix |
|---|---|
| `connect runs inside a layer, and … has no synalog.toml` | `cd` into the layer's folder first |
| `… is not connected: run 'semantic-layers connect <engine> key=value ...'` | the layer has no `[connection]`: ask the user for the database details |
| `synalog.toml: password is a secret — remove it from the file and set SYNALOG_PSQL_PASSWORD in the project's .env` | move the secret to `.env`; never commit it |
| `The databricks connection needs SYNALOG_DATABRICKS_ACCESS_TOKEN` | the secret is missing from `.env`: ask the user for it |
| `The psql engine needs the 'psycopg' package: pip install psycopg` | run synalog with the driver: `uvx --with psycopg synalog …` |
| `psql has no field hots (fields: …)` | a misspelt field given to `connect`: use one of the fields listed |

A query that runs but returns nothing is not an error: check the filter
values against the data (`uvx synalog concepts/OrderStatus.l run OrderStatus`
lists the statuses that exist) before concluding there is no data.
