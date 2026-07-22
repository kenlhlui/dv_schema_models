"""Test dv_schema_models."""

import dv_schema_models


def test_import() -> None:
    """Test that the package can be imported."""
    assert isinstance(dv_schema_models.__name__, str)
