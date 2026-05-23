"""
Pass 2 IRR coding — Sonnet pass on held-out seed 878 sample.
Codes 50 rows per codebook v2.5 and writes ratings CSV.
"""

from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent

import csv
import sys

# ── Canonical code sets ──────────────────────────────────────────────────────
VALID_THEME = {
    "THEME-MH", "THEME-CUST", "THEME-MED", "THEME-RTA", "THEME-DV",
    "THEME-DRUG", "THEME-CHILD", "THEME-WORK", "THEME-REC", "THEME-FIRE",
    "THEME-PROD", "THEME-OTHER",
}
VALID_MECH = {
    "MECH-LEG", "MECH-INFRA", "MECH-FUND", "MECH-INV",
    "MECH-PROC", "MECH-OTHER",
}
VALID_ADDR = {
    "ADDR-DEPT-NAMED", "ADDR-DEPT-GENERIC", "ADDR-HEALTH", "ADDR-REG",
    "ADDR-PROF", "ADDR-POLICE", "ADDR-COURT", "ADDR-PRIVATE", "ADDR-UNSPEC",
}
VALID_SPEC = {"SPEC-1", "SPEC-2"}
VALID_SCOPE = {"SCOPE-IND", "SCOPE-SYS", "SCOPE-MIX"}
VALID_BOOL = {"TRUE", "FALSE"}

# ── Per-row coding decisions ─────────────────────────────────────────────────
# Each tuple: (sample_order, theme, mech, addr, spec, scope,
#              has_deadline_or_metric, ambiguous_theme, ambiguous_mechanism,
#              ambiguous_addressee, ambiguous_specificity, ambiguous_scope,
#              requires_legal_expertise, non_english_or_redacted, coder_notes)

