# Data Dictionary

Variable definitions for the deposited classification parquets.

## `data/recommendations_v2.5_classified.no_text.parquet`

n = 2,702 rows × 31 columns. One row per case-level recommendation extract that passed the no-recommendation filter. The raw `text` column is omitted for redistribution reasons (see `data/README.md`).

### Source metadata (from upstream pipeline)

| Column | Type | Description |
|---|---|---|
| `case_id` | string | Upstream case identifier (jurisdiction-prefixed) |
| `jurisdiction` | string | Australian state/territory: `NSW`, `VIC`, `QLD`, `WA`, `SA`, `TAS`, `NT`, `ACT` |
| `db_code` | string | Upstream coronial database code |
| `db_type` | string | Upstream database type |
| `year` | int | Year of the coronial finding |
| `case_number` | string | Original case number assigned by the issuing court |
| `title` | string | Title of the coronial finding (typically the deceased's name; potentially identifying) |
| `citation` | string | Formal legal citation |
| `date_iso` | string | ISO 8601 date of the finding |
| `finding_type` | string | Upstream finding-type code |
| `coroner` | string | Coroner's name |
| `url` | string | AustLII URL where the original finding is hosted |
| `recommendation_count` | int | Number of distinct recommendations identified by the upstream parser (raw; may be inflated for long documents) |
| `recommendation_id` | string | Recommendation identifier (equals `case_id` in case-level mode) |
| `recommendation_idx` | int | Within-case recommendation index (always 0 in case-level mode) |
| `text_chars` | int | Character count of the original recommendation text (preserved as a quality / filter indicator after `text` was dropped) |
| `classification_target_idx` | int | Sequential row index in the filtered classification target (0..2,701) |

### Classification axes (frozen v2.5 codebook)

| Column | Type | Categories |
|---|---|---|
| `theme` | string | `THEME-MH`, `THEME-CUST`, `THEME-MED`, `THEME-RTA`, `THEME-DV`, `THEME-DRUG`, `THEME-CHILD`, `THEME-WORK`, `THEME-REC`, `THEME-FIRE`, `THEME-PROD`, `THEME-OTHER` |
| `mechanism` | string | `MECH-LEG`, `MECH-INFRA`, `MECH-FUND`, `MECH-INV`, `MECH-PROC`, `MECH-OTHER` |
| `addressee` | string | `ADDR-DEPT-NAMED`, `ADDR-DEPT-GENERIC`, `ADDR-HEALTH`, `ADDR-REG`, `ADDR-PROF`, `ADDR-POLICE`, `ADDR-COURT`, `ADDR-PRIVATE`, `ADDR-UNSPEC` |
| `specificity` | string | `SPEC-1` (aspirational), `SPEC-2` (specific) |
| `scope` | string | `SCOPE-IND` (one-off discrete remediation), `SCOPE-SYS` (ongoing system change), `SCOPE-MIX` (release-valve category) |
| `has_deadline_or_metric` | bool | TRUE if the recommendation contains a deadline cue or measurable outcome target (preserves the v1.x SPEC-3 signal as an independent flag) |

Full decision rules, worked examples, and the 30+ canonical borderline-entity list for each axis are in `codebook/codebook_v2.5_frozen_2026-05-22.md`.

### Classification ambiguity flags

| Column | Type | Description |
|---|---|---|
| `ambiguous_theme` | bool | TRUE if the recommendation contained multiple sub-recommendations with different themes |
| `ambiguous_mechanism` | bool | Multi-rec mechanism disagreement flag |
| `ambiguous_addressee` | bool | Multi-rec addressee disagreement flag |
| `ambiguous_specificity` | bool | Multi-rec specificity disagreement flag |
| `ambiguous_scope` | bool | Multi-rec scope disagreement flag |

For multi-rec sets, the headline axis value reflects the FIRST stated recommendation; the ambiguity flag indicates whether later recommendations would have been coded differently.

### Quality flags

| Column | Type | Description |
|---|---|---|
| `requires_legal_expertise` | bool | Coder flagged the recommendation as requiring legal expertise for confident classification |
| `non_english_or_redacted` | bool | TRUE if the text contained non-English material or significant redaction |
| `coder_notes` | string | Free-text notes from the LLM coder (≤ 200 characters per row) |

## `data/classification_target.no_text.parquet`

n = 2,702 rows × 17 columns. Pre-classification corpus filtered to the analytic sample. Same source-metadata columns as above, without the classification axes. The `classification_target_idx` column matches between the two parquets for joining.

## `irr_results/pilot_sample_v2.5_heldout_seed878.no_text.csv`

n = 50 rows × 22 columns. The held-out IRR sample used for codebook external validation. Columns include the source metadata (case_id, jurisdiction, year, etc.), the `year_bin` derived field (`pre-2010`, `2010-2019`, `2020+`), and the classification + ambiguity + quality flag columns described above. The `text` column is omitted; the raw text can be re-fetched via the `url` column.

## `irr_results/ratings_heldout_opus_seed878.csv` and `ratings_heldout_sonnet_seed878.csv`

n = 50 rows × 22 columns each. The two coders' independent classifications of the held-out sample under the frozen v2.5 codebook. Used to produce the held-out IRR table in `irr_results/irr_heldout_v2.5.csv`.

## `irr_results/irr_heldout_v2.5.csv`

The held-out IRR table reported as Table 1 in the manuscript. Five rows (one per axis) × columns: `axis`, `krippendorff_alpha`, `pct_agreement`, `modal_share`, `verdict` (Reliable / Tentative / Unreliable).

## `irr_results/irr_final_v2.5.csv`

The development-sample IRR table (author vs Opus 4.7) across two pilot samples under v2.5. Reported as a supplementary IRR table for transparency.

## `outputs/tables/` and `outputs/figures/`

The 31 tables and 28 figures produced under the pre-registered analysis plan (sections A–G). File naming follows the section letter: `A_*` for single-axis distributions, `B_*` for axis × jurisdiction, `C_*` for axis × year-bin, `D_*` for two-axis cross-tabs, `E_*` for three-axis configurations, `F_*` for compliance descriptive analyses, `G_*` for the methodological appendix.
