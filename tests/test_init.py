"""Setting up a layer project, and publishing it."""

import sys

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

import pytest
from samples import SALES, layer, scope, write

from semantic_layers.cli import main
from semantic_layers.install import add
from semantic_layers.layers import verify


def test_init_sets_up_a_layer_project(tmp_path):
    from semantic_layers.init import init

    result = init(tmp_path / "sales", description="Orders and customers.")
    layer = tmp_path / "sales"
    assert result["name"] == "sales"
    assert {"tables/", "concepts/", "rules/", "layer.toml", "README.md", ".gitignore", ".git/"} <= set(
        result["created"]
    )
    assert "connection" not in tomllib.loads((layer / "layer.toml").read_text())  # not connected yet
    assert ".env" in (layer / ".gitignore").read_text().splitlines()
    assert "semantic-layers add <owner>/sales" in (layer / "README.md").read_text()
    (layer / "README.md").write_text("mine\n")
    with pytest.raises(ValueError, match="not empty: pass --force"):
        init(layer, description="Orders and customers.")
    assert init(layer, description="Orders and customers.", force=True)["created"] == []  # nothing overwritten
    assert (layer / "README.md").read_text() == "mine\n"
    with pytest.raises(ValueError, match="not a layer name"):
        init(tmp_path / "Bad_Name", description="x")
    with pytest.raises(ValueError, match="needs a description"):
        init(tmp_path / "undescribed")


def test_init_then_publish_then_add(tmp_path, project, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(["init", "sales", "--description", "Orders and customers."]) == 0
    assert "cd sales" in capsys.readouterr().out
    write(tmp_path / "sales", {k: v for k, v in SALES.items()})
    monkeypatch.chdir(tmp_path / "sales")
    assert main(["check", "."]) == 0
    assert "Everything verifies." in capsys.readouterr().out
    add(str(tmp_path / "sales"), scope(project))
    installed_layer = layer(project) / "sales"
    assert (installed_layer / "rules" / "ActiveCustomer.l").exists() and not (installed_layer / ".git").exists()
    assert verify(installed_layer) == []


def test_init_names_and_describes_the_layer(tmp_path):
    from semantic_layers.init import init

    init(tmp_path / "sales", description="Orders and customers.")
    data = tomllib.loads((tmp_path / "sales" / "layer.toml").read_text())
    assert data["project"] == {"name": "sales", "description": "Orders and customers."}


def test_init_asks_for_the_name_and_the_description(tmp_path, monkeypatch, capsys):
    """In a terminal, what is not given is asked; a bad name is asked again."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    answers = iter(["Bad_Name", "shop", "Orders of the shop."])
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))
    assert main(["init"]) == 0
    assert "not a layer name" in capsys.readouterr().err
    data = tomllib.loads((tmp_path / "shop" / "layer.toml").read_text())
    assert data["project"] == {"name": "shop", "description": "Orders of the shop."}


def test_init_without_a_terminal_says_what_to_pass(tmp_path, monkeypatch, capsys):
    """A coding agent has no terminal to answer in: it is told the flags."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)
    assert main(["init"]) == 1
    assert "init <name>' or with -n" in capsys.readouterr().err
    assert main(["init", "shop"]) == 1
    assert "-d" in capsys.readouterr().err
    assert not (tmp_path / "shop").exists()
    assert main(["init", "-n", "shop", "-d", "Orders of the shop."]) == 0
    assert (tmp_path / "shop" / "layer.toml").is_file()
    assert main(["init", "shop", "-d", "Again."]) == 1  # not empty
    assert "--force" in capsys.readouterr().err
