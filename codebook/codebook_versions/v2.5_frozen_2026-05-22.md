# Coronial Recommendation Coding Guide — v2.5

**Status:** Working version, post v2.4 mechanical-simulation review. v2.5 is an **addressee-only revision** of v2.4. The v2.3 human pilot left addressee at α 0.686 (v2.3 sample) / 0.480 (v2.2 sample). Diagnostic on 27 addressee disagreements identified five distinct boundary patterns; v2.5 fixes the three biggest with three targeted changes.

| Axis | v2.5 change |
|---|---|
| theme | unchanged |
| mechanism | unchanged |
| **addressee** | **(A) DEPT-NAMED tightened to exclude pure jurisdictional shorthand. (B) First-stated rule strengthened with explicit worked examples. (C) Borderline-addressee canonical list added.** |
| specificity | unchanged (v2.4 fix retained) |
| scope | unchanged |

The addressee-axis changes are entirely consistent with the v2.4 SPEC-2 named-actor refinement: both axes now apply the same standard for "what counts as a specifically-named accountable entity vs jurisdictional shorthand".

---

## Axis 1 — Theme

*Unchanged from v2.3 / v2.4.* See `taxonomy/codebook_versions/v2.3_frozen_2026-05-22.md`.

---

## Axis 2 — Mechanism

*Unchanged from v2.3 / v2.4.* Q1..Q6 decision tree; statutory-status LEG vs PROC; Q3 FUND endpoint test; INV/PROC operational-endpoint; first-stated rule for multi-rec.

---

## Axis 3 — Addressee (revised in v2.5)

*Who is being directed to act?* **Nine categories (unchanged).** Three rule revisions in v2.5.

| Code | Label | Definition |
|---|---|---|
| ADDR-DEPT-NAMED | Named government department, ministry, or agency | **A specifically-named department, ministry, agency, ministerial office, or named body within a government**, including state regulatory authorities that sit inside a department, and including state health authorities. **Pure jurisdictional shorthand fails.** |
| ADDR-DEPT-GENERIC | Government (generic or jurisdictional) | "The government", "the State", "the Crown", **"the ACT Government"**, **"the Commonwealth Government"**, **"the NSW Government"**, "the Territory" — any reference at the level of jurisdiction without identifying a specific department/agency/office. |
| ADDR-HEALTH | Health service / LHD / hospital | A specific operational health body BELOW the state level: named LHD, named hospital, named area health service, named ambulance service, named community health centre. |
| ADDR-REG | Independent regulator | A standalone statutory regulator whose head reports to a board or parliament, NOT to a department secretary. |
| ADDR-PROF | Professional body / college | A named professional body or college (RACGP, ANMF, AMA, Law Society). |
| ADDR-POLICE | Police / corrections | A police force, corrections agency, or operational executor (NSW Police, AFP, Corrective Services NSW, Corrections Victoria). |
| ADDR-COURT | Coroner's court / judiciary | The coroner's court itself or other courts. |
| ADDR-PRIVATE | Private body | Named company, NGO, school, charity. |
| ADDR-UNSPEC | Unspecified | No clear addressee. |

### v2.5 change (A) — DEPT-NAMED tightened to exclude jurisdictional shorthand

The v2.3 codebook said ADDR-DEPT-NAMED includes "any named state or federal department, ministry, or agency". This was ambiguous on jurisdictional shorthand. v2.5 sharpens:

**DEPT-NAMED requires a specifically-named department, ministry, ministerial office, agency, or body WITHIN a government** — not the level of government itself.

| Addressee text | v2.3 | **v2.5** | Why |
|---|---|---|---|
| "the ACT Government" | DEPT-NAMED (ambiguous) | **DEPT-GENERIC** | Jurisdictional shorthand without specific department |
| "the Commonwealth Government" | DEPT-NAMED (ambiguous) | **DEPT-GENERIC** | Jurisdictional |
| "the NSW Government" | DEPT-NAMED (ambiguous) | **DEPT-GENERIC** | Jurisdictional |
| "the Territory" / "the State" | DEPT-GENERIC | DEPT-GENERIC | Unchanged |
| "the ACT Department of Health" | DEPT-NAMED | **DEPT-NAMED** | Named department within ACT Government |
| "the Commonwealth Department of Health and Aged Care" | DEPT-NAMED | **DEPT-NAMED** | Named federal department |
| "the Minister for Health" | DEPT-NAMED | **DEPT-NAMED** | Named ministerial office |
| "the NSW Ministry of Health" | DEPT-NAMED | **DEPT-NAMED** | Named ministry |
| "the Department of Justice and Community Safety" | DEPT-NAMED | **DEPT-NAMED** | Named department |
| "VicRoads" | DEPT-NAMED | **DEPT-NAMED** | Named agency |

