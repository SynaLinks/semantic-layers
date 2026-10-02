# Development

The repository:

```
semantic-layers/
├── src/semantic_layers/   # the package and the semantic-layers command
│   ├── layers.py          #   reading, verifying and searching layers
│   ├── connect.py         #   synalog.toml, .env, tables from the database
│   ├── install.py         #   add, list, update; the AGENTS.md / CLAUDE.md section
│   ├── init.py            #   layer projects
│   └── cli.py, banner.py  #   the command
├── layers/                # example layers (sales, support)
├── tests/                 # pytest, one file per module
├── docs/                  # this site (zensical)
└── shell/                 # test, lint, format, doc
```

Semantic layers build on [synalog](https://github.com/SynaLinks/synalog): it
parses, checks and runs the definitions, and owns `synalog.toml`. Until the
features this repository needs are released, `pyproject.toml` takes synalog
from a checkout beside this one (`../synalog`).

## Tests

```shell
./shell/test.sh                 # every test
uv run pytest tests/test_connect.py -q
```

Tests run synalog for real on temporary layers; nothing reaches a database
(`connect` is tested with a stand-in for `synalog introspect`).

## Lint and format

```shell
./shell/lint.sh
./shell/format.sh
```

## Documentation

```shell
./shell/doc.sh                  # serve this site on http://localhost:8000
```

The pages are `docs/*.md`, the navigation is `zensical.toml`. Example files
are included from `layers/` (`--8<-- "layers/sales/rules/Revenue.l"`), so the
documentation shows the files the tests verify.
