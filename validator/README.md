# dpa-art28 Validator (v1.0.0)

Deterministic Python program that validates a `dpa-art28-sidecar.json` file
against `references/dpa-art28-sidecar-schema.json` and the dpa-art28
structural rule set. Runs without Claude in the loop, mirroring the
architecture of `skills/toms-art32/validator/` (frozen `Finding` dataclass,
`@rule` decorator + `RULES` registry, a runner that iterates every
registered rule).

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
| CONS-1 | rejection | consistency | `annex2_toms.present == false` never coexists with `outcome.compliant == true` — Annex 2 absence is a stated Art. 28(3)(c) failure |
| TIER-1 | rejection | consistency | `tier == 3` requires `transfers.sections_intact.{I,II,III}` all true — Tier 3 must keep every Section of the Clauses intact (v1.4 fixed a real shipped defect where Section III was dropped) |
| SRC-1 | warning | freshness | Every on-disk `references/**/*.md` file is declared in `sources.lock.json`, and every declared entry's `last_verified` is within the last 12 months |
| RUNNER-0 | rejection | runner | Guard, not a data rule: `validate()` with an **empty rule registry** fails closed instead of returning a green result — import `dpa_validator.rules` (which populates the registry) before calling `validate()`; importing `dpa_validator.runner` alone does not |

Rule modules: `schema_conformance.py` (SCHEMA-1), `consistency.py`
(CONS-1, TIER-1), `sources.py` (SRC-1); RUNNER-0 lives in `runner.py` itself.

## Fixtures convention

- `fixtures/must_pass/*.json` — synthetic, schema-valid sidecars that must
  produce a `"passed"` or `"passed_with_warnings"` result. No real
  organisation, party, or personal data — every name and id is fictional.
- `fixtures/must_fail/<RULE-ID>__<short-description>.json` — a fixture that
  deliberately violates exactly the named rule.

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
