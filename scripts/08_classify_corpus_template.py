"""Template script for classifying the full corpus under the frozen v2.5 codebook.

The deposited `data/recommendations_v2.5_classified.no_text.parquet` is the result
of running this classification pipeline against the n = 2,702 filtered corpus
using Anthropic Claude Opus 4.7 (model ID `claude-opus-4-7`) during May 2026.

This file is a TEMPLATE: it documents the classification approach so that a
reader with API access can re-run the classification themselves. The actual
classifications used in the accompanying paper were produced by sub-agent
invocations within a Claude Code session, with each sub-agent classifying a
batch of approximately 200 cases. The aggregated output is the deposited
parquet.

Reproduction options:

1. **Accept the deposited classifications** as a research artefact. The
   classifications are downstream of (a) a frozen codebook (v2.5), (b) a
   pre-registered analysis plan (OSF DOI 10.17605/OSF.IO/NEX85), and (c) a
   held-out IRR check (n = 40 clean; see irr_results/irr_heldout_v2.5.csv).
   This is the default for replicating tables and figures in the paper.

2. **Re-run the classification yourself** using this template with your own
   Anthropic API key. Note that LLM outputs are not deterministic across model
   versions or temperatures; expect minor variation from the deposited
   classifications. Held-out IRR between two frontier models (Opus 4.7 +
   Sonnet 4.6) was α = 0.84 on addressee, 0.84 on specificity, 1.00 on scope,
   0.71 on theme, and 0.38 on mechanism — the mechanism axis in particular
   has substantial interpretive variability and should be treated as
   descriptive only.

Pre-requisites:
    pip install anthropic pandas pyarrow
    export ANTHROPIC_API_KEY=sk-ant-...

Usage:
    python scripts/08_classify_corpus_template.py --start 0 --end 200 \\
        --in data/classification_target.no_text.parquet \\
        --codebook codebook/codebook_v2.5_frozen_2026-05-22.md \\
        --out batches/batch_000.parquet

    # ... repeat with --start 200 --end 400 etc. until the corpus is exhausted.
    # Then concatenate the batch parquets:
    python -c "import pandas as pd; pd.concat([pd.read_parquet(f) for f in \\
        sorted(__import__('pathlib').Path('batches').glob('*.parquet'))]) \\
        .to_parquet('data/recommendations_v2.5_classified.no_text.parquet', index=False)"

The deposited parquet at data/recommendations_v2.5_classified.no_text.parquet
omits the raw recommendation text (per AustLII redistribution constraints); the
classification target parquet does the same. To run this template you will
either (a) re-acquire the text via the upstream pipeline (see scripts/01) or
(b) rebuild the target parquet WITH text using your own AustLII fetch.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Canonical code sets — must match those in codebook_v2.5_frozen_2026-05-22.md
THEMES = {"THEME-MH", "THEME-CUST", "THEME-MED", "THEME-RTA", "THEME-DV",
          "THEME-DRUG", "THEME-CHILD", "THEME-WORK", "THEME-REC", "THEME-FIRE",
          "THEME-PROD", "THEME-OTHER"}
MECHS = {"MECH-LEG", "MECH-INFRA", "MECH-FUND", "MECH-INV", "MECH-PROC", "MECH-OTHER"}
ADDRS = {"ADDR-DEPT-NAMED", "ADDR-DEPT-GENERIC", "ADDR-HEALTH", "ADDR-REG",
         "ADDR-PROF", "ADDR-POLICE", "ADDR-COURT", "ADDR-PRIVATE", "ADDR-UNSPEC"}
SPECS = {"SPEC-1", "SPEC-2"}
SCOPES = {"SCOPE-IND", "SCOPE-SYS", "SCOPE-MIX"}

CLASSIFICATION_COLUMNS = [
    "theme", "mechanism", "addressee", "specificity", "scope",
    "has_deadline_or_metric",
    "ambiguous_theme", "ambiguous_mechanism", "ambiguous_addressee",
    "ambiguous_specificity", "ambiguous_scope",
    "requires_legal_expertise", "non_english_or_redacted",
    "coder_notes",
]

PROMPT_TEMPLATE = """\
You are a coding assistant applying a fixed taxonomy to coronial recommendation
text. The codebook is FROZEN — do not deviate from its decision rules even if
you believe a better classification would be possible. Pre-registered under OSF
DOI 10.17605/OSF.IO/NEX85 (CC-BY 4.0).

CODEBOOK (verbatim):
====================
{codebook}
====================

For each recommendation below, return a single JSON object per recommendation
on its own line (JSON Lines format). The schema is exactly:

