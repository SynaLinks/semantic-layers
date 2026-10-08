"""The semantic-layers command."""

import shutil
from pathlib import Path

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
    assert "has no layer.toml" in capsys.readouterr().err
    assert main(["init", "shop", "--description", "Orders of the shop."]) == 0
    monkeypatch.chdir(tmp_path / "shop")
    assert main(["connect", "psql", "hots=x"]) == 1  # past the guard: the fields are checked
    assert "no field hots" in capsys.readouterr().err


def _sales_with_data(tmp_path, amounts=(30, 50)):
    """The example sales layer, installed, with its two tables as CSV files."""
    layers = tmp_path / ".agents" / "layers"
    shutil.copytree(Path(__file__).resolve().parents[1] / "layers" / "sales", layers / "sales")
    (tmp_path / "customers.csv").write_text("customer_id,country\n1,FR\n2,DE\n")
    orders = "".join(f"{i},{i},delivered,{a},2026-01-0{i}\n" for i, a in enumerate(amounts, 1))
    (tmp_path / "orders.csv").write_text("order_id,customer_id,status,amount,ordered_at\n" + orders)
    return layers / "sales", ["--load", "customers=customers.csv", "--load", "orders=orders.csv"]


def test_run_finds_a_definition_however_it_is_named(tmp_path, monkeypatch, capsys):
    layer, load = _sales_with_data(tmp_path)
    monkeypatch.chdir(tmp_path)
    for target in ("sales/RevenueByCountry", "sales/rules/RevenueByCountry.l"):  # the second as search prints it
        assert main(["run", target, *load]) == 0
        out = capsys.readouterr().out
        assert "| DE      | 50      |" in out and "2 rows" in out
    assert main(["run", "sales/RevenueByCountry", "--csv", "--limit", "1", *load]) == 0
    assert capsys.readouterr().out.splitlines() == ["country,revenue", "DE,50"]
    monkeypatch.chdir(layer)
    (layer / "customers.csv").write_text((tmp_path / "customers.csv").read_text())
    (layer / "orders.csv").write_text((tmp_path / "orders.csv").read_text())
    assert main(["run", "RevenueByCountry", *load]) == 0  # inside the layer: its name alone


def test_run_refuses_a_definition_whose_assertion_is_violated(tmp_path, monkeypatch, capsys):
    _, load = _sales_with_data(tmp_path, amounts=(30, -50))  # a refund counted as a sale
    monkeypatch.chdir(tmp_path)
    assert main(["run", "sales/RevenueByCountry", *load]) == 1
    err = capsys.readouterr().err
    assert "Assertion 'RevenueByCountry.positive' is violated" in err and '("DE")' in err
    assert main(["check", "sales", *load]) == 1  # check runs them on the same data
    assert "RevenueByCountry.positive" in capsys.readouterr().out


def test_run_says_what_is_missing(tmp_path, monkeypatch, capsys):
    _sales_with_data(tmp_path)
    monkeypatch.chdir(tmp_path)
    assert main(["run", "sales/RevenueByCountry"]) == 1  # no database, no data
    assert "sales is not connected" in capsys.readouterr().err
    assert main(["run", "sales/Nope"]) == 1
    assert "has no definition Nope" in capsys.readouterr().err
    assert main(["run", "nowhere/Revenue"]) == 1
    assert "No layer holds nowhere/Revenue" in capsys.readouterr().err
