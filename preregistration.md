# Pre-registration: Multi-axis structural analysis of Australian coronial recommendations

This pre-registration locks the analysis plan for an applied descriptive study of Australian coronial recommendations using a multi-axis taxonomy. It is filed BEFORE the full-corpus classification runs to address the methodological concern that iterative codebook refinement during development phases could enable post-hoc analytical fishing.

**Registration type:** OSF Pre-Registration (Standard).
**Date frozen:** 2026-05-23.
**Codebook version:** v2.5 (frozen).

---

## 1. Title

A multi-axis taxonomy of Australian coronial recommendations: distributions, jurisdictional variation, and structural configurations.

## 2. Authors

Hayden Farquhar (sole author at the time of pre-registration).

## 3. Research questions

Descriptive, not predictive. The study answers four questions about the structural patterns of coronial recommendations issued by Australian coroners between 1998 and 2026:

**Q1.** What is the distribution of recommendations across five conceptual axes (theme, mechanism, addressee, specificity, scope) under a unified codebook?

**Q2.** How does each axis vary by jurisdiction (8 Australian state and territory coronial systems)?

**Q3.** How does each axis vary across three time-bins (pre-2010, 2010–2019, 2020+)?

**Q4.** What are the most common multi-axis configurations of recommendations (e.g., theme × mechanism × addressee combinations) and how do they differ by jurisdiction?

A fifth question addresses compliance descriptively (Q5): how do compliance outcomes (already classified by the parent coronial-NLP pipeline) vary across the four axes (excluding theme, which the parent pipeline already analyses)? Predictive analyses on compliance are explicitly out of scope (reserved for an ongoing longitudinal companion analysis).

## 4. Hypotheses

This is a descriptive study; no formal hypotheses are advanced. We do not pre-specify which patterns should emerge.

Where descriptive findings would inform downstream causal or predictive analyses (e.g., compliance prediction by axis), those analyses are deferred to sibling projects (a longitudinal companion analysis for compliance over time; a cross-national companion comparing the Australian and English/Welsh systems; a public-dashboard implementation companion).

## 5. Sampling plan

**Data source:** Australian coronial findings published on AustLII between 1998 and 2026, scraped via the parent coronial-NLP pipeline. Recommendation text was extracted from coronial findings during the upstream preprocessing step.

**Sample:** Full filtered corpus of n=2,702 case-level recommendation extracts after the following exclusions:

- `recommendation_count ∈ [1, 25]` (excludes upstream parser pathology where the recommendation counter overcounted numbered paragraphs in long inquest findings; max raw value was 1,150)
- `text_chars ∈ [200, 12,000]` (excludes truncated extracts and pathologically long blocks)
- No-recommendation regex filter excludes 676 cases where the coroner explicitly declined to recommend ("I make no formal recommendations", "no need to make any further comment", etc. — see `scripts/05_sample_irr_pilot.py:NO_REC_PATTERNS` for the exact patterns)

Filter from 3,703 case-level rows → 3,354 (size+count bounds) → 2,702 (after no-rec filter).

**Filter rationale:** the exclusions are upstream-data-quality decisions. They were locked during this study's IRR pilot phase (see `taxonomy/codebook_versions/v2.2_frozen_2026-05-22.md` and the project's development log archived alongside this deposit). No further data-driven exclusions will be added.

**Distribution after filter:** VIC 1,232; SA 356; QLD 333; TAS 274; NSW 202; NT 160; WA 127; ACT 18.

## 6. Variables

**Measured variables (5 axes):**

| Axis | Categories | Frozen rules |
|---|---|---|
| Theme | 12 (THEME-MH, -CUST, -MED, -RTA, -DV, -DRUG, -CHILD, -WORK, -REC, -FIRE, -PROD, -OTHER) | v2.5 codebook §"Axis 1" |
| Mechanism | 6 (MECH-LEG, -INFRA, -FUND, -INV, -PROC, -OTHER) | v2.5 codebook §"Axis 2" — Q1..Q6 decision tree |
| Addressee | 9 (ADDR-DEPT-NAMED, -DEPT-GENERIC, -HEALTH, -REG, -PROF, -POLICE, -COURT, -PRIVATE, -UNSPEC) | v2.5 codebook §"Axis 3" |
| Specificity | 2 (SPEC-1, SPEC-2) | v2.5 codebook §"Axis 4" |
| Scope | 3 (SCOPE-IND, SCOPE-SYS, SCOPE-MIX) | v2.5 codebook §"Axis 5" |

**Derived/joined variables:**
- `has_deadline_or_metric` (boolean) — flagged per v2.5 specificity rules
- `compliance_outcome` (from the upstream pipeline — implemented / under consideration / partially accepted / not supported / noted / unclassifiable) — joined on `case_id`
- `jurisdiction` (8 states/territories)
- `year_bin` (pre-2010 / 2010-2019 / 2020+)

**Codebook freeze:** `taxonomy/codebook_versions/v2.5_frozen_2026-05-22.md` is the authoritative reference. No revisions to the codebook will be made during analysis. If a classification ambiguity is identified post-classification, it will be reported as a limitation rather than triggering a codebook amendment.

## 7. Design plan

**Study type:** Observational, descriptive corpus analysis.

**Randomisation/blinding:** Not applicable (corpus is fully enumerated).

**Classification procedure:** All 2,702 cases will be classified by a single competent frontier large language model applying the frozen v2.5 codebook. The classification is run in batches of approximately 200 cases per invocation. Each row's classification is the result of the model reading the recommendation text and applying the codebook's decision rules. Outputs are validated against the canonical code sets for each axis before saving. The chosen classifier was the higher-performing of two frontier coders in the held-out validation reported below; using a single competent classifier is standard for automated coding studies of this size. (Specific model identity and version are recorded in the AI-use declaration of the accompanying manuscript.)

