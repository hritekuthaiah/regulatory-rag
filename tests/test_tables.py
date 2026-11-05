"""Tests for ingest/tables.py, using tables copied from real SEBI circulars where possible."""
from ingest.tables import count_text_columns, has_two_text_columns

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
