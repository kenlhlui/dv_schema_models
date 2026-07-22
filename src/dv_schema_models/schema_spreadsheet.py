"""Turns the dataverse schema into a spreadsheet."""

import random
from pathlib import Path

import xlsxwriter
from xlsxwriter.format import Format

from dv_schema_models.dataverse_schema import DataverseSchemaResponse, MetadataBlock, MetadataField

# (title, definition, usage, repeatable, example, is_top_level, is_last_row_of_field)
Row = tuple[str, str, str, str, str, bool, bool]

COLUMN_WIDTHS = [30, 90, 10, 16, 60]


class SchemaSpreadsheet:
    """Turns the dataverse schema into a spreadsheet."""

    def __init__(self, schema: DataverseSchemaResponse) -> None:
        """Initialize the SchemaSpreadsheet with a DataverseSchemaResponse."""
        self.schema = schema.data

    @staticmethod
    def _header_row() -> list[str]:
        return ["Field", "Definition", "Usage", "Repeatable (Y/N)", "Example"]

    def _title_fmt(self, workbook: xlsxwriter.Workbook):
        return workbook.add_format({"bold": True})

    def _block_fmt(self, workbook: xlsxwriter.Workbook):
        return workbook.add_format({
            "bold": True,
            "align": "center",
            "bg_color": f"#{random.randrange(0x1000000):06x}",
        })

    @staticmethod
    def _field_rows(field: MetadataField) -> list[Row]:
        """Turn one top-level field (and its children) into spreadsheet rows."""
        # ponytail: usage is RQ/O from isRequired; the schema has no "recommended" flag
        usage = lambda f: "RQ" if f.isRequired else "O"  # noqa: E731
        repeatable = lambda f: "Y" if f.multiple else "N"  # noqa: E731

        if not field.childFields:
            return [
                (
                    field.title,
                    field.description,
                    usage(field),
                    repeatable(field),
                    field.watermark,
                    True,
                    True,
                )
            ]
        # Compound field: parent row carries only the definition, children the rest.
        rows: list[Row] = [(field.title, field.description, "", "", "", True, False)]
        children = sorted(field.childFields.values(), key=lambda f: f.displayOrder)
        rows.extend(
            (
                child.title,
                child.description,
                usage(child),
                # A child of a repeatable compound is effectively repeatable.
                "Y" if (child.multiple or field.multiple) else "N",
                child.watermark,
                False,
                child is children[-1],
            )
            for child in children
        )
        return rows

    def _write_sheet(
        self,
        workbook: xlsxwriter.Workbook,
        sheet_name: str,
        blocks: list[MetadataBlock],
        cell_fmts: dict[tuple[bool, bool], Format],
    ) -> None:
        sheet = workbook.add_worksheet(sheet_name)
        for col, width in enumerate(COLUMN_WIDTHS):
            sheet.set_column(col, col, width)

        sheet.write_row(0, 0, self._header_row(), self._title_fmt(workbook))

        row_num = 1
        for block in blocks:
            sheet.merge_range(
                row_num, 0, row_num, 4, f"{block.displayName} Block", self._block_fmt(workbook)
            )
            row_num += 1
            for field in sorted(block.fields.values(), key=lambda f: f.displayOrder):
                for title, *cells, bold, end in self._field_rows(field):
                    sheet.write(row_num, 0, title, cell_fmts[bold, end])
                    for col, value in enumerate(cells, start=1):
                        sheet.write(row_num, col, value, cell_fmts[False, end])
                    row_num += 1

    def write(self, path: str | Path) -> Path:
        """Write an 'All' worksheet plus one per metadata block to an .xlsx file at `path`."""
        path = Path(path)
        workbook = xlsxwriter.Workbook(str(path))
        cell_fmts = {
            (bold, end): workbook.add_format({
                "bold": bold,
                "bottom": 1 if end else 0,
                "text_wrap": True,
                "valign": "top",
            })
            for bold in (True, False)
            for end in (True, False)
        }
        blocks = sorted(self.schema, key=lambda b: b.id)
        self._write_sheet(workbook, "All", blocks, cell_fmts)
        for block in blocks:
            self._write_sheet(
                workbook, block.displayName.removesuffix(" Metadata")[:31], [block], cell_fmts
            )
        workbook.close()
        return path