**Held-out IRR for codebook quality:** A separate held-out sample (n=50, seed 878, never used in codebook development) was double-coded by two frontier large language models from the same model family under the frozen v2.5 codebook. Results (n=40 clean):

| Axis | Krippendorff's α | % agreement | Verdict |
|---|---:|---:|---|
| theme | 0.709 | 75.0% | Tentative |
| mechanism | 0.376 | 75.0% | Unreliable (INV/PROC residual ambiguity) |
| addressee | 0.841 | 87.5% | Reliable |
| specificity | 0.844 | 92.5% | Reliable |
| scope | 1.000 | 100.0% | Reliable |

The mechanism axis result is the load-bearing limitation for this study. The MECH-INV ↔ MECH-PROC boundary has residual interpretive ambiguity in the v2.5 codebook that did not surface during the development-sample IRR (where the operational-endpoint rule appeared to resolve it). Findings on the mechanism axis are reported descriptively in this study with explicit acknowledgement of this limitation; predictive claims involving mechanism are not made.

Held-out IRR results saved at `outputs/tables/irr_heldout_v2.5.csv`. Development-sample IRR at `outputs/tables/irr_final_v2.5.csv`.

## 8. Analysis plan

Locked at the time of this pre-registration. Analyses below will be conducted exactly as specified. Any post-hoc exploration will be labelled as such and reported separately from pre-registered analyses.

### Pre-registered analyses

**A. Single-axis distributions (5 figures + 1 table)**
- Bar chart per axis showing N and % per category
- Theme distribution to be cross-validated against the upstream 24-topic BERTopic recommendation model (consistency check, not used for codebook revision)

**B. Axis × jurisdiction (5 heatmaps + 5 tables)**
- Each axis × 8 jurisdictions
- Pearson's χ² test of independence for each axis × jurisdiction table
- χ² interpreted descriptively (test of structural variation across jurisdictions, not as inferential claim about Australian coronial systems)

**C. Axis × year-bin (5 line charts)**
- Each axis × 3 year-bins (pre-2010, 2010-2019, 2020+)
- Temporal trend reported descriptively

**D. Two-axis cross-tabulations (6 heatmaps + 6 tables)**
- Mechanism × Addressee
- Theme × Mechanism
- Theme × Addressee
- Specificity × Mechanism
- Specificity × Addressee
- Scope × Theme

**E. Three-axis modal configurations (1 figure + 1 table)**
- The top-5 most-common Theme × Mechanism × Addressee triples by jurisdiction
- Visualised as a stacked bar by jurisdiction

**F. Compliance descriptive analyses (4 heatmaps + 4 tables)**
- Compliance outcome × Mechanism, × Addressee, × Specificity, × Scope
- Compliance × Theme is reserved for the parent coronial-NLP pipeline's own analysis
- Reported descriptively; no causal or predictive claims. Predictive analyses are reserved for the longitudinal companion analysis.

**G. Methodological appendix (1 table)**
- Held-out IRR table + development-sample IRR table
- Brief documentation of the LLM-IRR diagnostic patterns discovered (deterministic-LLM-artefact, capability-tier-mismatch, axis-conflation) with references to the audit document (`manuscript/peer_review_audit.md`)

### Statistical methods

- All figures: matplotlib or seaborn for static figures; tables in pandas / CSV
- Cross-tabulation tests: Pearson's χ² with continuity correction where 2×2 cells exist; Cramér's V as effect size
- Multiple comparisons: Benjamini-Hochberg FDR correction across all χ² tests, p<0.05 significance threshold (descriptive)
- No predictive modeling. No regression. No causal inference.

### Inference criteria

This study reports descriptive findings on the corpus of Australian coronial recommendations 1998–2026. Findings should not be interpreted as causal claims about coronial systems, predictive claims about future recommendations, or generalisable claims to non-Australian jurisdictions. The corpus represents the population of recommendations actually issued in this period; statistical tests assess structural variation within the corpus, not inferential claims to a larger population.

### Data exclusions

Exclusions are locked at the pre-filter stage (see §5 Sampling plan). No further exclusions will be applied during analysis. Cases with `addressee = ADDR-UNSPEC` (no clear addressee in the text) will be reported descriptively but excluded from analyses that condition on addressee (no manipulation of the catchall).

## 9. Other

**Computational reproducibility:** Analysis code will be deposited to GitHub or Zenodo at submission. The classification target file (`data/au/classification_target.parquet`) and the full LLM classifications will be deposited as supplementary data.

**Relationship to companion work:** This study sits in a cluster of related coronial-recommendation work by the same author. A parent coronial-NLP pipeline provides the corpus, an upstream theme cross-validation, and the compliance classifications joined in section F. Three companion projects (a cross-national AU-vs-England/Wales comparison; a public Australian dashboard implementation; a longitudinal compliance analysis with policy-response linkage) build on the v2.5 codebook frozen here. None of those companion projects are affected by this pre-registration, and the predictive-compliance analyses excluded from this study are reserved for the longitudinal companion.

**Amendments:** Any amendments to this pre-registration will be logged via OSF amendment process with date and reason. Codebook will not be amended; analysis plan may be amended only with explicit justification deposited to OSF before the amended analysis is run.

**Anticipated venue:** Open at the time of pre-registration. Final venue choice will be made at submission time.

---

## Frozen artefacts (deposited at the same OSF DOI as this pre-registration)

- Frozen v2.5 codebook
- Held-out IRR sample (seed 878) + both rater files
- Development-sample IRR archives (v2.0 through v2.5)

## Signatures

This pre-registration is filed by Hayden Farquhar (sole author, independent researcher). No co-authors at the time of filing.

Date: 2026-05-23
