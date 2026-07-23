"""Pydantic models for a Dataverse dataset export (`GET /api/datasets/:id` response).

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
# ruff:file-ignore[mixed-case-variable-in-class-scope]

from __future__ import annotations

from typing import Any, Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from dv_schema_models.file_instance import FileInstance


class DatasetFieldValue(BaseModel):
    """One metadata field value, as it appears inside metadataBlocks.<block>.fields."""

    model_config = ConfigDict(extra="ignore")

    typeName: str
    multiple: bool
    typeClass: str  # 'primitive', 'compound', or 'controlledVocabulary'
    value: str | list[str] | dict[str, DatasetFieldValue] | list[dict[str, DatasetFieldValue]]

    def simple_value(self) -> Any:
        """Recursively strip away the typeName/multiple/typeClass wrapper, returning plain Python values.

        Compound fields become plain dicts (or lists of dicts); primitive and
        controlledVocabulary fields are already plain strings or lists of strings.
        """
        if self.typeClass == "compound":
            if isinstance(self.value, list):
                return [{k: v.simple_value() for k, v in item.items()} for item in self.value]
            if isinstance(self.value, dict):
                return {k: v.simple_value() for k, v in self.value.items()}
        return self.value

    def get_fields(self) -> list[DatasetFieldValue]:
        """Return a flat list of all DatasetFieldValue objects nested inside this one."""
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

    def get_subfield_values(self, type_name: str, subfield: str) -> list[Any]:
        """Collect one subfield from a compound field, e.g. get_subfield_values('author', 'authorName') -> ['Author1', 'Author2']."""
        value = self.get_value(type_name)
        items = value if isinstance(value, list) else [value] if value else []
        return [item[subfield] for item in items if subfield in item]


class DatasetVersion(BaseModel):
    """One version of a dataset, holding the actual metadata block values and files."""

    model_config = ConfigDict(extra="allow")

    id: int
    datasetId: int
    versionState: str
    datasetPersistentId: str
    datasetType: (
        str | None
    )  # backward compatibility: some datasets /older Dataverse versions don't have this field
    storageIdentifier: str
    versionNumber: int | None = None
    internalVersionNumber: int
    versionMinorNumber: int | None = None
    latestVersionPublishingState: str
    deaccessionLink: str | None = Field(None)
    UNF: str | None = Field(None)
    lastUpdateTime: str
    releaseTime: str | None = Field(None)
    createTime: str
    termsOfUse: str | None = Field(None)
    termsOfAccess: str | None = Field(None)
    dataAccessPlace: str | None = Field(None)
    fileAccessRequest: bool

    metadataBlocks: dict[str, MetadataBlockInstance]

    files: list[FileInstance] | None = None

    def get_value(self, block_name: str, type_name: str) -> Any:
        """Get a field's plain value by block name (e.g. 'citation') and field typeName (e.g. 'title')."""
        block = self.metadataBlocks.get(block_name)
        return block.get_value(type_name) if block else None

    def field_names(self, block_name: str) -> list[str]:
        """Get the typeNames of every field present in the given block (e.g. 'citation').

        Parameters
        ----------
        block_name
            The name of the metadata block (e.g. 'citation', 'geospatial').

        Returns
        -------
        list[str]
            A list of typeNames for the fields present in the specified block.

        """
        block = self.metadataBlocks.get(block_name)
        return block.field_names() if block else []

    def get_raw(self, key: str) -> object | None:
        """Get a raw top-level field not covered by the schema.

        Parameters
        ----------
        key
            The name of the top-level field to retrieve.

        Returns
        -------
        object | None
            The value of the specified field, or None if not found.


        """
        return self.model_extra.get(key) if self.model_extra else None


