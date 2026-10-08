"""The wordmark and the welcome screen, in the logo's purple.

Shown to people only: never when an agent runs the command (its output is
read, not looked at), nor when the output is piped. ``NO_COLOR`` drops the
colors (rich honours it).
"""

from __future__ import annotations

import os
import sys

from rich.console import Console
from rich.text import Text

LOGO = (
    "██╗      █████╗ ██╗   ██╗███████╗██████╗ ███████╗",
    "██║     ██╔══██╗╚██╗ ██╔╝██╔════╝██╔══██╗██╔════╝",
    "██║     ███████║ ╚████╔╝ █████╗  ██████╔╝███████╗",
    "██║     ██╔══██║  ╚██╔╝  ██╔══╝  ██╔══██╗╚════██║",
    "███████╗██║  ██║   ██║   ███████╗██║  ██║███████║",
    "╚══════╝╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚══════╝",
)
#: The logo's purple.
PURPLE = "#A866CF"
_LILAC = "#D7AFFF"

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
    ("run <layer>/<Name>", "Run a definition"),
    ("check", "Verify every definition"),
    ("list", "List installed layers"),
    ("update", "Update installed layers"),
    ("init <name>", "Create a new layer"),
)


def for_people() -> bool:
    return sys.stdout.isatty() and not any(os.environ.get(name) for name in AGENT_VARIABLES)


def show_logo() -> None:
    if not for_people():
        return
    console = Console(highlight=False)
    console.print()
    for line in LOGO:
        console.print(line, style=PURPLE)
    console.print()


def show_banner() -> bool:
    """The welcome screen of a bare ``semantic-layers``; False when nobody
    would look at it (the caller prints the usage instead)."""
    if not for_people():
        return False
    console = Console(highlight=False)
    show_logo()
    console.print("Business definitions your agents run, not paraphrase", style="dim")
    console.print()
    width = max(len(command) for command, _ in COMMANDS)
    for command, what in COMMANDS:
        console.print(
            Text.assemble(
                "  ", ("$ ", "dim"), ("uvx semantic-layers " + command.ljust(width), _LILAC), "  ", (what, "dim")
            )
        )
    console.print()
    console.print(Text.assemble(("try: ", "dim"), ("uvx semantic-layers add SynaLinks/semantic-layers", _LILAC)))
    console.print()
    return True
