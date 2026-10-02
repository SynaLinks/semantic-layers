"""``semantic-layers add / list / update``: share semantic layers between projects.

``add`` fetches a source (a GitHub ``owner/repo``, a git URL or a folder) —
one layer, or a repository of layer folders — and copies the chosen layer
folders into the layers folder, ``.agents/layers/<layer>/``. A layer you already
connected keeps its tables and its connection: only its concepts and rules
are replaced, and the result must verify against your tables before
anything is written. Every install is recorded in a lock file; agents are
told about the layers through a companion Agent Skill and a section of
``AGENTS.md``.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from importlib import resources
from pathlib import Path

from .connect import PROJECT_FILE, SECRET_FILES
from .layers import FOLDERS, SemanticLayer, find_layers, read_layers, verify

LOCK_FILE = "semantic-layers-lock.json"
AGENTS_START = "<!-- semantic-layers:start -->"
AGENTS_END = "<!-- semantic-layers:end -->"
_GITHUB = re.compile(r"^[\w.-]+/[\w.-]+$")
#: What belongs to the layer's user, never to its source.
_LOCAL_FILES = (*SECRET_FILES, ".gitignore")

#: Agents whose skills folder we know, by name: project and global folders.
AGENT_SKILL_DIRS = {
    "claude-code": (".claude/skills", "~/.claude/skills"),
}
#: The agent-neutral skills folder, always written.
NEUTRAL_SKILL_DIR = (".agents/skills", "~/.agents/skills")


class InstallError(Exception):
    pass


@dataclass
class Scope:
    """Where a layer lives: a project (``.agents/layers`` in ``root``) or the user."""

    root: Path
    layers: Path
    is_global: bool

    @classmethod
    def resolve(cls, project: Path, layers: str | None = None, is_global: bool = False) -> Scope:
        root = Path.home() if is_global else project
        path = Path(layers).expanduser() if layers else root / ".agents" / "layers"
        return cls(root, path if path.is_absolute() else project / path, is_global)

    @property
    def lock(self) -> Path:
        return (self.root / ".agents" / LOCK_FILE) if self.is_global else self.root / LOCK_FILE


# -- fetching ------------------------------------------------------------------


def fetch(source: str, workdir: Path) -> tuple[dict[str, SemanticLayer], str | None]:
    """The layers a source offers, and its commit when it is a git repository."""
    local = Path(source).expanduser()
    if local.exists():
        root = local.resolve()
    else:
        url = f"https://github.com/{source}.git" if _GITHUB.match(source) else source
        root = workdir / "source"
        result = subprocess.run(
            ["git", "clone", "-q", "--depth", "1", url, str(root)], capture_output=True, text=True, check=False
        )
        if result.returncode != 0:
            raise InstallError(f"Could not fetch {source}: {result.stderr.strip()}")
    name = local.resolve().name if local.exists() else source.rstrip("/").rsplit("/", 1)[-1].removesuffix(".git")
    layers = find_layers(root, name)
    if not layers:
        raise InstallError(f"No semantic layer in {source}: no folder holding tables/, concepts/ or rules/.")
    return layers, _commit_of(root)


def _commit_of(path: Path) -> str | None:
    result = subprocess.run(["git", "-C", str(path), "rev-parse", "HEAD"], capture_output=True, text=True, check=False)
    return result.stdout.strip() or None if result.returncode == 0 else None


# -- the lock file ---------------------------------------------------------------


def read_lock(scope: Scope) -> dict:
    try:
        data = json.loads(scope.lock.read_text())
    except (OSError, ValueError):
        return {"version": 2, "layers": {}}
    data.setdefault("layers", {})
    return data


def write_lock(scope: Scope, data: dict) -> None:
    scope.lock.parent.mkdir(parents=True, exist_ok=True)
    data["version"] = 2
    data["layers"] = dict(sorted(data["layers"].items()))
    scope.lock.write_text(json.dumps(data, indent=2) + "\n")


# -- add -------------------------------------------------------------------------


def summary(layer: SemanticLayer) -> dict:
    kinds = {kind: sorted(n for n, p in layer.predicates.items() if p.kind == kind) for kind in FOLDERS}
    return {"name": layer.name, **{FOLDERS[k]: v for k, v in kinds.items()}}


def available(source: str) -> list[dict]:
    """The layers a source offers, with their tables, concepts and rules."""
    with tempfile.TemporaryDirectory() as tmp:
        layers, _ = fetch(source, Path(tmp))
        return [summary(layer) for layer in layers.values()]


def add(
    source: str,
    scope: Scope,
    layers: list[str] | None = None,
    *,
    force: bool = False,
    agents: list[str] | None = None,
    all_agents: bool = False,
) -> dict:
    """Install the layer folders ``layers`` (every one when empty) from ``source``."""
    lock = read_lock(scope)
    current = read_layers(scope.layers)
    with tempfile.TemporaryDirectory() as tmp:
        offered, commit = fetch(source, Path(tmp))
        wanted = layers or list(offered)
        unknown = [name for name in wanted if name not in offered]
        if unknown:
            raise InstallError(f"{source} has no layer {', '.join(unknown)}; it offers {', '.join(offered)}.")

        clashes = [
            name
            for name in wanted
            if name in current
            and (name not in lock["layers"] or current[name].digest != lock["layers"][name]["sha256"])
        ]
        if clashes and not force:
            raise InstallError(
                f"You already have layer(s) {', '.join(clashes)} that you wrote or changed: "
                "pass --force to replace their concepts and rules."
            )

        staged = Path(tmp) / "staged"
        errors = []
        for name in wanted:
            folder = _stage(offered[name], current.get(name), staged / name)
            errors += [f"{name}/{error}" for error in verify(folder)]
        if errors:
            raise InstallError("The layers would not verify; nothing was installed:\n  " + "\n  ".join(errors))

        scope.layers.mkdir(parents=True, exist_ok=True)
        for name in wanted:
            target = scope.layers / name
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(staged / name, target)
            lock["layers"][name] = {"source": source, "commit": commit, "sha256": SemanticLayer(name, target).digest}

    write_lock(scope, lock)
    told = install_companion(scope, agents or [], all_agents)
    return {"installed": wanted, "agents": told}


def _stage(offered: SemanticLayer, mine: SemanticLayer | None, folder: Path) -> Path:
    """The layer as it would be installed: the source's folder — its
    ``synalog.toml`` included, the database it was written for — with the
    user's tables and connection when the layer is already connected."""
    shutil.copytree(offered.path, folder, ignore=shutil.ignore_patterns(".git", *_LOCAL_FILES))
    if mine is not None and mine.connected:
        shutil.rmtree(folder / "tables", ignore_errors=True)
        if (mine.path / "tables").is_dir():
            shutil.copytree(mine.path / "tables", folder / "tables")
        for name in (*_LOCAL_FILES, PROJECT_FILE):
            if (mine.path / name).exists():
                shutil.copy2(mine.path / name, folder / name)
    return folder


