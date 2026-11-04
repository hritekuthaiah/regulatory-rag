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
