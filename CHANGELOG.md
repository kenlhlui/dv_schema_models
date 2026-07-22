# Changelog

## v0.9.0 (2026-07-22)

### Feat

- support IsPartOf and allow empty latestVersion in DatasetData (#16)

### Fix

- pyproject version
- docstring

## v0.8.3 (2026-07-21)

### Fix

- standardize name of roleAlias in RoleAssignment

## v0.8.2 (2026-07-21)

### Fix

- populate correctly in role_alias (_role_alias in the source)

## v0.8.1 (2026-07-21)

### Fix

- accept error status to load_role_assignments (#13)

## v0.8.0 (2026-07-21)

### Feat

- add RoleAssignment models and methods (#12)

## v0.7.0 (2026-07-21)

### Feat

- add list_field method to list[FileInstance]

### Fix

- allow versionNumber and versionMinorNumber be none

## v0.6.0 (2026-07-21)

### Feat

- add versionNumber and versionMinorNumber to dataset_instance

## v0.5.1 (2026-07-20)

### Fix

- handle empty list in dataFile (i.e. no files in a dataset)

## v0.5.0 (2026-07-20)

### Feat

- add file_instance method that allow querying files (#11)

## v0.4.0 (2026-07-20)

### Feat

- add get_raw to DatasetVersion
- switch DatasetData to allow extra and introduce get_raw method

## v0.3.3 (2026-07-20)

### Fix

- add releaseTime to DatasetVersion

## v0.3.2 (2026-07-20)

### Fix

- allow deaccessionLink is None

## v0.3.1 (2026-07-20)

### Fix

- allow `none` value in termsOfAccess & termsOfUse (#10)

## v0.3.0 (2026-07-17)

### Feat

- add get_subfield_values (#9)

## v0.2.0 (2026-07-17)

## v0.2.0-a.3 (2026-07-09)

### Feat

- create XLSX spreadsheet from schema for all the possible fields (#6)

## [0.2.0-a.3](https://github.com/kenlhlui/dv_schema_models/compare/v0.2.0-a.2...v0.2.0-a.3) (2026-07-09)


### Features

* create XLSX spreadsheet from schema for all the possible fields ([#6](https://github.com/kenlhlui/dv_schema_models/issues/6)) ([07fb962](https://github.com/kenlhlui/dv_schema_models/commit/07fb9622748ac28edf9871f5b5fd40262d862458))

## [0.2.0-a.2](https://github.com/kenlhlui/dv_schema_models/compare/v0.2.0-a.1...v0.2.0-a.2) (2026-07-08)


### Features

* add the field_names method for DatasetExport model ([1c3c427](https://github.com/kenlhlui/dv_schema_models/commit/1c3c427f4d76e6f1bba6af7d483cb008c4155082))


### Documentation

* update example in README ([e79fce0](https://github.com/kenlhlui/dv_schema_models/commit/e79fce03e07c809a8159dcf905ae4e2adfb9a6b9))

## [0.2.0-a.1](https://github.com/kenlhlui/dv_schema_models/compare/v0.2.0-a...v0.2.0-a.1) (2026-07-08)


### Bug Fixes

* DatasetData fields and datasetVersion compatibility ([17b5da4](https://github.com/kenlhlui/dv_schema_models/commit/17b5da4536cba4c37fd2bb68e788ef5df9160f7a))

## [0.2.0-a](https://github.com/kenlhlui/dv_schema_models/compare/v0.1.0...v0.2.0-a) (2026-07-08)


### Features

* initial release ([2dcc9cf](https://github.com/kenlhlui/dv_schema_models/commit/2dcc9cf79749fa94be694bf764e75e672db021a1))
