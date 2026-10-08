"""The ``semantic-layers`` command: init, connect, add, list, update, search, run, check.

Built with click and rich, as the ``synalinks`` command is. Output is for two
readers: people at a terminal get colors, panels and the logo; coding agents
and pipes get plain lines, never wrapped, so they read every word of them.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from synalog.cli import render_table

from . import __version__
from .banner import PURPLE, for_people, show_banner, show_logo
from .connect import PROJECT_FILE, generate_tables, layer_connection, write_connection
from .init import check_name, init
from .install import InstallError, Scope, add, available, installed, update
from .layers import check, find_definition, is_layer, read_layers, run, search

#: Never wrapped: an agent reads the lines whole, and a path stays one word.
out = Console(soft_wrap=True, highlight=False)
err = Console(stderr=True, soft_wrap=True, highlight=False)


def _fail(message: str) -> int:
    """Show an error: a red panel for people, one plain line otherwise. Returns 1."""
    if for_people():
        body = Text.assemble(("✗ ", "bold red"), ("Error  ", "bold red"), (message, "default"))
        Console(stderr=True, highlight=False).print(Panel(body, border_style="red", padding=(0, 1), expand=False))
    else:
        err.print(f"error: {message}", markup=False)
    return 1


def _next_steps(commands: list[str]) -> None:
    """The commands to run next: a terminal-like panel for people."""
    if not for_people():
        out.print("Next:", markup=False)
        for command in commands:
            out.print(f"  {command}", markup=False)
        return
    body = Text()
    for i, command in enumerate(commands):
        if i:
            body.append("\n")
        body.append("$ ", style=f"bold {PURPLE}")
        body.append(command, style="bold")
    title = Text.assemble(("● ", "#FF5F56"), ("● ", "#FFBD2E"), ("●", "#27C93F"), ("  Next steps", "dim"))
    out.print(Panel(body, title=title, title_align="left", border_style=PURPLE, padding=(1, 2), expand=False))


def _scope(layers: str | None, is_global: bool) -> Scope:
    return Scope.resolve(Path.cwd(), layers, is_global)


def _layers_options(command):
    """--global and --layers: which layers folder a command works on."""
    command = click.option("--layers", metavar="FOLDER", help="Another layers folder (default: .agents/layers).")(
        command
    )
    return click.option("--global", "is_global", is_flag=True, help="The user's layers (~/.agents/layers).")(command)


def _loads(pairs: tuple[str, ...]) -> list[tuple[str, str]]:
    loads = []
    for pair in pairs:
        table, sep, path = pair.partition("=")
        if not sep or not table or not Path(path).is_file():
            raise ValueError(f"--load takes TABLE=PATH, a data file (csv, json, parquet): not {pair!r}")
        loads.append((table, path))
    return loads


def _report(errors: list[str], warnings: list[str]) -> None:
    for line in errors:
        out.print(line, style="red", markup=False)
    for line in warnings:
        out.print(f"warning: {line}", style="yellow", markup=False)


def _engine_fields() -> str:
    """Each engine's connection fields, from synalog (secrets marked *)."""
    from synalog import project

    lines = ["\b", "Engines and their fields (* secret: written to .env, never to layer.toml):"]
    for name, spec in project.ENGINES.items():
        lines.append(f"  {name:<11} " + ", ".join(f.key + ("*" if f.secret else "") for f in spec.fields))
    return "\n".join(lines)


@click.group(invoke_without_command=True, context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, "-V", "--version", prog_name="semantic-layers")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """Install, connect, search, run and verify semantic layers."""
    if ctx.invoked_subcommand is None and not show_banner():
        click.echo(ctx.get_help())


@cli.command("init", short_help="Create a layer project.")
@click.argument("name", required=False)
@click.option("-n", "--name", "name_option", metavar="NAME", help="The layer's name, as an option.")
@click.option("-d", "--description", help="What the layer is about, written in its layer.toml.")
@click.option("-f", "--force", is_flag=True, help="Set up a named folder that exists and is not empty.")
def init_command(name, name_option, description, force) -> int:
    """Set up a layer project in ./NAME, or in the current folder, named after it.

    In a terminal, the description is asked when it is not given. Examples:

    \b
        semantic-layers init sales
        semantic-layers init sales -d "Orders and customers: revenue, active customers."
        semantic-layers init            # the current folder
    """
    show_logo()
    # -n wins over the positional name, as in `synalinks init`.
    name = (name_option or name or "").strip()
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
        out.print(
            f"No name given: setting up the layer in the current folder, {target}, named '{name}' after it.",
            markup=False,
        )
    description = (description or "").strip()
    if not description and sys.stdin.isatty():
        description = click.prompt("Description (what the layer is about)").strip()
    if not description:
        raise ValueError('a layer needs a description: pass it with -d "..." (it goes in layer.toml).')
    # The current folder is often a repository already: it is filled in,
    # never overwritten. A new folder must be empty, unless --force.
    result = init(target, name, description, force=force or target == Path.cwd())
    out.print(Text.assemble("✨ Layer project ", (result["name"], "bold"), f" in {result['path']}"))
    for item in result["created"]:
        out.print(f"  {item}", style="dim", markup=False)
    _next_steps(
        ([f"cd {name}"] if target != Path.cwd() else [])
        + [
            "uvx semantic-layers connect <engine> host=... user=... password=...",
            "uvx semantic-layers check .",
            "git push, then anyone installs it: uvx semantic-layers add <owner>/<repo>",
        ]
    )
    return 0


