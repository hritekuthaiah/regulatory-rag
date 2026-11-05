"""Tests for ingest/tables.py, using tables copied from real SEBI circulars where possible."""
import pytest

from ingest.tables import (
    clause_cell_share,
    count_text_columns,
    has_two_text_columns,
    looks_like_clause,
    looks_like_clause_grid,
)

# Registration fee table, SEBI/HO/MIRSD/MIRSD-PoD/P/CIR/2025/105, page 7 (shortened)
FEE_TABLE = [
    ["S. No.", "Category", "Application Fee", "Registration Fee", "Renewal Fee"],
    ["1", "Individual and Partnership Firm", "Rs. 2,000", "Rs. 3,000", "Rs. 1,000"],
]

# Boxed paragraph, SEBI/HO/AFD/AFD-PoD-2/P/CIR/2024/70, page 50: one column of running text
BOXED_PARAGRAPH = [
    ["In the event an FPI and its investor group requires to sell shares\nof the company"],
    [None],
]

# Empty bordered box, SEBI/HO/AFD/AFD-PoD-2/P/CIR/2024/70, page 22
EMPTY_BOX = [["", None, ""], [None, "", "  "]]


def test_real_table_has_two_text_columns():
    assert count_text_columns(FEE_TABLE) == 5
    assert has_two_text_columns(FEE_TABLE)


def test_boxed_paragraph_is_rejected():
    assert count_text_columns(BOXED_PARAGRAPH) == 1
    assert not has_two_text_columns(BOXED_PARAGRAPH)


def test_empty_box_is_rejected():
    assert count_text_columns(EMPTY_BOX) == 0
    assert not has_two_text_columns(EMPTY_BOX)


def test_whitespace_only_cells_do_not_count_as_text():
    table = [["Real text", "   ", "\n"]]
    assert count_text_columns(table) == 1


def test_one_row_continuation_of_a_real_table_is_kept():
    # Last row of the fee table, spilled onto page 8 on its own. Must not be thrown away.
    spilled_row = [["3", "Body Corporate", "Rs. 20,000", "Rs.30,000", "Rs. 5,000"]]
    assert has_two_text_columns(spilled_row)


def test_rows_of_different_lengths():
    # pdfplumber can return ragged rows when cells are merged.
    table = [["Header spanning the table"], ["a", "b", "c"]]
    assert count_text_columns(table) == 3


def test_empty_table():
    assert count_text_columns([]) == 0
    assert not has_two_text_columns([])


# --- Rule 2: clause text laid out in a grid ---

# Clause text drawn inside table borders, SEBI/HO/MIRSD/PoD-2/P/CIR/2023/90, page 20 (shortened).
# Real layout: marker and sentence share one cell; wrapped lines continue in the next row without a marker.
CLAUSE_GRID = [
    ["", "", "", ""],
    ["", "7.3. The aforesaid provisions on advertisement code and usage of brand name/", "", ""],
    ["", "trade name became applicable with effect from", "", ""],
    ["8. Unauthenticated news circulated by SEBI Registered Intermediaries through", "", "", ""],
]

# Boxed clause that slipped past Rule 1, SEBI/HO/MIRSD/MIRSD_RTAMB/P/CIR/2021/687, page 2
BOXED_CLAUSE = [["", "", "b) bring the provisions of this circular to the notice of their members and\nalso disseminate the same on their website.", ""]]


@pytest.mark.parametrize("cell", [
    "7.3. The aforesaid provisions on advertisement code shall apply to all intermediaries.",
    "h. not deal in securities while in possession of material non published information.",
    "b) bring the provisions of this circular to the notice of their members.",
    "(c) the intermediary shall maintain records for a period of eight years.",
    "II. The Master Circular shall come into force with immediate effect from today.",
    "12.6.\nReporting to Financial Intelligence Unit (FIU) - The BTIs are required to report.",
])
def test_clause_like_cells(cell):
    assert looks_like_clause(cell)


@pytest.mark.parametrize("cell", [
    "Rs. 2,000",                                         # a value
    "1.",                                                # a bare row number
    "6. Details of Underlying",                          # a short numbered heading
    "15 days from the date of receipt of complete application",  # a quantity, not a marker
    "Individual and Partnership Firm",                   # a label
    "i.e. the entity which is registered with SEBI as an intermediary under the Act",  # 'i.e.' is not a marker
])
def test_not_clause_like_cells(cell):
    assert not looks_like_clause(cell)


def test_clause_grid_is_rejected():
    assert clause_cell_share(CLAUSE_GRID) == 2 / 3  # 2 clause cells out of 3 non-empty cells
    assert looks_like_clause_grid(CLAUSE_GRID)


def test_boxed_clause_is_rejected():
    assert looks_like_clause_grid(BOXED_CLAUSE)


def test_real_table_is_kept():
    assert clause_cell_share(FEE_TABLE) == 0.0
    assert not looks_like_clause_grid(FEE_TABLE)


def test_real_table_with_one_sentence_cell_is_kept():
    # The example from our quiz: one clause-like cell among many short values.
    table = FEE_TABLE + [
        ["2", "Body Corporate", "Rs. 20,000", "Rs. 30,000", "Rs. 5,000"],
        ["", "5. The fee shall be paid within 30 days of the registration being granted.", "", "", ""],
    ]
    assert clause_cell_share(table) < 0.3
    assert not looks_like_clause_grid(table)


def test_clause_share_of_empty_table_is_zero():
    assert clause_cell_share([]) == 0.0
    assert clause_cell_share(EMPTY_BOX) == 0.0
