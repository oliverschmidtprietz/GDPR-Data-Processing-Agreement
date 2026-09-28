"""CONS-1 / TIER-1 : cross-field consequential-invalid-input rules.

Both rules catch a sidecar that is individually schema-valid field-by-field
but internally contradictory — the class of defect SCHEMA-1 cannot see
because no single field is malformed.
"""
from ..findings import Finding
from ..registry import rule

_CONS1_SPEC = "SKILL.md#hard-rules (Annex 2 / Art. 28(3)(c))"
_TIER1_SPEC = "SKILL.md#out-of-scope + CHANGELOG.md v1.4 (Clause 2(a)/2(b))"


@rule(
    id="CONS-1",
    severity="rejection",
    category="consistency",
    description="annex2_toms.present == false must never coexist with outcome.compliant == "
                "true — a DPA without a specified Annex 2 fails Art. 28(3)(c) (+ Art. 32) "
                "per SKILL.md's hard rules, so the instrument cannot simultaneously be "
                "reported compliant.",
    spec_anchor=_CONS1_SPEC,
)
def annex2_absence_contradicts_compliant_outcome(sidecar, ctx):
    out = []
    annex2 = sidecar.get("annex2_toms")
    outcome = sidecar.get("outcome")
    if not isinstance(annex2, dict) or not isinstance(outcome, dict):
        return out  # SCHEMA-1 already reports missing/malformed required `outcome`
    if annex2.get("present") is False and outcome.get("compliant") is True:
        out.append(Finding(
            rule_id="CONS-1", category="consistency", severity="rejection",
            message="annex2_toms.present is false but outcome.compliant is true — Annex 2 "
                    "(TOMs) absence is a stated Art. 28(3)(c) failure and cannot coexist with "
                    "a compliant outcome.",
            spec_anchor=_CONS1_SPEC,
            fix_hint="Either confirm Annex 2 is actually present (correct annex2_toms.present), "
                     "or set outcome.compliant to false / recommendation to "
                     "'do_not_sign_without_changes'.",
        ))
    return out


@rule(
    id="TIER-1",
    severity="rejection",
    category="consistency",
    description="tier == 3 requires Sections I, II AND III of the incorporated Clauses to "
                "remain intact (Clause 2(a) bars replacing any Section; v1.4 fixed a real "
                "shipped defect where the Tier 3 template dropped Section III).",
    spec_anchor=_TIER1_SPEC,
)
def tier3_requires_all_sections_intact(sidecar, ctx):
    out = []
    if sidecar.get("tier") != 3:
        return out
    transfers = sidecar.get("transfers")
    if not isinstance(transfers, dict):
        return out  # no transfers/sections_intact data to check — not this rule's concern
    sections = transfers.get("sections_intact")
    if not isinstance(sections, dict):
        return out
    dropped = [name for name in ("I", "II", "III") if sections.get(name) is False]
    for name in dropped:
        out.append(Finding(
            rule_id="TIER-1", category="consistency", severity="rejection",
            message=f"tier is 3 (Hybrid) but transfers.sections_intact.{name} is false — "
                     "Tier 3 must keep Sections I, II and III of the Clauses fully intact; "
                     "replacing a Section is not a permitted Clause 2(b) addition.",
            spec_anchor=_TIER1_SPEC, field=f"transfers.sections_intact.{name}",
            fix_hint="Restore the dropped Section and move any commercial terms into the "
                     "additive Section 4 layer instead (CHANGELOG.md v1.4).",
        ))
    return out