def _details(pairs: tuple[str, ...]) -> dict:
    details = {}
    for pair in pairs:
        key, sep, value = pair.partition("=")
        if not sep or not key:
            raise ValueError(f"'{pair}' is not key=value (e.g. host=db.example.com)")
        details[key.strip()] = value
    return details


@cli.command("connect", short_help="Connect the layer in this folder to its database.", epilog=_engine_fields())
@click.argument("engine", required=False)
@click.argument("fields", nargs=-1, metavar="[KEY=VALUE]...")
def connect_command(engine, fields) -> int:
    """Connect the layer in this folder (it has a layer.toml) to its database.

    Writes the connection (secrets to .env, the rest to layer.toml), generates
    tables/ from the database, then checks the layer against it. Without
    ENGINE, uses the connection the layer's layer.toml already has.
    """
    folder = Path.cwd()
    if not (folder / PROJECT_FILE).is_file():
        raise ValueError(
            f"connect runs inside a layer, and {folder} has no {PROJECT_FILE}: cd into one "
            "(.agents/layers/<layer>/ for an installed layer), or create one with 'semantic-layers init'."
        )
    if engine:
        write_connection(folder, engine, _details(fields))
    elif fields:
        raise ValueError("name the engine before its fields: connect <engine> key=value ...")
    engine = layer_connection(folder)["engine"]
    try:
        result = generate_tables(folder)
    except Exception as exc:  # a missing driver, an unreachable server, bad credentials
        raise ValueError(f"Could not read the tables of {folder.name}'s {engine} database: {exc}") from None
    out.print(
        Text.assemble(
            "Connected ",
            (folder.name, "bold"),
            f" to {engine}: {len(result['written'])} table(s) in {folder / 'tables'}",
        )
    )
    for name in result["written"]:
        out.print(f"  tables/{name}.l", style="dim", markup=False)
    if result["gone"]:
        out.print(
            "Not in this database (kept, fix or delete them): " + ", ".join(result["gone"]),
            style="yellow",
            markup=False,
        )
    errors, warnings = check(folder, assertions=True)
    _report(errors, warnings)
    if errors:
        out.print(
            f"{len(errors)} problem(s): a table or column this database lacks, or an assertion its data violates.",
            style="bold red",
            markup=False,
        )
        return 1
    out.print(f"✓ {folder.name} verifies against your database.", style="green", markup=False)
    return 0


@cli.command("add", short_help="Install layers from a repository or a folder.")
@click.argument("source")
@click.option("--layer", "layer_names", multiple=True, help="A layer folder to install (repeatable; default: all).")
@click.option("--list", "list_only", is_flag=True, help="List the source's layers, install nothing.")
@click.option("--force", is_flag=True, help="Replace layers you wrote or changed.")
@click.option(
    "--agent", "agents", multiple=True, help="Also tell this agent, in its own file (repeatable): claude-code."
)
@click.option("--all", "all_agents", is_flag=True, help="Tell every agent semantic-layers knows.")
@_layers_options
def add_command(source, layer_names, list_only, force, agents, all_agents, layers, is_global) -> int:
    """Install semantic layers from SOURCE: owner/repo on GitHub, a git URL, or a folder."""
    if list_only:
        for layer in available(source):
            about = f" — {layer['description']}" if layer["description"] else ""
            out.print(Text.assemble((layer["name"], "bold"), about))
            for folder in ("tables", "concepts", "rules"):
                if layer[folder]:
                    out.print(f"  {folder + ':':<10} {', '.join(layer[folder])}", markup=False)
        return 0
    show_logo()
    result = add(
        source,
        _scope(layers, is_global),
        list(layer_names) or None,
        force=force,
        agents=list(agents),
        all_agents=all_agents,
    )
    out.print(f"✓ Installed {len(result['installed'])} layer(s): {', '.join(result['installed'])}", markup=False)
    out.print(f"Agents told in: {', '.join(result['agents'])}", markup=False)
    return 0


@cli.command("list", short_help="List the installed layers.")
@_layers_options
def list_command(layers, is_global) -> int:
    """The installed layers: where they came from, whether you changed them, whether they are connected."""
    rows = installed(_scope(layers, is_global))
    if not rows:
        out.print("No semantic layers installed.")
    for row in rows:
        connected = "connected" if row["connected"] else "not connected"
        out.print(
            Text.assemble(
                (f"{row['name']:<32} ", "bold"), (f"{row['source'] or '-':<40} ", "dim"), f"{row['state']}, {connected}"
            )
        )
        if row["description"]:
            out.print(f"  {row['description']}", markup=False)
    return 0


