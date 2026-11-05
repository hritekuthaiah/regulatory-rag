"""Clean every circular in the raw dataset and write data/processed/corpus_clean.jsonl.

Run from the project root:  python -m ingest.build_clean_corpus
Prints a before/after report so each run shows what the cleaning changed.
"""
import json
import re
from pathlib import Path

from ingest.clean import DEVANAGARI, FOOTER, GARBLED, clean_text
from ingest.tables import CLAUSE_START

RAW = Path("data/raw/aikosh-v2026.07/corpus.jsonl")
OUT = Path("data/processed/corpus_clean.jsonl")
ENGLISH_WORD = re.compile(r"[A-Za-z]{2,}")


def stats(texts: list[str]) -> dict[str, int]:
    lines = [line.strip() for t in texts for line in t.splitlines() if line.strip()]
    return {
        "lines": len(lines),
        "clause-start lines": sum(CLAUSE_START.match(line) is not None for line in lines),
        "'Page X of Y' footers": sum(len(FOOTER.findall(t)) for t in texts),
        "(cid:NN) codes": sum(len(GARBLED.findall(t)) for t in texts),
        "Devanagari runs": sum(len(DEVANAGARI.findall(t)) for t in texts),
        "English words": sum(len(ENGLISH_WORD.findall(t)) for t in texts),
    }


def main() -> None:
    records = [json.loads(line) for line in RAW.open()]
    cleaned = [{**r, "text": clean_text(r["text"])} for r in records]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w") as f:
        for r in cleaned:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    before, after = stats([r["text"] for r in records]), stats([r["text"] for r in cleaned])
    print(f"cleaned {len(cleaned)} circulars -> {OUT}\n")
    print(f"{'':<24}{'before':>12}{'after':>12}")
    for key in before:
        print(f"{key:<24}{before[key]:>12,}{after[key]:>12,}")


if __name__ == "__main__":
    main()