{{
  "classification_target_idx": <int>,
  "theme": "<one of THEME-*>",
  "mechanism": "<one of MECH-*>",
  "addressee": "<one of ADDR-*>",
  "specificity": "<one of SPEC-*>",
  "scope": "<one of SCOPE-*>",
  "has_deadline_or_metric": <true|false>,
  "ambiguous_theme": <true|false>,
  "ambiguous_mechanism": <true|false>,
  "ambiguous_addressee": <true|false>,
  "ambiguous_specificity": <true|false>,
  "ambiguous_scope": <true|false>,
  "requires_legal_expertise": <true|false>,
  "non_english_or_redacted": <true|false>,
  "coder_notes": "<≤ 200 chars>"
}}

Validate every classification value against the canonical code sets. Apply the
multi-rec first-stated rule. Do not invent codes outside the canonical sets.

RECOMMENDATIONS TO CLASSIFY:
{rows}
"""


def classify_with_anthropic(codebook: str, rows: list[dict]) -> list[dict]:
    """Call Anthropic Claude Opus 4.7 to classify a batch of recommendations.

    Returns a list of classification dicts, one per input row. Each dict
    contains the CLASSIFICATION_COLUMNS keys plus `classification_target_idx`.
    """
    try:
        import anthropic
    except ImportError as e:
        raise SystemExit(
            "anthropic package not installed. Run: pip install anthropic"
        ) from e

    client = anthropic.Anthropic()  # uses $ANTHROPIC_API_KEY

    rows_block = "\n\n".join(
        f"--- recommendation {r['classification_target_idx']} "
        f"(jurisdiction={r['jurisdiction']}, year={r['year']}) ---\n"
        f"{r['text']}"
        for r in rows
    )
    prompt = PROMPT_TEMPLATE.format(codebook=codebook, rows=rows_block)

    response = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=16000,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.content[0].text

    parsed = []
    for line in raw.splitlines():
        line = line.strip()
        if not line or not line.startswith("{"):
            continue
        try:
            parsed.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return parsed


def validate(rec: dict, target_indices: set[int]) -> dict:
    """Validate a single classification dict against the canonical code sets."""
    assert rec.get("classification_target_idx") in target_indices, \
        f"unknown classification_target_idx: {rec.get('classification_target_idx')}"
    assert rec["theme"] in THEMES, f"invalid theme: {rec['theme']}"
    assert rec["mechanism"] in MECHS, f"invalid mechanism: {rec['mechanism']}"
    assert rec["addressee"] in ADDRS, f"invalid addressee: {rec['addressee']}"
    assert rec["specificity"] in SPECS, f"invalid specificity: {rec['specificity']}"
    assert rec["scope"] in SCOPES, f"invalid scope: {rec['scope']}"
    return rec


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--in", dest="input_path", type=Path, required=True,
                    help="Classification-target parquet (must have a 'text' column for re-runs).")
    ap.add_argument("--codebook", type=Path, required=True,
                    help="Path to codebook_v2.5_frozen_*.md")
    ap.add_argument("--out", type=Path, required=True,
                    help="Output parquet for this batch.")
    ap.add_argument("--start", type=int, required=True, help="Inclusive row start.")
    ap.add_argument("--end", type=int, required=True, help="Exclusive row end.")
    args = ap.parse_args()

    if "ANTHROPIC_API_KEY" not in os.environ:
        print("ERROR: set $ANTHROPIC_API_KEY before running.", file=sys.stderr)
        return 2

    df = pd.read_parquet(args.input_path)
    if "text" not in df.columns:
        print(
            "ERROR: input parquet has no 'text' column. The deposited "
            "classification_target.no_text.parquet excludes raw text for "
            "redistribution reasons; you must re-acquire the text from the "
            "upstream pipeline (scripts/01_load_upstream_recommendations.py) "
            "before running this template.",
            file=sys.stderr,
        )
        return 2

    batch = df.iloc[args.start:args.end].copy()
    target_indices = set(int(x) for x in batch["classification_target_idx"])
    codebook_text = args.codebook.read_text(encoding="utf-8")

    rows = batch[["classification_target_idx", "jurisdiction", "year", "text"]].to_dict("records")
    classifications = classify_with_anthropic(codebook_text, rows)

    validated = [validate(rec, target_indices) for rec in classifications]
    out_df = pd.DataFrame(validated)

    # Merge back onto the source metadata
    merged = batch.drop(columns=["text"]).merge(
        out_df, on="classification_target_idx", how="left"
    )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    merged.to_parquet(args.out, index=False)
    print(f"Wrote {args.out}: {merged.shape}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
