"""The wordmark and the welcome screen, in the logo's purple.

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
#: The logo's purple (#A866CF), as a 256-color code.
_PURPLE = 134

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


def show_logo() -> None:
    if not for_people():
        return
    print()
    for line in LOGO:
        print(_color(f"38;5;{_PURPLE}", line))
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
