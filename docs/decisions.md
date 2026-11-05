# Decision Log

One entry per decision, newest at the bottom. Copy the template below for each new decision.

---

## Template

### Decision: <short title>
- **Stage:** <number and name>
- **Options considered:**
  - <option A>: <one-line trade-off>
  - <option B>: <one-line trade-off>
- **Chosen:** <option>
- **Why:** <reasoning specific to the SEBI corpus>
- **Measured result:** <metric and value, or "not measurable at this stage" with the spot-check done instead>
- **Date:** YYYY-MM-DD

---

<!-- Decisions start below this line -->

### Decision: Use the AIKosh dataset text as the source; defer table re-extraction
- **Stage:** 1 — Data ingestion & parsing
- **Options considered:**
  - A — Clean the dataset's text only: fastest; inherits its extraction quirks.
  - B — Re-extract every circular from the original SEBI PDFs: full control and page numbers; needs ~728 downloads, and some SEBI pages expose no PDF link.
  - C — Dataset text + cleaning, re-extract from PDF only where needed. Within C: re-extract tables now (Option 2) vs only once the eval set shows table questions failing (Option 1).
- **Chosen:** C, Option 1 — dataset text + cleaning; tables re-extracted later only if measured to hurt.
- **Why:** On 9 sampled PDFs, our own PyMuPDF extraction matched the dataset almost exactly (99.3–100% of words, identical clause numbers, identical footers), so re-extracting plain text adds nothing. The only measurable gap is tables (one circular: 19 of 30 rows lost their structure). Following the project rule, a fix is added only after a number shows it is needed.
- **Measured result:** Dataset vs own extraction on 9 PDFs — word coverage 99.3–100%; clause sequences identical 9/9; table rows intact 210/240 overall, worst case 11/30 (SEBI/HO/MRD/MRD-PoD-3/P/CIR/2023/190; lenient first-word check).
- **Data version:** AIKosh / Hugging Face `opnsrcntrbtrian/sebi-circulars` v2026.07 — 728 records (dataset card says 705). SHA-256: corpus.jsonl `61a6201b67162144c09220d621a8461faeb77c12bff4d181d415a00c4676da4b`, lineage.jsonl `3aa393f22cf8e03965811f86a7b08eb5d41f5713c1e81f23d9f068f82e2ea725`, eval.jsonl `f01d877949d12cfd59f0104d45cf800400949e6fce703e96cec052b003e26eb9`.
- **Cleaning steps this implies:** (1) remove "Page X of Y" footers anywhere; (2) re-join lines broken mid-sentence; (3) squash stray spaces/blank lines; (4) count clauses only after "Subject:"; (5) drop garbled Hindi lines; tables (6, 7) deferred.
- **Date:** 2026-11-05

### Decision: Re-extract tables now, for master circulars only (revises the table part above)
- **Stage:** 1 — Data ingestion & parsing
- **Options considered:**
  - Keep deferring tables until eval questions show they fail: least work now; risks building chunking around broken tables.
  - Fix tables now for master circulars only: pdfplumber on their original PDFs; master circulars hold most of the rule tables.
  - Fix tables now for all 728 circulars: most complete; most downloads, and most tables outside master circulars are blank forms.
- **Chosen:** Fix tables now, master circulars only (133 documents).
- **Why:** A hand check of ~47 tables in 6 sample PDFs found ~19 rule tables (fees, limits, deadlines, applicability), ~16 blank forms, and ~12 false tables (boxed paragraphs). The rule tables, which carry high-value compliance answers, were concentrated in master circulars.
- **Known risks:** pdfplumber detects false tables, so a filter is needed before replacing any text; some SEBI pages expose no PDF link.
- **Measured result:** Pending. Eval set will include ~5 table-answer questions to confirm the fix.
- **Date:** 2026-11-05

### Decision: Defer merging re-extracted tables into the text (compressed timeline)
- **Stage:** 1 — Data ingestion & parsing
- **Options considered:**
  - Merge filtered pdfplumber tables into master-circular text now: completes the earlier table decision; costs about one more session.
  - Defer the merge; keep the three table-filter rules built and tested; decide from eval results.
- **Chosen:** Defer the merge.
- **Why:** Interview expected in December 2026, project target ~2 weeks. The filter rules are done and measured, so the remaining merge can be added later if the eval set's table questions fail. Most rule-table rows already survive on one line in the dataset text (210/240 in the 9-PDF sample, lenient check).
- **What was built:** `ingest/tables.py` — Rule 1 (at least 2 text columns), Rule 2 (≥30% of cells read like clauses), Rule 3 (per page: ≥50% of 3+ clause lines inside table borders). Rule 3 cut-off measured on 12,392 pages of 93 master circulars: pages split into ~0% (6,132) and ~100% (1,267), quietest point 40–50%. Spot-check of 10 skipped pages: 9 correct, 1 real table skipped (keeps dataset text).
- **Measured result:** Pending — eval set table questions (Stage 11).
- **Date:** 2026-11-05

### Decision: Cleaning rules for the dataset text
- **Stage:** 1 — Data ingestion & parsing
- **Options considered:** for hyphen line breaks — drop the hyphen ("regu-lation" → "regulation"), keep it, or decide per word from corpus word counts. For Hindi — drop whole lines with Devanagari, or strip Devanagari and keep the English left on the line.
- **Chosen:** Remove `(cid:NN)` codes and "Page X of Y" anywhere; strip Devanagari (plus its orphan brackets/commas) but keep English on the same line; squash spaces; re-join wrapped lines unless the previous line ends a sentence, is a bare `CIRCULAR` heading, or the next line starts a clause / letter-structure line (To, Dear, Sub:, Annexure); keep hyphens when joining.
- **Why:** Of 3,492 hyphen line breaks, ~92% are real hyphenated words (sub-paragraph, non-regulatory); true word splits are rare because the source is Word documents. Bilingual lines often carry the English version on the same line, so dropping whole lines would lose English text.
- **Measured result (all 728 circulars):** footers 13,698 → 0; `(cid:)` codes 170 → 0; Devanagari runs 17,316 → 0; lines 649,715 → 182,100 (wrapped lines re-joined); clause-start lines 113,963 → 113,961; English words 5,107,661 → 5,080,095 (−27,566 ≈ the two words "Page"/"of" in each removed footer, so no rule text lost). 49 tests pass.
- **Known limitation:** ~3 bilingual circulars with a side-by-side Hindi/English layout (e.g. SEBI/HO/ITD-1/ITD_CSC_EXT/P/CIR/2024/113) have the two columns interleaved line by line in the dataset text; fixing needs re-extracting the English column from the PDF. Deferred.
- **Date:** 2026-11-05
