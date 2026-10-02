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