# -- list / update -----------------------------------------------------------------


def installed(scope: Scope) -> list[dict]:
    """Every installed layer: where it came from, and whether it changed."""
    lock = read_lock(scope)
    current = read_layers(scope.layers)
    rows = []
    for name in sorted(set(lock["layers"]) | set(current)):
        entry = lock["layers"].get(name, {})
        layer = current.get(name)
        if layer is None:
            state = "missing"
        elif not entry:
            state = "local"
        else:
            state = "modified" if layer.digest != entry["sha256"] else "ok"
        rows.append(
            {
                "name": name,
                "source": entry.get("source", ""),
                "commit": entry.get("commit"),
                "connected": bool(layer and layer.connected),
                "state": state,
            }
        )
    return rows


def update(scope: Scope) -> dict:
    """Bring installed layers to their source's latest version. Layers
    modified locally are kept — and reported — rather than overwritten."""
    rows = [r for r in installed(scope) if r["source"]]
    kept = [r["name"] for r in rows if r["state"] == "modified"]
    updated: list[str] = []
    for source in sorted({r["source"] for r in rows}):
        names = [r["name"] for r in rows if r["source"] == source and r["state"] != "modified"]
        if names:
            updated += add(source, scope, names, force=True)["installed"]
    return {"updated": updated, "kept": kept}


