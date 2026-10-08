"""The ``semantic-layers`` command: init, connect, add, list, update, search, check."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .banner import show_banner, show_logo
from .connect import PROJECT_FILE, generate_tables, layer_connection, write_connection
from .init import check_name, init
from .install import InstallError, Scope, add, available, installed, update
from .layers import check, is_layer, read_layers, search


def _scope(args) -> Scope:
    return Scope.resolve(Path.cwd(), getattr(args, "layers", None), getattr(args, "is_global", False))


def _layer_folder(args) -> Path:
    """A layer given by its folder's path (``.`` in a layer project), else by
    its name in the layers folder."""
    path = Path(args.layer).expanduser()
    if args.layer in (".", "..") or "/" in args.layer or is_layer(path):
        return path.resolve()
    return _scope(args).layers / args.layer


def _ask(label: str) -> str:
    """Ask in a terminal until the answer is non-empty; ``""`` when there is
    no terminal to ask in — a coding agent, a script."""
    if not sys.stdin.isatty():
        return ""
    while True:
        try:
            answer = input(f"{label}: ").strip()
        except EOFError:
            return ""
        if answer:
            return answer


def cmd_init(args) -> int:
    # -n wins over the positional name, as in `synalinks init`.
    name = (args.name_option or args.name or "").strip()
    if name:
        check_name(name)
        target = Path(name)
    else:
        target = Path.cwd()
        name = target.name
        try:
            check_name(name)
        except ValueError as exc:
            raise ValueError(f"the current folder names the layer: {exc} Rename it, or pass a name.") from None
        print(f"No name given: setting up the layer in the current folder, {target}, named '{name}' after it.")
    description = (args.description or "").strip() or _ask("Description (what the layer is about)")
    if not description:
        raise ValueError('a layer needs a description: pass it with -d "..." (it goes in layer.toml).')
    # The current folder is often a repository already: it is filled in,
    # never overwritten. A new folder must be empty, unless --force.
    result = init(target, name, description, force=args.force or target == Path.cwd())
    print(f"Layer project {result['name']} in {result['path']}")
    for item in result["created"]:
        print(f"  {item}")
    print(
        "Next:\n"
        + (f"  cd {name}\n" if target != Path.cwd() else "")
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
    engine = layer_connection(folder)["engine"]
    try:
        result = generate_tables(folder)
    except Exception as exc:  # a missing driver, an unreachable server, bad credentials
        raise ValueError(f"Could not read the tables of {folder.name}'s {engine} database: {exc}") from None
    print(f"Connected {folder.name} to {engine}: {len(result['written'])} table(s) in {folder / 'tables'}")
    for name in result["written"]:
        print(f"  tables/{name}.l")
    if result["gone"]:
        print("Not in this database (kept, fix or delete them): " + ", ".join(result["gone"]))
    errors, warnings = check(folder, assertions=True)
    for line in errors + [f"warning: {w}" for w in warnings]:
        print(line)
    print(
        f"{folder.name} verifies against your database."
        if not errors
        else f"{len(errors)} problem(s): a table or column this database lacks, or an assertion its data violates."
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
    if args.layer:
        path = _layer_folder(args)
        layers = {path.name: path}
    else:
        layers = {name: layer.path for name, layer in read_layers(_scope(args).layers).items()}
    errors, warnings = [], []
    for name, path in layers.items():
        # A connected layer's assertions run on its database, unless --offline.
        found, notes = check(path, assertions=not args.offline)
        errors += [f"{name}/{e}" for e in found]
        warnings += [f"{name}/{w}" for w in notes]
    for line in errors + [f"warning: {w}" for w in warnings]:
        print(line)
    print("Everything verifies." if not errors else f"{len(errors)} problem(s).")
    return 1 if errors else 0


def _folder_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--global", dest="is_global", action="store_true", help="the user's layers (~/.agents/layers)")
    parser.add_argument("--layers", help="another layers folder (default: .agents/layers)")


def _engine_fields() -> str:
    """Each engine's connection fields, from synalog (secrets marked *)."""
    from synalog import project

    lines = ["engines and their fields (* secret: written to .env, never to layer.toml):"]
    for name, spec in project.ENGINES.items():
        fields = ", ".join(f.key + ("*" if f.secret else "") for f in spec.fields)
        lines.append(f"  {name:<11} {fields}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="semantic-layers", description="Install and connect semantic layers.")
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)

    p = commands.add_parser(
        "init",
        help="set up a semantic layer project",
        description="Set up a layer project in ./<name>, or in the current folder, named after it. In a terminal,"
        " asks for the description when it is not given.",
        epilog='e.g.: semantic-layers init sales -d "Orders and customers: revenue, active customers."',
    )
    p.add_argument("name", nargs="?", help="the layer's name, also its folder (default: the current folder)")
    p.add_argument(
        "-n", "--name", dest="name_option", metavar="NAME", help="the layer's name (instead of the argument)"
    )
    p.add_argument("-d", "--description", help="what the layer is about, written in its layer.toml")
    p.add_argument("-f", "--force", action="store_true", help="set up a folder that exists and is not empty")
    p.set_defaults(func=cmd_init)

    p = commands.add_parser(
        "connect",
        help="connect the layer in this folder (it has a layer.toml) to a database, generate its tables",
        epilog=_engine_fields(),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "engine",
        nargs="?",
        help="psql, trino, presto, databricks or bigquery (default: the layer's layer.toml, as it is)",
    )
    p.add_argument(
        "fields",
        nargs="*",
        metavar="key=value",
        help="connection details, e.g. host=db.example.com database=sales user=analyst"
        " password=... (secrets go to .env, the rest to layer.toml)",
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

    p = commands.add_parser(
        "check", help="verify the installed layers with synalog; run their assertions on their databases"
    )
    p.add_argument("layer", nargs="?", help="one layer, or a layer folder's path (default: every installed layer)")
    p.add_argument(
        "--offline", action="store_true", help="check the definitions only: run no assertion on the layers' databases"
    )
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
