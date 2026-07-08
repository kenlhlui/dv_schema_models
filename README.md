# dv_schema_models

Pydantic models for Dataverse metadata — parse the schema, load dataset 
exports, and validate field values against the schema.

> [!CAUTION]
> This library is under active development and the API is not yet stable. Breaking changes may occur between releases. Please pin to a specific version in your `pyproject.toml` or `requirements.txt` if you want to avoid surprises.

## Pre-requisites
1. Python 3.13+ 

## Installation

1. With `uv` (recommended):
```bash
uv add dv_schema_models
```

2. With `pip`:
```bash
pip install dv_schema_models
```

## Concepts

| Thing | What it is |
|---|---|
| **Schema** | `/api/metadatablocks` response — defines what fields *can* exist, their types, and rules |
| **Dataset instance** | `GET /api/datasets/:id` response — the actual metadata values for one dataset |
| **Record model** | A Pydantic model *generated from* the schema, used to validate instance values |

## Usage

### 1. Load and query the schema

```python
import json
from dv_schema_models.dataverse_schema import load_schema

schema = load_schema(json.load(open("dv_schema.json")))

schema.block_names()                        # ['citation', 'geospatial', ...]
block = schema.get_block("citation")
block.fields.keys()                         # top-level field names
block.required_fields()                     # leaf fields where isRequired=True
block.all_leaf_fields()                     # flattened, including nested compound fields

field = block.get_field("keyword")
field.is_compound()                         # True — has childFields
field.iter_leaf_fields()                    # [keywordValue, keywordVocabulary, ...]
```

### 2. Load a dataset and read values

```python
import json
from dv_schema_models.dataset_instance import load_dataset

dataset = load_dataset(json.load(open("ds_metadata.json")))

# Load the possible typeNames for a given block
dataset.field_names("citation")  # ['title', 'author', 'keyword', ...] 
dataset.data.latestVersion.metadataBlocks.get("citation").field_names() # same


# Shortcut from the top level
dataset.get_value("citation", "title")      # plain string

# Or drill down
block = dataset.data.latestVersion.metadataBlocks.get("citation")
block.get_value("keyword")                  # unwrapped Python value (str / list / dict)
block.get_field("author").simple_value()    # [{'authorName': 'Author1', 'authorAffiliation': 'Author1Aff'...} ... {'authorName': 'Author2', 'authorAffiliation': 'Author2Aff'...}]
```

### 3. Validate instance values against the schema

```python
import json
from dv_schema_models.dataverse_schema import load_schema
from dv_schema_models.dataset_instance import load_dataset
from dv_schema_models.schema_driven_records import build_record_model, flatten_instance


schema = load_schema(json.load(open("dv_schema.json")))
dataset = load_dataset(json.load(open("ds_metadata.json")))

citation_schema = schema.get_block("citation")
CitationRecord = build_record_model(citation_schema)   # dynamic Pydantic model

block = dataset.data.latestVersion.metadataBlocks.get("citation")
raw = flatten_instance(block)              # {typeName: value, ...}
record = CitationRecord.model_validate(raw)
```

The generated model enforces field names, required/optional status, list wrapping for `multiple=True` fields, and `int`/`float` types where declared by the schema.

### 4. Discover available fields

```python
# Fields actually present in this dataset instance
block = dataset.data.latestVersion.metadataBlocks.get("citation")
block.field_names()                            # e.g. ['title', 'author', 'keyword', ...]

# All fields the schema defines (including absent/optional ones)
schema.get_block("citation").all_leaf_fields().keys()

# After validation, access as typed attributes
record = CitationRecord.model_validate(flatten_instance(block))
record.title          # str
record.author         # list[...] for multiple=True compound fields
record.keyword        # None if not present in this dataset (optional fields default to None)
# Note: field names with dots become underscores — e.g. 'resolution.Spatial' → record.resolution_Spatial
```

## Input file shapes

**Schema** — output of Dataverse `/api/metadatablocks`:
```json
{"status": "OK", "data": [{"id": 10, "name": "citation", "fields": {...}}]}
```

**Dataset** — output of Dataverse `GET /api/datasets/:id`:
```json
{"status": "OK", "data": {"latestVersion": {"metadataBlocks": {"citation": {"fields": [...]}}}}}
```

## Citation
If you use this library in your work, please cite according to [CITATION](CITATION.cff)

## License
[MIT](LICENSE)