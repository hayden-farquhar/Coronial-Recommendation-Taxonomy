"""Generate a stratified random sample for the internal IRR pilot.

Strategy (informed by scripts/04_eda.py):

* Stratify by **jurisdiction × year-bin**, where year-bins are
  pre-2010, 2010-2019, 2020+ to balance era effects without
  fragmenting strata.
* **Oversample small jurisdictions.** Use square-root proportional
  allocation rather than strict proportional — VIC otherwise dwarfs
  the sample and ACT goes missing entirely.
* **Bound `recommendation_count`** to [1, 25] to exclude the
  upstream parser's pathological case (max = 1,150) and any case
  with no extracted recommendations.
* **Bound `text_chars`** to [200, 12000] so coders don't spend the
  pilot wrestling with one 30-page document and a one-line stub.
* Reproducibility: seeded with --seed (default 78).

Output:
    taxonomy/gold_standard/pilot_sample_<date>.csv
    taxonomy/gold_standard/pilot_sample_<date>_metadata.json

The CSV is structured as the coder-facing rating template: one row
per recommendation_id with blank label columns for each axis. Each
rater fills in their copy and saves as
`taxonomy/gold_standard/ratings_<rater>.csv` — that file is what
scripts/03_irr_analysis.py consumes.

Usage:
    python scripts/05_sample_irr_pilot.py
    python scripts/05_sample_irr_pilot.py --n 50 --seed 78
"""

from __future__ import annotations

import argparse
import json
import math
import re
from datetime import date
from pathlib import Path

import pandas as pd

# Upstream-pipeline data-quality regex: cases that explicitly say "no
# recommendations made" are nevertheless flagged has_recommendations=True
# with recommendation_count>=1. The IRR pilot must not waste rater time
# on these — exclude from the sampling pool.
#
# 2026-05-21: expanded after v0 IRR-pilot inspection. Patterns use \s+
# instead of literal spaces because upstream PDF extraction leaves
# embedded newlines that split target phrases (e.g. "to make any\n
# comments or recommendations"). Use ``_no_rec_match(text)`` rather
# than calling NO_REC_PATTERNS.search directly — it normalises
# whitespace before applying the regex, so both forms hit.
#
# Patterns caught (after v1.0 pilot inspection, 2026-05-21):
#   - "no recommendations (are/to be) (made/to make)"
#   - "make no [formal] recommendations"
#   - "I have no recommendations to make"
#   - "I do not make any recommendations [in this matter]"   <-- new
#   - "no recommendations arise"
#   - "nil recommendations"
#   - "there are no recommendations" (with or without "pursuant to") <-- relaxed
#   - "do(es) not see a need to make any (comments|recommendations)"
#   - "not such as to require (me) to make any (comments|recommendations)"
#   - "do(es) not call for any further comment"
#   - "no [further] (comments|comments or recommendations) are warranted/required/necessary"
NO_REC_PATTERNS = re.compile(
    r"(?:"
    r"\bno\s+recommendations?\s+(?:are\s+|to\s+be\s+|to\s+)?(?:made|to\s+make)\b"
    r"|\bmake\s+no\s+(?:formal\s+)?recommendations?\b"
    r"|\bi\s+have\s+no\s+recommendations?\s+to\s+make\b"
    r"|\bi\s+do\s+not\s+make\s+any\s+(?:further\s+)?recommendations?\b"
    r"|\bno\s+recommendations?\s+arise\b"
    r"|\bnil\s+recommendations?\b"
    r"|\bthere\s+are\s+no\s+recommendations?\b"
    r"|\bdo(?:es)?\s+not\s+see\s+(?:a|the)\s+need\s+to\s+make\s+any\s+(?:comments?(?:\s+or\s+recommendations?)?|recommendations?)\b"
    r"|\bnot\s+such\s+as\s+to\s+require\s+(?:me\s+)?to\s+make\s+any\s+(?:comments?|recommendations?)\b"
    r"|\bdo(?:es)?\s+not\s+call\s+for\s+any\s+further\s+comment\b"
    r"|\bno\s+(?:further\s+)?(?:comments?|comments?\s+or\s+recommendations?)\s+(?:are\s+)?(?:warranted|required|necessary)\b"
    # Added 2026-05-21 after v1.0 pilot inspection — 4 more refusal phrasings:
    r"|\bno\s+need\s+(?:for\s+me\s+)?to\s+make\s+any\s+(?:further\s+)?(?:comment(?:s)?(?:\s+or\s+recommendations?)?|recommendations?)\b"
    r"|\bunnecessary\s+to\s+make\s+any\s+(?:comment(?:s)?(?:\s+or\s+recommendations?)?|recommendations?)\b"
    r"|\bdecline\s+to\s+make\s+(?:any\s+)?(?:recommendations?|further\s+comment(?:s)?(?:\s+or\s+recommendations?)?)\b"
    r"|\b(?:it\s+is\s+)?not\s+appropriate\s+to\s+(?:make\s+any\s+recommendations?|investigate\s+this\s+issue\s+further)\b"
    # Added 2026-05-21 second-round — Row 32 esoterics:
    r"|\bnot\s+inclined\s+to\s+make\s+(?:any\s+)?(?:recommendations?|comment(?:s)?(?:\s+or\s+recommendations?)?)\b"
    r"|\bdo(?:es)?\s+not\s+raise\s+any\s+further\s+issues?\s+for\s+consideration\b"
    r"|\bdo(?:es)?\s+not\s+raise\s+any\s+(?:further\s+)?issues?\s+for\s+(?:my\s+)?consideration\b"
    # Row 16: "do not raise any further issues for consideration" was already added,
    # but this gets the variant "in my view, do not raise any further issues for
    # consideration" (which is what row 16 contains).
    r")",
    re.IGNORECASE,
)


