"""Pydantic models for the Dataverse '/api/metadatablocks' schema response.

This models the *schema definition* JSON itself (block -> fields -> optional
recursive childFields), not an individual dataset's metadata values. Use it to
parse, validate, and query the schema (e.g. "what fields exist in the citation
block?", "is authorAffiliation required?", "what controlled vocab values does
subject accept?").
"""

# ruff: noqa: N815

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class MetadataField(BaseModel):
    """A single metadata field definition.

    For compound fields (typeClass == 'compound'), `childFields` holds the
    nested sub-fields, keyed by field name, recursively using this same model.
    Leaf fields (primitive or controlledVocabulary) have `childFields = None`.
    """

    model_config = ConfigDict(extra="ignore")  # tolerate any schema fields we did not model

    name: str
    displayName: str
    displayOnCreate: bool
    title: str
    type: str  # e.g. 'TEXT', 'TEXTBOX', 'DATE', 'INT', 'FLOAT', 'URL', 'EMAIL', 'NONE'
    typeClass: str  # 'primitive', 'compound', or 'controlledVocabulary'
    watermark: str = ""
    description: str = ""
    multiple: bool
    isControlledVocabulary: bool
    isAdvancedSearchFieldType: bool
    displayFormat: str = ""
    displayOrder: int
    isRequired: bool
    controlledVocabularyValues: list[str] | None = None
    childFields: dict[str, MetadataField] | None = None

    def is_compound(self) -> bool:
        """Return True if this field wraps nested childFields rather than holding a value directly."""
        return self.childFields is not None

    def iter_leaf_fields(self) -> list[MetadataField]:
        """Recursively collect every leaf (non-compound) field reachable from this field."""
        if self.childFields:
            leaves: list[MetadataField] = []
            for child in self.childFields.values():
                leaves.extend(child.iter_leaf_fields())
            return leaves
        return [self]


# Needed because MetadataField references itself by forward-reference string.
MetadataField.model_rebuild()


class MetadataBlock(BaseModel):
    """A single metadata block (e.g. citation, geospatial, astrophysics)."""

    model_config = ConfigDict(extra="ignore")

    id: int
    name: str
    displayName: str
    displayOnCreate: bool
    fields: dict[str, MetadataField]

    def get_field(self, field_name: str) -> MetadataField | None:
        """Look up a top-level field in this block by its key name."""
        return self.fields.get(field_name)

    def all_leaf_fields(self) -> dict[str, MetadataField]:
        """Flatten every leaf field in this block (including nested ones) into a single dict."""
        flat: dict[str, MetadataField] = {}
        for field in self.fields.values():
            for leaf in field.iter_leaf_fields():
                flat[leaf.name] = leaf
        return flat

    def required_fields(self) -> list[str]:
        """Return the names of all leaf fields marked isRequired = True."""
        return [name for name, field in self.all_leaf_fields().items() if field.isRequired]


class DataverseSchemaResponse(BaseModel):
    """Top-level wrapper matching the raw JSON returned by /api/metadatablocks."""

    model_config = ConfigDict(extra="ignore")

    status: str
    data: list[MetadataBlock]

    def get_block(self, block_name: str) -> MetadataBlock | None:
        """Look up a metadata block by its short name (e.g. 'citation', 'geospatial')."""
        return next((b for b in self.data if b.name == block_name), None)

    def block_names(self) -> list[str]:
        """List the short names of every block in the response."""
        return [b.name for b in self.data]


def load_schema(metadata: dict) -> DataverseSchemaResponse:
    """Parse a metadatablocks JSON payload (already loaded as a dict) into a DataverseSchemaResponse."""
    return DataverseSchemaResponse.model_validate(metadata)