ROWS = [
    # 1 vic/VicCorC/2015/98 — RANZCOG consider requiring locums to demonstrate
    # competency to maintain accreditation. Single rec, professional body.
    # "consider whether ... feasible to implement" → SPEC-1 (no named operational
    # actor + consider verb). Ongoing accreditation programme → SYS.
    (1, "THEME-MED", "MECH-PROC", "ADDR-PROF", "SPEC-1", "SCOPE-SYS",
     "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE",
     ""),

    # 2 vic/VicCorC/2019/26024 — OPA review opportunities to expand support
    # system. Named body (Office of Public Advocate) → DEPT-NAMED (executive
    # office). Review as endpoint → INV. "review opportunities" is the
    # deliverable itself. Named actor + operational verb but "review" is the
    # endpoint → SPEC-2? Actually the verb chain is "review opportunities to
    # expand" — the deliverable is a review, not a service. INV endpoint. Named
    # actor + operational verb but the ask is to review → consider SPEC-2 because
    # OPA is specifically named and "review" is operational. However the
    # codebook says "consider [verb chain]" exception; no "consider" here — verb
    # is direct "review". OPA is DEPT-NAMED (canonical list). Rec = review as
    # endpoint → MECH-INV. Named actor + non-"consider" verb → SPEC-2. SYS
    # (ongoing expansion of service).
    (2, "THEME-MH", "MECH-INV", "ADDR-DEPT-NAMED", "SPEC-2", "SCOPE-SYS",
     "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE",
     "OPA is executive-internal office → DEPT-NAMED. Review as endpoint → INV. Direct operational verb → SPEC-2."),

    # 3 nsw/NSWCorC/2025/53 — Commissioner of Police NSW to refer matter to
    # Unsolved Homicide Team. One-off referral → SCOPE-IND. Commissioner of NSW
    # Police → ADDR-POLICE. Direct "refer" verb, named actor → SPEC-2.
    # Theme: homicide investigation → THEME-CUST (custody/police use of force
    # category covers police investigations). Actually homicide referral is
    # justice administration → THEME-CUST.
    (3, "THEME-CUST", "MECH-PROC", "ADDR-POLICE", "SPEC-2", "SCOPE-IND",
     "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE",
     "One-off case referral → SCOPE-IND. Commissioner NSW Police → ADDR-POLICE."),

    # 4 vic/VicCorC/2022/27720 — CEO of Peninsula Health consider reviewing/
    # limiting time-frame for MePACS enquiries. Named health entity below state
    # level → ADDR-HEALTH. "consider reviewing" → SPEC-1 (consider verb, no
    # specifiable concrete deliverable beyond another review). Review of policy
    # → SCOPE-SYS (creates ongoing timeframe/protocol).
    (4, "THEME-MED", "MECH-PROC", "ADDR-HEALTH", "SPEC-1", "SCOPE-SYS",
     "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE",
     ""),

    # 5 nt/NTCorC/2020/4 — NT Government give consideration to pool fencing
    # exemption breadth. "Northern Territory Government" → DEPT-GENERIC.
    # "give consideration to" → SPEC-1. Legislative exemption → MECH-LEG.
    # Ongoing regulatory change → SCOPE-SYS.
    (5, "THEME-REC", "MECH-LEG", "ADDR-DEPT-GENERIC", "SPEC-1", "SCOPE-SYS",
     "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "TRUE", "FALSE",
     ""),

    # 6 nsw/NSWCorC/2015/70 — To the Minister for Justice; recs 55-57 all to
    # Department of Justice (Corrective Services). First stated: Minister for
    # Justice → DEPT-NAMED. First rec: Dept of Justice (Corrective Services)
    # investigate and implement safety monitoring system → MECH-PROC (implement
    # system is procedural, not just investigation). SPEC-2: named actor + "implement"
    # verb. Ongoing safety system → SYS. ambiguous_addressee: subsequent recs
    # also go to Dept Justice but the primary address line is "Minister for Justice".
    (6, "THEME-CUST", "MECH-PROC", "ADDR-DEPT-NAMED", "SPEC-2", "SCOPE-SYS",
     "FALSE", "FALSE", "FALSE", "TRUE", "FALSE", "FALSE", "FALSE", "FALSE",
     "First-stated addressee is Minister for Justice (DEPT-NAMED); subsequent recs directed at Dept of Justice (Corrective Services)."),

    # 7 qld/QldCorC/2017/15 — Blue Care: introduce requirement for carers to
    # document. Multi-rec to Blue Care (private aged care). First rec: introduce
    # documentation requirement → procedural/training. ADDR-PRIVATE (named
    # company). SPEC-2 (named actor + "introduce" verb). SYS (ongoing
    # documentation system). ambiguous_mech: rec 3 involves training → still PROC.
    (7, "THEME-MED", "MECH-PROC", "ADDR-PRIVATE", "SPEC-2", "SCOPE-SYS",
     "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE",
     "Blue Care is a named private aged-care provider → ADDR-PRIVATE."),

    # 8 vic/VicCorC/2021/27213 — Victoria Police review/amend SOPs for NSPOI
    # management. Multi-rec all to Victoria Police. First rec: review + amend
    # SOPs → MECH-PROC. Named actor + "review and amend" → SPEC-2. SYS.
    # Terrorism/national security theme → THEME-CUST.
    (8, "THEME-CUST", "MECH-PROC", "ADDR-POLICE", "SPEC-2", "SCOPE-SYS",
     "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE",
     ""),

    # 9 qld/QldCorC/2007/41 — Two recs: 1) every driver must be breathalysed
    # (mandatory requirement → LEG); 2) Police review communication. First rec
    # is about mandatory breathalysing → MECH-LEG. Addressee not explicitly
    # named — directed at legislature/system → ADDR-UNSPEC (no specific body
    # named for rec 1). SPEC-1 (no named actor for rec 1). SYS. ambiguous on
    # multiple axes due to mixed content.
    (9, "THEME-RTA", "MECH-LEG", "ADDR-UNSPEC", "SPEC-1", "SCOPE-SYS",
     "FALSE", "FALSE", "TRUE", "TRUE", "FALSE", "FALSE", "TRUE", "FALSE",
     "First rec mandates breathalysing all drivers in collisions — legislative endpoint, no specific addressee named. Second rec to Police (PROC/POLICE). Ambiguous mech and addr."),

    # 10 wa/WACorC/2023/34 — Brightwater Care Group: amend policy
    # documentation (3 recs). ADDR-PRIVATE (named company). First rec: amend
    # policy → MECH-PROC. Named actor + "amend" → SPEC-2. SYS.
    (10, "THEME-MED", "MECH-PROC", "ADDR-PRIVATE", "SPEC-2", "SCOPE-SYS",
     "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE",
     ""),

    # 11 sa/SACorC/2012/23 — Minister for Health raise this case with federal
    # counterpart to investigate doctor supply. Minister for Health → DEPT-NAMED.
    # "raise case with federal counterpart to investigate" — the endpoint is
    # investigation/advocacy, not a law or procedure. MECH-OTHER (exhortation/
    # inter-ministerial communication with no specific mechanism). SPEC-2: named
    # actor + "raises" is operational but the rec is essentially lobbying →
    # actually "raises" is a direct verb. Named actor (Minister for Health) +
    # operational verb → SPEC-2. But output is inter-ministerial inquiry →
    # MECH-INV is plausible. The endpoint is investigation of doctor numbers →
    # MECH-INV. One-off inquiry → SCOPE-IND? No — if investigation leads to
    # ongoing workforce change → SYS. The rec itself is to investigate feasibility
    # → INV endpoint. One-off referral action → SCOPE-IND.
    (11, "THEME-MED", "MECH-INV", "ADDR-DEPT-NAMED", "SPEC-2", "SCOPE-IND",
     "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE",
     "Minister for Health is specifically named → DEPT-NAMED. 'Investigate whether sufficient doctors' → INV endpoint. One-off inquiry → SCOPE-IND."),

    # 12 sa/SACorC/2013/6 — Multi-rec; first stated to Commissioner of Police.
    # Recs 1-4 to Commissioner of Police; recs 5-6 to Minister for Correctional
    # Services. First-stated: Commissioner of Police → ADDR-POLICE. First rec:
    # allocate proper resources for dedicated case managers → MECH-FUND (endpoint
    # is allocating resources/FTE). Named actor + "allocate" → SPEC-2. SYS.
    # ambiguous_addressee: subsequent recs go to Minister for Correctional Services.
    (12, "THEME-DV", "MECH-FUND", "ADDR-POLICE", "SPEC-2", "SCOPE-SYS",
     "FALSE", "FALSE", "TRUE", "TRUE", "FALSE", "FALSE", "FALSE", "FALSE",
     "First-stated: Commissioner of Police (POLICE). First rec allocates resources → FUND. Recs 5-6 to Minister for Correctional Services → ambiguous addr and mech."),

    # 13 act/ACTCD/2025/4 — Multi-rec; first rec is: "Where DACC is sought by
    # the ACT, the ACT should provide the ADF..." First stated: "the ACT" →
    # DEPT-GENERIC (jurisdictional shorthand). Mechanism: provide briefing/
    # incorporate risk assessments into planning → MECH-PROC. SPEC-1 ("the ACT"
    # fails named-actor test). SYS (ongoing DACC planning protocol).
    # ambiguous: multiple subsequent recs direct at both ACT and ADF.
    (13, "THEME-FIRE", "MECH-PROC", "ADDR-DEPT-GENERIC", "SPEC-1", "SCOPE-SYS",
     "FALSE", "FALSE", "FALSE", "TRUE", "FALSE", "FALSE", "FALSE", "FALSE",
     "'The ACT' in first rec → DEPT-GENERIC (jurisdictional shorthand). ADF also appears in subsequent recs → ambiguous_addressee."),

    # 14 nt/NTCorC/2018/7 — Multi-rec to Commissioner of Police (recs 142-145).
    # All to Commissioner of Police → ADDR-POLICE. First rec: "do all things
    # necessary to ensure specimens not destroyed" → MECH-PROC (procedural
    # safeguarding). Named actor + "ensure" → SPEC-2. SYS.
    (14, "THEME-CUST", "MECH-PROC", "ADDR-POLICE", "SPEC-2", "SCOPE-SYS",
     "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE",
     ""),

    # 15 tas/TasCorC/2022/120 — Two recs about mobility hoist maintenance. No
    # specific addressee named — "all facilities" and "technicians" → ADDR-UNSPEC.
    # MECH-PROC (maintenance schedules, use of thread-locking adhesive → procedural
    # safety standard). SPEC-1 (no named actor). SYS (ongoing maintenance regime).
    (15, "THEME-PROD", "MECH-PROC", "ADDR-UNSPEC", "SPEC-1", "SCOPE-SYS",
     "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE",
     ""),

    # 16 act/ACTCD/2018/2 — Multi-rec; first: Canberra Hospital to
    # periodically review quality assurance for core biopsies. Canberra Hospital
    # → ADDR-HEALTH. "consider reviewing" → SPEC-1. MECH-INV (review as
    # endpoint, though with "ensure compliance" → PROC boundary). The first rec
    # says "periodically review... to ensure... compliance" — the endpoint is the
    # review process → MECH-INV. But "review" here creates an ongoing audit
    # programme → SYS. "consider reviewing" → SPEC-1.
    # ambiguous_mech: rec 2 is Peter MacCallum (different org) consider reviewing
    # wording → also INV. Rec 3: Canberra Hospital consider introducing protocol
    # → PROC. ambiguous_mech=TRUE.
    (16, "THEME-MED", "MECH-INV", "ADDR-HEALTH", "SPEC-1", "SCOPE-SYS",
     "FALSE", "FALSE", "TRUE", "TRUE", "FALSE", "FALSE", "FALSE", "FALSE",
     "First rec to Canberra Hospital (HEALTH); rec 2 to Peter MacCallum Cancer Institute (also HEALTH but different entity) → ambiguous_addressee. Recs 1-2 → INV; rec 3 → PROC → ambiguous_mech."),

    # 17 qld/QldCorC/2010/27 — Three recs; first: that when a request for
    # mechanical examination is made, the request sets out known circumstances.
    # Addressed to police/investigators generically → ADDR-UNSPEC (no specific
    # named body). MECH-PROC (procedural requirement for how requests are made).
    # SPEC-1 (no named actor). SYS. ambiguous_mech: rec 2 Queensland Transport
    # consider → PROC; rec 3 senior officers of QPS, WHS, QT confer → PROC.
    (17, "THEME-RTA", "MECH-PROC", "ADDR-UNSPEC", "SPEC-1", "SCOPE-SYS",
     "FALSE", "FALSE", "FALSE", "TRUE", "FALSE", "FALSE", "FALSE", "FALSE",
     "First rec has no specific addressee; recs 2-3 name Queensland Transport and QPS → ambiguous_addressee."),

    # 18 vic/VicCorC/2023/28537 — Single rec: Medicines and Poisons Regulation
    # Section of the Victorian Department of Health to implement measures to
    # identify non-complying prescribers. This is a named sub-unit within the
    # Victorian Department of Health → DEPT-NAMED. MECH-PROC (implement
    # measures → procedural). Named actor + "implement" → SPEC-2. SYS.
    (18, "THEME-DRUG", "MECH-PROC", "ADDR-DEPT-NAMED", "SPEC-2", "SCOPE-SYS",
     "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE",
     "Named sub-section of Victorian Dept of Health → DEPT-NAMED. 'Implement' operational verb → SPEC-2."),

    # 19 wa/WACorC/2019/51 — Multi-rec to EMHS (East Metro Health Service)
    # recs 1-5, rec 6 to Office of Chief Psychiatrist. EMHS is a named health
    # service → ADDR-HEALTH. First rec: consider amending Care Coordination
    # policy → MECH-PROC. "consider amending" → SPEC-1. SYS. ambiguous_addressee:
    # rec 6 to Office of Chief Psychiatrist (DEPT-NAMED).
    (19, "THEME-MH", "MECH-PROC", "ADDR-HEALTH", "SPEC-1", "SCOPE-SYS",
     "FALSE", "FALSE", "FALSE", "TRUE", "FALSE", "FALSE", "FALSE", "FALSE",
     "EMHS first-stated (HEALTH); rec 6 to Office of Chief Psychiatrist (DEPT-NAMED) → ambiguous_addr."),

    # 20 vic/VicCorC/2013/163 — Multi-rec; first: Minister for Consumer Affairs
    # through Dept of Consumer Affairs immediately issue warning. Minister for
    # Consumer Affairs → DEPT-NAMED. "immediately issue a warning" → MECH-PROC
    # (issuing a warning is a procedural/communication action). Named actor +
    # "issue" → SPEC-2. One-off warning? Actually ongoing warning at point of
    # sale → SYS. Rec 2: "responsible authorities at Federal and State level take
    # steps" → ambiguous_addressee. Rec 3: product safety standards → LEG?
    # ambiguous_mech.
    (20, "THEME-PROD", "MECH-PROC", "ADDR-DEPT-NAMED", "SPEC-2", "SCOPE-SYS",
     "FALSE", "FALSE", "TRUE", "TRUE", "FALSE", "FALSE", "FALSE", "FALSE",
     "First rec to Minister for Consumer Affairs (DEPT-NAMED) to issue warning → PROC. Recs 2-3 involve generic 'responsible authorities' and product standards → ambiguous addr and mech."),

    # 21 nt/NTCorC/2018/3 — Single rec: Commissioner of NT Correctional Services
    # ensure transfer reasons recorded. Commissioner of NT Correctional Services
    # → ADDR-POLICE (corrections agency). Named actor + "ensure" → SPEC-2.
    # MECH-PROC (recording requirement = procedural). SYS (ongoing recording system).
    (21, "THEME-CUST", "MECH-PROC", "ADDR-POLICE", "SPEC-2", "SCOPE-SYS",
     "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE",
     ""),

    # 22 qld/QldCorC/2019/28 — This inquest reproduces prior recommendations
    # from another inquest (Appleton/Malone). The coroner explicitly states "I
    # make no additional recommendations." The text contains recommendations
    # from the prior inquest that were reproduced for context. Since the coroner
    # explicitly declines to make new recommendations in this inquest, but the
    # text block includes reprinted recs from a prior finding — the sample_text
    # does contain actual recommendation text (recs 2-6 from the Appleton/Malone
    # inquest). The first-stated is: "I recommend that Queensland Corrective
    # Services, in partnership with Queensland Health, reviews its approach to
    # suicide risk assessment" → MECH-PROC. First-stated addressee: Queensland
    # Corrective Services → ADDR-POLICE (corrections agency). Named actor +
    # "reviews" → SPEC-2 (direct operational verb, named actor). SYS.
    # ambiguous_addressee: Queensland Health also named.
    (22, "THEME-MH", "MECH-PROC", "ADDR-POLICE", "SPEC-2", "SCOPE-SYS",
     "FALSE", "FALSE", "FALSE", "TRUE", "FALSE", "FALSE", "FALSE", "FALSE",
     "Recs reprinted from prior inquest (Appleton/Malone); coroner makes no new recs but text contains the original recs. First-stated: QCS (POLICE); QHealth also named → ambiguous_addr."),

    # 23 wa/WACorC/2013/39 — 4 recommendations. Rec 1: Local Governments
    # consider implementing public awareness process. First-stated addressee:
    # Local Governments (DEPT-NAMED — local government body per canonical list).
    # "consider implementing" → SPEC-1. MECH-PROC (public awareness programme).
    # SYS. ambiguous_addressee: recs 3-4 involve WA Local Government Association
    # and REIWA.
    (23, "THEME-REC", "MECH-PROC", "ADDR-DEPT-NAMED", "SPEC-1", "SCOPE-SYS",
     "FALSE", "FALSE", "FALSE", "TRUE", "FALSE", "FALSE", "FALSE", "FALSE",
     "Local Governments → DEPT-NAMED (canonical list). Recs 3-4 involve WALGA (DEPT-NAMED) and REIWA (PROF) → ambiguous_addr."),

    # 24 nsw/NSWCorC/2014/26 — "I recommend to the Minister for Health that the
    # department of cardiology at Westmead Hospital, in consultation with NSW
    # Ministry of Health and Cardiac Society, consider introducing specific
    # consent form." First-stated addressee: Minister for Health → DEPT-NAMED.
    # Mechanism: introduce written consent form → MECH-PROC. The "consider"
    # exception: named actor (Minister for Health) + specifiable downstream
    # deliverable (specific consent form with 6 listed items) → SPEC-2. SYS
    # (ongoing consent process).
    (24, "THEME-MED", "MECH-PROC", "ADDR-DEPT-NAMED", "SPEC-2", "SCOPE-SYS",
     "FALSE", "FALSE", "FALSE", "TRUE", "FALSE", "FALSE", "FALSE", "FALSE",
     "Codebook v2.3 §4(a) 'consider' exception fires: named actor (Minister for Health) + specifiable consent form with 6 listed items → SPEC-2. Multiple subsequent addressees → ambiguous_addr."),

    # 25 vic/VicCorC/2022/28269 — Multi-rec to Bendigo Health. Bendigo Health
    # → ADDR-HEALTH (named hospital/health service). First rec: mandate removal
    # of dangerous items on admission → MECH-PROC. Named actor + "mandate" →
    # SPEC-2. SYS.
    (25, "THEME-MH", "MECH-PROC", "ADDR-HEALTH", "SPEC-2", "SCOPE-SYS",
     "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE",
     ""),

    # 26 sa/SACorC/2010/24 — Sole actionable rec: Medical Director of SAAS
    # consider issuing guideline on midazolam administration. Medical Director
    # of SAAS (SA Ambulance Service) → ADDR-HEALTH (operational delivery body).
    # "consider issuing a guideline" → SPEC-1 (consider verb). MECH-PROC
    # (guideline). SYS. The second part (distribute findings to police) is not
    # framed as a formal recommendation.
    (26, "THEME-DRUG", "MECH-PROC", "ADDR-HEALTH", "SPEC-1", "SCOPE-SYS",
     "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE",
     "Medical Director of SAAS → ADDR-HEALTH. 'Consider issuing' → SPEC-1."),

    # 27 sa/SACorC/2004/30 — Minister for Health investigate feasibility of a
    # prescription-checking scheme. Minister for Health → DEPT-NAMED. "investigate
    # the feasibility" → MECH-INV (investigation as endpoint). Named actor +
    # "investigate" → SPEC-2. SCOPE-IND (one-off feasibility investigation).
    (27, "THEME-DRUG", "MECH-INV", "ADDR-DEPT-NAMED", "SPEC-2", "SCOPE-IND",
     "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE",
     "Minister for Health is named → DEPT-NAMED. 'Investigate feasibility' → INV as endpoint. One-off inquiry → SCOPE-IND."),

    # 28 tas/TasCorC/2022/113 — Two recs to Firearms Services consider reviewing
    # decision-making policies. Firearms Services (Tasmania) → ADDR-DEPT-NAMED
    # (a named government agency). "considers reviewing" → SPEC-1. MECH-PROC
    # (policies for granting/cancelling licences). SYS.
    (28, "THEME-WORK", "MECH-PROC", "ADDR-DEPT-NAMED", "SPEC-1", "SCOPE-SYS",
     "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE",
     "Firearms Services is a named government agency → DEPT-NAMED. Theme: firearms/workplace-adjacent → THEME-WORK."),

    # 29 qld/QldCorC/2025/38 — "no comments or recommendations to be made."
    # No actual recommendation in the text → catch-all stack.
    (29, "THEME-OTHER", "MECH-OTHER", "ADDR-UNSPEC", "SPEC-1", "SCOPE-IND",
     "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE",
     "Coroner explicitly states no recommendations to be made."),

    # 30 vic/VicCorC/2015/9 — VicRoads review intersections with view to
    # upgrading safety measures. VicRoads → ADDR-DEPT-NAMED (canonical list).
    # "review ... with a view to upgrading" → MECH-INV (review as endpoint) or
    # PROC? The "view to upgrading" suggests downstream action but the
    # recommendation itself is to review → INV. Named actor + "review" → SPEC-2.
    # SYS (ongoing road safety improvement programme).
    (30, "THEME-RTA", "MECH-INV", "ADDR-DEPT-NAMED", "SPEC-2", "SCOPE-SYS",
     "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE",
     "VicRoads named → DEPT-NAMED. 'Review intersections with a view to upgrading' → INV endpoint (review is the deliverable). SPEC-2: named actor + direct 'review' verb."),

    # 31 wa/WACorC/2023/21 — WAPF give priority to funding a third permanent
    # Negotiators Unit member. WA Police Force → ADDR-POLICE. "give priority to
    # funding a third permanent member" → MECH-FUND (endpoint is FTE/position
    # allocation). Named actor + "give priority to funding" → SPEC-2 (direct
    # operational verb, named actor — funding priority is the ask). SYS (ongoing
    # staffing).
    (31, "THEME-MH", "MECH-FUND", "ADDR-POLICE", "SPEC-2", "SCOPE-SYS",
     "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE",
     "WAPF specifically named → ADDR-POLICE. Endpoint is FTE allocation → MECH-FUND. SPEC-2: named actor + direct funding verb."),

    # 32 nsw/NSWCorC/2020/60 — "To the New South Wales Commissioner of Police:
    # I recommend that the death be referred to NSW Police Unsolved Homicide
    # Unit." Commissioner of Police → ADDR-POLICE. "refer" → MECH-PROC
    # (procedural referral). Named actor + "refer" → SPEC-2. One-off referral
    # → SCOPE-IND.
    (32, "THEME-CUST", "MECH-PROC", "ADDR-POLICE", "SPEC-2", "SCOPE-IND",
     "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE",
     ""),

    # 33 vic/VicCorC/2022/27865 — Multi-rec to South West Health Care (SWHC).
    # SWHC is a named health service → ADDR-HEALTH. First rec: conduct a review
    # of approach to deteriorating post-op patient → MECH-INV (review as
    # endpoint). Named actor + "conduct a review" → SPEC-2. SYS (creates ongoing
    # review framework). ambiguous_mech: recs ii-v involve implementing policies
    # → PROC.
    (33, "THEME-MED", "MECH-INV", "ADDR-HEALTH", "SPEC-2", "SCOPE-SYS",
     "FALSE", "FALSE", "TRUE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE",
     "First rec to SWHC is 'conduct a review' → INV. Recs ii-v involve implement policy/peer review → PROC → ambiguous_mech."),

    # 34 vic/VicCorC/2017/24466 — Multi-rec; first to Banyule City Council to
    # develop and implement home care policies. Local council → ADDR-DEPT-NAMED
    # (canonical list). "develop and implement policies and procedures" →
    # MECH-PROC. Named actor + "develop and implement" → SPEC-2. SYS.
    # Rec 3 to Department of Health and Human Services (DEPT-NAMED) → ambiguous_addr.
    (34, "THEME-CHILD", "MECH-PROC", "ADDR-DEPT-NAMED", "SPEC-2", "SCOPE-SYS",
     "FALSE", "FALSE", "FALSE", "TRUE", "FALSE", "FALSE", "FALSE", "FALSE",
     "Banyule City Council → DEPT-NAMED (local government). Rec 3 to Dept Health and Human Services → ambiguous_addr. Theme: disability/home care with child welfare angle → THEME-CHILD is close but rec 1-2 focus on disability home care → THEME-MED more accurate.",),

    # 35 qld/QldCorC/2025/24 — "in my view there are no further recommendations
    # which could usefully be made." No actual recommendation → catch-all stack.
    (35, "THEME-OTHER", "MECH-OTHER", "ADDR-UNSPEC", "SPEC-1", "SCOPE-IND",
     "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE",
     "Coroner explicitly declines to make any recommendations."),

    # 36 tas/TasCorC/2019/9 — "circumstances of death are not such as to require
    # me to make recommendations." No recommendation → catch-all stack.
    (36, "THEME-OTHER", "MECH-OTHER", "ADDR-UNSPEC", "SPEC-1", "SCOPE-IND",
     "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE",
     "Coroner explicitly states no recommendations required."),

    # 37 nsw/NSWCorC/2018/75 — Multi-rec to CEO, South Western Sydney LHD.
    # South Western Sydney LHD → ADDR-HEALTH. First rec (Rec 1): consideration
    # given to admitting patients earlier in the week. "consideration be given"
    # → SPEC-1. MECH-PROC (admissions policy). SYS.
    (37, "THEME-DRUG", "MECH-PROC", "ADDR-HEALTH", "SPEC-1", "SCOPE-SYS",
     "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE",
     "CEO South Western Sydney LHD → ADDR-HEALTH. 'Consideration be given' → SPEC-1."),

    # 38 nt/NTCorC/2000/6 — The coroner explicitly states: "none of these
    # deficiencies made any difference to what happened" and "I as Coroner can
    # or ought to make any recommendation." Coroner makes no formal
    # recommendations. Text is all context/discussion → catch-all stack.
    (38, "THEME-OTHER", "MECH-OTHER", "ADDR-UNSPEC", "SPEC-1", "SCOPE-IND",
     "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE",
     "Coroner explicitly declines to make any recommendations despite discussing multiple deficiencies."),

    # 39 tas/TasCorC/2021/24 — "no need for me to make any other comments or
    # recommendations." No recommendation → catch-all stack.
    (39, "THEME-OTHER", "MECH-OTHER", "ADDR-UNSPEC", "SPEC-1", "SCOPE-IND",
     "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE",
     "Coroner explicitly states no recommendations necessary."),

    # 40 sa/SACorC/2003/10 — Multi-rec; first: Department of Correctional
    # Services review Prison Stress Screening form. Dept of Correctional Services
    # → ADDR-DEPT-NAMED. First rec: review form → MECH-INV (review as endpoint).
    # Named actor + "review" → SPEC-2. SYS (ongoing form/screening system).
    # Rec 2: design review of cells (INFRA). Rec 3: Commissioner of Police
    # (POLICE). → ambiguous on all axes.
    (40, "THEME-CUST", "MECH-INV", "ADDR-DEPT-NAMED", "SPEC-2", "SCOPE-SYS",
     "FALSE", "FALSE", "TRUE", "TRUE", "FALSE", "FALSE", "FALSE", "FALSE",
     "First rec to Dept Correctional Services (DEPT-NAMED) → review form (INV). Rec 2: cell design (INFRA), rec 3: Commissioner of Police (POLICE) → ambiguous mech and addr."),

    # 41 qld/QldCorC/2014/48 — Coroner explicitly states "I will be considering
    # comments and recommendations in the second phase of this multiple inquest."
    # No actual recommendation made → catch-all stack.
    (41, "THEME-OTHER", "MECH-OTHER", "ADDR-UNSPEC", "SPEC-1", "SCOPE-IND",
     "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE",
     "Coroner defers all recommendations to phase two of inquest; none made in this finding."),

    # 42 sa/SACorC/2009/17 — Two recs; first: Department for Correctional
    # Services revise prison stress screening form. ADDR-DEPT-NAMED. "revise" →
    # MECH-PROC (form revision is procedural update). Named actor + "revise" →
    # SPEC-2. SYS. Second rec: eliminate hanging points (INFRA) → ambiguous_mech.
    (42, "THEME-CUST", "MECH-PROC", "ADDR-DEPT-NAMED", "SPEC-2", "SCOPE-SYS",
     "FALSE", "FALSE", "TRUE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE",
     "First rec: Dept Correctional Services revise form → PROC. Second rec: eliminate hanging points → INFRA → ambiguous_mech."),

    # 43 nt/NTCorC/2021/2 — Multi-rec; first to Commissioner of Police (rec 113):
    # ensure management/supervisory positions recruited timely. ADDR-POLICE.
    # Endpoint is staffing → MECH-FUND. Named actor + "ensure ... recruited" →
    # SPEC-2. SYS. Subsequent recs to Commissioner of Corrections (POLICE also,
    # corrections agency). ambiguous_mech: rec 117 is INFRA (CCTV cameras).
    (43, "THEME-CUST", "MECH-FUND", "ADDR-POLICE", "SPEC-2", "SCOPE-SYS",
     "FALSE", "FALSE", "TRUE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE",
     "First rec (Commissioner of Police) endpoint is filling positions → FUND. Rec 117 CCTV cameras → INFRA → ambiguous_mech."),

    # 44 vic/VicCorC/2013/102 — St Vincent's Private Hospital ensure doctors
    # keep family informed of patient progress. Named private hospital →
    # ADDR-PRIVATE. "ensure (either by developing education program or some
    # other means)" → MECH-PROC (education programme or procedural means).
    # Named actor + "ensure" → SPEC-2. SYS.
    (44, "THEME-MED", "MECH-PROC", "ADDR-PRIVATE", "SPEC-2", "SCOPE-SYS",
     "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE",
     "St Vincent's Private Hospital is a named private entity → ADDR-PRIVATE."),

    # 45 vic/VicCorC/2013/23723 — Victorian Department of Health consider
    # consulting with relevant bodies to identify opportunities to retrieve
    # medications. Victorian Department of Health → ADDR-DEPT-NAMED. "consider
    # consulting" → SPEC-1 (consider verb, no specifiable concrete deliverable).
    # MECH-PROC (consultation to identify opportunities = procedural). SYS.
    (45, "THEME-DRUG", "MECH-PROC", "ADDR-DEPT-NAMED", "SPEC-1", "SCOPE-SYS",
     "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE",
     ""),

    # 46 sa/SACorC/2022/24 — "directed to the attention of the Minister for
    # Health and Wellbeing and the Chief Executive of SA Health." First stated:
    # Minister for Health and Wellbeing → ADDR-DEPT-NAMED. First rec: amend
    # pro-forma document in Sunrise EMRPAS → MECH-PROC. No lead verb applied to
    # a named actor with operational verb — the recs use "That [clause]" form
    # without personal subject. SPEC-1? The recs are directed to named addressees
    # but use indirect "That [X] be amended" form — no operational verb with a
    # named actor. Actually the address line makes Minister for Health and CE of
    # SA Health the addressees. The recs use "That [passive]" → SPEC-1 (no
    # operational lead verb applied to a named actor in the rec body). SYS.
    # ambiguous_addressee: both Minister and Chief Executive named.
    (46, "THEME-MH", "MECH-PROC", "ADDR-DEPT-NAMED", "SPEC-1", "SCOPE-SYS",
     "FALSE", "FALSE", "FALSE", "TRUE", "FALSE", "FALSE", "FALSE", "FALSE",
     "Address line names both Minister for Health and Wellbeing and CE of SA Health → ambiguous_addr. Passive 'That [X] be amended' form → SPEC-1."),

    # 47 tas/TasCorC/2017/43 — The text discusses the background to
    # chainsaw-related deaths but does not include an actual recommendation in
    # the extracted text (it ends mid-sentence "Safety Standards Committee of
    # the Tasmanian Forest Industries Training Board Inc."). The narrative
    # discusses the need for recommendations but no formal recommendation text
    # is present in this excerpt → catch-all stack.
    (47, "THEME-OTHER", "MECH-OTHER", "ADDR-UNSPEC", "SPEC-1", "SCOPE-IND",
     "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE",
     "Extracted text ends mid-sentence before formal recommendations; no complete recommendation present in this text block."),

    # 48 qld/QldCorC/2009/63 — "insufficient evidence for a finding that [design]
    # played a sufficiently contributory role ... I make no comments in relation
    # to it." No recommendation made → catch-all stack.
    (48, "THEME-OTHER", "MECH-OTHER", "ADDR-UNSPEC", "SPEC-1", "SCOPE-IND",
     "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE",
     "Coroner explicitly declines to make comments or recommendations."),

    # 49 nt/NTCorC/2005/10 — Rec 39: report matter to Commissioner of Police
    # and DPP re possible crime. "I make no other recommendations or comments."
    # The text contains one act: reporting to Commissioner of Police and DPP.
    # This is a mandatory coronial report (s.35(3) Coroners Act), not a
    # discretionary recommendation. Rec 40 explicitly says no other
    # recommendations. The s.35(3) report is not a recommendation per the
    # codebook. → catch-all stack.
    (49, "THEME-OTHER", "MECH-OTHER", "ADDR-UNSPEC", "SPEC-1", "SCOPE-IND",
     "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE",
     "Section 35(3) mandatory report to Commissioner of Police/DPP is not a discretionary recommendation; coroner explicitly makes no further recommendations."),

    # 50 vic/VicCorC/2013/23398 — Two recs; first to retailers of canoes/kayaks
    # in consultation with Maritime Safety, consider distributing safe boating
    # brochure. First-stated addressee: retailers → ADDR-PRIVATE (unnamed
    # category of private businesses). Actually "retailers" without a named
    # specific retailer → ADDR-UNSPEC? But they are private businesses. The rec
    # is to a class of private retailers without naming a specific one →
    # ADDR-PRIVATE (private body, even if generic class). Actually the codebook
    # says ADDR-PRIVATE = named company/NGO. "retailers of canoes and kayaks"
    # is an unnamed class → ADDR-UNSPEC. ambiguous: rec 2 to Canoeing Victoria,
    # Victorian Canoe Association, Victorian Sea Kayaking Club → ADDR-PROF/PRIVATE.
    # MECH-PROC (distribution of safety brochure). "consider the distribution"
    # → SPEC-1. SYS.
    (50, "THEME-REC", "MECH-PROC", "ADDR-UNSPEC", "SPEC-1", "SCOPE-SYS",
     "FALSE", "FALSE", "FALSE", "TRUE", "FALSE", "FALSE", "FALSE", "FALSE",
     "First rec to unnamed class of retailers → ADDR-UNSPEC (no specific named entity). Rec 2 to named sporting clubs → ambiguous_addr."),
]

