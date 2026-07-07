from src.dv_schema_models.dataset_instance import load_dataset
from src.dv_schema_models.dataverse_schema import load_schema
from src.dv_schema_models.schema_driven_records import (
    build_record_model,
    flatten_instance,
)

if __name__ == "__main__":
    # 1. Learn what fields are available from the schema.
    schema = load_schema("./tests/dv_schema.json")
    citation_schema_block = schema.get_block("citation")
    print("Fields defined by the schema:", list(citation_schema_block.fields.keys()))
    print("Required fields:", citation_schema_block.required_fields())

    # 2. Build a Pydantic model FROM that schema.
    CitationRecord = build_record_model(citation_schema_block)

    # 3. Load the actual dataset and flatten its citation block to {typeName: value}.
    dataset = load_dataset("./tests/ds_metadata.json")
    citation_instance = dataset.data.latestVersion.metadataBlocks["citation"]
    raw_values = flatten_instance(citation_instance)

    # 4. Validate the real values against the schema-derived model. Report problems instead
    #    of crashing -- a schema mismatch here is exactly the kind of thing a curation check
    #    for this repository should surface, not something the loader should hide.
    from pydantic import ValidationError

    try:
        record = CitationRecord.model_validate(raw_values)
        print("\nValid against the schema. Parsed record:")
        print("title:", record.title)
        print("author[0].authorName:", record.author[0].authorName)
    except ValidationError as exc:
        print("\nSchema violations found in this dataset:")
        for error in exc.errors():
            location = ".".join(str(part) for part in error["loc"])
            print(f" - {location}: {error['msg']}")  # 3. validate real data against it
