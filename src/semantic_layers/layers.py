"""Reading and verifying semantic layers.

A semantic layer is a folder holding up to
three folders: ``tables/``, ``concepts/``, ``rules/``. Each predicate is one
``.l`` file in them: YAML front matter (read with synalog, which also checks
it), ``import`` lines for the predicates it builds on, then its synalog. The
front matter's ``name`` is the predicate that runs — one the file defines,
beside any helpers — and, by convention, the file's name; its kind is the
folder; the layer's name is its folder's.

A layer is self-contained: synalog resolves ``import tables.Orders.Orders;``
from the layer's folder, so everything a layer imports is inside it — its
tables included. Installed layers sit side by side in a layers folder
(``.agents/layers/``).
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import synalog
import yaml

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib

FOLDERS = {"table": "tables", "concept": "concepts", "rule": "rules"}
KINDS = {folder: kind for kind, folder in FOLDERS.items()}

_IMPORT = re.compile(r"^import\s+(tables|concepts|rules)\.(\w+)\.(\w+)\s*;", re.MULTILINE)
#: synalog's rewrite of a predicate with several aggregating or distinct
#: bodies — every recursive one — is one ``<Name>_MultBodyAggAux`` rule per body.
_AUX = "_MultBodyAggAux"
_IMPORT_LINE = re.compile(r"^import\s+[\w.]+\s*;[ \t]*$", re.MULTILINE)
_DECLARATION = re.compile(r"^\s*(?P<name>\w+)\((?P<args>[^)]*)\)\s*:-\s*(?P<physical>[\w.]+)\(", re.MULTILINE)


@dataclass
class Predicate:
    """One ``.l`` file of a layer."""

    name: str
    kind: str
    path: Path
    text: str
    meta: dict = field(default_factory=dict)

    @property
    def relative(self) -> str:
        return f"{FOLDERS[self.kind]}/{self.name}.l"

    @property
    def description(self) -> str:
        return str(self.meta.get("description") or "").strip()

    @property
    def imports(self) -> list[tuple[str, str]]:
        """``(kind, name)`` of every predicate this one imports."""
        return [(KINDS[folder], name) for folder, _module, name in _IMPORT.findall(self.text)]

    @property
    def columns(self) -> list[str]:
        """A table's declared columns."""
        match = _DECLARATION.search(self.text)
        if not match:
            return []
        return [a.strip().split(":")[0].strip() for a in match["args"].split(",") if a.strip()]


@dataclass
class SemanticLayer:
    """A layer folder."""

    name: str
    path: Path

    @property
    def predicates(self) -> dict[str, Predicate]:
        return read_predicates(self.path)

    @property
    def digest(self) -> str:
        """The layer's concepts and rules — what its author wrote. Tables are
        left out: ``connect`` regenerates them from your database."""
        h = hashlib.sha256()
        for p in sorted(self.predicates.values(), key=lambda p: p.relative):
            if p.kind != "table":
                h.update(p.relative.encode() + b"\0" + p.text.encode() + b"\0")
        return h.hexdigest()

    @property
    def connected(self) -> bool:
        """Whether its ``synalog.toml`` names a database (a ``[connection]``)."""
        return "connection" in _project_file(self.path)

    @property
    def description(self) -> str:
        """What the layer is about: its ``synalog.toml``'s ``[project]``."""
        return str(read_project(self.path).get("description") or "").strip()


def _project_file(folder: Path) -> dict:
    """A layer's ``synalog.toml``, parsed (``{}`` without one, or unreadable)."""
    path = folder / "synalog.toml"
    try:
        return tomllib.loads(path.read_text()) if path.is_file() else {}
    except tomllib.TOMLDecodeError:
        return {}


def read_project(folder: Path) -> dict:
    """The ``[project]`` table of a layer's ``synalog.toml``: its ``name`` and
    ``description`` (``{}`` without one)."""
    table = _project_file(folder).get("project")
    return table if isinstance(table, dict) else {}


def front_matter(text: str) -> dict:
    """The file's front matter, or ``{}`` when it has none or it is not valid
    YAML (``verify`` reports why, from synalog's own check)."""
    raw = synalog.front_matter(text)
    try:
        meta = yaml.safe_load(raw) if raw else None
    except yaml.YAMLError:
        return {}
    return meta if isinstance(meta, dict) else {}


def defined(text: str) -> list[str]:
    """The predicates a file defines itself — not its imports', not its
    ``@`` directives. Empty when it does not parse (``check`` says why)."""
    try:
        ast = json.loads(synalog.parse(_IMPORT_LINE.sub("", text)))
    except ValueError:
        return []
    return list(dict.fromkeys(name for rule in ast.get("rule", []) if (name := _defines(rule))))


