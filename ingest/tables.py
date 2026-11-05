"""Decide which tables pdfplumber found are real tables, and which are normal text with borders drawn around it.

A table here is what pdfplumber's `extract_tables()` returns for one table: a list of rows,
each row a list of cells, each cell a string or None.
"""
import re

Table = list[list[str | None]]

# A clause marker followed by a full sentence, e.g. "7.3. The aforesaid provisions ..." or "h. not deal in ...".
# Markers: 7. / 7.3. / 12.6.1. (numbers must end in a full stop, so "15 days ..." is not a marker),
#          a. / b) / (c) / II.
# The sentence part must be at least 40 characters, so short numbered headings and bare row numbers don't count.
CLAUSE_SENTENCE = re.compile(r"^(\d+(\.\d+)*\.|[a-z][.)]|\([a-z]+\)|[ivxIVX]+\.)\s+\S.{39,}")

CLAUSE_GRID_THRESHOLD = 0.3


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


def looks_like_clause(cell: str) -> bool:
    """True if the cell starts with a clause marker and continues with a full sentence."""
    text = " ".join(cell.split())  # cells span several lines; flatten them first
    return CLAUSE_SENTENCE.match(text) is not None


def clause_cell_share(table: Table) -> float:
    """Fraction of non-empty cells that read like clauses (0.0 to 1.0)."""
    cells = [cell for row in table for cell in row if _has_text(cell)]
    if not cells:
        return 0.0
    return sum(looks_like_clause(cell) for cell in cells) / len(cells)


def looks_like_clause_grid(table: Table) -> bool:
    """Rule 2: clause text laid out in a grid, not a real table.

    Uses a share rather than "any cell", so a real table with one sentence-like cell is kept.
    """
    return clause_cell_share(table) >= CLAUSE_GRID_THRESHOLD
