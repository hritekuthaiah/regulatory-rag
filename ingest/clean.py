"""Clean the dataset's circular text: remove PDF-extraction noise without touching the words of the rules.

Steps, in order (each one is a separate function so it can be tested on its own):
  1. remove_garbled   - drop "(cid:366)"-style glyph codes left by broken font mappings
  2. remove_footers   - drop "Page X of Y" anywhere, including when it is glued mid-sentence
  3. clean_line       - drop Devanagari (garbled Hindi) and squash repeated spaces, per line
  4. join_wrapped_lines - re-join lines that the PDF wrapped mid-sentence, keeping clause starts on their own line

Fake clause numbers in the "To:" address list are left alone here: the text is correct, and
clause detection (Stage 3, chunking) is where we skip everything before "Subject:".
"""
import re

from ingest.tables import CLAUSE_START

GARBLED = re.compile(r"\(cid:\d+\)")
FOOTER = re.compile(r"Page \d+ of \d+")
DEVANAGARI = re.compile(r"[ऀ-ॿ]+")
LATIN_LETTER = re.compile(r"[A-Za-z]")
SPACES = re.compile(r"[ \t ]+")  # includes non-breaking spaces

# A line ending in one of these finishes a sentence or introduces a list, so the next line starts fresh.
ENDS_SENTENCE = (".", ":", ";", "?", "!")
# Letter-structure lines that always start fresh even if the previous line didn't end a sentence:
# "To,", "Dear Sir / Madam,", "Sub: ...", annexure and circular headings.
STARTS_FRESH = re.compile(
    r"^(To\b,?|Dear\b|Sir\b|Madam\b|Sub(ject)?\s*:|Annexure\b|ANNEXURE\b|CIRCULAR\b|MASTER CIRCULAR\b)"
)


def remove_garbled(text: str) -> str:
    return GARBLED.sub("", text)


def remove_footers(text: str) -> str:
    """Remove page footers. Measured: the capitalised pattern never appears in real rule text in this corpus."""
    return FOOTER.sub("", text)


PUNCTUATION_ONLY = re.compile(r"^[()\[\]/,.;:|\-]+$")
DUPLICATE_MARKER = re.compile(r"^(\d+(?:\.\d+)*\.?\s+)\1")


def clean_line(line: str) -> str:
    """Drop Devanagari runs and squash spaces. Returns "" if nothing readable in English is left.

    On lines that contained Hindi, the Hindi text's brackets and commas are left behind as orphan
    tokens (") (", "/ ,"), so those are dropped too. Lines without Hindi are not touched by that step.
    """
    if DEVANAGARI.search(line):
        line = DEVANAGARI.sub(" ", line)
        line = " ".join(token for token in line.split() if not PUNCTUATION_ONLY.match(token))
        # Side-by-side bilingual layouts number both versions: "1. <Hindi> 1. All ..." -> "1. 1. All ..."
        line = DUPLICATE_MARKER.sub(r"\1", line)
    line = SPACES.sub(" ", line).strip()
    return line if LATIN_LETTER.search(line) or re.search(r"\d", line) else ""


# A line that is only a document heading never takes the next line onto it.
HEADING_ONLY = re.compile(r"^(/ )?(MASTER )?CIRCULAR$")


def starts_new_line(previous: str, current: str) -> bool:
    """Should `current` stay on its own line, rather than be joined onto `previous`?"""
    return (
        previous.endswith(ENDS_SENTENCE)
        or HEADING_ONLY.match(previous) is not None
        or CLAUSE_START.match(current) is not None
        or STARTS_FRESH.match(current) is not None
    )


def join_wrapped_lines(lines: list[str]) -> list[str]:
    """Re-join lines broken by the PDF's line wrapping.

    A line ending in "-" is joined without a space, keeping the hyphen: measured on 3,492 cases,
    ~92% are real hyphenated words ("non-regulatory", "sub-paragraph"), not split words.
    """
    out: list[str] = []
    for line in lines:
        if out and not starts_new_line(out[-1], line):
            out[-1] = out[-1] + line if out[-1].endswith("-") else out[-1] + " " + line
        else:
            out.append(line)
    return out


def clean_text(text: str) -> str:
    text = remove_footers(remove_garbled(text))
    lines = [clean_line(line) for line in text.splitlines()]
    return "\n".join(join_wrapped_lines([line for line in lines if line]))
