"""Fixtures: a source repository of two layers, and an empty project."""

import pytest
from samples import SALES, SUPPORT, write


@pytest.fixture
def source(tmp_path):
    """A repository of two layer folders."""
    root = tmp_path / "source"
    write(root / "sales", SALES)
    write(root / "support", SUPPORT)
    return root


@pytest.fixture
def project(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    return root
