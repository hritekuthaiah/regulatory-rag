"""Decide which tables pdfplumber found are real tables, and which are normal text with borders drawn around it.

A table here is what pdfplumber's `extract_tables()` returns for one table: a list of rows,
each row a list of cells, each cell a string or None.
"""

Table = list[list[str | None]]


def _has_text(cell: str | None) -> bool:
    return cell is not None and cell.strip() != ""


def count_text_columns(table: Table) -> int:
    """Number of columns that contain text in at least one row."""
    columns_with_text = {j for row in table for j, cell in enumerate(row) if _has_text(cell)}
    return len(columns_with_text)


def has_two_text_columns(table: Table) -> bool:
    """Rule 1: a real table splits its content into at least two columns.

    A paragraph inside a bordered box comes out as a single column, so it fails this check.
    """
    return count_text_columns(table) >= 2
