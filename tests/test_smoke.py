"""Smoke tests to verify basic project setup."""

import pytest

from hjeon139_mcp_outofcontext import __version__


@pytest.mark.unit
def test_package_imports() -> None:
    """Verify the package can be imported and version is valid."""
    # Verify version is a string
    assert isinstance(__version__, str)

    # Parse version (expected format: major.minor.patch)
    version_parts = __version__.split(".")
    assert len(version_parts) == 3, f"Version should be in format X.Y.Z, got: {__version__}"

    # Validate each part is numeric
    major, minor, patch = version_parts
    assert major.isdigit(), f"Major version must be numeric, got: {major}"
    assert minor.isdigit(), f"Minor version must be numeric, got: {minor}"
    assert patch.isdigit(), f"Patch version must be numeric, got: {patch}"

    # Validate version is >= 1.0.0 (launch release)
    assert int(major) >= 1, f"Expected major version >= 1 (launched), got: {major}"


@pytest.mark.unit
def test_basic_assertion() -> None:
    """Verify pytest is working."""
    assert True
