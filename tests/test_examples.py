"""The example layers under layers/: they verify, and the repository installs them."""

from pathlib import Path

from semantic_layers.layers import find_layers, verify_layers

ROOT = Path(__file__).resolve().parents[1]


def test_example_layers_verify():
    assert verify_layers(ROOT / "layers") == []


def test_the_repository_is_a_source_of_its_examples():
    assert set(find_layers(ROOT, "semantic-layers")) == {"sales", "support"}