@cli.command("update", short_help="Update the installed layers.")
@_layers_options
def update_command(layers, is_global) -> int:
    """Bring installed layers to their source's latest version, keeping the ones you modified."""
    result = update(_scope(layers, is_global))
    out.print(f"Updated: {', '.join(result['updated']) or 'nothing'}", markup=False)
    if result["kept"]:
        out.print(f"Kept, modified locally: {', '.join(result['kept'])}", style="yellow", markup=False)
    return 0


@cli.command("search", short_help="Find definitions by name, keywords, description.")
@click.argument("pattern")
@click.option("--limit", type=int, default=20, show_default=True, help="How many results.")
@click.option("--tables", is_flag=True, help="Search the tables too.")
@_layers_options
def search_command(pattern, limit, tables, layers, is_global) -> int:
    """Find definitions whose name, keywords or description match PATTERN.

    PATTERN is a regular expression, case-insensitive: 'churn|retention'. A
    match in the name ranks first, then in the keywords, then in the
    description.
    """
    show_logo()
    kinds = ("table", "concept", "rule") if tables else ("concept", "rule")
    rows = search(_scope(layers, is_global).layers, pattern, limit, kinds)
    if not rows:
        out.print("No definition matches: try another pattern (synonyms, alternatives), or write the definition.")
    for row in rows:
        out.print(Text.assemble((f"{row['path']:<48}", f"bold {PURPLE}"), " ", row["description"]))
    return 0


@cli.command("run", short_help="Check a definition, then run it.")
@click.argument("definition")
@click.option("--limit", type=int, help="At most this many rows.")
@click.option("--offset", type=int, help="Skip this many rows (the next page).")
@click.option("--csv", "as_csv", is_flag=True, help="Print CSV, to read the values.")
@click.option(
    "--load", "load", multiple=True, metavar="TABLE=PATH", help="Run in memory on this data file (repeatable)."
)
@_layers_options
def run_command(definition, limit, offset, as_csv, load, layers, is_global) -> int:
    """Check DEFINITION, then run it on its layer's database.

    DEFINITION is <layer>/<Name>, the path search prints, or <Name> inside a
    layer's folder. A definition whose assertions the data violates is
    refused. Examples:

    \b
        semantic-layers run sales/RevenueByCountry --limit 20
        semantic-layers run sales/rules/RevenueByCountry.l --csv
    """
    layer, predicate = find_definition(definition, _scope(layers, is_global).layers)
    loads = _loads(load)
    try:
        columns, rows = run(layer, predicate, limit, offset, loads)
    except ValueError:
        raise
    except Exception as exc:  # the database's own error (a driver, a server): one line, no traceback
        raise ValueError(f"{layer.name}.{predicate.name} did not run: {type(exc).__name__}: {exc}") from None
    if as_csv:
        writer = csv.writer(sys.stdout)
        writer.writerow(columns)
        writer.writerows(rows)
        return 0
    # synalog's own table: the same rows look the same from either command.
    out.print(render_table(columns, rows))
    return 0


@cli.command("check", short_help="Verify layers, and run their assertions.")
@click.argument("layer", required=False)
@click.option("--offline", is_flag=True, help="Check the definitions only: run no assertion on the databases.")
@click.option(
    "--load", "load", multiple=True, metavar="TABLE=PATH", help="Run the assertions in memory on this data file."
)
@_layers_options
def check_command(layer, offline, load, layers, is_global) -> int:
    """Verify the installed layers, or LAYER (a name, or a folder's path: .).

    Every definition is checked with synalog, and a connected layer's
    assertions run on its database.
    """
    scope = _scope(layers, is_global)
    if layer:
        path = Path(layer).expanduser()
        if not (layer in (".", "..") or "/" in layer or is_layer(path)):
            path = scope.layers / layer
        path = path.resolve()
        folders = {path.name: path}
    else:
        folders = {name: found.path for name, found in read_layers(scope.layers).items()}
    loads = _loads(load)
    errors, warnings = [], []
    for name, path in folders.items():
        found, notes = check(path, assertions=not offline, loads=loads)
        errors += [f"{name}/{e}" for e in found]
        warnings += [f"{name}/{w}" for w in notes]
    _report(errors, warnings)
    if errors:
        out.print(f"{len(errors)} problem(s).", style="bold red", markup=False)
        return 1
    out.print("✓ Everything verifies.", style="green", markup=False)
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run the command; its exit status. An error is one message, never a traceback."""
    args = sys.argv[1:] if argv is None else argv
    try:
        status = cli.main(args=args, prog_name="semantic-layers", standalone_mode=False)
    except click.exceptions.Exit as exc:  # --help, --version
        return exc.exit_code
    except click.Abort:
        err.print("Aborted.")
        return 1
    except click.ClickException as exc:  # a usage error
        exc.show()
        return exc.exit_code
    except (InstallError, ValueError) as exc:
        return _fail(str(exc))
    return status if isinstance(status, int) else 0


if __name__ == "__main__":
    sys.exit(main())
