# Agents

Files in a folder are not enough: an agent has to be told the layers exist and
how to use them. `add` does it through the file each agent reads at the start
of a session:

| The agent… | `add` writes |
|---|---|
| reads `AGENTS.md` (Codex, Cursor, Gemini CLI, and most others) | a section in the project's `AGENTS.md` |
| is Claude Code, which reads `CLAUDE.md` | the same section in `CLAUDE.md`, when the project has a `.claude/` folder or a `CLAUDE.md`, or with `--agent claude-code` |
| speaks MCP | nothing: connect it to a runtime that serves the layers, such as Lemma |

The file is created if missing; the section is replaced — never duplicated —
on the next `add`, and everything else in the file is kept. `--all` writes it
into every agent file `add` knows. Layers installed for the user (`--global`)
belong to no project, so no file is written.

## What the agent reads

```markdown
--8<-- "docs/agents-section.md"
```

## Runtimes

An agent that speaks [MCP](https://modelcontextprotocol.io) needs no files at
all when a runtime serves the layers. [Lemma](https://github.com/SynaLinks/lemma)
does: its MCP server exposes `search_predicates`, `read_predicates`,
`execute_predicate` and `update_predicates` over every layer of a workspace,
and its own analyst uses the same tools.