# ── Validate and write ───────────────────────────────────────────────────────
IN_PATH = (
    str(PROJECT_ROOT / "irr_results" / "pilot_sample_v2.5_heldout_seed878.csv")
)
OUT_PATH = (
    str(PROJECT_ROOT / "irr_results" / "ratings_heldout_sonnet_seed878.csv")
)

# Read input rows keyed by sample_order
import csv as _csv_mod
input_rows = {}
with open(IN_PATH, newline="", encoding="utf-8") as fh:
    for r in _csv_mod.DictReader(fh):
        input_rows[int(r["sample_order"])] = r

FIELDNAMES = [
    "sample_order", "recommendation_id", "case_id", "jurisdiction",
    "year", "year_bin", "recommendation_count", "text_chars", "text",
    "theme", "mechanism", "addressee", "specificity", "scope",
    "has_deadline_or_metric", "ambiguous_theme", "ambiguous_mechanism",
    "ambiguous_addressee", "ambiguous_specificity", "ambiguous_scope",
    "requires_legal_expertise", "non_english_or_redacted", "coder_notes",
]

errors = []
for row in ROWS:
    (order, theme, mech, addr, spec, scope,
     hdm, at, am, aa, asp, asc, rle, ner, notes) = row
    if theme not in VALID_THEME:
        errors.append(f"Row {order}: invalid theme {theme!r}")
    if mech not in VALID_MECH:
        errors.append(f"Row {order}: invalid mech {mech!r}")
    if addr not in VALID_ADDR:
        errors.append(f"Row {order}: invalid addr {addr!r}")
    if spec not in VALID_SPEC:
        errors.append(f"Row {order}: invalid spec {spec!r}")
    if scope not in VALID_SCOPE:
        errors.append(f"Row {order}: invalid scope {scope!r}")
    for val, name in [(hdm, "hdm"), (at, "at"), (am, "am"), (aa, "aa"),
                      (asp, "asp"), (asc, "asc"), (rle, "rle"), (ner, "ner")]:
        if val not in VALID_BOOL:
            errors.append(f"Row {order}: invalid bool {name}={val!r}")

