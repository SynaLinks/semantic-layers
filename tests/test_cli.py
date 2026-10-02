"""The semantic-layers command."""

from semantic_layers.cli import main


def test_cli(source, project, monkeypatch, capsys):
    monkeypatch.chdir(project)
    assert main(["add", str(source), "--list"]) == 0
    out = capsys.readouterr().out
    assert "sales" in out and "ActiveCustomer" in out
    assert main(["add", str(source), "--layer", "support"]) == 0
    assert main(["check"]) == 0
    assert main(["check", "support"]) == 0
    assert main(["list"]) == 0
    assert "support" in capsys.readouterr().out


def test_connect_runs_only_in_a_folder_with_synalog_toml(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(["connect", "psql", "host=h"]) == 1
    assert "has no synalog.toml" in capsys.readouterr().err
    assert main(["init", "shop", "--description", "Orders of the shop."]) == 0
    monkeypatch.chdir(tmp_path / "shop")
    assert main(["connect", "psql", "hots=x"]) == 1  # past the guard: the fields are checked
    assert "no field hots" in capsys.readouterr().err
