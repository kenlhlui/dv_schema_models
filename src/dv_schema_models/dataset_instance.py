"""Pydantic models for a Dataverse dataset export ('GET /api/datasets/:id' response).

This is the companion to dataverse_schema.py: that file models the *schema*
(what fields CAN exist and their rules), this file models actual *metadata
values* attached to one dataset. The shapes are different — here each field
is {typeName, multiple, typeClass, value}, and `value` itself is polymorphic
depending on typeClass/multiple:

  - primitive / controlledVocabulary, multiple=False -> a plain string
  - primitive / controlledVocabulary, multiple=True   -> a list of strings
  - compound, multiple=False                          -> a dict of nested fields
  - compound, multiple=True                           -> a list of dicts of nested fields
"""
# ruff: noqa: N815

from __future__ import annotations

import json
import pathlib
from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class DatasetFieldValue(BaseModel):
    """One metadata field value, as it appears inside metadataBlocks.<block>.fields."""

    model_config = ConfigDict(extra="ignore")

    typeName: str
    multiple: bool
    typeClass: str  # 'primitive', 'compound', or 'controlledVocabulary'
    value: (
        str
        | list[str]
        | dict[str, DatasetFieldValue]
        | list[dict[str, DatasetFieldValue]]
    )

    def simple_value(self) -> Any:
        """Recursively strip away the typeName/multiple/typeClass wrapper, returning plain Python values.

        Compound fields become plain dicts (or lists of dicts); primitive and
        controlledVocabulary fields are already plain strings or lists of strings.
        """
        if self.typeClass == "compound":
            if isinstance(self.value, list):
                return [
                    {k: v.simple_value() for k, v in item.items()}
                    for item in self.value
                ]
            if isinstance(self.value, dict):
                return {k: v.simple_value() for k, v in self.value.items()}
        return self.value

    def get_fields(self) -> list[DatasetFieldValue]:
        return [self.typeName for f in self.value]


# Needed because DatasetFieldValue references itself by forward-reference string.
DatasetFieldValue.model_rebuild()


class MetadataBlockInstance(BaseModel):
    """One populated metadata block (e.g. citation) within a dataset version."""

    model_config = ConfigDict(extra="ignore")

    displayName: str
    name: str
    fields: list[DatasetFieldValue]

    def field_names(self) -> list[str]:
        """Return the typeName of every field present in this block instance."""
        return [f.typeName for f in self.fields]

    def get_field(self, type_name: str) -> DatasetFieldValue | None:
        """Find a field in this block by its typeName (e.g. 'title', 'author')."""
        return next((f for f in self.fields if f.typeName == type_name), None)

    def get_value(self, type_name: str) -> Any:
        """Get the plain (unwrapped) value of a field in this block, or None if absent."""
        field = self.get_field(type_name)
        return field.simple_value() if field else None


class DatasetVersion(BaseModel):
    """One version of a dataset, holding the actual metadata block values and files."""

    model_config = ConfigDict(extra="ignore")

    id: int
    datasetId: int
    versionState: str
    datasetPersistentId: str
    datasetType: (
        str | None
    )  # backward compatibility: some datasets /older Dataverse versions don't have this field
    storageIdentifier: str
    internalVersionNumber: int
    versionState: str
    latestVersionPublishingState: str
    deaccessionLink: str | None
    UNF: str | None
    lastUpdateTime: str
    createTime: str
    termsOfUse: str | None
    termsOfAccess: str | None
    dataAccessPlace: str | None
    fileAccessRequest: bool

    metadataBlocks: dict[str, MetadataBlockInstance]

    def get_value(self, block_name: str, type_name: str) -> Any:
        """Get a field's plain value by block name (e.g. 'citation') and field typeName (e.g. 'title')."""
        block = self.metadataBlocks.get(block_name)
        return block.get_value(type_name) if block else None


class DatasetData(BaseModel):
    """The 'data' payload of a dataset export response."""

    model_config = ConfigDict(extra="ignore")

    id: int
    identifier: str
    persistentUrl: str
    protocol: str
    authority: str
    separator: str
    publisher: str
    storageIdentifier: str
    datasetType: (
        str | None
    )  # backward compatibility: some datasets /older Dataverse versions don't have this field

    latestVersion: DatasetVersion = Field(
        alias="latestVersion",
        validation_alias=AliasChoices(
            "datasetVersion",
            "latestVersion",
        ),
    )


class DatasetExport(BaseModel):
    """Top-level wrapper matching the raw JSON returned by GET /api/datasets/:id."""

    model_config = ConfigDict(extra="ignore")

    status: str
    data: DatasetData

    def get_value(self, block_name: str, type_name: str) -> Any:
        """Convenience shortcut: dataset.get_value('citation', 'title') straight from the top level."""
        return self.data.latestVersion.get_value(block_name, type_name)


def load_dataset(metadata: dict) -> DatasetExport:
    """Parse a dataset export JSON payload (already loaded as a dict) into a DatasetExport.

    Accepts either the full `{status, data: {...}}` export envelope, or a bare
    `data`-shaped payload (no envelope), by trying each model in turn.
    """
    if "data" in metadata:
        return DatasetExport.model_validate(metadata)
    return DatasetExport(status="OK", data=DatasetData.model_validate(metadata))
