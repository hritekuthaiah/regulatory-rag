"""Tests for ingest/tables.py, using tables copied from real SEBI circulars where possible."""
import pytest

from ingest.tables import (
    clause_cell_share,
    count_text_columns,
    has_two_text_columns,
    is_clause_grid_page,
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


# --- Rule 3: pages whose clause text sits inside table borders ---

def line(text, top, x0=72, x1=520):
    """A text line shaped like pdfplumber's extract_text_lines() output."""
    return {"text": text, "x0": x0, "x1": x1, "top": top, "bottom": top + 10}


GRID_BOX = (60, 100, 540, 700)  # one big table outline covering most of the page

GRIDDED_PAGE = [  # SEBI/HO/CFD/PoD-1/P/CIR/2024/072, page 17 style: clauses inside the grid
    line("11.1.5. Employees should be directed that any", 120),
    line("them either in their official mail/personal mail", 135),
    line("11.1.6. Communication with media shall be routed", 200),
    line("11.2. The BTIs shall maintain records of all", 300),
    line("a. complaints received from investors", 400),
]

NORMAL_PAGE = [
    line("4. In accordance with Regulation 14 (2) of FVCI Regulations, 2000, Custodian shall be", 120),
    line("responsible for timely submission of the report.", 135),
    line("5. The report for the quarter ending September 30, 2024 shall be", 200),
    line("6. This circular is issued in exercise of powers conferred under Section 11", 300),
]


def test_gridded_page_is_flagged():
    assert is_clause_grid_page(GRIDDED_PAGE, [GRID_BOX])


def test_normal_page_without_tables_is_not_flagged():
    assert not is_clause_grid_page(NORMAL_PAGE, [])


def test_page_with_a_real_table_beside_normal_clauses_is_not_flagged():
    # Clauses at the top of the page, a fee table below them. The table's lines aren't clause lines.
    fee_box = (60, 400, 540, 500)
    page = NORMAL_PAGE + [line("Individual and Partnership Firm  Rs. 2,000  Rs. 3,000", 420),
                          line("Body Corporate  Rs. 20,000  Rs. 30,000", 450)]
    assert not is_clause_grid_page(page, [fee_box])


def test_fewer_than_three_clause_lines_is_never_flagged():
    page = [line("1. Applicability of this circular to all intermediaries", 120),
            line("2. Effective date of the provisions", 200)]
    assert not is_clause_grid_page(page, [GRID_BOX])  # 100% inside, but only 2 clause lines


def test_exactly_half_inside_is_flagged():
    page = [line("1. First clause inside the grid", 120), line("2. Second clause inside the grid", 200),
            line("3. Third clause below the grid", 750), line("4. Fourth clause below the grid", 800)]
    assert is_clause_grid_page(page, [(60, 100, 540, 700)])


def test_just_under_half_inside_is_not_flagged():
    page = [line("1. Inside the grid", 120), line("2. Below", 750), line("3. Below", 800)]
    assert not is_clause_grid_page(page, [(60, 100, 540, 700)])  # 1 of 3 = 33%


def test_line_counts_as_inside_by_its_middle():
    # A line that starts just left of the box but whose middle is inside counts as inside.
    box = (100, 100, 540, 700)
    page = [line(f"{n}. Clause text that starts a little left of the grid line", 120 + 50 * n, x0=90) for n in range(1, 4)]
    assert is_clause_grid_page(page, [box])
