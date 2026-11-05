"""Tests for ingest/clean.py, using text copied from real SEBI circulars in the dataset."""
from ingest.clean import clean_line, clean_text, join_wrapped_lines, remove_footers, remove_garbled

# SEBI/HO/AFD/AFD-PoD-3/P/CIR/2024/121, start of the dataset text
FVCI = (
    "CIRCULAR\nSEBI/HO/AFD/AFD-PoD-3/P/CIR/2024/121 September 13, 2024\nTo,\n"
    "1. All Foreign Venture Capital Investors\n2. All Custodians\nDear Sir / Madam,\n"
    "Subject: Reporting by Foreign Venture Capital Investors (FVCIs).\n"
    "1. In accordance with Regulation 13(1) of SEBI (FVCI) Regulations, 2000, FVCIs are required\n"
    "to submit quarterly reports to SEBI in the format specified with respect to their venture\n"
    "capital activity as Foreign Venture Capital Investor.\n"
    "2. The format for the quarterly report on venture capital activity to be submitted by FVCIs is\n"
    "revised and same is enclosed as Annexure-1.\n"
)


def test_footer_removed_on_its_own_line():
    assert remove_footers("Yours faithfully,\nPage 2 of 231\nTABLE OF CONTENTS") == "Yours faithfully,\n\nTABLE OF CONTENTS"


def test_footer_glued_mid_sentence_removed():
    # Real case: the page break fell mid-sentence during extraction.
    text = clean_text("rescission, and pending before it, shall be deemed to have Page 6 of 13 been made")
    assert text == "rescission, and pending before it, shall be deemed to have been made"


def test_lowercase_page_reference_is_kept():
    assert remove_footers("as stated on page 2 of 10 of the form") == "as stated on page 2 of 10 of the form"


def test_garbled_glyph_codes_removed():
    assert remove_garbled("भारतीय (cid:366)ितभूित बोड(cid:330)") == "भारतीय ितभूित बोड"


def test_hindi_dropped_english_kept_on_mixed_line():
    assert clean_line("परिपत्र / CIRCULAR") == "CIRCULAR"


def test_hindi_leftover_brackets_dropped():
    # HO/13/19/12(1)2026-ITD-1_CIMGI/10873/2026: Hindi line "बकैं )एससीएसबी(" leaves ") (" behind
    assert clean_line("All Collective Investment Schemes (CIS) सभी )सीआईएस(") == "All Collective Investment Schemes (CIS)"


def test_duplicate_clause_marker_from_bilingual_layout_collapsed():
    # SEBI/HO/ITD-1/ITD_VIAP/P/CIR/2025/111: Hindi and English numbered side by side
    assert clean_line("1. सभी मान्यताप्राप्त स्टॉक एक्सचेंज 1. All Recognised Stock Exchanges") == "1. All Recognised Stock Exchanges"


def test_punctuation_on_english_only_line_untouched():
    assert clean_line("1. Fees / charges ( see Annexure ) apply") == "1. Fees / charges ( see Annexure ) apply"


def test_hindi_only_line_dropped():
    assert clean_line("सभी ऑल्टिनेटटव इनवेस्टमेंट फंड )एआईफ(") == ""


def test_spaces_squashed():
    assert clean_line("  SEBI/HO/AFD   2024  /121  ") == "SEBI/HO/AFD 2024 /121"


def test_wrapped_clause_is_rejoined():
    out = clean_text(FVCI).splitlines()
    assert ("1. In accordance with Regulation 13(1) of SEBI (FVCI) Regulations, 2000, FVCIs are required "
            "to submit quarterly reports to SEBI in the format specified with respect to their venture "
            "capital activity as Foreign Venture Capital Investor.") in out


def test_every_clause_starts_its_own_line():
    out = clean_text(FVCI).splitlines()
    assert any(line.startswith("1. In accordance") for line in out)
    assert any(line.startswith("2. The format") for line in out)


def test_subject_line_not_glued_to_salutation():
    out = clean_text(FVCI).splitlines()
    assert "Dear Sir / Madam," in out
    assert any(line.startswith("Subject: Reporting") for line in out)


def test_header_lines_stay_separate():
    out = clean_text(FVCI).splitlines()
    assert out[:3] == ["CIRCULAR", "SEBI/HO/AFD/AFD-PoD-3/P/CIR/2024/121 September 13, 2024", "To,"]


def test_hyphen_at_line_break_joined_without_space():
    assert join_wrapped_lines(["Issuers of non-", "convertible securities"]) == ["Issuers of non-convertible securities"]


def test_sentence_end_keeps_next_line_separate():
    assert join_wrapped_lines(["The circular is effective.", "All stock exchanges shall comply."]) == [
        "The circular is effective.", "All stock exchanges shall comply."]


def test_lettered_sub_clause_starts_new_line():
    assert join_wrapped_lines(["The intermediary shall", "a) maintain records for eight years"]) == [
        "The intermediary shall", "a) maintain records for eight years"]


def test_empty_text():
    assert clean_text("") == ""
