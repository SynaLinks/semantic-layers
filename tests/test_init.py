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


def test_init_asks_for_the_description(tmp_path, monkeypatch, capsys):
    """In a terminal, a missing description is asked: layer.toml needs it."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    answers = iter(["", "Orders of the shop."])  # an empty answer is asked again
    monkeypatch.setattr("click.termui.visible_prompt_func", lambda prompt: next(answers))
    assert main(["init", "shop"]) == 0
    data = tomllib.loads((tmp_path / "shop" / "layer.toml").read_text())
    assert data["project"] == {"name": "shop", "description": "Orders of the shop."}


def test_init_without_a_name_sets_up_the_current_folder(tmp_path, monkeypatch, capsys):
    """The current folder, named after it, even when it holds files already."""
    folder = tmp_path / "shop"
    folder.mkdir()
    (folder / "notes.md").write_text("mine\n")
    monkeypatch.chdir(folder)
    assert main(["init", "-d", "Orders of the shop."]) == 0
    out = capsys.readouterr().out
    assert "setting up the layer in the current folder" in out and "named 'shop'" in out
    assert "cd shop" not in out
    assert tomllib.loads((folder / "layer.toml").read_text())["project"]["name"] == "shop"
    assert (folder / "notes.md").read_text() == "mine\n"


def test_init_in_a_folder_that_is_no_layer_name(tmp_path, monkeypatch, capsys):
    folder = tmp_path / "My_Shop"
    folder.mkdir()
    monkeypatch.chdir(folder)
    assert main(["init", "-d", "Orders."]) == 1
    assert "the current folder names the layer" in capsys.readouterr().err
    assert not (folder / "layer.toml").exists()


def test_init_without_a_terminal_says_what_to_pass(tmp_path, monkeypatch, capsys):
    """A coding agent has no terminal to answer in: it is told the flag."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)
    assert main(["init", "shop"]) == 1
    assert 'pass it with -d "..."' in capsys.readouterr().err
    assert not (tmp_path / "shop").exists()
    assert main(["init", "-n", "shop", "-d", "Orders of the shop."]) == 0
    assert (tmp_path / "shop" / "layer.toml").is_file()
    assert main(["init", "shop", "-d", "Again."]) == 1  # not empty
    assert "--force" in capsys.readouterr().err


def test_layer_toml_shows_every_engine_ready_to_uncomment(tmp_path):
    """init's layer.toml carries, commented, each engine's [connection]: one
    uncommented is a connection synalog accepts, its secret named for .env."""
    import re

    from synalog import project

    from semantic_layers.init import init

    init(tmp_path / "sales", description="Orders and customers.")
    text = (tmp_path / "sales" / "layer.toml").read_text()
    blocks = re.findall(r"^# --- (.+) ---\n((?:# .*\n)+)", text, re.M)
    assert [label for label, _ in blocks] == [spec.label for spec in project.ENGINES.values()]
    for label, block in blocks:
        settings = "".join(line[2:] + "\n" for line in block.splitlines() if not line.startswith("#   "))
        path = tmp_path / label / "layer.toml"
        path.parent.mkdir()
        path.write_text(text + "\n" + settings)  # the block, uncommented, under the [project]
        connection = project.connection(path)
        assert connection is not None and project.ENGINES[connection["engine"]].label == label
        for field in project.ENGINES[connection["engine"]].fields:
            if field.secret:
                assert project.secret_env(connection["engine"], field.key) in block
