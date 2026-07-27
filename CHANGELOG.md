# Changelog — dpa-art28

All notable changes to this skill are documented here.

Format: `## [vX.Y] — YYYY-MM-DD`

---

## [v1.2] — 2026-07-25

Routes Article 32 security-of-processing work to the `toms-art32` skill. Part of the coordinated **sibling-routing pass** (`ropa` v2.15, `dpia-sentinel` v1.11, `dpa-art28` v1.2, `breach-sentinel` v3.3, `tia` v1.3) that closes the toms-art32 portfolio-integration gate recorded as Finding 1 in `docs/projects/gdpr-skills-marathon/ROADMAP-2026-07-25.md`. Routing pointers only — no Article 32 methodology is duplicated into any sibling.

- **Out of scope, rewritten.** The former "use Art. 32-specific guidance" pointer now names `toms-art32` and states the ownership boundary: this skill owns the *instrument* (does the agreement bind the processor to specified measures, is the annex contractually sufficient, what must the counterparty warrant); `toms-art32` owns the *substance* (Art. 32(1) appropriateness, control catalogue, measure ownership and implementation status, evidence, effectiveness testing) and generates the export-eligible annex text — bespoke DPA TOM annex, Decision 2021/915 Art. 28 SCC Annex III, Decision 2021/914 transfer-SCC Annex II.
  This also retires the dangling reference to a "standalone TOMs scaffold" that never existed as a generator — the confusion `toms-art32` records in its `templates.md` §0 is now fixed from this side too.
- **Hard rule (Annex 2).** Producing the TOM content is `toms-art32`'s job; bring its output back into the instrument rather than drafting substance here.
- **REVIEW_NEG annex review.** Contractual sufficiency is judged here; whether measures are appropriate to the risk and actually in force is flagged and routed, not assessed in the redline. Never warrant measures this skill has not seen assessed.

**Status:** reviewed (carried from v1.1) — routing/documentation only; no change to the mode router, Art. 28(3)/Art. 26 review logic, templates or workflows.

---

## [v1.1] — 2026-06-11

Additive audience-clarity + delegation-posture guidance from the LegalQuants QA review (PR #6). No change to the mode router, Art. 28(3) review logic, templates, or risk scoring.

- **"Who this is for" section.** Names the intended operator (privacy/commercial lawyer, or a trained paralegal under attorney supervision) and assumed AI-fluency, so the skill's conservative calibration is intentional rather than inferred.
- **Work shape stated explicitly.** Names the work as bounded-transactional, pattern-matched review against a fixed Art. 28 / Art. 26 benchmark — making the conservative-vs-autonomous posture auditable.
- **Privilege / work-product note.** One line clarifying the output is drafting and review support, not legal advice and not in itself a privileged work product; storage per the firm's work-product policy.

**Status:** reviewed (carried from v1.0) — additive documentation, no behavioral change.

---

## [v1.0] — 2026-05-14

First **reviewed** release. Eval pass via `/skill-creator` confirmed skill value against no-skill baseline.

- 8 realistic test cases run with-skill vs no-skill baseline (72 assertions total)
- Result: 72/72 (100%) with skill vs 67/72 (93%) without — **+7 pp differential**
- Diagnostic finding: skill's edge is structural reproducibility rather than substantive knowledge. With-skill consistently produces (1) explicit mode router classification (REVIEW_QUICK / REVIEW_NEG / DRAFT / REDLINE / JOINT_CONTROLLER), (2) Art. 28(3)(a)–(h) coverage table with PASS/WEAK/GAP/DEFECT labels, (3) per-leaf risk tier classification, (4) Practitioner's note synthesis, (5) JCA template instantiation. Baseline addresses defects correctly but doesn't apply the structured envelope
- Baseline matches on doctrinal content for DRAFT, REDLINE, Chapter V analysis, German public-sector advisory — the skill earns its keep on consistency and structural discipline
- See `../../dpa-art28-workspace/iteration-1/` for full eval artifacts

## [v0.9] — 2026-05-08

Initial import from CLAUDE_SKILLS_GDPR/dpa-art28/ (worked on 2026-05-05). Status: **pre-review** pending eval.

- Data Processing Agreement skill under Art. 28 GDPR (controller-processor) and Art. 26 GDPR (joint controller arrangements)
- Bilingual support: German (AVV) and English
- Both controller-side and processor-side perspectives
- Two review depths: quick (Art. 28(3)(a)–(h) coverage) and negotiation-grade (clause-by-clause risk scoring)
- 8 templates: commercial DE/EN, hybrid DE/EN, strict DE/EN, JCA DE/EN
- 5 workflows: draft, joint-controller, redline, review-negotiation, review-quick
- Reference files include Commission text 2021/915 (DE/EN), Art. 28(3) checklist, common defects, negotiation fallbacks, SCCs module guide, tier selection
- Import excluded the dpa-art28.tar.gz self-snapshot
