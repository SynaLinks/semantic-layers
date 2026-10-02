# Agent guide — Semantic Layers

**Semantic Layers** is an open format for business definitions agents run:
a layer is a folder of `tables/`, `concepts/` and `rules/`, one
[synalog](https://github.com/SynaLinks/synalog) `.l` file per predicate
(YAML front matter, then synalog). This repository holds the format's
documentation (`docs/`, a zensical site), the `semantic-layers` command
(`src/semantic_layers/`) and example layers (`layers/`).

## What to know

- **The spec is `docs/specification.md`.** Change the format there first,
  then the code, then the tests.
- **synalog does the work.** Parsing, checking (`synalog.check`), running,
  introspecting and the project file (`synalog.toml`, `synalog.project`) are
  synalog's; this package only arranges folders around them. `pyproject.toml`
  takes synalog from `../synalog` until the features used here are released.
- **A file's `name` is the predicate that runs**: one the file defines,
  beside any helpers (`layers.defined`, `verify`). Imports resolve from the
  layer's folder, so a layer is self-contained.
- **`synalog.toml`**: `[project]` names and describes the layer (`name` must
  be the folder's; `check` says so), `[connection]` holds the engine and its
  fields (committed); `connect` runs only in a folder that has one, and `add`
  writes one (`project_template`) when a source has none; secrets are in its `.env` (`SYNALOG_<ENGINE>_<FIELD>`,
  owner-only, git-ignored). `connect.write_connection` writes both;
  `connect.layer_dsn` reads them back.
- **Installing never lands anything unverified** (`install.add`): layers are
  staged, verified, then copied; a connected layer keeps its tables,
  `synalog.toml`, `.env` and `.gitignore`. `semantic-layers-lock.json`
  records sources and digests.
- **Agents are told through their instruction file**: a section of
  `AGENTS.md`, and of `CLAUDE.md` for Claude Code (`_agents_section`,
  `tell_agents`; `docs/agents-section.md` is its rendered copy, tested).
  The logo (`banner.py`) is for people only — never shown to an agent or a
  pipe.
- **The examples in `layers/` are tested** (`tests/test_examples.py`) and
  included in the docs with snippets, so keep them verifying.

## Commands

```bash
./shell/test.sh      # pytest, then `semantic-layers check` on layers/
./shell/lint.sh      # ruff check + format check
./shell/format.sh    # ruff fix + format
./shell/doc.sh       # serve the docs on http://localhost:8000
uv run semantic-layers --help
```
