"""The logo and the welcome screen: the onion of the project's logo (sliced,
its lid lifted, its rings in view) beside the wordmark, in the logo's
lilac-to-purple.

Shown to people only: never when an agent runs the command (its output is
read, not looked at), nor when the output is piped. ``NO_COLOR`` drops the
colors.
"""

from __future__ import annotations

import os
import sys

LOGO = (
    "██╗      █████╗ ██╗   ██╗███████╗██████╗ ███████╗",
    "██║     ██╔══██╗╚██╗ ██╔╝██╔════╝██╔══██╗██╔════╝",
    "██║     ███████║ ╚████╔╝ █████╗  ██████╔╝███████╗",
    "██║     ██╔══██║  ╚██╔╝  ██╔══╝  ██╔══██╗╚════██║",
    "███████╗██║  ██║   ██║   ███████╗██║  ██║███████║",
    "╚══════╝╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚══════╝",
)
#: The logo's lilac to purple, one per wordmark line (256-color codes).
_PURPLES = (225, 219, 183, 177, 141, 135)

#: The onion, line by line: (text, color) segments, color None for the
#: terminal's own. Sprouts, the lifted lid, the slice of rings, the face.
_SPROUT, _SKIN, _RINGS, _FACE = 114, 177, 225, 183
MASCOT = (
    (("     \\ /    ", _SPROUT),),
    (("   .-'^'-.  ", _SKIN),),
    (("  (_______) ", _SKIN),),
    (("  ( ", _SKIN), ("((@))", _RINGS), (" ) ", _SKIN)),
    (("  ( ", _SKIN), ("◕ ‿ ◕", _FACE), (" ) ", _SKIN)),
    (("  `-.___.-' ", _SKIN),),
)

#: Set by the coding agents that run commands (the list the Agent Skills CLI
#: checks, through @vercel/detect-agent).
AGENT_VARIABLES = (
    "AI_AGENT",
    "CLAUDECODE",
    "CLAUDE_CODE",
    "CODEX_SANDBOX",
    "CODEX_THREAD_ID",
    "CODEX_CI",
    "CURSOR_AGENT",
    "CURSOR_TRACE_ID",
    "GEMINI_CLI",
    "OPENCODE_CLIENT",
    "AUGMENT_AGENT",
    "ANTIGRAVITY_AGENT",
    "COPILOT_MODEL",
)

COMMANDS = (
    ("add <owner>/<repo>", "Install semantic layers"),
    ("connect <engine> ...", "Connect the layer in this folder"),
    ("search <regex>", "Find definitions"),
    ("list", "List installed layers"),
    ("update", "Update installed layers"),
    ("check", "Verify every definition"),
    ("init [name]", "Create a new layer"),
)


def for_people() -> bool:
    return sys.stdout.isatty() and not any(os.environ.get(name) for name in AGENT_VARIABLES)


def _color(code: str, text: str) -> str:
    return text if os.environ.get("NO_COLOR") else f"\x1b[{code}m{text}\x1b[0m"


def _mascot_line(segments) -> str:
    return "".join(_color(f"38;5;{color}", text) if color else text for text, color in segments)


def show_logo() -> None:
    if not for_people():
        return
    print()
    for segments, line, shade in zip(MASCOT, LOGO, _PURPLES, strict=True):
        print(f"{_mascot_line(segments)}  {_color(f'38;5;{shade}', line)}")
    print()


def show_banner() -> bool:
    """The welcome screen of a bare ``semantic-layers``; False when nobody
    would look at it (the caller prints the usage instead)."""
    if not for_people():
        return False
    dim = lambda text: _color("38;5;102", text)  # noqa: E731
    lilac = lambda text: _color("38;5;183", text)  # noqa: E731
    show_logo()
    print(dim("Business definitions your agents run, not paraphrase"))
    print()
    width = max(len(command) for command, _ in COMMANDS)
    for command, what in COMMANDS:
        print(f"  {dim('$')} {lilac('uvx semantic-layers ' + command.ljust(width))}  {dim(what)}")
    print()
    print(f"{dim('try:')} {lilac('uvx semantic-layers add SynaLinks/semantic-layers')}")
    print()
    return True
