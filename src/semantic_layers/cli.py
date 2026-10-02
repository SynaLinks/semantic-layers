"""The ``semantic-layers`` command: init, connect, add, list, update, search, check."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .banner import show_banner, show_logo
from .connect import PROJECT_FILE, generate_tables, layer_dsn, write_connection
from .init import init
from .install import InstallError, Scope, add, available, installed, update
from .layers import is_layer, search, verify, verify_layers


def _scope(args) -> Scope:
    return Scope.resolve(Path.cwd(), getattr(args, "layers", None), getattr(args, "is_global", False))


def _layer_folder(args) -> Path:
    """A layer given by its folder's path (``.`` in a layer project), else by
    its name in the layers folder."""
    path = Path(args.layer).expanduser()
    if args.layer in (".", "..") or "/" in args.layer or is_layer(path):
        return path.resolve()
    return _scope(args).layers / args.layer


def cmd_init(args) -> int:
    target = Path(args.name).expanduser() if args.name else Path.cwd()
    result = init(target, None if args.name is None else Path(args.name).name, args.description or "")
    where = "." if not args.name else args.name
    print(f"Layer project {result['name']} in {result['path']}")
    for item in result["created"]:
        print(f"  {item}")
    print(
        "Next:\n"
        + (f"  cd {where}\n" if args.name else "")
        + "  uvx semantic-layers connect <engine> host=... user=... password=...   # tables/ from your database\n"
        "  write concepts/<Name>.l and rules/<Name>.l, then: uvx semantic-layers check .\n"
        "  git push it, and anyone installs it with: uvx semantic-layers add <owner>/<repo>"
    )
    return 0


def _details(pairs: list[str]) -> dict:
    details = {}
    for pair in pairs:
        key, sep, value = pair.partition("=")
        if not sep or not key:
            raise ValueError(f"'{pair}' is not key=value (e.g. host=db.example.com)")
        details[key.strip()] = value
    return details


def cmd_connect(args) -> int:
    folder = Path.cwd()
    if not (folder / PROJECT_FILE).is_file():
        raise ValueError(
            f"connect runs inside a layer, and {folder} has no {PROJECT_FILE}: cd into one "
            "(.agents/layers/<layer>/ for an installed layer), or create one with 'semantic-layers init'."
        )
    if args.engine:
        write_connection(folder, args.engine, _details(args.fields))
    elif args.fields:
        raise ValueError("name the engine before its fields: connect <engine> key=value ...")
    engine, _dsn = layer_dsn(folder)
    try:
        result = generate_tables(folder)
    except Exception as exc:  # a missing driver, an unreachable server, bad credentials
        raise ValueError(f"Could not read the tables of {folder.name}'s {engine} database: {exc}") from None
    print(f"Connected {folder.name} to {engine}: {len(result['written'])} table(s) in {folder / 'tables'}")
    for name in result["written"]:
        print(f"  tables/{name}.l")
    if result["gone"]:
        print("Not in this database (kept, fix or delete them): " + ", ".join(result["gone"]))
    errors = verify(folder)
    for error in errors:
        print(error)
    print(
        f"{folder.name} verifies against your tables."
        if not errors
        else f"{len(errors)} problem(s): the layer needs tables or columns this database does not have."
    )
    return 1 if errors else 0


def cmd_add(args) -> int:
    if args.list:
        for layer in available(args.source):
            print(layer["name"] + (f" — {layer['description']}" if layer["description"] else ""))
            for folder in ("tables", "concepts", "rules"):
                if layer[folder]:
                    print(f"  {folder + ':':<10} {', '.join(layer[folder])}")
        return 0
    result = add(
        args.source, _scope(args), args.layer or None, force=args.force, agents=args.agent or [], all_agents=args.all
    )
    print(f"Installed {len(result['installed'])} layer(s): {', '.join(result['installed'])}")
    print(f"Agents told in: {', '.join(result['agents'])}")
    return 0


def cmd_list(args) -> int:
    rows = installed(_scope(args))
    if not rows:
        print("No semantic layers installed.")
    for row in rows:
        connected = "connected" if row["connected"] else "not connected"
        print(f"{row['name']:<32} {row['source'] or '-':<40} {row['state']}, {connected}")
        if row["description"]:
            print(f"  {row['description']}")
    return 0


def cmd_update(args) -> int:
    result = update(_scope(args))
    print(f"Updated: {', '.join(result['updated']) or 'nothing'}")
    if result["kept"]:
        print(f"Kept, modified locally: {', '.join(result['kept'])}")
    return 0


def cmd_search(args) -> int:
    kinds = ("table", "concept", "rule") if args.tables else ("concept", "rule")
    rows = search(_scope(args).layers, args.pattern, args.limit, kinds)
    if not rows:
        print("No definition matches: try another pattern (synonyms, alternatives), or write the definition.")
    for row in rows:
        print(f"{row['path']:<48} {row['description']}")
    return 0


def cmd_check(args) -> int:
    folder = _scope(args).layers
    errors = [f"{args.layer}/{e}" for e in verify(_layer_folder(args))] if args.layer else verify_layers(folder)
    for error in errors:
        print(error)
    print("Everything verifies." if not errors else f"{len(errors)} problem(s).")
    return 1 if errors else 0


def _folder_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--global", dest="is_global", action="store_true", help="the user's layers (~/.agents/layers)")
    parser.add_argument("--layers", help="another layers folder (default: .agents/layers)")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="semantic-layers", description="Install and connect semantic layers.")
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)

    p = commands.add_parser("init", help="set up a semantic layer project")
    p.add_argument("name", nargs="?", help="the layer's folder to create (default: the current folder)")
    p.add_argument("--description", help="what the layer is about, written in its synalog.toml")
    p.set_defaults(func=cmd_init)

    p = commands.add_parser(
        "connect", help="connect the layer in this folder (it has a synalog.toml) to a database, generate its tables"
    )
    p.add_argument(
        "engine",
        nargs="?",
        help="psql, trino, presto, databricks or bigquery (default: the layer's synalog.toml, as it is)",
    )
    p.add_argument(
        "fields",
        nargs="*",
        metavar="key=value",
        help="connection details, e.g. host=db.example.com database=sales user=analyst"
        " password=... (secrets go to .env, the rest to synalog.toml)",
    )
    p.set_defaults(func=cmd_connect)

    p = commands.add_parser("add", help="install semantic layers from a repository or a folder")
    p.add_argument("source", help="owner/repo on GitHub, a git URL, or a folder")
    p.add_argument("--layer", action="append", help="a layer folder to install (repeatable; default: all)")
    p.add_argument("--list", action="store_true", help="list the source's layers, install nothing")
    p.add_argument("--force", action="store_true", help="replace layers you wrote or changed")
    p.add_argument(
        "--agent", action="append", help="also write the section into this agent's file (repeatable): claude-code"
    )
    p.add_argument("--all", action="store_true", help="write it into every known agent's file")
    _folder_options(p)
    p.set_defaults(func=cmd_add)

    p = commands.add_parser("list", help="the installed layers and where they came from")
    _folder_options(p)
    p.set_defaults(func=cmd_list)

    p = commands.add_parser("update", help="bring installed layers to their source's latest version")
    _folder_options(p)
    p.set_defaults(func=cmd_update)

    p = commands.add_parser(
        "search", help="find definitions whose name, keywords or description match a regular expression"
    )
    p.add_argument("pattern", help="a regular expression, case-insensitive, e.g. 'churn|retention'")
    p.add_argument("--limit", type=int, default=20, help="how many results (default 20)")
    p.add_argument("--tables", action="store_true", help="search the tables too")
    _folder_options(p)
    p.set_defaults(func=cmd_search)

    p = commands.add_parser("check", help="verify the installed layers with synalog")
    p.add_argument("layer", nargs="?", help="one layer, or a layer folder's path (default: every installed layer)")
    _folder_options(p)
    p.set_defaults(func=cmd_check)

    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        if not show_banner():
            parser.print_help()
        return 0
    args = parser.parse_args(argv)
    if args.command in ("init", "add", "search") and not getattr(args, "list", False):
        show_logo()
    try:
        return args.func(args)
    except (InstallError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
