"""``semantic-layers connect``: give a layer its database, and its tables.

A layer's ``layer.toml`` says what it is — ``[project]``: its ``name``
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
import re
from pathlib import Path

import yaml
from synalog import project
from synalog.introspect import table_description as describe_table

from .layers import read_predicates, read_project

PROJECT_FILE = project.PROJECT_FILE
#: Engines synalog connects to; duckdb and sqlite run in memory.
REMOTE_ENGINES = tuple(project.ENGINES)
#: What never reaches git: the secrets, and BigQuery's key file.
SECRET_FILES = project.SECRET_FILES
#: What a field looks like, for the examples of the commented template.
_EXAMPLES = {
    "host": "db.example.com",
    "database": "sales",
    "user": "analyst",
    "catalog": "hive",
    "schema": "public",
    "server_hostname": "adb-1234567890123456.7.azuredatabricks.net",
    "http_path": "/sql/1.0/warehouses/abcdef1234567890",
    "project": "my-gcp-project",
    "dataset": "sales",
    "location": "EU",
}


#: When a secret is needed, where it is not simply required.
_SECRET_NOTES = {
    ("psql", "password"): "if the server asks for one",
    ("trino", "password"): 'with auth = "password"; the token with auth = "jwt"',
    ("presto", "password"): 'with auth = "password"',
    ("bigquery", "credentials"): "required: the path to the service account's key file",
}


def connection_help() -> str:
    """The commented block of a layer's ``layer.toml`` before it is connected:
    how to connect it, and every engine's ``[connection]``, field by field —
    written from synalog's own description of the engines, so it says what
    synalog accepts."""
    lines = [
        "# The database this layer runs on: one [connection] table. Either run, in this folder,",
        "#   uvx semantic-layers connect <engine> key=value ...",
        "# which writes it (and the secrets to .env), or uncomment the block of your engine below",
        "# and fill it in. Fields marked required must be given; the others show their default.",
        "# Secrets never go in this file (synalog refuses them): each goes in .env, kept out of git,",
        "# under the variable named on its line.",
    ]
    for engine, spec in project.ENGINES.items():
        lines += ["#", f"# --- {spec.label} ---", "# [connection]", f'# engine = "{engine}"']
        for field in spec.fields:
            if field.secret:
                note = _SECRET_NOTES.get((engine, field.key), "required" if field.required else "optional")
                lines.append(f"#   {field.key}: in .env, {project.secret_env(engine, field.key)}=...  ({note})")
                continue
            value = field.default if field.default is not None else _EXAMPLES.get(field.key, "...")
            notes = []
            if field.required and field.default is None:
                notes.append("required")
            if field.options:
                notes.append("one of " + ", ".join(field.options))
            if field.default is not None:
                notes.append("default")
            elif not field.required:
                notes.append("optional")
            shown = str(value) if field.type == "number" else f'"{value}"'
            lines.append(f"# {field.key} = {shown}" + (f"  # {'; '.join(notes)}" if notes else ""))
    return "\n".join(lines) + "\n"


def project_section(name: str, description: str = "") -> str:
    """The ``[project]`` table: the layer's name and what it is about."""
    return f"[project]\nname = {json.dumps(name)}\ndescription = {json.dumps(description)}\n"


def project_template(name: str, description: str = "") -> str:
    """A layer's layer.toml before it is connected (written by ``init``, and
    by ``add`` when a source has none)."""
    return project_section(name, description) + "\n" + connection_help()


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
    """Connect the layer: synalog writes the connection (``layer.toml``'s
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


def layer_connection(layer: Path) -> dict:
    """A connected layer's connection, as synalog resolves it from the
    layer's ``layer.toml``, its secrets from its ``.env`` (the environment
    wins)."""
    conn = project.resolve(layer) if (layer / PROJECT_FILE).is_file() else None
    if conn is None:
        raise ValueError(
            f"{layer.name} is not connected: run 'semantic-layers connect <engine> key=value ...' in {layer}"
        )
    return conn


def table_declarations(introspected: str) -> dict[str, str]:
    """``name → declaration`` from ``synalog introspect``'s output."""
    found = {}
    for line in introspected.splitlines():
        match = _DECLARATION.match(line.strip())
        if match:
            found[match["name"]] = line.strip()
    return found


def table_description(declaration: str) -> str:
    """A table's description from its name — synalog's, as `synalog
    introspect` writes it — until someone writes a better one."""
    match = re.match(r"\s*\w+\([^)]*\)\s*:-\s*(?P<physical>[\w.]+)\(", declaration)
    return describe_table(match["physical"]) if match else "A table of the database."


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
    conn = layer_connection(layer)
    tables = table_declarations(introspect(conn["engine"], conn))
    existing = {name: p for name, p in read_predicates(layer).items() if p.kind == "table"}
    folder = layer / "tables"
    folder.mkdir(parents=True, exist_ok=True)
    for name, declaration in tables.items():
        previous = existing.get(name).meta if name in existing else None
        (folder / f"{name}.l").write_text(render_table(name, declaration, previous))
    return {"written": sorted(tables), "gone": sorted(set(existing) - set(tables))}
