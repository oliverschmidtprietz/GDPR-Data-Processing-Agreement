# dpa-art28 Validator (v1.1.0)

Deterministic Python program that validates a `dpa-art28-sidecar.json` file
against `references/dpa-art28-sidecar-schema.json` and the dpa-art28
structural rule set. Runs without Claude in the loop, mirroring the
architecture of `skills/toms-art32/validator/` (frozen `Finding` dataclass,
`@rule` decorator + `RULES` registry, a runner that iterates every
registered rule).

**A pass means the sidecar is internally consistent and complete against
these structural rules — it is NOT a check that the underlying legal
analysis is correct.** In particular, the validator trusts the `status`
value a human (or Claude) wrote into each `art28_coverage[]` entry; it
cannot see whether a `PASS` on, say, obligation `(d)` actually reflects a
sub-processor clause that grants the controller a real objection right, or
whether a `PASS` on `(h)` reflects audit rights that are more than nominal.
Per-clause substance like this is not machine-checkable from a structural
summary and this validator makes no attempt to infer it — that judgement
remains the reviewing lawyer's. `fixtures/must_pass/known-limitation-per-clause-substance-not-checked.json`
is a regression lock on this disclosed gap, not an endorsement of the
sidecar's own conclusions.

## Quick start

```bash
# Validate a sidecar (internal mode, human-readable output)
uv run skills/dpa-art28/validator/validate.py path/to/sidecar.json

# JSON findings-report-2.0 output
uv run skills/dpa-art28/validator/validate.py path/to/sidecar.json --format json

# Also emit the portfolio core-artefact projection
uv run skills/dpa-art28/validator/validate.py path/to/sidecar.json --emit-core-artefact /tmp/artefact.json

# Run the test suite
uv run --with pytest --with jsonschema python -m pytest skills/dpa-art28/validator -q
```

## Findings are the only output — rules never raise

Every rule module in `dpa_validator/rules/` takes `(sidecar, ctx)` and
**returns** a list of `Finding` objects; a data defect is reported as a
`rejection`-severity finding, never as a raised exception. `validate()`
aggregates every rule's findings into a `Result` whose `status` is
`"failed"` if any `rejection` finding is present, `"passed_with_warnings"`
if only `warning` findings are present, else `"passed"`.

## Rule IDs

| ID | Severity | Category | Checks |
|---|---|---|---|
| SCHEMA-1 | rejection | schema | Sidecar conforms to `dpa-art28-sidecar-schema.json` (Draft 2020-12) |
| CONS-1 | rejection | consistency | `annex2_toms.present == false`, OR `annex2_toms` being omitted entirely, never coexists with a positive outcome (`compliant == true` and/or `recommendation == "sign"`) — Annex 2 absence (or unconfirmed presence) is a stated Art. 28(3)(c) failure |
| ANNEX2-2 | warning | consistency | `annex2_toms.present == true` but `toms_art32_assessed == false`, with `outcome.compliant == true`, is an open handoff to `toms-art32` (not blocked) — dpa-art28 certifies the instrument's contractual sufficiency, not the TOMs' substantive appropriateness |
| TIER-1 | rejection | consistency | `tier == 3` requires `transfers.sections_intact.{I,II,III}` all true, AND the field being present at all whenever the outcome is positive — Tier 3 must keep every Section of the Clauses intact (v1.4 fixed a real shipped defect where Section III was dropped) |
| TRANSFER-1 | rejection | consistency | `transfers.in_scope == true` with no identified mechanism (`scc_module` empty/missing and no non-SCC `transfers.mechanism`) never coexists with a positive outcome, at any tier |
| COVERAGE-1 | rejection | consistency | `art28_coverage[]` having any `GAP`/`DEFECT` entry, or being missing/empty, never coexists with a positive outcome — only an all-PASS(/WEAK) coverage table ever reaches a bare `sign` (`workflows/review-quick.md` Step 7 verdict-pattern table) |
| SRC-1 | warning | freshness | Every on-disk `references/**/*.md` file is declared in `sources.lock.json`, and every declared entry's `last_verified` is within the last 12 months |
| RUNNER-0 | rejection | runner | Guard, not a data rule: `validate()` with an **empty rule registry** fails closed instead of returning a green result — import `dpa_validator.rules` (which populates the registry) before calling `validate()`; importing `dpa_validator.runner` alone does not |
| INPUT-0 | rejection | input | Not a registered rule — `validate.py`'s own fail-closed path when the sidecar file can't even be loaded (missing, unreadable, invalid UTF-8, invalid JSON, or a non-object top level). Always exactly one finding, status `"failed"`, exit 1; never a traceback. |

"Positive outcome" (CONS-1, TIER-1's omission branch, TRANSFER-1, COVERAGE-1)
means `outcome.compliant == true` and/or `outcome.recommendation == "sign"`.
`sign_with_side_letter` / `do_not_sign_without_changes` / `escalate_to_review_neg`
are deliberately NOT positive — those are exactly how an open GAP/DEFECT is
supposed to surface, per `workflows/review-quick.md`'s own verdict-pattern
table, and none of these rules are stricter than that table.

Rule modules: `schema_conformance.py` (SCHEMA-1), `consistency.py`
(CONS-1, ANNEX2-2, TIER-1, TRANSFER-1, COVERAGE-1), `sources.py` (SRC-1);
RUNNER-0 lives in `runner.py` itself; INPUT-0 lives in `validate.py` itself
(it runs before any rule, on input that never reaches the registry).

## Fixtures convention

- `fixtures/must_pass/*.json` — synthetic, schema-valid sidecars that must
  produce a `"passed"` or `"passed_with_warnings"` result. No real
  organisation, party, or personal data — every name and id is fictional.
- `fixtures/must_fail/<RULE-ID>__<short-description>.json` — a fixture that
  deliberately violates exactly the named rule.
- `fixtures/must_warn/<RULE-ID>__<short-description>.json` — a fixture that
  deliberately trips a `warning`-severity rule (currently only ANNEX2-2) and
  must produce `"passed_with_warnings"`, never `"failed"`.
- `fixtures/malformed_input/*` — deliberately non-parseable or non-object
  input (invalid JSON syntax, an empty file, a top-level array/string) used
  by `test_cli.py` to prove the CLI's file-read/parse step fails closed with
  one clean line, never a Python traceback. These are not sidecars and are
  never run through `dpa_validator.runner.validate()` directly.

## Core artefact adapter

`dpa_validator/core_artefact.py`'s `to_core_artefact()` projects a native
sidecar (plus the live validation result) into the portfolio
`skill-artefact-1.1` shape. `sources[]`/`handoffs[]`/`unknowns[]` are
data-driven, not hard-coded empty:

- `sources[]` — the `references/**/*.md` files this run's own
  `mode`/`tier`/`transfers`/`instrument.language` fields would actually have
  loaded (per SKILL.md's "Reference loading order"), resolved against
  `sources.lock.json` for citation + `last_verified`.
- `handoffs[]` — a `toms-art32` entry when `annex2_toms` is present in the
  sidecar and signals the Annex 2 substance has not been confirmed
  (`present: false` or `toms_art32_assessed: false`); silent when the
  sidecar carries no `annex2_toms` data at all.
- `unknowns[]` — a `ropa` entry when the sidecar's own optional
  `ropa_relevant` flag is `true` (dpa-art28 never assesses RoPA coverage
  itself); silent otherwise.
