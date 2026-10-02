# Agents

Files in a folder are not enough: an agent has to be told the layer exists and
how to use it. `add` does that for every coding agent, through whichever
channel it reads:

| The agent… | `add` installs |
|---|---|
| supports Agent Skills | the companion **Agent Skill** `semantic-layers`: always in the agent-neutral `.agents/skills/`, and in the agent's own skills folder when `add` knows it |
| reads `AGENTS.md` | a short section in the project's `AGENTS.md` (created if missing, replaced — never duplicated — on the next `add`) |
| speaks MCP | nothing more to install: connect it to a runtime that serves the layer, such as Lemma |

`add` detects the agents it knows and covers them; `--agent <name>`
(repeatable) names one, `--all` every agent it knows. Today that is Claude
Code — `.claude/skills/` gets the companion skill and `.claude/layers` links
to `.agents/layers` — with every other agent reached through `.agents/skills/`
and `AGENTS.md`.

The companion skill teaches the agent to find definitions by searching them
with a regular expression (`semantic-layers search`), read one only when it
needs it, answer by running it from its layer's folder, and write missing
definitions — in the layer whose tables they use, checked with synalog before
they are saved. It teaches the how; the semantic layers hold the what.

## What the agent reads

The companion skill, installed as `.agents/skills/semantic-layers/SKILL.md`:

```markdown
--8<-- "src/semantic_layers/companion/SKILL.md"
```

## Runtimes

An agent that speaks [MCP](https://modelcontextprotocol.io) needs no files at
all when a runtime serves the layers. [Lemma](https://github.com/SynaLinks/lemma)
does: its MCP server exposes `search_predicates`, `read_predicates`,
`execute_predicate` and `update_predicates` over every layer of a workspace,
and its own analyst uses the same tools.
