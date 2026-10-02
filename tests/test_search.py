"""Discovery: a regular expression over the front matter."""

import pytest
from samples import layer, scope

from semantic_layers.cli import main
from semantic_layers.install import add


def test_search_is_a_regex_over_front_matter(source, project, capsys, monkeypatch):
    from semantic_layers.layers import search

    add(str(source), scope(project))
    found = search(layer(project), "customer")
    assert [r["name"] for r in found][:2] == ["ActiveCustomer", "Customer"]
    assert found[0]["path"] == "sales/rules/ActiveCustomer.l"
    assert [r["name"] for r in search(layer(project), "open|still")] == ["OpenTickets"]
    assert [r["name"] for r in search(layer(project), r"deliver(ed|y)")] == ["ActiveCustomer"]
    assert [r["name"] for r in search(layer(project), "^orders")] == ["OrdersByStatus"]
    assert all(r["kind"] != "table" for r in search(layer(project), "order"))
    assert any(r["kind"] == "table" for r in search(layer(project), "order", kinds=("table", "concept", "rule")))
    with pytest.raises(ValueError, match="Invalid pattern"):
        search(layer(project), "(")
    monkeypatch.chdir(project)
    assert main(["search", "deliver"]) == 0
    assert "sales/rules/ActiveCustomer.l" in capsys.readouterr().out
