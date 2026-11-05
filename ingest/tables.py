"""Decide which tables pdfplumber found are real tables, and which are normal text with borders drawn around it.

A table here is what pdfplumber's `extract_tables()` returns for one table: a list of rows,
each row a list of cells, each cell a string or None.
"""
import re

Table = list[list[str | None]]
Box = tuple[float, float, float, float]  # x0, top, x1, bottom, as pdfplumber gives a table's bbox

# Clause markers: 7. / 7.3. / 12.6.1. (numbers must end in a full stop, so "15 days ..." is not a marker),
#                 a. / b) / (c) / II.
CLAUSE_MARKER = r"(\d+(\.\d+)*\.|[a-z][.)]|\([a-z]+\)|[ivxIVX]+\.)"

# A clause marker followed by a full sentence, e.g. "7.3. The aforesaid provisions ..." or "h. not deal in ...".
# The sentence part must be at least 40 characters, so short numbered headings and bare row numbers don't count.
CLAUSE_SENTENCE = re.compile(rf"^{CLAUSE_MARKER}\s+\S.{{39,}}")

# A line of page text that begins a clause (no length requirement: one line is often only part of a clause).
CLAUSE_START = re.compile(rf"^{CLAUSE_MARKER}\s+\S")

CLAUSE_GRID_THRESHOLD = 0.3

# Rule 3 cut-offs, measured on 12,392 pages of 93 master circulars: pages split into ~0% and ~100%
# clause-lines-inside-tables, with the quietest point at 40-50%.
MIN_CLAUSE_LINES = 3
GRID_PAGE_THRESHOLD = 0.5


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


def _center_inside(line: dict, box: Box) -> bool:
    """True if the middle of a text line falls inside a table's box."""
    x0, top, x1, bottom = box
    cx = (line["x0"] + line["x1"]) / 2
    cy = (line["top"] + line["bottom"]) / 2
    return x0 <= cx <= x1 and top <= cy <= bottom


def is_clause_grid_page(lines: list[dict], table_boxes: list[Box]) -> bool:
    """Rule 3: on this page, is the clause text itself laid out inside table borders?

    `lines` are the page's text lines as pdfplumber's `extract_text_lines()` returns them
    (each with "text", "x0", "x1", "top", "bottom"). `table_boxes` are the bboxes of the page's
    tables that passed Rule 1. If it returns True, none of this page's tables should be used.

    Pages with fewer than MIN_CLAUSE_LINES clause lines are never flagged: one or two lines
    swing the share between 0% and 100%, which is too noisy to judge.
    """
    clause_lines = [line for line in lines if CLAUSE_START.match(line["text"].strip())]
    if len(clause_lines) < MIN_CLAUSE_LINES:
        return False
    inside = sum(any(_center_inside(line, box) for box in table_boxes) for line in clause_lines)
    return inside / len(clause_lines) >= GRID_PAGE_THRESHOLD
