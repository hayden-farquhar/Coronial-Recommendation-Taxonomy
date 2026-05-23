"""Pull recommendation text from an upstream coronial-NLP pipeline.

This script reads a `cases_clean.jsonl` file produced by an upstream pipeline and
extracts the case-level recommendation text into a single parquet.

The upstream schema stores all recommendations for a case as a single
concatenated string in `recommendation_text`; the pipeline does not split them
into discrete items. The per-case `embeddings_recs.npy` file (when present) is
one embedding per case-with-recommendations.

This script offers two operating modes:

* **case mode (default)** — one row per case-with-recommendations. Unit of
  analysis matches the upstream embeddings file, so embeddings line up with
  rows 1:1.

* **naive-split mode** — heuristic split of `recommendation_text` into
  discrete recommendations using a numbered-list / lettered-list regex.
  Opt in with `--split naive`. Best-effort only; complex nested numbering
  is known to confuse the regex.

Upstream paths are configured via environment variables:

    UPSTREAM_CASES        Path to upstream `cases_clean.jsonl` (REQUIRED)
    UPSTREAM_EMB_NPY      Path to upstream `embeddings_recs.npy` (optional)
    UPSTREAM_EMB_IDS      Path to upstream `embedding_ids_recs.json` (optional)

Or via CLI flag `--upstream-cases PATH`.

Resumable: skips work if `data/recommendations.parquet` already exists and is
newer than the upstream source. Pass --force to override.

Usage:
    export UPSTREAM_CASES=/path/to/cases_clean.jsonl
    python scripts/01_load_upstream_recommendations.py
    python scripts/01_load_upstream_recommendations.py --split naive
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUT_PARQUET = PROJECT_ROOT / "data" / "recommendations.parquet"
OUT_EMB = PROJECT_ROOT / "data" / "recommendation_embeddings.npy"
OUT_EMB_IDS = PROJECT_ROOT / "data" / "recommendation_embedding_ids.json"

CASE_META_FIELDS = (
    "case_id", "jurisdiction", "db_code", "db_type", "year",
    "case_number", "title", "citation", "date_iso", "finding_type",
    "coroner", "url", "recommendation_count",
)

# Match leading numbered or lettered list markers at the start of a line.
SPLIT_RE = re.compile(
    r"(?:\n|^)\s*(?:\(?[0-9]{1,3}\)?[\.\)]|\(?[A-Z]\)?[\.\)])\s+",
    re.MULTILINE,
)


def _newer_than(target: Path, source: Path) -> bool:
    if not target.exists():
        return False
    return target.stat().st_mtime >= source.stat().st_mtime


def _naive_split(text: str) -> list[str]:
    if not text or not text.strip():
        return []
    parts = SPLIT_RE.split(text)
    cleaned = [p.strip() for p in parts if p and p.strip()]
    return cleaned if len(cleaned) > 1 else [text.strip()]


def load_case_level(upstream_cases: Path) -> pd.DataFrame:
    rows = []
    with upstream_cases.open("r", encoding="utf-8") as fh:
        for line in fh:
            case = json.loads(line)
            if not case.get("has_recommendations"):
                continue
            text = case.get("recommendation_text") or ""
            if not text.strip():
                continue
            row = {field: case.get(field) for field in CASE_META_FIELDS}
            row["recommendation_id"] = case.get("case_id")
            row["recommendation_idx"] = 0
            row["text"] = text
            rows.append(row)
    return pd.DataFrame(rows)


def load_naive_split(upstream_cases: Path) -> pd.DataFrame:
    rows = []
    with upstream_cases.open("r", encoding="utf-8") as fh:
        for line in fh:
            case = json.loads(line)
            if not case.get("has_recommendations"):
                continue
            text = case.get("recommendation_text") or ""
            parts = _naive_split(text)
            for idx, part in enumerate(parts):
                row = {field: case.get(field) for field in CASE_META_FIELDS}
                row["recommendation_id"] = f"{case.get('case_id')}__r{idx}"
                row["recommendation_idx"] = idx
                row["text"] = part
                rows.append(row)
    return pd.DataFrame(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="Rebuild even if cached.")
    parser.add_argument(
        "--split",
        choices=["case", "naive"],
        default="case",
        help="Unit of analysis. 'case' (default): one row per case. "
        "'naive': heuristic regex split into discrete recommendations.",
    )
    parser.add_argument(
        "--upstream-cases",
        type=Path,
        default=None,
        help="Path to upstream cases_clean.jsonl. Overrides $UPSTREAM_CASES.",
    )
    args = parser.parse_args()

    cases_path = args.upstream_cases or (
        Path(os.environ["UPSTREAM_CASES"]) if "UPSTREAM_CASES" in os.environ else None
    )
    if cases_path is None:
        print("ERROR: provide --upstream-cases PATH or set $UPSTREAM_CASES.", file=sys.stderr)
        return 2
    if not cases_path.exists():
        print(f"ERROR: upstream cases file not found at {cases_path}", file=sys.stderr)
        return 2

    if not args.force and _newer_than(OUT_PARQUET, cases_path):
        print(f"Cache hit: {OUT_PARQUET} is newer than upstream — skipping.")
        print("  Pass --force to rebuild.")
        return 0

    print(f"Loading recommendations from {cases_path} (mode={args.split}) ...")
    df = load_case_level(cases_path) if args.split == "case" else load_naive_split(cases_path)
    print(f"  {len(df):,} rows across {df['case_id'].nunique():,} cases.")

    OUT_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT_PARQUET, index=False)
    print(f"  Wrote {OUT_PARQUET}")

    emb_npy = os.environ.get("UPSTREAM_EMB_NPY")
    emb_ids = os.environ.get("UPSTREAM_EMB_IDS")
    if args.split == "case" and emb_npy and emb_ids and Path(emb_npy).exists() and Path(emb_ids).exists():
        emb = np.load(emb_npy)
        ids = json.loads(Path(emb_ids).read_text())
        np.save(OUT_EMB, emb)
        OUT_EMB_IDS.write_text(json.dumps(ids))
        print(f"  Mirrored embeddings: {emb.shape} -> {OUT_EMB}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
