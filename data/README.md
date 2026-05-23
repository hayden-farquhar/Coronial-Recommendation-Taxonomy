# Data — how to obtain the raw recommendation text

The deposited parquet files in this directory (`recommendations_v2.5_classified.no_text.parquet`, `classification_target.no_text.parquet`) contain case-level metadata and classifications but **omit the raw recommendation text**. This is a redistribution constraint: the underlying coronial-finding text remains the property of the issuing Australian jurisdictions and is hosted on AustLII under terms that permit personal/research use but restrict redistribution.

## To re-acquire the text

Two paths.

### Path 1 — Re-fetch from AustLII per case

Each row in the deposited parquets contains a `url` column pointing to the AustLII page for the relevant coronial finding. A reader can iterate the URLs and download the underlying findings, then re-extract the recommendation block using the same logic as the upstream pipeline. AustLII rate-limits aggressive crawling — please respect a polite request rate (e.g. one request per second) and use the User-Agent header to identify yourself.

### Path 2 — Use an upstream coronial-NLP pipeline

The classifications in this repository were downstream of an upstream NLP pipeline that scraped, parsed, and segmented Australian coronial findings 1998–2026 into a `cases_clean.jsonl` file. The schema is documented in the docstring of `scripts/01_load_upstream_recommendations.py`. Equivalent pipelines can be built using AustLII's site map; alternatively, the upstream `cases_clean.jsonl` may be available on request to the author for academic research purposes, subject to AustLII terms of use.

Once you have a `cases_clean.jsonl` with the schema described in `scripts/01`, set:

```bash
export UPSTREAM_CASES=/path/to/cases_clean.jsonl
python ../scripts/01_load_upstream_recommendations.py
```

This will produce `data/recommendations.parquet` with the `text` column populated, ready for the classification pipeline (`08_classify_corpus_template.py`) or for re-running the IRR pilot sampler (`05_sample_irr_pilot.py`).

## Compliance descriptive analyses (section F)

`scripts/07_shape_b_analyses_FG.py` joins the classified corpus to an upstream `findings_responses_linked.csv` file that captures whether each recommendation received a documented response from the addressee and what compliance classification that response received. This file is produced by a separate upstream analysis (the parent coronial-NLP project) and is not included in this repository. To re-run section F:

```bash
export UPSTREAM_LINKED_CSV=/path/to/findings_responses_linked.csv
python ../scripts/07_shape_b_analyses_FG.py
```

The deposited `outputs/tables/F_*.csv` and `outputs/figures/F_*.png` files are the aggregated results — these can be inspected directly without re-running.
