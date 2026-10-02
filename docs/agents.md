# Agents

Files in a folder are not enough: an agent has to be told the layers exist and
how to use them. `add` does it through the file each agent reads at the start
of a session:

| The agent… | `add` writes |
|---|---|
| reads `AGENTS.md` (Codex, Cursor, Gemini CLI, and most others) | a section in the project's `AGENTS.md` |
| is Claude Code, which reads `CLAUDE.md` | the same section in `CLAUDE.md`, when the project has a `.claude/` folder or a `CLAUDE.md`, or with `--agent claude-code` |

The file is created if missing; the section is replaced — never duplicated —
on the next `add`, and everything else in the file is kept. `--all` writes it
into every agent file `add` knows. Layers installed for the user (`--global`)
belong to no project, so no file is written.

## The Agent Skill

For agents that support [Agent Skills](https://agentskills.io), this
repository ships one: `skills/semantic-layers/`. Where the `AGENTS.md`
section says *what* to do, the skill teaches *how* — searching and reading
definitions, writing synalog in a layer, every modelling pattern, every error
message — with an example layer that runs without a database. Install it
with the Agent Skills CLI:

```shell
npx skills add SynaLinks/semantic-layers
```

## What the agent reads

```markdown
--8<-- "docs/agents-section.md"
```
