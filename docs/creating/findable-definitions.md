# Writing findable definitions

How to write a definition's `name`, `description` and `keywords` so an agent
finds it when a question needs it — and doesn't when it doesn't.

A definition only helps if it is found. An agent never sees a layer's full
catalog: it searches it, and reads only what the search returns. A
definition whose front matter doesn't use the words of the question is, for
that question, not there — and the agent writes a second one.

## How search works

The agent builds a regular expression from the question — the words it
expects, their synonyms and word forms as alternatives — and searches the
front matter of every concept and rule:

```shell
uvx semantic-layers search 'cancel(led|lation)|churn|attrition'
```

```text
sales/rules/ChurnedCustomer.l        Customers whose last delivered order is more than 180 days old.
sales/concepts/CancelledOrder.l      Orders cancelled before shipping, by the customer or the shop.
```

- The match is **case-insensitive**, anywhere in the text.
- A match in the **`name`** ranks first, then in the **`keywords`**, then in
  the **`description`**; ties are ordered by layer and name.
- Only concepts and rules are searched; `--tables` adds the tables.
- Search reads front matter only, never the definitions: it costs the same
  on a layer of ten files or ten thousand.

The search is deterministic; the pattern is not — it is the agent's guess at
how the definition is worded. Front matter is written to meet that guess.

## Writing the front matter

- **A `name` that says what the rows are**: `RevenueByCountry`, `RepeatBuyer`,
  `LateOrder`. Plain, PascalCase, no suffix (`Revenue`, not
  `RevenueRule` or `revenue_v2`). An agent's first pattern is usually the
  name it expects.
- **A `description` in the words people ask with**: *customers who stopped
  buying* matches the question as it is asked; *entities with null recency
  flag* does not. Name the measure, the entity and the exact meaning — the
  filter, the period, the unit.
- **`keywords` for every other word**: the synonyms (`turnover`, `sales`,
  `income` for revenue), the business's own terms and acronyms (`GMV`,
  `ARR`), the team's other language (`chiffre d'affaires`), the old name of a
  renamed metric.
- **Concise**: one or two sentences of description, a handful of keywords.
  Every result line reaches the agent's context.

Before and after:

```yaml
# Before
name: Rev2
description: Revenue.

# After
name: NetRevenue
description: Sum of delivered order amounts net of refunds, per month, in euros.
keywords: [revenue, sales, turnover, income, net, refunds, monthly, CA]
```

The improved front matter is more specific about what the rows are (net of
refunds, per month, in euros) and broader about how people ask for them.

### Avoid near-duplicates that read the same

Two definitions whose descriptions say the same thing in the same words
will both be returned, and the agent picks one. Make the difference the
first thing each description says: *Gross revenue: all delivered orders,
before refunds* and *Net revenue: delivered orders, minus refunds*.

## Testing findability

To test whether a layer's definitions are found, you need a set of
questions, each labeled with the definition that should answer it — or with
none:

```json title="questions.json"
[
  { "question": "how much did we sell in germany last quarter?", "definition": "RevenueByCountry" },
  { "question": "which customers came back for a second order", "definition": "RepeatBuyer" },
  { "question": "what's the weather in Berlin", "definition": null }
]
```

Aim for about twenty questions, worded the way your users write them —
casual, abbreviated, with typos, in the team's languages — and include
**near-misses**: questions that share words with a definition but need
something else (*how many orders were refunded* is not a revenue question).

### Search alone

The fast check: for each question, write the pattern an agent would, and see
whether the expected definition comes back near the top:

```shell
uvx semantic-layers search 'sell|sales|revenue|germany|country'
```

If it doesn't, the front matter lacks the question's words.

### End to end, with an agent

The real check runs the agent: ask each question in a fresh session, and
see which definition it ran. Run each question several times — the
agent's pattern varies from run to run — and count how often it ran the
expected one. A script, for Claude Code; replace `ask` with your agent's
non-interactive mode:

```bash
#!/bin/bash
# For each question, how often the agent ran the expected definition.
QUESTIONS="${1:?Usage: $0 <questions.json>}"
RUNS=3

ask() {  # the agent's transcript, as JSON lines
  claude -p "$1" --output-format stream-json --verbose 2>/dev/null
}

jq -c '.[]' "$QUESTIONS" | while read -r item; do
  question=$(jq -r '.question' <<<"$item")
  expected=$(jq -r '.definition // empty' <<<"$item")
  hits=0
  for _ in $(seq "$RUNS"); do
    if [ -n "$expected" ]; then
      ask "$question" | grep -q "semantic-layers run [^ ]*$expected\b" && hits=$((hits + 1))
    else
      ask "$question" | grep -q "semantic-layers run" || hits=$((hits + 1))
    fi
  done
  echo "$hits/$RUNS  ${expected:-(none)}  $question"
done
```

A question passes when the agent ran the expected definition in most runs.

### Improving without overfitting

When a question fails, find the general reason, not the word: if *"how much
did we sell"* misses `RevenueByCountry`, the fix is that the description
never says *sales* — add the concept, not the question's phrasing. Keep a
few questions aside that you never tune against, and use them to check that
a change helps questions it wasn't written for.

## Next steps

- [Evaluating layers](evaluating.md): once the right definition is found,
  check that it returns the right rows.