**This rule is identical in form to the v2.4 SPEC-2 named-actor sharpening.** A rec that addresses "the ACT Government" gets coded ADDR-DEPT-GENERIC for addressee and SPEC-1 for specificity (both fail their respective named-entity tests). A rec that addresses "the ACT Department of Health" gets ADDR-DEPT-NAMED and (if the verb is operational) SPEC-2.

### v2.5 change (B) — First-stated rule strengthened with worked examples

The v2.3 codebook had a multi-rec first-stated rule. v2.5 makes it unmissable for multi-addressee blocks with explicit worked examples.

**Rule (unchanged):** when a rec block contains multiple recommendations directed at different addressees, code the addressee of the **first-stated recommendation** and set `ambiguous_addressee=TRUE`.

**Worked examples (new in v2.5):**

| Multi-addressee block | First-stated addressee | Coded as | Ambiguous flag |
|---|---|---|---|
| "I recommend to the Minister for Health, the Royal Australasian College of Surgeons, and the Neurosurgical Society of Australasia that they consider X" | "the Minister for Health" | **ADDR-DEPT-NAMED** | TRUE (subsequent addressees are PROF) |
| "I recommend that the Minister for Health, the department of cardiology at Westmead Hospital, in consultation with the NSW Ministry of Health and the Cardiac Society of Australia and New Zealand, consider Y" | "the Minister for Health" | **ADDR-DEPT-NAMED** | TRUE (subsequent: HEALTH, DEPT-NAMED, PROF) |
| "I recommend that the Commissioner of NSW Police Force and the Department of Communities and Justice review Z" | "the Commissioner of NSW Police Force" | **ADDR-POLICE** | TRUE (subsequent: DEPT-NAMED) |
| "I recommend that Royal Darwin Hospital implement Y and that NT Health amend its protocols" | "Royal Darwin Hospital" | **ADDR-HEALTH** | TRUE (subsequent: DEPT-NAMED) |
| "directed to the Minister for Recreation, Sport and Racing. 12.7.1 That SafeWork SA conduct an audit..." | "the Minister for Recreation, Sport and Racing" | **ADDR-DEPT-NAMED** | TRUE (subsequent: DEPT-NAMED) |

**Identification rule for "first-stated"**: the addressee is identified by the **first explicit "I recommend to [X]"** statement, the first "[X] should/must/will [verb]" statement, or the first letter of the rec block's address line (e.g., "directed to..."). If multiple addressees are stated in a single sentence with conjunctions ("To Y and Z..."), code by the first one mentioned.

### v2.5 change (C) — Borderline-addressee canonical list

The v2.3 codebook had brief examples for REG vs DEPT-NAMED (AHPRA → REG; SafeWork NSW → DEPT-NAMED). v2.5 adds an explicit canonical list for borderline cases:

| Addressee | Code | Why |
|---|---|---|
| AHPRA | ADDR-REG | Independent statutory regulator (board-reporting) |
| TGA | ADDR-REG | Independent statutory regulator |
| ASIC | ADDR-REG | Independent statutory regulator |
| ACMA | ADDR-REG | Independent statutory regulator |
| Australian Health Care Safety and Quality Commission | ADDR-REG | Independent commission |
| Coroners Court (when itself the addressee) | ADDR-COURT | Court |
| SafeWork SA / SafeWork NSW / WorkSafe Victoria | ADDR-DEPT-NAMED | Executive-internal regulator |
| EPA NSW / EPA Victoria | ADDR-DEPT-NAMED | Executive-internal regulator |
| Australian Border Force | ADDR-DEPT-NAMED | Executive-internal agency |
| Office of the Public Advocate | ADDR-DEPT-NAMED | Executive-internal office |
| Office of the Public Guardian and Trustee | ADDR-DEPT-NAMED | Executive-internal office |
| Mental Health Review Board / Mental Health Tribunal | ADDR-REG | Independent statutory tribunal/board |
| Child Death Review Committee / Child Death and Serious Injury Review Committee | ADDR-DEPT-NAMED | Executive-internal review committee |
| Corrections Victoria | ADDR-POLICE | Corrections agency (per v2.3 rule) |
| Corrective Services NSW | ADDR-POLICE | Corrections agency |
| NSW Police / AFP / VIC Police / QLD Police | ADDR-POLICE | Police force |
| Commissioner of [Police Force] | ADDR-POLICE | Operational executor |
| Minister for Police | ADDR-DEPT-NAMED | Political direction (not operational) |
| Department of Communities and Justice | ADDR-DEPT-NAMED | Department overseeing police |
| Department of Justice | ADDR-DEPT-NAMED | Department |
| Local council (e.g., City of Palmerston Council) | ADDR-DEPT-NAMED | Local government body |
| Local Government Association (e.g., WA Local Government Association) | ADDR-DEPT-NAMED | Peak intergovernmental body |
| Real Estate Institute of WA (REIWA) | ADDR-PROF | Industry/professional body |
| RACGP / ANMF / AMA / Law Society | ADDR-PROF | Professional body / college |
| Australian College of Rural and Remote Medicine | ADDR-PROF | College |
| Royal Australasian College of Surgeons (RACS) | ADDR-PROF | College |
| Neurosurgical Society of Australasia | ADDR-PROF | Professional society |
| Cardiac Society of Australia and New Zealand | ADDR-PROF | Professional society |
| RACGP | ADDR-PROF | College |
| Maritime Safety Victoria | ADDR-DEPT-NAMED | Executive agency |
| Department of State Growth (Tas) | ADDR-DEPT-NAMED | State department |
| NSW Health / Queensland Health / WA Health / SA Health / ACT Health | ADDR-DEPT-NAMED | **State health authority — DEPT-NAMED, not HEALTH** |
| Sydney LHD / Hunter New England LHD / [any named LHD] | ADDR-HEALTH | Sub-state operational LHD |
| Royal Prince Alfred Hospital / [any named hospital] | ADDR-HEALTH | Named hospital |
| Ambulance Tasmania / NSW Ambulance | ADDR-HEALTH | Operational delivery body |

