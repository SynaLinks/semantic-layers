# Evaluating layers

How to test that a layer's definitions return the right rows, and that agents
answer better with the layer than without it.

A definition that checks is well-formed: its imports resolve, its program is
sound. It can still compute the wrong thing — a join that duplicates rows, a
filter applied on one side, refunds counted as sales. Two kinds of tests
catch that: **assertions**, properties of the rows checked on every run,
and **answer evals**, questions whose right answer you know.

## Assertions

An assertion states what a definition's rows must satisfy, in first-order
logic. synalog checks it by searching the data for a counterexample: the
assertion holds when there is none.

```prolog
@Assert(RevenueByCountry,
        one_row_per_country: "∀ c r s, RevenueByCountry c r → RevenueByCountry c s → r = s",
        positive:            "∀ c, RevenueByCountry c > 0");
```

A predicate is applied by position, in the order its rule declares its
columns: `RevenueByCountry c r` is the row `(country: c, revenue: r)`, and
`RevenueByCountry c` — all but the last column — is a function: the revenue
of country `c`.

### What to assert

The properties worth stating are the ones a rule can silently get wrong:

| Property | Statement | Catches |
|---|---|---|
| A key | `∀ c r s, Revenue c r → Revenue c s → r = s` | a join that duplicates rows, a missing `distinct` |
| A reference | `∀ c r, Revenue c r → ∃ k, Customer c k` | orphan rows, a filter applied on one side only |
| A bound | `∀ c, 0 ≤ Share c ∧ Share c ≤ 1` | a wrong denominator, an integer division |
| A total | `∑ c, Share c = 1` | rows lost or counted twice |
| A sign | `∀ c, Revenue c > 0` | refunds or cancellations counted as sales |
| Transitivity | `∀ x y z, Manages x y → Manages y z → Manages x z` | a recursion that stops too early |
| Irreflexivity | `∀ x, ¬ Manages x x` | a cycle in the data, an edge in the wrong direction |
| A period | `∀ p t f u, MemberOf p t f u → f < u` | an interval closed before it opens |

The statement language — quantifiers, sums, the ASCII spelling of every
symbol — is in synalog's [Assertions](https://synalinks.github.io/synalog/assertions/).

### Where they run

| Command | Assertions |
|---|---|
| `semantic-layers check` | Run on the database of every **connected** layer; each violated one is an error quoting a few counterexamples. `--offline` skips them. |
| `semantic-layers connect` | Run on the database just connected, after the tables are generated. |
| `semantic-layers add` | Not run: a layer is installed before it is connected. |
| `synalog <file> run <Name>` | Run before the rows are printed; a violated one stops the run. |
| `synalog <file> verify` | Run, every counterexample printed (`--load` for CSV files). |

```text
$ uvx semantic-layers check sales
sales/rules/RevenueByCountry.l: Assertion 'RevenueByCountry.positive' is violated: ∀ c, RevenueByCountry c > 0
  counterexamples (c): ("DE")
1 problem(s).
```

A violated assertion means the rule computes something other than what it
claims — or the claim was wrong. Fix whichever is wrong; never delete the
assertion to make the check pass.

!!! warning "A check, not a proof"
    An assertion that holds has no counterexample *in the data it was run
    on*. Run the assertions on representative data — in CI, against a
    staging database that holds the cases that broke before.

## Answer evals

Assertions test properties; answer evals test answers. An eval is a
question, and the answer that is right for a given dataset:

```json title="evals/evals.json"
{
  "layer": "sales",
  "evals": [
    {
      "id": "revenue-germany",
      "question": "How much revenue did Germany bring in?",
      "definition": "RevenueByCountry",
      "expected": "Germany: 4,180.50"
    },
    {
      "id": "repeat-buyers",
      "question": "how many customers ordered more than once",
      "definition": "RepeatBuyer",
      "expected": "312 customers"
    }
  ]
}
```

Take the expected answers from numbers the business already trusts — a
report, a reconciled dashboard — on a fixed dataset, so they do not drift.

### With and without the layer

Run each question twice, in fresh sessions: once **with the layer**
installed, once **without** it, where the agent writes its own SQL. Run each
several times. Then compare:

- **Correctness**: did the answer match `expected`?
- **Consistency**: did every run give the same answer? Without a layer, the
  same question asked three times often gives three numbers; with one, the
  agent runs the same definition and gets the same rows.
- **Traceability**: did the answer name the definition it ran?
- **Cost**: tokens and time per answer. Running a definition is usually
  cheaper than exploring a schema.

A layer that does not beat the baseline on a question is missing a
definition, or has one that search does not find — see
[Writing findable definitions](findable-definitions.md).

### Grading

Grade what can be checked mechanically with a script: the definition the
agent ran (from its transcript), the numbers in its answer. Grade the rest —
whether the answer explains what the definition counts — by reading it.
Record each run's result, so a change to the layer can be compared with the
run before it.

## Iterating

1. Write the questions the layer must answer, and their expected answers.
2. Run them with and without the layer.
3. For each failure, find the cause: no definition (write one), a
   definition search misses (fix its front matter), a definition that
   returns the wrong rows (fix the rule, and add the assertion that would
   have caught it).
4. Check the layer — `semantic-layers check` — and run the evals again.

Every failure fixed adds a definition, a keyword, or an assertion: the layer
keeps what was learned.
