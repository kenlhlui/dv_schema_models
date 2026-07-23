"""Test load_dataset."""

import json
from pathlib import Path

from dv_schema_models.dataset_instance import DatasetJson, load_dataset, safe_load_dataset

FIXTURES = Path(__file__).parent


def test_load_dataset_ok() -> None:
    """A normal `{status: OK, data: {...}}` payload parses into a DatasetJson."""
    metadata = json.loads((FIXTURES / "ds_metadata.json").read_text())
    result = load_dataset(metadata)
    assert isinstance(result, DatasetJson)


def test_load_dataset_error() -> None:
    """A `{status: ERROR, message: ...}` payload returns the message instead of raising."""
    metadata = json.loads((FIXTURES / "ds_metadata_error.json").read_text())
    result = safe_load_dataset(metadata)
    assert result == metadata["message"]


def test_load_dataset_error_no_message() -> None:
    """A `{status: ERROR}` payload with no message returns None instead of a synthesized string."""
    result = safe_load_dataset({"status": "ERROR"})
    assert result is None