# -- telling the agents ----------------------------------------------------------------


def _companion_text() -> str:
    return resources.files("semantic_layers").joinpath("companion/SKILL.md").read_text()


def _agents_section(scope: Scope) -> str:
    folder = scope.layers if scope.is_global else Path(*scope.layers.parts[len(scope.root.parts) :])
    return (
        f"{AGENTS_START}\n"
        "## Semantic layer\n\n"
        f"This project's business definitions are semantic layers in `{folder}/`: one\n"
        "folder per layer, each with `tables/`, `concepts/` and `rules/` — one synalog\n"
        "`.l` file per predicate, described by its front matter (`name`,\n"
        "`description`). Before answering a question about the data, search for the\n"
        "definitions that fit (`uvx semantic-layers search '<regex from the question>'`),\n"
        "read them, and answer by running them from\n"
        "their layer's folder (`uvx synalog rules/<Name>.l run <Name>`: the folder's\n"
        "`synalog.toml` names the database) — never by re-deriving a\n"
        "definition. Write new concepts and rules in the same format, inside the layer\n"
        "whose tables they use, and check them with synalog before saving them.\n"
        f"{AGENTS_END}\n"
    )


def install_companion(scope: Scope, agents: list[str], all_agents: bool) -> list[str]:
    """The companion Agent Skill (agent-neutral folder, plus each named or
    detected agent's) and the ``AGENTS.md`` section. Returns where it went."""
    told = []
    targets = [NEUTRAL_SKILL_DIR]
    names = set(AGENT_SKILL_DIRS) if all_agents else set(agents)
    for name, dirs in AGENT_SKILL_DIRS.items():
        detected = (
            (scope.root / dirs[0].split("/")[0]).is_dir()
            if not scope.is_global
            else Path(dirs[1]).expanduser().parent.is_dir()
        )
        if name in names or detected:
            targets.append(dirs)
            told.append(name)
    unknown = names - set(AGENT_SKILL_DIRS)
    if unknown:
        raise InstallError(f"Unknown agent(s): {', '.join(sorted(unknown))}. Known: {', '.join(AGENT_SKILL_DIRS)}.")
    for project_dir, global_dir in targets:
        folder = (Path(global_dir).expanduser() if scope.is_global else scope.root / project_dir) / "semantic-layers"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "SKILL.md").write_text(_companion_text())
    for name in told:  # the layers folder under each agent's own folder too
        link = (
            Path(AGENT_SKILL_DIRS[name][1]).expanduser().parent
            if scope.is_global
            else scope.root / AGENT_SKILL_DIRS[name][0].split("/")[0]
        ) / "layers"
        if not link.exists() and not link.is_symlink():
            link.symlink_to(scope.layers, target_is_directory=True)
    if not scope.is_global:
        _write_agents_md(scope)
        told.append("AGENTS.md")
    return told


def _write_agents_md(scope: Scope) -> None:
    path = scope.root / "AGENTS.md"
    text = path.read_text() if path.exists() else ""
    section = _agents_section(scope)
    if AGENTS_START in text and AGENTS_END in text:
        before, rest = text.split(AGENTS_START, 1)
        after = rest.split(AGENTS_END, 1)[1].lstrip("\n")
        text = before + section + after
    else:
        text = (text.rstrip("\n") + "\n\n" if text.strip() else "") + section
    path.write_text(text)
