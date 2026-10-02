"""Installing, listing and updating layers from a source."""

import json
import subprocess
import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

import pytest
from samples import ORDERS, SALES, SUPPORT, connected_sales, layer, scope, write

from semantic_layers.install import AGENTS_START, InstallError, Scope, _agents_section, add, installed, update
from semantic_layers.layers import verify_layers


def test_add_everything(source, project):
    result = add(str(source), scope(project))
    assert result["installed"] == ["sales", "support"]
    assert (layer(project) / "sales" / "rules" / "ActiveCustomer.l").read_text() == SALES["rules/ActiveCustomer.l"]
    assert (layer(project) / "support" / "tables" / "Tickets.l").exists()
    assert verify_layers(layer(project)) == []
    lock = json.loads((project / "semantic-layers-lock.json").read_text())
    assert set(lock["layers"]) == {"sales", "support"} and lock["layers"]["sales"]["source"] == str(source)
    assert result["agents"] == ["AGENTS.md"]
    assert AGENTS_START in (project / "AGENTS.md").read_text()
    assert not (project / ".agents" / "skills").exists() and not (project / "CLAUDE.md").exists()


def test_add_one_layer_folder(source, project):
    assert add(str(source), scope(project), ["support"])["installed"] == ["support"]
    assert not (layer(project) / "sales").exists()
    with pytest.raises(InstallError, match="no layer nope"):
        add(str(source), scope(project), ["nope"])


def test_a_source_can_be_one_layer(source, project):
    add(str(source / "sales"), scope(project))
    assert (layer(project) / "sales" / "concepts" / "Customer.l").exists()


def test_connected_layer_keeps_its_tables_and_connection(source, project):
    folder = connected_sales(project)
    add(str(source), scope(project), ["sales"], force=True)
    assert "description: Mine." in (folder / "tables" / "Orders.l").read_text()
    assert not (folder / "tables" / "Customers.l").exists()
    assert tomllib.loads((folder / "synalog.toml").read_text())["connection"]["host"] == "h"
    assert (folder / ".env").read_text() == 'SYNALOG_PSQL_PASSWORD="p"\n'
    assert (folder / "rules" / "ActiveCustomer.l").exists()


def test_missing_column_in_your_tables_is_refused(source, project):
    folder = connected_sales(project, ORDERS.replace("status:, ", ""))
    with pytest.raises(InstallError, match="sales/rules/.*status"):
        add(str(source), scope(project), ["sales"], force=True)
    assert not (folder / "rules").exists()
    assert not (project / "semantic-layers-lock.json").exists()


def test_your_own_layer_is_not_replaced_without_force(source, project):
    write(layer(project) / "sales", {"rules/OrdersByStatus.l": SALES["rules/OrdersByStatus.l"]})
    with pytest.raises(InstallError, match="sales"):
        add(str(source), scope(project))
    add(str(source), scope(project), force=True)
    assert (layer(project) / "sales" / "concepts" / "Customer.l").exists()


def test_unverifiable_source_installs_nothing(source, project):
    path = source / "sales" / "rules" / "OrdersByStatus.l"
    path.write_text(SALES["rules/OrdersByStatus.l"].replace("Orders(status:)", "Nope(status:)"))
    with pytest.raises(InstallError, match="would not verify"):
        add(str(source), scope(project))
    assert not layer(project).exists()
    assert not (project / "semantic-layers-lock.json").exists()


def test_list_and_update(source, project):
    add(str(source), scope(project))
    write(layer(project), {"mine/rules/X.l": "---\nname: X\n---\nX(a: 1);\n"})
    sales = layer(project) / "sales" / "rules" / "ActiveCustomer.l"
    sales.write_text(SALES["rules/ActiveCustomer.l"].replace("Customers with", "Clients with"))
    states = {row["name"]: row["state"] for row in installed(scope(project))}
    assert states == {"mine": "local", "sales": "modified", "support": "ok"}
    path = source / "support" / "rules" / "OpenTickets.l"
    path.write_text(SUPPORT["rules/OpenTickets.l"].replace("Tickets still open.", "Every open ticket."))
    result = update(scope(project))
    assert result == {"updated": ["support"], "kept": ["sales"]}
    assert "Every open ticket." in (layer(project) / "support" / "rules" / "OpenTickets.l").read_text()
    assert "Clients with" in sales.read_text()


def test_agents_md_section_is_not_duplicated(source, project):
    (project / "AGENTS.md").write_text("# My project\n\nKeep this.\n")
    add(str(source), scope(project))
    add(str(source), scope(project), force=True)
    text = (project / "AGENTS.md").read_text()
    assert text.count(AGENTS_START) == 1 and "Keep this." in text


def test_claude_code_gets_the_section_in_claude_md(source, project):
    (project / ".claude").mkdir()
    result = add(str(source), scope(project))
    assert result["agents"] == ["AGENTS.md", "CLAUDE.md"]
    assert AGENTS_START in (project / "CLAUDE.md").read_text()
    assert not (project / ".claude" / "skills").exists()


def test_an_agent_can_be_named(source, project):
    assert add(str(source), scope(project), agents=["claude-code"])["agents"] == ["AGENTS.md", "CLAUDE.md"]
    with pytest.raises(InstallError, match="Unknown agent"):
        add(str(source), scope(project), agents=["nope"], force=True)


def test_the_users_layers_tell_no_project(source, project, monkeypatch):
    monkeypatch.setenv("HOME", str(project))
    assert add(str(source), Scope.resolve(project, is_global=True))["agents"] == []
    assert not (project / "AGENTS.md").exists()


def test_git_source_records_its_commit(source, project):
    for cmd in (
        ["init", "-q"],
        ["add", "-A"],
        ["-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "layers"],
    ):
        subprocess.run(["git", "-C", str(source), *cmd], check=True)
    add(str(source), scope(project))
    commit = json.loads((project / "semantic-layers-lock.json").read_text())["layers"]["sales"]["commit"]
    assert commit and len(commit) == 40


def test_the_docs_show_the_section_agents_get(tmp_path):
    shown = (Path(__file__).resolve().parents[1] / "docs" / "agents-section.md").read_text()
    assert shown == _agents_section(Scope.resolve(tmp_path))
