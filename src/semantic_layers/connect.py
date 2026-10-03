"""``semantic-layers connect``: give a layer its database, and its tables.

A layer's ``synalog.toml`` says what it is — ``[project]``: its ``name``
and ``description`` — and which database it runs on — ``[connection]``: the
engine and its connection details as plain fields, read by synalog run from
the folder. It is committed with the layer. Secrets —
the password, a token — go in the layer's ``.env`` (``SYNALOG_PSQL_PASSWORD``),
owner-only and git-ignored. Then one table file is generated per table of
the database, with ``synalog introspect``; descriptions and keywords already
written survive.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

import yaml
from synalog import project
from synalog.config import parse_dotenv

from .layers import read_predicates, read_project

PROJECT_FILE = project.PROJECT_FILE
#: Engines synalog connects to; duckdb and sqlite run in memory.
REMOTE_ENGINES = tuple(project.ENGINES)
#: What never reaches git: the secrets, and BigQuery's key file.
SECRET_FILES = project.SECRET_FILES
_CONNECTION_HELP = """\
# The database this layer runs on. Run `semantic-layers connect <engine> key=value ...`
# in this folder to write it, or fill it in by hand:
#
# [connection]
# engine = "psql"
# host = "db.example.com"
# port = 5432
# database = "sales"
# user = "analyst"
# schema = "public"
#
# Secrets never go here: put them in .env (kept out of git), e.g.
# SYNALOG_PSQL_PASSWORD=...
"""


def project_section(name: str, description: str = "") -> str:
    """The ``[project]`` table: the layer's name and what it is about."""
    return f"[project]\nname = {json.dumps(name)}\ndescription = {json.dumps(description)}\n"


def project_template(name: str, description: str = "") -> str:
    """A layer's synalog.toml before it is connected (written by ``init``, and
    by ``add`` when a source has none)."""
    return project_section(name, description) + "\n" + _CONNECTION_HELP


_DECLARATION = re.compile(r"^(?P<name>\w+)\((?P<args>[^)]*)\) :- (?P<physical>[\w.]+)\((?P=args)\);$")


def ordered(declaration: str) -> str:
    """A table's declaration after its ``@OrderBy`` on its first column (its
    key, usually): synalog wants the predicate a file names ordered, so the
    same page of rows comes back on every run."""
    match = re.match(r"\s*(\w+)\((\w+):", declaration)
    if not match:
        return declaration
    return f'@OrderBy({match[1]}, "{match[2]}");\n{declaration}'


def write_connection(layer: Path, engine: str, details: dict) -> None:
    """Connect the layer: synalog writes the connection (``synalog.toml``'s
    ``[connection]``, the secrets in ``.env``, ``.gitignore``); the layer's
    ``[project]`` is written first when the file has none."""
    if engine not in REMOTE_ENGINES:
        raise ValueError(
            f"'{engine}' has no connection: synalog runs it in memory "
            f"(load files with --load). Engines to connect: {', '.join(REMOTE_ENGINES)}."
        )
    path = layer / PROJECT_FILE
    if not read_project(layer):
        layer.mkdir(parents=True, exist_ok=True)
        rest = path.read_text() if path.exists() else ""
        path.write_text(project_section(layer.name) + ("\n" + rest if rest.strip() else ""))
    project.write(layer, engine, details)


def layer_dsn(layer: Path) -> tuple[str, str]:
    """``(engine, connection string)`` of a connected layer, its secrets
    read from its ``.env`` (the environment wins)."""
    path = layer / PROJECT_FILE
    conn = project.connection(path) if path.exists() else None
    if conn is None:
        raise ValueError(
            f"{layer.name} is not connected: run 'semantic-layers connect <engine> key=value ...' in {layer}"
        )
    env_file = layer / ".env"
    env = dict(parse_dotenv(env_file.read_text())) if env_file.exists() else {}
    return conn["engine"], project.dsn(conn["engine"], project.details(conn, {**env, **os.environ}))


def table_declarations(introspected: str) -> dict[str, str]:
    """``name → declaration`` from ``synalog introspect``'s output."""
    found = {}
    for line in introspected.splitlines():
        match = _DECLARATION.match(line.strip())
        if match:
            found[match["name"]] = line.strip()
    return found


def table_description(declaration: str) -> str:
    """What a table holds, as its schema says it — until someone writes a
    better description: synalog wants every file described."""
    match = re.match(r"\s*\w+\((?P<args>[^)]*)\)\s*:-\s*(?P<physical>[\w.]+)\(", declaration)
    if not match:
        return "A table of the database."
    columns = [a.strip().rstrip(":").strip() for a in match["args"].split(",") if a.strip()]
    return f"Rows of the {match['physical']} table, with {', '.join(columns)}."


def render_table(name: str, declaration: str, previous: dict | None) -> str:
    meta = {"name": name, "description": table_description(declaration)}
    for key in ("description", "keywords", "locked", "protected"):
        if previous and previous.get(key) not in (None, "", []):
            meta[key] = previous[key]
    return (
        "---\n"
        + yaml.safe_dump(meta, sort_keys=False, allow_unicode=True, width=1000)
        + "---\n"
        + ordered(declaration)
        + "\n"
    )


def generate_tables(layer: Path, introspect=None) -> dict[str, list[str]]:
    """Write one table file per table of the database into the layer. Returns
    what was ``written`` and which of the layer's tables the database does not
    have (``gone``: kept, since its concepts may import them — they then fail
    ``check`` until the layer is fixed or connected to the right database)."""
    if introspect is None:
        from synalog.introspect import introspect
    tables = table_declarations(introspect(*layer_dsn(layer)))
    existing = {name: p for name, p in read_predicates(layer).items() if p.kind == "table"}
    folder = layer / "tables"
    folder.mkdir(parents=True, exist_ok=True)
    for name, declaration in tables.items():
        previous = existing.get(name).meta if name in existing else None
        (folder / f"{name}.l").write_text(render_table(name, declaration, previous))
    return {"written": sorted(tables), "gone": sorted(set(existing) - set(tables))}