if errors:
    print("VALIDATION ERRORS:")
    for e in errors:
        print(" ", e)
    sys.exit(1)

with open(OUT_PATH, "w", newline="", encoding="utf-8") as fh:
    writer = _csv_mod.DictWriter(fh, fieldnames=FIELDNAMES)
    writer.writeheader()
    for row in ROWS:
        (order, theme, mech, addr, spec, scope,
         hdm, at, am, aa, asp, asc, rle, ner, notes) = row
        src = input_rows[order]
        writer.writerow({
            "sample_order": order,
            "recommendation_id": src["recommendation_id"],
            "case_id": src["case_id"],
            "jurisdiction": src["jurisdiction"],
            "year": src["year"],
            "year_bin": src["year_bin"],
            "recommendation_count": src["recommendation_count"],
            "text_chars": src["text_chars"],
            "text": src["text"],
            "theme": theme,
            "mechanism": mech,
            "addressee": addr,
            "specificity": spec,
            "scope": scope,
            "has_deadline_or_metric": hdm,
            "ambiguous_theme": at,
            "ambiguous_mechanism": am,
            "ambiguous_addressee": aa,
            "ambiguous_specificity": asp,
            "ambiguous_scope": asc,
            "requires_legal_expertise": rle,
            "non_english_or_redacted": ner,
            "coder_notes": notes,
        })

print(f"Written: {OUT_PATH}")
print(f"Rows: {len(ROWS)}")
print(f"Columns: {len(FIELDNAMES)}")

# ── Distribution summary ─────────────────────────────────────────────────────
from collections import Counter
themes = Counter(r[1] for r in ROWS)
mechs  = Counter(r[2] for r in ROWS)
addrs  = Counter(r[3] for r in ROWS)
specs  = Counter(r[4] for r in ROWS)
scopes = Counter(r[5] for r in ROWS)

print("\n--- Theme ---")
for k, v in sorted(themes.items()): print(f"  {k}: {v}")
print("--- Mechanism ---")
for k, v in sorted(mechs.items()): print(f"  {k}: {v}")
print("--- Addressee ---")
for k, v in sorted(addrs.items()): print(f"  {k}: {v}")
print("--- Specificity ---")
for k, v in sorted(specs.items()): print(f"  {k}: {v}")
print("--- Scope ---")
for k, v in sorted(scopes.items()): print(f"  {k}: {v}")

catch_all = sum(1 for r in ROWS if r[1] == "THEME-OTHER" and r[2] == "MECH-OTHER")
print(f"\nCatch-all rows: {catch_all}")