def _no_rec_match(text: str) -> bool:
    """Apply NO_REC_PATTERNS after whitespace normalisation.

    PDF-extracted text from the upstream pipeline has embedded newlines
    splitting target phrases. The regex uses ``\\s+`` already, but we
    additionally collapse to single spaces so anchors and word boundaries
    behave as on flat text. Use this helper everywhere instead of
    ``NO_REC_PATTERNS.search(text)`` directly.
    """
    if not isinstance(text, str):
        return False
    flat = " ".join(text.split())
    return bool(NO_REC_PATTERNS.search(flat))

PROJECT_ROOT = Path(__file__).resolve().parent.parent
IN_PARQUET = PROJECT_ROOT / "data" / "au" / "recommendations.parquet"
OUT_DIR = PROJECT_ROOT / "taxonomy" / "gold_standard"

AXIS_COLUMNS = ["theme", "mechanism", "addressee", "specificity", "scope"]
FLAG_COLUMNS = [
    "has_deadline_or_metric",
    "ambiguous_theme",
    "ambiguous_mechanism",
    "ambiguous_addressee",
    "ambiguous_specificity",
    "ambiguous_scope",
    "requires_legal_expertise",
    "non_english_or_redacted",
    "coder_notes",
]


def _year_bin(year: int) -> str:
    if year < 2010:
        return "pre2010"
    if year < 2020:
        return "2010-2019"
    return "2020plus"


def _allocate(strata_sizes: dict[tuple[str, str], int], n_target: int) -> dict[tuple[str, str], int]:
    """Square-root proportional allocation, rounded so the total equals n_target."""
    sqrts = {k: math.sqrt(v) for k, v in strata_sizes.items()}
    total_sqrt = sum(sqrts.values())
    raw = {k: n_target * s / total_sqrt for k, s in sqrts.items()}
    floor = {k: int(v) for k, v in raw.items()}
    remainder = n_target - sum(floor.values())
    fractional = sorted(raw.items(), key=lambda kv: kv[1] - floor[kv[0]], reverse=True)
    for k, _ in fractional[:remainder]:
        floor[k] += 1
    floor = {k: min(v, strata_sizes[k]) for k, v in floor.items()}
    return floor


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=50, help="Target sample size.")
    parser.add_argument("--seed", type=int, default=78)
    parser.add_argument(
        "--rec-count-max",
        type=int,
        default=25,
        help="Exclude cases whose upstream recommendation_count exceeds this.",
    )
    args = parser.parse_args()

    df = pd.read_parquet(IN_PARQUET)
    df = df.assign(
        text_chars=df["text"].str.len(),
        year_bin=df["year"].astype(int).apply(_year_bin),
    )

    before = len(df)
    df = df[
        (df["recommendation_count"].between(1, args.rec_count_max))
        & (df["text_chars"].between(200, 12000))
    ].reset_index(drop=True)
    print(f"Filtered {before:,} -> {len(df):,} rows (rec_count 1-{args.rec_count_max}, text 200-12000 chars).")

    no_rec_mask = df["text"].apply(_no_rec_match)
    n_no_rec = int(no_rec_mask.sum())
    if n_no_rec:
        print(f"Dropping {n_no_rec:,} cases whose text matches a 'no recommendations made' pattern (upstream parser false positives).")
        df = df.loc[~no_rec_mask].reset_index(drop=True)

    strata_sizes = df.groupby(["jurisdiction", "year_bin"]).size().to_dict()
    allocation = _allocate(strata_sizes, args.n)

    chosen_idx: list[int] = []
    for (juris, ybin), n_pick in allocation.items():
        if n_pick == 0:
            continue
        pool = df[(df["jurisdiction"] == juris) & (df["year_bin"] == ybin)]
        chosen = pool.sample(n=n_pick, random_state=args.seed)
        chosen_idx.extend(chosen.index.tolist())

    sample = df.loc[chosen_idx].copy()
    sample = sample.sample(frac=1, random_state=args.seed).reset_index(drop=True)
    sample["sample_order"] = sample.index + 1

    keep_cols = [
        "sample_order",
        "recommendation_id",
        "case_id",
        "jurisdiction",
        "year",
        "year_bin",
        "recommendation_count",
        "text_chars",
        "text",
    ]
    coder_template = sample[keep_cols].copy()
    for col in AXIS_COLUMNS + FLAG_COLUMNS:
        coder_template[col] = ""

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    out_csv = OUT_DIR / f"pilot_sample_{today}.csv"
    coder_template.to_csv(out_csv, index=False)
    print(f"Wrote {out_csv}  ({len(coder_template)} rows)")

    distribution = (
        sample.groupby(["jurisdiction", "year_bin"])
        .size()
        .reset_index(name="n_sampled")
        .to_dict(orient="records")
    )
    meta = {
        "generated_on": today,
        "seed": args.seed,
        "n_target": args.n,
        "n_actual": len(sample),
        "filters": {
            "recommendation_count_range": [1, args.rec_count_max],
            "text_chars_range": [200, 12000],
            "no_recommendations_dropped": n_no_rec,
        },
        "allocation_method": "square-root proportional by jurisdiction × year-bin",
        "distribution": distribution,
    }
    out_meta = OUT_DIR / f"pilot_sample_{today}_metadata.json"
    out_meta.write_text(json.dumps(meta, indent=2))
    print(f"Wrote {out_meta}")

    print("\nDistribution (jurisdiction × year_bin):")
    cross = sample.groupby(["jurisdiction", "year_bin"]).size().unstack(fill_value=0)
    print(cross.to_string())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
