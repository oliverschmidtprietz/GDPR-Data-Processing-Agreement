# Changelog — dpa-art28

All notable changes to this skill are documented here.

Format: `## [vX.Y] — YYYY-MM-DD`

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