class IsPartOf(BaseModel):
    """The 'isPartOf' payload of a dataset export response.

    See: https://github.com/IQSS/dataverse/blob/dd1859dde249df8b0612ca3899b5f00fcc6d082e/src/main/java/edu/harvard/iq/dataverse/util/json/JsonPrinter.java#L533-L562 (v6.11)

    """  # ruff:ignore[doc-line-too-long]

    model_config = ConfigDict(extra="allow")

    type: str
    identifier: str
    isReleased: bool | None = None  # backward compatibility
    persistentIdentifier: str | None = None
    displayName: str
    isPartOf: IsPartOf | None = None  # recursive

    @staticmethod
    def get_field_list(node: IsPartOf | None, field_name: str, *, from_root: bool = False) -> list:
        """Return the values of a field from a node to the root.

        Parameters
        ----------
        node
            The node to start from. May be None, in which case an empty list is returned.

        field_name
            The name of the field to retrieve (e.g. 'identifier', 'displayName').

        from_root
            If True, return the values from the root to this node; if False, return from this node to the root.

        Returns
        -------
        list
            A list of the values of the specified field.

        """  # ruff:ignore[doc-line-too-long]
        values = []
        current = node

        while current is not None:
            values.append(getattr(current, field_name))
            current = current.isPartOf

        if not from_root:
            values.reverse()
        return values


class DatasetData(BaseModel):
    """The 'data' payload of a dataset export response."""

    model_config = ConfigDict(extra="allow")

    id: int
    identifier: str
    persistentUrl: str
    protocol: str
    authority: str
    separator: str
    publisher: str
    storageIdentifier: str
    isPartOf: IsPartOf | None = None
    datasetType: str | None = (
        None  # backward compatibility: some datasets /older Dataverse versions don't have this field
    )

    latestVersion: DatasetVersion | None = Field(
        None, validation_alias=AliasChoices("datasetVersion", "latestVersion")
    )  # Deaccessioned dataset does not have this field.

    @property
    def datasetVersion(self) -> DatasetVersion | None:
        """Supports both export and Native JSON endpoints.

        Returns
        -------
        DatasetVersion | None
            The latest version of the dataset, or None if not present.

        """
        return self.latestVersion

    def get_raw(self, key: str) -> object | None:
        """Get a raw top-level field not covered by the schema.

        Parameters
        ----------
        key
            The name of the top-level field to retrieve.

        Returns
        -------
        object | None
            The value of the specified field, or None if not found.

        """
        return self.model_extra.get(key) if self.model_extra else None


class DatasetJson(BaseModel):
    """Top-level wrapper matching the raw JSON returned by GET /api/datasets/:id."""

    model_config = ConfigDict(extra="ignore")

    status: Literal["OK", "ERROR"]
    data: DatasetData

    def get_value(
        self, block_name: str, type_name: str
    ) -> str | list[str] | dict[str, Any] | list[dict[str, Any]] | None:
        """Get the value of a field by its block and type names.

        Parameters
        ----------
            block_name: The name of the metadata block (e.g. 'citation', 'geospatial').
            type_name: The typeName of the field within that block (e.g. 'title', 'author').

        Returns
        -------
            str | list[str] | dict[str, Any] | list[dict[str, Any]] | None: The value of the specified field, or None if not found.

        """  # ruff:ignore[doc-line-too-long]
        return self.data.latestVersion.get_value(block_name, type_name)

    def field_names(self, block_name: str) -> list[str]:
        """Check what fields are present in a given block.

        Parameters
        ----------
            block_name: The name of the metadata block (e.g. 'citation', 'geospatial').

        Returns
        -------
            list[str]: A list of typeNames for the fields present in the specified block.

        """
        return self.data.latestVersion.field_names(block_name)


def load_dataset(metadata: dict) -> DatasetJson:
    """Parse a dataset export JSON payload (already loaded as a dict) into a DatasetExport.

    Accepts either the full `{status, data: {...}}` export envelope, or a bare
    `data`-shaped payload (no envelope), by trying each model in turn.

    Parameters
    ----------
    metadata
        The JSON payload from the Dataverse API, already loaded as a dict.

    Returns
    -------
    DatasetJson
        The parsed dataset.

    """
    if "data" in metadata:
        return DatasetJson.model_validate(metadata)
    return DatasetJson(status="OK", data=DatasetData.model_validate(metadata))


def safe_load_dataset(metadata: dict) -> DatasetJson | str | None:
    """Like `load_dataset`, but return the API's error message instead of raising when status is "ERROR".

    Parameters
    ----------
    metadata
        The JSON payload from the Dataverse API, already loaded as a dict.

    Returns
    -------
    DatasetJson | str | None
        The parsed dataset, or the API's error message (if any) if the status is "ERROR".

    """  # ruff:ignore[doc-line-too-long]
    if metadata.get("status") == "OK":
        return load_dataset(metadata)
    return metadata.get("message")
