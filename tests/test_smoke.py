"""Smoke tests to verify basic project setup."""

import pytest

from out_of_context import __version__


@pytest.mark.unit
def test_package_imports() -> None:
    """Verify the package can be imported."""
    assert __version__ == "0.1.0"


@pytest.mark.unit
def test_basic_assertion() -> None:
    """Verify pytest is working."""
    assert True