**REG vs DEPT-NAMED rule (carried forward):** REG = independent statutory regulator whose head reports to a board or parliament; DEPT-NAMED = department/agency inside the executive even if it has regulatory functions. The boundary test: "can you name the minister responsible?" → almost certainly DEPT-NAMED.

**HEALTH vs DEPT-NAMED rule (carried forward):** state-level health authorities ("NSW Health", "ACT Health", "Department of Health and Aged Care") are DEPT-NAMED. Sub-state operational bodies (LHDs, named hospitals, ambulance services) are HEALTH. Boundary test: "could a Minister for Health direct this entity?" → DEPT-NAMED.

**POLICE vs DEPT-NAMED rule (carried forward):** the operational police/corrections entity itself is POLICE. The political department overseeing them is DEPT-NAMED. Boundary: "operational executor" → POLICE; "direction-only" → DEPT-NAMED.

---

## Axis 4 — Specificity

*Unchanged from v2.4.* "Consider [verb chain]" exception eliminated; named-actor test for SPEC-2 sharpened to exclude jurisdictional shorthand. The Axis 3 / Axis 4 named-actor tests are now consistent under v2.5.

---

## Axis 5 — Scope

*Unchanged from v2.3 / v2.4.* Intervention-type framing.

---

## Flags, Reading IRR, Multi-rec rule, Appendix

*Unchanged from v2.3 / v2.4.* See those frozen codebooks for the full content.

---

## Versioning

| Version | Date | Change | Driver |
|---|---|---|---|
| v0 — v2.4 | 2026-05-21 / 22 | See v2.4 codebook for v0..v2.4 history. |
| v2.5 | 2026-05-22 | **Addressee-only revision.** (A) DEPT-NAMED tightened to require specifically-named department/agency/office within a government — pure jurisdictional shorthand ("the ACT Government", "the Commonwealth Government", "the NSW Government") falls to DEPT-GENERIC. (B) First-stated rule strengthened with five worked examples for multi-addressee blocks. (C) Borderline-addressee canonical list of 30+ entities added (SafeWork SA → DEPT-NAMED; Corrections Victoria → POLICE; Mental Health Review Board → REG; etc.). The DEPT-NAMED tightening (change A) makes the addressee axis consistent with the v2.4 SPEC-2 named-actor refinement — both apply the same standard. No theme, mechanism, specificity, or scope changes. | v2.3 human pilot (Hayden vs Opus): addressee α 0.686 (v2.3 sample) / 0.480 (v2.2 sample). 27 addressee disagreements across both samples concentrated on five boundary patterns: DEPT-NAMED ↔ DEPT-GENERIC ×5 (jurisdictional shorthand ambiguity — fixed by change A), DEPT-NAMED ↔ {PROF, HEALTH} ×8 (multi-rec first-stated misapplication — fixed by change B), DEPT-NAMED ↔ {REG, POLICE} ×8 (borderline-addressee knowledge gaps — fixed by change C), with a few residual singletons. |

**Success criterion for v2.5 addressee revision:** human-vs-Opus addressee α ≥ 0.80 on at least one sample (the v2.3 sample, which was Tentative in v2.3 codebook) and ≥ 0.70 on the other (v2.2 sample, which was Unreliable). If achieved → v2.5 is the canonical pilot-validated codebook. If addressee α stays below those thresholds, the residual disagreement is likely on rows with multiple distinct addressees where the first-stated rule alone is insufficient.
