# Changelog — dpa-art28

All notable changes to this skill are documented here.

Format: `## [vX.Y] — YYYY-MM-DD`

---

## [v1.5] — 2026-09-24

Level 1 (structural-tier) adoption of the portfolio standard
(`docs/standards/PORTFOLIO-STANDARD.md`), per
`docs/projects/gdpr-skills-marathon/SIX-SKILL-ADOPTION-BRIEF-2026-09-24.md`.
No change to the mode router, Art. 28(3)/Art. 26 review logic, templates, or
workflows.

- **Native sidecar defined.** `references/dpa-art28-sidecar-schema.json` — a
  minimal structural record of one run: instrument identity, router mode,
  Art. 28(3)(a)–(h) coverage checklist, Annex 2 (TOMs) presence, transfer
  tier + Clause-section integrity, and the outcome recommendation.
- **Structural validator added.** `validator/validate.py` (PEP 723 launcher)
  plus `validator/dpa_validator/` — a findings-based, never-raising rule
  runner (`toms_validator`-shaped: frozen `Finding`, `@rule` registry,
  fail-closed empty-registry guard `RUNNER-0`) implementing `SCHEMA-1`
  (schema conformance), `CONS-1` (an `annex2_toms.present == false` /
  `outcome.compliant == true` contradiction — Annex 2 absence is a stated
  Art. 28(3)(c) failure per this skill's own hard rules), `TIER-1` (`tier ==
  3` requires Sections I, II **and** III of the Clauses intact — the exact
  class of defect v1.4 fixed in prose, now a machine rule), and `SRC-1`
  (`sources.lock.json` coverage/freshness over `references/**/*.md`). 40
  pytest cases, `must_pass`/`must_fail` fixtures.
- **`--emit-core-artefact` adapter.** Projects the native sidecar plus the
  live validation result into the portfolio `skill-artefact-1.1` shape.
  `sources[]`/`handoffs[]`/`unknowns[]` are driven by the sidecar's own
  fields for the run, not hard-coded empty: `sources[]` from which
  `references/**/*.md` files this run's mode/tier/transfers actually load,
  resolved against `sources.lock.json`; `handoffs[]` names `toms-art32` when
  Annex 2 substance hasn't been confirmed; `unknowns[]` names `ropa` when
  the optional `ropa_relevant` flag is true.
- **`sources.lock.json` added**, covering all 8 `references/**/*.md` files.
  `last_verified` is this skill's own most recent documented verification
  per `CHANGELOG.md`: 2026-09-15 (this file's own v1.4 EUR-Lex re-check) for
  the 2021/915 text, `tier-selection.md` and `sccs-module-guide.md`; the
  2026-05-08 v0.9 import date, marked `confidence: medium`, for
  `art28-3-checklist.md`, `common-defects.md`, `negotiation-fallbacks.md`
  and `art26-joint-controller.md` — none of which `CHANGELOG.md` records a
  later substantive touch to.
- **`conformance.json` declared** — `tier: structural`, `standard_version:
  1.4`. Verified via `scripts/check_conformance.py`: `CONFORMANT dpa-art28`.
- **SKILL.md** gains a short "Machine-readable output" section pointing at
  the validator invocation.

**Status:** reviewed — additive machine-readable layer; no behavioral
change to the human-facing review/draft/redline/JCA workflows.

---

## [v1.4] — 2026-09-15

Legal-drafting correction to the Tier 3 (Hybrid) template architecture, prompted by finding 6 of the external adversarial review (`docs/projects/gdpr-skills-marathon/ADVERSARIAL-REVIEW-2026-09-08.md`) against the EUR-Lex text of Commission Implementing Decision (EU) 2021/915.

- **Hybrid tier restructured — Section III is never replaced.** The prior architecture (`templates/dpa-hybrid-{en,de}.md`) deleted Section III of the Clauses (Clause 10 — non-compliance and termination) and substituted negotiated term/termination/liability provisions, describing this as "permitted under Clause 2(b)". That was wrong: Clause 2(a) bars modifying the Clauses (all of them, not just Sections I–II) except to complete or update the Annexes; Clause 2(b) permits only *adding* clauses or safeguards that do not contradict the Clauses. Replacing a Clause is not an addition. The templates are rebuilt to keep Sections I, II **and** III of the Clauses fully intact (same incorporation as Tier 2), with all commercial terms (term, commercial termination rights, transition assistance, liability allocation, indemnification, insurance) moved into a new Section 4 "Commercial framework terms (outside the Clauses)" that Clause 2(b) does permit. Section 4 carries an explicit non-contradiction guard clause (4.1): commercial termination rights are in addition to, and never replace, Clause 10; liability caps never limit the Processor's obligations under the Clauses or the Parties' Article 82 liability to data subjects; nothing in Section 4 modifies, amends, or narrows Sections I, II or III. A "Presumption of compliance" note is added: because the Clauses are now unmodified in full, Tier 3 carries the same full Art. 28(7) presumption as Tier 2 — the two tiers differ only in how extensive the additive Section 4 layer is, not in presumption strength.
- **Clause 2(a)/2(b) labels corrected.** `references/sccs-module-guide.md` had the two halves of Clause 2 backwards (attributing the "adding clauses/additional safeguards" permission to 2(a) instead of 2(b), and conflating it with the unrelated Clause 5 docking mechanism). Corrected.
- **Reference and workflow files reconciled to the new architecture**: `references/2021-915-commission-text-{en,de}.md` (Section III clause-map entries + load-order notes), `references/tier-selection.md` (tier comparison table, decision tree Q3, defaults, "what changes between tiers" table, common-misuses list — Tier 3's compliance presumption is now stated as full, not partial), `SKILL.md` (tier description in intake item 4), `workflows/draft.md` (tier table, template selection table, tier-aware quality gates), `templates/dpa-strict-{en,de}.md` and `templates/jca-en.md` (cross-references to Tier 3 updated to the new description). No eval assertion encoded the old claim, so `evals/evals.json` required no change.
- **Special-category free-text intake question added.** `SKILL.md`'s "Intake — ALWAYS gather" block gains item 9: for Annex I / the categories-of-data description, ask what free-text or unstructured inputs the processing includes, whether any real control (not just a policy) catches special-category content in them, and whether such content has actually been observed — with the rule that unfiltered data-subject/staff-facing free-text channels should be described as potentially containing special-category data.

**Status:** reviewed — legal-drafting correction (hybrid-tier architecture) + intake addition; no change to the mode router or REVIEW/REDLINE review logic.

---

## [v1.3] — 2026-08-21

Portfolio audit fix (source: `AUDIT-2026-08-19.md`). Reference-doc correction only — no change to the mode router, Art. 28(3)/Art. 26 review logic, templates, or workflows.

- **CF-21.** `references/sccs-module-guide.md`'s special-status table had hedged the UK adequacy renewal as still pending, framing a settled fact as an open question. The original UK adequacy decisions sunset in June 2025; the European Commission renewed them by Implementing Decision under Art. 45(3) GDPR adopted 19 December 2025, valid until 27 December 2031. The row now states the sunset, the renewal date, and the 27 December 2031 expiry, with a "monitor before expiry" note replacing the old hedged language.

**Status:** reviewed — documentation-only correction; no behavioral change.

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
