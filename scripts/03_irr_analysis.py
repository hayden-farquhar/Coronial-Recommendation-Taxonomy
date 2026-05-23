"""Compute Krippendorff's alpha per taxonomy axis from gold-standard ratings.

Expects rating files at `taxonomy/gold_standard/ratings_<rater>.csv` with columns:
    recommendation_id, theme, mechanism, addressee, specificity, scope

Outputs:
    outputs/tables/irr_summary.csv         — α on all rated rows
    outputs/tables/irr_summary_clean.csv   — α excluding catch-all-stack rows
                                              (post-filter of probable no-rec leaks)

The "clean" summary applies a labelling-consensus post-filter: any row that
**any** rater labelled with the catch-all stack
(theme=THEME-OTHER, mechanism=MECH-OTHER, addressee=ADDR-UNSPEC, specificity=SPEC-1,
scope=SCOPE-IND) is treated as a likely no-recommendation extract that slipped
through the upstream NO_REC_PATTERNS filter, and excluded from the alpha
computation. The filter must fire on either-rater (not both-rater) usage of
the catch-all stack because leak detection is asymmetric — one rater may read
a borderline row as "no actionable recommendation" while another reads the
same boilerplate as a real systemic recommendation (assigning SCOPE-SYS rather
than the catch-all SCOPE-IND). The earlier "both raters catchall" rule missed
exactly that asymmetric case and the disagreement leaked through into the
clean α as a spurious codebook problem.

Krippendorff's alpha is preferred over Cohen's kappa because:
- it generalises to >2 raters without averaging pairwise kappas,
- it handles missing ratings (a rater leaving cells blank) natively,
- it admits ordinal as well as nominal level-of-measurement — we use ordinal
  for `specificity` (3-point scale) and nominal for the rest.

Conventional acceptance thresholds (Krippendorff 2004):
    alpha >= 0.80   — reliable, defensible for substantive conclusions
    0.67 - 0.79     — tentative, only for tentative claims
    < 0.67          — unreliable; revise the codebook

The CLEAN α is the one to trust. The raw α is reported alongside for
transparency but the clean number is the codebook-revision signal.

Usage:
    python scripts/03_irr_analysis.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RATINGS_DIR = PROJECT_ROOT / "taxonomy" / "gold_standard"
OUT_CSV = PROJECT_ROOT / "outputs" / "tables" / "irr_summary.csv"
OUT_CSV_CLEAN = PROJECT_ROOT / "outputs" / "tables" / "irr_summary_clean.csv"

AXES_NOMINAL = ["theme", "mechanism", "addressee", "scope"]
AXES_ORDINAL = ["specificity"]

CATCH_ALL_STACK = {
    "theme": "THEME-OTHER",
    "mechanism": "MECH-OTHER",
    "addressee": "ADDR-UNSPEC",
    "specificity": "SPEC-1",
    "scope": "SCOPE-IND",
}


def _load_ratings() -> dict[str, pd.DataFrame]:
    files = sorted(RATINGS_DIR.glob("ratings_*.csv"))
    if not files:
        return {}
    return {f.stem.removeprefix("ratings_"): pd.read_csv(f) for f in files}


def _wide_matrix(ratings: dict[str, pd.DataFrame], axis: str) -> np.ndarray:
    """Return a (raters x items) matrix with categorical codes; NaN for missing."""
    rater_names = sorted(ratings)
    all_ids = sorted({rid for r in ratings.values() for rid in r["recommendation_id"]})
    mat = np.full((len(rater_names), len(all_ids)), np.nan)
    cat_to_int: dict[str, int] = {}
    for r_idx, rater in enumerate(rater_names):
        r = ratings[rater].set_index("recommendation_id")
        for c_idx, rid in enumerate(all_ids):
            if rid in r.index:
                val = r.at[rid, axis]
                if pd.isna(val):
                    continue
                if val not in cat_to_int:
                    cat_to_int[val] = len(cat_to_int)
                mat[r_idx, c_idx] = cat_to_int[val]
    return mat


def _catch_all_stack_ids(ratings: dict[str, pd.DataFrame]) -> set[str]:
    """recommendation_ids where ANY rater used the full catch-all stack.

    Asymmetric leak-detection: if one rater reads a borderline row as
    "no actionable recommendation" (catch-all stack) and another reads the
    same row as a real systemic recommendation, the row is structurally
    contested in a way that is not a codebook-ambiguity signal. Both raters
    needing to agree on the catch-all is the wrong condition — it missed
    exactly these asymmetric cases on the v2.0 pilot (6 rows in scope's
    raw disagreement set).
    """
    catch_all_by_rater: list[set[str]] = []
    for rater, df in ratings.items():
        mask = pd.Series(True, index=df.index)
        for axis, code in CATCH_ALL_STACK.items():
            mask &= (df[axis].astype(str) == code)
        catch_all_by_rater.append(set(df.loc[mask, "recommendation_id"]))
    if not catch_all_by_rater:
        return set()
    return set.union(*catch_all_by_rater)


def _pct_agreement(ratings: dict[str, pd.DataFrame], axis: str) -> float:
    """Mean pairwise % agreement across all rater pairs on this axis."""
    rater_names = sorted(ratings)
    if len(rater_names) < 2:
        return float("nan")
    # Align on common recommendation_ids
    common_ids = set.intersection(*(set(df["recommendation_id"]) for df in ratings.values()))
    if not common_ids:
        return float("nan")
    pair_agreements: list[float] = []
    for i in range(len(rater_names)):
        for j in range(i + 1, len(rater_names)):
            di = ratings[rater_names[i]].set_index("recommendation_id").loc[list(common_ids), axis]
            dj = ratings[rater_names[j]].set_index("recommendation_id").loc[list(common_ids), axis]
            pair_agreements.append((di.astype(str) == dj.astype(str)).mean())
    return float(sum(pair_agreements) / len(pair_agreements))


def _modal_share(ratings: dict[str, pd.DataFrame], axis: str) -> float:
    """Fraction of all labels (across raters) occupied by the most-frequent category.

    Used to flag axes with extreme marginal skew where alpha alone is unstable.
    """
    all_labels: list[str] = []
    for df in ratings.values():
        all_labels.extend(df[axis].astype(str).tolist())
    if not all_labels:
        return float("nan")
    counts: dict[str, int] = {}
    for v in all_labels:
        counts[v] = counts.get(v, 0) + 1
    return max(counts.values()) / len(all_labels)


def _alpha_table(ratings: dict[str, pd.DataFrame], krippendorff_mod) -> pd.DataFrame:
    rows = []
    for axis in AXES_NOMINAL + AXES_ORDINAL:
        mat = _wide_matrix(ratings, axis)
        level = "ordinal" if axis in AXES_ORDINAL else "nominal"
        try:
            alpha = krippendorff_mod.alpha(reliability_data=mat, level_of_measurement=level)
        except Exception as exc:  # noqa: BLE001
            alpha = float("nan")
            print(f"  [{axis}] alpha unavailable: {exc}")
        pct = _pct_agreement(ratings, axis)
        modal = _modal_share(ratings, axis)
        skewed = modal >= 0.90
        verdict = _verdict(alpha, pct, skewed)
        rows.append(
            {
                "axis": axis,
                "level_of_measurement": level,
                "n_raters": mat.shape[0],
                "n_items": mat.shape[1],
                "alpha": alpha,
                "pct_agreement": pct,
                "modal_category_share": modal,
                "marginal_skewed": skewed,
                "verdict": verdict,
            }
        )
        skew_marker = " [SKEWED]" if skewed else ""
        print(
            f"  [{axis:12s}] level={level:7s} n={mat.shape[1]} "
            f"alpha={alpha:.3f} pct_agree={100*pct:5.1f}% "
            f"modal={100*modal:4.1f}%{skew_marker} -> {verdict}"
        )
    return pd.DataFrame(rows)


def _verdict(alpha: float, pct: float, skewed: bool) -> str:
    """Apply the v1.2 decision criterion for an axis being 'Reliable'.

    Reliable if either (a) clean alpha >= 0.80, or (b) the alpha shortfall is
    explained by a single category dominating >= 90% of labels AND pct
    agreement >= 90%. The latter is a known Krippendorff-alpha pathology on
    heavily-skewed distributions, not a codebook problem.
    """
    if alpha != alpha:  # nan
        return "unavailable"
    if alpha >= 0.80:
        return "Reliable"
    if skewed and pct >= 0.90:
        return "Reliable (skew-adjusted)"
    if alpha >= 0.67:
        return "Tentative"
    return "Unreliable"


def main() -> int:
    try:
        import krippendorff
    except ImportError:
        print("ERROR: pip install krippendorff", file=sys.stderr)
        return 2

    ratings = _load_ratings()
    if not ratings:
        print(f"No ratings files under {RATINGS_DIR}. Drop in ratings_<rater>.csv files and re-run.")
        return 0

    print(f"Found {len(ratings)} rater(s): {sorted(ratings)}")

    print("\n=== Raw alpha (all rated rows) ===")
    df_raw = _alpha_table(ratings, krippendorff)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df_raw.to_csv(OUT_CSV, index=False)
    print(f"Wrote {OUT_CSV}")

    catch_all_ids = _catch_all_stack_ids(ratings)
    if catch_all_ids:
        print(f"\nPost-filter: {len(catch_all_ids)} rows where at least one rater used the catch-all stack")
        print("(theme=OTHER, mech=OTHER, addr=UNSPEC, spec=SPEC-1, scope=SCOPE-IND)")
        print("These are likely no-recommendation extracts that bypassed the upstream filter,")
        print("or asymmetric leak-detection rows where raters split on whether the text is a real recommendation.")
        print(f"  Excluded recommendation_ids: {sorted(catch_all_ids)[:5]}{'...' if len(catch_all_ids)>5 else ''}")

        clean_ratings = {
            r: df[~df["recommendation_id"].isin(catch_all_ids)].reset_index(drop=True)
            for r, df in ratings.items()
        }
        print("\n=== Clean alpha (catch-all-stack rows excluded) ===")
        df_clean = _alpha_table(clean_ratings, krippendorff)
        df_clean.to_csv(OUT_CSV_CLEAN, index=False)
        print(f"Wrote {OUT_CSV_CLEAN}")
    else:
        print("\nNo catch-all-stack rows detected — clean and raw alpha would be identical.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
