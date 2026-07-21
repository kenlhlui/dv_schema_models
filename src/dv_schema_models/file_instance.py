"""File representation models."""
# ruff: noqa: N815

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class DataFile(BaseModel):
    """The 'dataFile' object nested inside a FileInstance."""

    model_config = ConfigDict(extra="allow")

    id: int | None = None
    persistentId: str | None = None
    filename: str | None = None
    contentType: str | None = None
    friendlyType: str | None = None
    filesize: int | None = None
    description: str | None = None
    storageIdentifier: str | None = None
    rootDataFileId: int | None = None
    md5: str | None = None
    checksum: CheckSum | None = None
    tabularData: bool | None = None
    creationDate: str | None = None
    directoryLabel: str | None = None
    lastUpdateTime: str | None = None
    fileAccessRequest: bool | None = None

    def get_raw(self, key: str) -> object | None:
        """Get a raw top-level field not covered by the schema (requires extra='allow')."""
        return self.model_extra.get(key) if self.model_extra else None


class CheckSum(BaseModel):
    """The 'checksum' object nested inside a DataFile."""

    model_config = ConfigDict(extra="allow")

    type: str
    value: str

    def get_raw(self, key: str) -> object | None:
        """Get a raw top-level field not covered by the schema (requires extra='allow')."""
        return self.model_extra.get(key) if self.model_extra else None


class FileInstance(BaseModel):
    """One file, as it appears inside a dataset version."""

    model_config = ConfigDict(extra="allow")

    label: str | None = None
    restricted: bool | None = None
    directoryLabel: str | None = None
    version: int | None = None
    datasetVersionId: int | None = None
    dataFile: DataFile | None = None

    def get_raw(self, key: str) -> object | None:
        """Get a raw top-level field not covered by the schema (requires extra='allow')."""
        return self.model_extra.get(key) if self.model_extra else None

    @staticmethod
    def sum_field(instances: list[FileInstance], field: str) -> float | None:
        """Sum a DataFile field across FileInstances, skipping entries with no dataFile or None values.

        Returns None (and logs a warning) if any present value isn't int/float.
        """
        values = [getattr(i.dataFile, field) for i in instances if i.dataFile is not None]
        for v in values:
            if v is not None and not isinstance(v, (int, float)):
                logger.warning("sum_field: field %r has non-numeric value %r", field, v)
                return None
        return sum(v for v in values if v is not None)
