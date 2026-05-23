# Coronial Recommendation Taxonomy

Code, codebook, and analytic outputs for:

**A multi-axis taxonomy of Australian coronial recommendations: distributions, jurisdictional variation, and structural configurations, 1998–2026**

Hayden Farquhar, MBBS MPHTM. Independent researcher, Finley, New South Wales, Australia. ORCID: 0009-0002-6226-440X.

Pre-registration: [https://doi.org/10.17605/OSF.IO/NEX85](https://doi.org/10.17605/OSF.IO/NEX85) (Open Science Framework, CC-BY 4.0, binding analysis plan).

## Overview

This repository contains the analysis code, frozen codebook, pre-registered analysis outputs, and inter-rater reliability artefacts for a corpus-level study of Australian coronial recommendations (1998–2026). The study applies a five-axis taxonomy (theme, mechanism, addressee, specificity, scope) to n = 2,702 case-level recommendation extracts and reports descriptive distributions, jurisdictional variation, and structural configurations.

This repository **does not** contain the accompanying manuscript itself, nor any submission-preparation artefacts. The manuscript, when posted as a preprint, will reference this repository for code and outputs.

## Data Sources

| Source | URL | Access | License |
|--------|-----|--------|---------|
| Australasian Legal Information Institute (AustLII) coronial findings | https://www.austlii.edu.au/ | Free / public | AustLII terms of use — personal and research use; redistribution restricted |
| OSF pre-registration deposit (codebook, IRR samples, analysis plan) | https://doi.org/10.17605/OSF.IO/NEX85 | Free / public | CC-BY 4.0 |

**Recommendation text is NOT redistributed in this repository.** The deposited parquet files contain case-level metadata (case ID, jurisdiction, year, citation URL, classification axes) but omit the `text` column. To re-acquire the text, follow the instructions in `data/README.md`.

## Requirements

- Python 3.10 or later
- See `requirements.txt` for package versions

```bash
pip install -r requirements.txt
```

## Reproduction

The analysis pipeline produces the figures and tables reported in the accompanying manuscript. Two reproduction paths are supported:

### Path A — Reproduce analyses from the deposited classifications (default, no API access required)

The deposited `data/recommendations_v2.5_classified.no_text.parquet` contains the corpus-level classifications produced under the frozen v2.5 codebook. From this, the pre-registered analyses can be regenerated end-to-end:

```bash
# Step 1: Pre-registered analyses, sections A–E (single-axis, axis × jurisdiction,
#         axis × year-bin, two-axis cross-tabs, three-axis configurations)
python scripts/06_shape_b_analyses_ABCDE.py

# Step 2: Pre-registered analyses, sections F–G (compliance descriptive,
#         methodological appendix)
#         Requires the upstream pipeline's findings_responses_linked.csv —
#         see data/README.md for acquisition instructions
export UPSTREAM_LINKED_CSV=/path/to/findings_responses_linked.csv
python scripts/07_shape_b_analyses_FG.py
```

Expected outputs: 28 figures in `outputs/figures/` and 31 tables in `outputs/tables/`.

### Path B — Re-run the corpus classification (requires Anthropic API access)

If you wish to re-run the classification rather than accept the deposited results:

```bash
# Step 1: Acquire raw text from the upstream coronial-NLP pipeline
export UPSTREAM_CASES=/path/to/cases_clean.jsonl
python scripts/01_load_upstream_recommendations.py

# Step 2: Apply the IRR-pilot sampler and no-recommendation filter
python scripts/05_sample_irr_pilot.py --seed 878   # held-out IRR sample

# Step 3: Run the classification template against the codebook in batches of ~200
export ANTHROPIC_API_KEY=sk-ant-...
python scripts/08_classify_corpus_template.py \
    --in data/classification_target.parquet \
    --codebook codebook/codebook_v2.5_frozen_2026-05-22.md \
    --start 0 --end 200 --out batches/batch_000.parquet
# ... repeat with --start 200 --end 400, etc.

# Step 4: Concatenate batch outputs into a single corpus-level classification
python -c "import pandas as pd; from pathlib import Path; \
    pd.concat([pd.read_parquet(p) for p in sorted(Path('batches').glob('*.parquet'))]) \
    .to_parquet('data/recommendations_v2.5_classified.parquet', index=False)"

# Step 5: Re-run inter-rater reliability against the held-out sample
python scripts/09_classify_heldout.py
python scripts/03_irr_analysis.py
```

Note that LLM outputs are not deterministic across model versions or temperatures — expect minor variation from the deposited classifications.

### Estimated runtime

- Path A (analyses only): ~5 minutes on a modern laptop
- Path B (re-classify full corpus): ~2–4 hours wall-clock against the Anthropic API, depending on rate limits

## Script Descriptions

| Script | Description | Inputs | Outputs |
|--------|-------------|--------|---------|
| `01_load_upstream_recommendations.py` | Extract case-level recommendation text from upstream coronial-NLP pipeline | `$UPSTREAM_CASES` JSONL | `data/recommendations.parquet` |
| `03_irr_analysis.py` | Krippendorff's α per axis (nominal + ordinal); raw and catchall-filtered | `irr_results/ratings_*.csv` | `irr_results/irr_summary*.csv` |
| `04_eda.py` | Corpus exploratory analysis (jurisdiction × year distributions, text-length stats) | `data/recommendations.parquet` | `outputs/figures/corpus_eda.png`, `outputs/tables/corpus_eda_*.csv` |
| `05_sample_irr_pilot.py` | Stratified random sampler for IRR pilots; includes the no-recommendation regex filter | `data/recommendations.parquet`, `--seed` | `data/classification_target.parquet`, pilot CSVs |
| `06_shape_b_analyses_ABCDE.py` | Pre-registered analyses A–E (single-axis distributions, axis × jurisdiction, axis × year-bin, two-axis cross-tabs, three-axis configurations) | `data/recommendations_v2.5_classified.no_text.parquet` | `outputs/figures/A_*.png … E_*.png`, `outputs/tables/A_*.csv … E_*.csv` |
| `07_shape_b_analyses_FG.py` | Pre-registered analyses F–G (compliance descriptive joining upstream response data; methodological appendix) | Classified parquet + `$UPSTREAM_LINKED_CSV` | `outputs/figures/F_*.png, G_*.png`, `outputs/tables/F_*.csv, G_*.csv` |
| `08_classify_corpus_template.py` | TEMPLATE for re-running the classification under the frozen v2.5 codebook via Anthropic API | `classification_target` parquet (with text), codebook, `$ANTHROPIC_API_KEY` | batch parquets |
| `09_classify_heldout.py` | Audit-trail record of the Sonnet 4.6 held-out classification (frozen output as Python tuples) | Held-out IRR sample | `irr_results/ratings_heldout_sonnet_seed878.csv` |

## Outputs

| File | Paper reference |
|------|----------------|
| `outputs/tables/A_theme_distribution.csv` | Table 2 (theme row) |
| `outputs/tables/A_mechanism_distribution.csv` | Table 2 (mechanism row) |
| `outputs/tables/A_addressee_distribution.csv` | Table 2 (addressee row) |
| `outputs/tables/A_specificity_distribution.csv` | Table 2 (specificity row) |
| `outputs/tables/A_scope_distribution.csv` | Table 2 (scope row) |
| `outputs/tables/B_chi2_axis_by_jurisdiction.csv` | Table 3 |
| `outputs/tables/B_specificity_by_jurisdiction.csv` | §3.2 jurisdictional specificity range |
| `outputs/tables/E_top10_configurations_overall.csv` | Table 4 |
| `outputs/tables/F_response_presence_rate.csv` | Table 5 |
| `outputs/tables/F_chi2_compliance.csv` | §3.6 compliance × axis tests |
| `outputs/tables/G_irr_summary_combined.csv` | Table 1 (held-out IRR rows) + supplementary IRR table (development rows) |
| `outputs/figures/A_*.png` … `G_*.png` | Supplementary figures |
| `irr_results/irr_heldout_v2.5.csv` | Table 1 |
| `irr_results/irr_final_v2.5.csv` | Supplementary IRR table |

## Codebook

The frozen v2.5 codebook (the analytic instrument) is at `codebook/codebook_v2.5_frozen_2026-05-22.md`. Earlier frozen versions (v0 through v2.4) are preserved in `codebook/codebook_versions/` as the development audit trail.

## Pre-registration

`preregistration.md` is a verbatim copy of the analysis plan filed at [https://doi.org/10.17605/OSF.IO/NEX85](https://doi.org/10.17605/OSF.IO/NEX85). The OSF deposit is the authoritative version.

## Citation

If you use this code, please cite the accompanying paper (citation to be added when the preprint is posted) and the OSF pre-registration:

```
Farquhar H. Pre-registration: A multi-axis taxonomy of Australian coronial
recommendations. Open Science Framework, 2026.
https://doi.org/10.17605/OSF.IO/NEX85
```

## License

- **Code** (everything under `scripts/`): MIT License (see `LICENSE`).
- **Codebook and documentation** (`codebook/`, `preregistration.md`, this README, `data_dictionary.md`): CC-BY 4.0 (see `LICENSE`).
- **Output tables and figures** (`outputs/`, `irr_results/`): CC-BY 4.0.
- **Deposited classification parquets** (`data/*.parquet`): CC-BY 4.0 for the classifications; raw recommendation text is NOT redistributed and remains subject to the original AustLII terms of use.

## Contact

Hayden Farquhar — hayden.farquhar@icloud.com — ORCID 0009-0002-6226-440X
