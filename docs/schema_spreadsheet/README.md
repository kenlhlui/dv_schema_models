# Schema spreadsheet

Turns a Dataverse `/api/metadatablocks` schema into a human-readable `.xlsx`
workbook — one worksheet per metadata block, plus a combined **All** sheet.

Requires the `spreadsheet` extra:

```bash
uv add "dv_schema_models[spreadsheet]"   # or: pip install "dv_schema_models[spreadsheet]"
```

## Usage

```python
import json
from dv_schema_models.dataverse_schema import load_schema
from dv_schema_models.schema_spreadsheet import SchemaSpreadsheet

schema = load_schema(json.load(open("dv_schema.json")))
SchemaSpreadsheet(schema).write("dv_schema.xlsx")
```

That's the whole API: construct with a parsed `DataverseSchemaResponse`, call
`write(path)`, get the `Path` of the written file back.

## Output layout

Worksheets, in order:

1. **All** — every block stacked on one sheet
2. One sheet per block, sorted by the block's schema `id` (so `Citation`
   first). Sheet names are the block's `displayName` with the trailing
   " Metadata" stripped, truncated to Excel's 31-char limit
   (e.g. `Citation`, `Geospatial`, `3D Objects`).

Each sheet:

| Row | Content |
|---|---|
| 1 | Header: `Field`, `Definition`, `Usage`, `Repeatable (Y/N)`, `Example` |
| 2 | Merged block-title row, e.g. "Citation Metadata Block" (on **All**, one per block) |
| 3+ | Field rows, sorted by `displayOrder` |

Field-row formatting:

- **Top-level fields are bold.** A leaf top-level field (e.g. *Title*) is a
  single row with all columns filled.
- A **compound field** (e.g. *Author*) gets a bold parent row carrying only
  the definition, followed by unbolded child rows (*Name*, *Affiliation*, …)
  carrying Usage/Repeatable/Example.
- The **last row of each field group has a bottom border**, visually closing
  the group.

## Column mapping

| Column | Schema source |
|---|---|
| Field | `title` |
| Definition | `description` |
| Usage | `isRequired` → `RQ`, otherwise `O` |
| Repeatable (Y/N) | `multiple` → `Y`/`N`; a child of a repeatable compound is always `Y` |
| Example | `watermark` |

The schema has no "recommended" flag, so the three-level `RQ`/`R`/`O` usage
scale seen in some curated Dataverse documentation collapses to `RQ`/`O` here.

## Architecture

Everything lives in [`src/dv_schema_models/schema_spreadsheet.py`](../../src/dv_schema_models/schema_spreadsheet.py),
one class, three moving parts:

```
SchemaSpreadsheet(schema)
└── write(path)                      # entry point
    ├── sorts blocks by id
    ├── creates the 4 shared cell formats: {bold?, bottom-border?}
    ├── _write_sheet(wb, "All", all_blocks)     # combined sheet
    └── _write_sheet(wb, name, [block])          # one call per block
        └── _field_rows(field)       # field -> list of Row tuples
```

- `_field_rows` is the only place that understands the schema shape: it turns
  one top-level `MetadataField` (and its `childFields`, one level deep — the
  Dataverse schema does not nest compounds further) into flat `Row` tuples of
  `(title, definition, usage, repeatable, example, is_top_level, is_last_row_of_field)`.
- `_write_sheet` is pure presentation: it writes a header row, then for each
  block a merged title row followed by its field rows, picking the cell format
  from the `(bold, end)` pair. The **All** sheet and the per-block sheets are
  the same code path — only the block list differs.
- Formats are created once per workbook (xlsxwriter requires formats to belong
  to the workbook) and shared across sheets; only the block-title row gets a
  fresh format per call because its background color varies.

Writing uses [xlsxwriter](https://xlsxwriter.readthedocs.io/) (write-only,
no read-back), which is why it is an optional dependency rather than a core
one — the models work without it.
