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

Semantic layers build on [synalog](https://github.com/SynaLinks/synalog) (2.0
or later, from PyPI): it parses, checks and runs the definitions, runs their
assertions, and owns `synalog.toml`.

## Tests

```shell
./shell/test.sh                 # every test
uv run pytest tests/test_connect.py -q
```

Tests run synalog for real on temporary layers; nothing reaches a database
(`connect` is tested with a stand-in for `synalog introspect`, assertions on
an in-memory DuckDB standing in for the layer's database).

## Lint and format

```shell
./shell/lint.sh
./shell/format.sh
```

## The skill's synalog references

`skills/semantic-layers/references/synalog.md` and `errors.md` are generated
from synalog's own skill, so the language and its error messages are written
once, in synalog. After synalog's skill changes, from a synalog checkout
beside this one (`../synalog`):

```shell
uv run python shell/sync_skill.py
```

The layer-specific parts are in `shell/skill/`; a test fails while the
generated files are stale.

## Releasing

Publishing to PyPI is automated by `.github/workflows/release.yml`, which
runs the lint and the tests, then builds and publishes the package when a
version tag is pushed. The tag must be the version in `pyproject.toml`:

```shell
git tag v0.1.0 && git push origin v0.1.0
```

One-time setup on the GitHub repository: an Environment named `pypi`
(Settings → Environments), ideally restricted to tags matching `v*`, with a
`PYPI_API_TOKEN` secret.

## Documentation

```shell
./shell/doc.sh                  # serve this site on http://localhost:8000
```

The pages are `docs/*.md`, the navigation is `zensical.toml`. Example files
are included from `layers/` (`--8<-- "layers/sales/rules/Revenue.l"`), so the
documentation shows the files the tests verify.
