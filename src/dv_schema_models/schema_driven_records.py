"""Build a Pydantic model FROM the Dataverse schema, then use it to validate real dataset values.

Workflow:
  1. Load the metadatablocks schema (dataverse_schema.py) -> know what fields exist, their
     types, whether they're required/multiple, and what compound sub-fields they contain.
  2. Dynamically build a Pydantic model that mirrors that schema exactly, using pydantic.create_model.
  3. Load a dataset export (dataset_instance.py) and flatten it to {typeName: value}.
  4. Validate that flat dict against the schema-derived model, so the actual metadata is checked
     against the same field names, required-ness, and structure the schema defines -- instead of
     a generic model that would accept any field.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, create_model

from dv_schema_models.dataset_instance import MetadataBlockInstance
from dv_schema_models.dataverse_schema import MetadataBlock, MetadataField

# Maps a Dataverse field 'type' to a Python type. Anything not listed here (TEXT, TEXTBOX,
# DATE, URL, EMAIL, and controlled-vocabulary text) is treated as a plain str.
_PRIMITIVE_TYPE_MAP: dict[str, type] = {"INT": int, "FLOAT": float}


def _python_type_for(field: MetadataField) -> type:
    """Map a leaf schema field's declared 'type' to a Python type."""
    return _PRIMITIVE_TYPE_MAP.get(field.type, str)


def _safe_identifier(name: str) -> str:
    """Turn a Dataverse field name that may contain dots (e.g. 'resolution.Spatial') into a valid Python identifier."""
    return name.replace(".", "_")


def build_record_model(
    source: MetadataBlock | MetadataField, *, model_name: str | None = None
) -> type[BaseModel]:
    """Recursively build a Pydantic model matching a schema MetadataBlock (or a compound MetadataField).

    The resulting model accepts exactly the fields the schema defines: correct nested structure
    for compound fields, List[...] wrapping for multiple=True fields, and required vs Optional
    matching isRequired.
    """
    if isinstance(source, MetadataBlock):
        fields = source.fields
        default_name = f"{source.name.capitalize()}Record"
    else:
        fields = source.childFields or {}
        default_name = f"{source.name.capitalize()}Record"

    field_definitions: dict[str, Any] = {}

    for field_name, field in fields.items():
        py_name = _safe_identifier(field_name)

        if field.is_compound():
            base_type: Any = build_record_model(
                field, model_name=f"{field_name.capitalize()}Record"
            )
        else:
            base_type = _python_type_for(field)

        if field.multiple:
            base_type = list[base_type]

        if not field.isRequired:
            base_type = Optional[base_type]
            default = None
        else:
            default = ...

        if py_name != field_name:
            # Field name isn't a valid Python identifier as-is -- alias back to the original.
            field_definitions[py_name] = (base_type, Field(default, alias=field_name))
        else:
            field_definitions[py_name] = (base_type, default)

    return create_model(
        model_name or default_name,
        __config__=ConfigDict(populate_by_name=True, extra="forbid"),
        **field_definitions,
    )


def flatten_instance(block_instance: MetadataBlockInstance) -> dict[str, Any]:
    """Turn a dataset export's field list into a flat {typeName: value} dict, ready to validate."""
    return {f.typeName: f.simple_value() for f in block_instance.fields}
