# Codebook

The frozen v2.5 codebook (`codebook_v2.5_frozen_2026-05-22.md`) is the analytic instrument used to classify the corpus. It defines:

- **Five axes** (theme, mechanism, addressee, specificity, scope)
- **30 categories** total across the five axes
- **Decision rules** for axis-internal boundary cases (six-question decision tree for mechanism; first-stated rule for multi-addressee blocks; named-actor-plus-operational-verb test for specificity; intervention-type test for scope)
- **Canonical borderline-entity list** for 30+ Australian government bodies that recurrently arise on the addressee axis (SafeWork SA vs the relevant department; Corrective Services vs the police force; named LHDs vs state health authorities; etc.)
- **Worked examples** for each axis demonstrating the application of the decision rules

## Version history

| Version | Date frozen | Headline change |
|---|---|---|
| v0 | 2026-05-21 | Initial nine-theme draft |
| v1.0 | 2026-05-21 | Theme expanded to 12; SPEC-3 made reachable; MECH-OTHER clarified |
| v1.1 | 2026-05-21 | Decision rules added on three axes (deadline cues, mechanism precedence, REG vs DEPT-NAMED) |
| v1.2 | 2026-05-22 | Boundary-rule revisions (MECH-INV/PROC review disambiguation, ADDR-POLICE vs DEPT-NAMED, SPEC-1/SPEC-2 two-part test) |
| v2.0 | 2026-05-22 | Structural revisions: specificity binary; mechanism fixed-order decision tree; addressee HEALTH/DEPT-NAMED block |
| v2.1 | 2026-05-22 | MECH-TRAIN collapsed into MECH-PROC; operational-endpoint tie-break for INV/PROC |
| v2.2 | 2026-05-22 | Targeted LEG ↔ PROC boundary fix (statutory-status test; "consider [regulatory action]" rule; multi-rec first-stated rule) |
| v2.3 | 2026-05-22 | Scope re-framed as intervention-type (not addressee-anchored); mechanism Q3 endpoint test; specificity clarifications |
| v2.4 | 2026-05-22 | Specificity sharpening — eliminated "consider [verb chain]" exception; tightened named-actor test |
| **v2.5** | **2026-05-22** | **Addressee revision — 30+ entity canonical list; first-stated rule strengthened; jurisdictional shorthand → DEPT-GENERIC. THIS IS THE FROZEN VERSION USED FOR ALL CORPUS-LEVEL CLASSIFICATION.** |

Earlier frozen versions are preserved in `codebook_versions/` for audit-trail transparency. The decision to include the full version history (rather than only the final v2.5) is deliberate: the trajectory itself is a methodological contribution and a transparent record of iteration.

## Held-out validation

The frozen v2.5 codebook was applied to a held-out sample (n = 50, seed 878, drawn without prior use during codebook development) by two frontier large language models (Anthropic Claude Opus 4.7 + Anthropic Claude Sonnet 4.6). Inter-rater agreement on n = 40 clean rows:

| Axis | Krippendorff's α | Verdict |
|---|---:|---|
| Scope | 1.00 | Reliable |
| Specificity | 0.84 | Reliable |
| Addressee | 0.84 | Reliable |
| Theme | 0.71 | Tentative |
| Mechanism | 0.38 | Unreliable (INV/PROC residual ambiguity) |

The mechanism axis is the load-bearing limitation of the v2.5 codebook. The MECH-INV ↔ MECH-PROC boundary has residual interpretive ambiguity that did not surface during development-sample testing. Mechanism findings should be treated as descriptive only; predictive analyses using mechanism are not supported by the held-out validation.

Full held-out IRR results are in `../irr_results/irr_heldout_v2.5.csv`. Development-sample IRR (author vs Opus 4.7 on two earlier samples) is in `../irr_results/irr_final_v2.5.csv` — reported for transparency, not as independent external validation (the author was both the human coder and the codebook architect; see the manuscript's Limitations section for the full methodological-context discussion).
