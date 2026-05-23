"""Corpus EDA — distributions over jurisdiction, year, text length, recommendation count.

Designed to inform the IRR-pilot sampling strategy: which strata exist, are
they balanced, how long are the recommendation texts? Answers feed
scripts/05_sample_irr_pilot.py.

Outputs:
    outputs/tables/corpus_eda_jurisdiction.csv
    outputs/tables/corpus_eda_year.csv
    outputs/tables/corpus_eda_summary.csv
    outputs/figures/corpus_eda.png

Usage:
    python scripts/04_eda.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
IN_PARQUET = PROJECT_ROOT / "data" / "au" / "recommendations.parquet"
TABLES_DIR = PROJECT_ROOT / "outputs" / "tables"
FIGURES_DIR = PROJECT_ROOT / "outputs" / "figures"


def main() -> int:
    df = pd.read_parquet(IN_PARQUET)
    print(f"Loaded {len(df):,} rows from {IN_PARQUET}")
    df = df.assign(
        text_chars=df["text"].str.len(),
        text_words=df["text"].str.split().str.len(),
    )

    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    summary = pd.DataFrame(
        {
            "metric": [
                "n_rows",
                "n_unique_cases",
                "n_jurisdictions",
                "year_min",
                "year_max",
                "text_chars_mean",
                "text_chars_median",
                "text_chars_p90",
                "text_words_mean",
                "rec_count_mean",
                "rec_count_median",
                "rec_count_max",
            ],
            "value": [
                len(df),
                df["case_id"].nunique(),
                df["jurisdiction"].nunique(),
                int(df["year"].min()),
                int(df["year"].max()),
                round(df["text_chars"].mean(), 1),
                int(df["text_chars"].median()),
                int(df["text_chars"].quantile(0.9)),
                round(df["text_words"].mean(), 1),
                round(df["recommendation_count"].mean(), 2),
                int(df["recommendation_count"].median()),
                int(df["recommendation_count"].max()),
            ],
        }
    )
    summary.to_csv(TABLES_DIR / "corpus_eda_summary.csv", index=False)
    print("\nSummary:")
    print(summary.to_string(index=False))

    by_juris = (
        df.groupby("jurisdiction", dropna=False)
        .agg(
            n_cases=("case_id", "nunique"),
            n_rows=("recommendation_id", "count"),
            text_chars_median=("text_chars", "median"),
            rec_count_median=("recommendation_count", "median"),
        )
        .sort_values("n_cases", ascending=False)
        .reset_index()
    )
    by_juris.to_csv(TABLES_DIR / "corpus_eda_jurisdiction.csv", index=False)
    print("\nBy jurisdiction:")
    print(by_juris.to_string(index=False))

    by_year = (
        df.groupby("year", dropna=False)
        .agg(n_cases=("case_id", "nunique"))
        .reset_index()
        .sort_values("year")
    )
    by_year.to_csv(TABLES_DIR / "corpus_eda_year.csv", index=False)
    print(f"\nYear coverage: {len(by_year)} years")

    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(2, 2, figsize=(12, 8))

        axes[0, 0].bar(by_juris["jurisdiction"], by_juris["n_cases"])
        axes[0, 0].set_title("Cases by jurisdiction")
        axes[0, 0].set_ylabel("Cases with recommendations")
        axes[0, 0].tick_params(axis="x", rotation=45)

        axes[0, 1].plot(by_year["year"], by_year["n_cases"], marker="o")
        axes[0, 1].set_title("Cases by year")
        axes[0, 1].set_xlabel("Year")
        axes[0, 1].set_ylabel("Cases with recommendations")

        axes[1, 0].hist(df["text_chars"].clip(upper=10000), bins=40)
        axes[1, 0].set_title("Recommendation text length (chars; capped 10k)")
        axes[1, 0].set_xlabel("Characters")
        axes[1, 0].set_ylabel("Cases")

        axes[1, 1].hist(df["recommendation_count"].clip(upper=20), bins=range(0, 22))
        axes[1, 1].set_title("Recommendations per case (capped 20)")
        axes[1, 1].set_xlabel("recommendation_count")
        axes[1, 1].set_ylabel("Cases")

        fig.tight_layout()
        out = FIGURES_DIR / "corpus_eda.png"
        fig.savefig(out, dpi=120)
        print(f"\nWrote {out}")
    except ImportError:
        print("matplotlib not installed — skipping figure.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