def _defines(rule: dict) -> str | None:
    """The predicate a parsed rule defines: its head, or — for a functor,
    ``New := Generic(...)``, parsed as an ``@Make`` directive — the new
    predicate. ``None`` for every other directive."""
    head = rule["head"]
    if head["predicate_name"] == "@Make":
        first = head["record"]["field_value"][0]["value"]["expression"]["literal"]
        return first["the_predicate"]["predicate_name"]
    name = head["predicate_name"].removesuffix(_AUX)
    return None if name.startswith("@") else name


def read_predicates(layer: Path) -> dict[str, Predicate]:
    """Every predicate of the layer folder ``layer``, by name (empty if absent)."""
    found: dict[str, Predicate] = {}
    for folder, kind in KINDS.items():
        for path in sorted((layer / folder).glob("*.l")):
            text = path.read_text()
            found[path.stem] = Predicate(path.stem, kind, path, text, front_matter(text))
    return found


def is_layer(path: Path) -> bool:
    return path.is_dir() and any((path / folder).is_dir() for folder in FOLDERS.values())


def read_layers(folder: Path) -> dict[str, SemanticLayer]:
    """The layers in ``folder``: its sub-folders that are layers."""
    if not folder.is_dir():
        return {}
    return {p.name: SemanticLayer(p.name, p) for p in sorted(folder.iterdir()) if is_layer(p)}


def find_layers(root: Path, name: str) -> dict[str, SemanticLayer]:
    """The layers a fetched source offers. A source is one layer (the three
    folders at its root, named ``name``) or holds several, as sub-folders of
    its root, ``layers/``, ``layers/`` or ``.agents/layers/``."""
    if is_layer(root):
        name = str(read_project(root).get("name") or name)
        return {name: SemanticLayer(name, root)}
    for candidate in (root, root / "layers", root / "layers", root / ".agents" / "layers"):
        layers = read_layers(candidate)
        if layers:
            return layers
    return {}


def verify(layer: Path) -> list[str]:
    """Check every predicate of a layer folder with synalog, imports resolved
    from the folder. Returns ``"<file>: <error>"`` lines, empty when it checks."""
    errors: list[str] = []
    for p in read_predicates(layer).values():
        try:
            problems = synalog.check(p.text, import_root=[str(layer)])
        except ValueError as exc:
            problems = [str(exc).strip().splitlines()[-1]]
        if not problems:
            own = defined(p.text)
            if "name" not in p.meta:
                problems = [f"its front matter has no name: the predicate that runs, one of {', '.join(own)}"]
            elif p.meta["name"] not in own:
                problems = [f"its front matter names '{p.meta['name']}', which it does not define ({', '.join(own)})"]
        errors.extend(f"{p.relative}: {problem}" for problem in problems)
    return errors + _check_project_file(layer)


def _check_project_file(layer: Path) -> list[str]:
    """``synalog.toml`` reads as TOML, and its ``[project]`` name — when it
    gives one — is the layer's folder name."""
    path = layer / "synalog.toml"
    if not path.is_file():
        return []
    try:
        data = tomllib.loads(path.read_text())
    except tomllib.TOMLDecodeError as exc:
        return [f"synalog.toml: {exc}"]
    named = (data.get("project") or {}).get("name") if isinstance(data.get("project"), dict) else None
    folder = layer.resolve().name
    if named and named != folder:
        return [f"synalog.toml: names the layer '{named}', but its folder is '{folder}' — they must match"]
    return []


def verify_layers(folder: Path) -> list[str]:
    """``verify`` for every layer in ``folder``, lines prefixed with the layer."""
    return [f"{name}/{error}" for name, layer in read_layers(folder).items() for error in verify(layer.path)]


# -- discovery -----------------------------------------------------------------


def search(folder: Path, pattern: str, limit: int = 20, kinds: tuple[str, ...] = ("concept", "rule")) -> list[dict]:
    """The definitions of the layers in ``folder`` whose front matter matches ``pattern``, a
    regular expression (case-insensitive, like synalog's own search), best
    first: a match in the ``name`` ranks above one in the ``keywords``,
    above one in the ``description``.

    Discovery reads front matter only, never the definitions: a layer of
    thousands stays one command away. Raises ``ValueError`` on an invalid
    pattern.
    """
    try:
        regex = re.compile(pattern, re.IGNORECASE)
    except re.error as exc:
        raise ValueError(f"Invalid pattern {pattern!r}: {exc}") from None
    found = []
    for layer in read_layers(folder).values():
        for p in layer.predicates.values():
            if p.kind not in kinds:
                continue
            name = str(p.meta.get("name") or p.name)
            keywords = p.meta.get("keywords") or []
            keywords = " ".join(map(str, keywords if isinstance(keywords, list) else [keywords]))
            score = sum(weight for weight, text in ((3, name), (2, keywords), (1, p.description)) if regex.search(text))
            if score:
                found.append(
                    {
                        "layer": layer.name,
                        "kind": p.kind,
                        "name": name,
                        "description": p.description,
                        "path": f"{layer.name}/{p.relative}",
                        "score": score,
                    }
                )
    found.sort(key=lambda r: (-r["score"], r["layer"], r["name"]))
    return found[:limit]
