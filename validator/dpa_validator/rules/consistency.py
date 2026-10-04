"""CONS-1 / ANNEX2-2 / TIER-1 / TRANSFER-1 / COVERAGE-1 : cross-field
consequential-invalid-input rules.

Every rule here catches a sidecar that is individually schema-valid
field-by-field but internally contradictory — the class of defect SCHEMA-1
cannot see because no single field is malformed.

Shared "omission bypass" pattern (break-it fix 2026-10-02): a rule that only
checks an explicit false/bad value on a field is blind to the same sidecar
simply OMITTING that field while still making a positive claim
(`outcome.compliant: true` and/or `outcome.recommendation: "sign"`). Per the
fix brief's hard rule, a missing load-bearing field is treated as a failure
of that positive claim, not as "nothing to check" — CONS-1 and TIER-1 below
both gained this second branch; TRANSFER-1 and COVERAGE-1 are new rules
built on the same positive-claim test from the start.
"""
from ..findings import Finding
from ..registry import rule

_CONS1_SPEC = "SKILL.md#hard-rules (Annex 2 / Art. 28(3)(c))"
_ANNEX2_2_SPEC = "SKILL.md#out-of-scope (Annex 2 substance routed to toms-art32)"
_TIER1_SPEC = "SKILL.md#out-of-scope + CHANGELOG.md v1.4 (Clause 2(a)/2(b))"
_TRANSFER1_SPEC = "SKILL.md#hard-rules (international-transfer language binding only if " \
                  "SCCs/a mechanism are actually identified)"
_COVERAGE1_SPEC = "workflows/review-quick.md#step-7-recommendation (verdict-pattern table)"

# A non-SCC transfers.mechanism value that, on its own, is treated as an identified
# mechanism for TRANSFER-1 — kept out of the schema's `scc_module` field because it is
# not an SCC module choice (schema v1.0 gained this field as an additive, optional
# escape hatch; see dpa-art28-sidecar-schema.json).
_NON_SCC_MECHANISMS = {"dpf", "adequacy_decision", "bcr", "art49_derogation"}


def _outcome_is_positive(sidecar) -> bool:
    """True when the sidecar's outcome makes a positive claim — compliant == true
    and/or recommendation == "sign" (the only bare-sign row in review-quick.md's
    verdict-pattern table). sign_with_side_letter / do_not_sign_without_changes /
    escalate_to_review_neg are deliberately NOT positive: those recommendations are
    exactly how a GAP/DEFECT or an open item is supposed to surface."""
    outcome = sidecar.get("outcome")
    if not isinstance(outcome, dict):
        return False
    return outcome.get("compliant") is True or outcome.get("recommendation") == "sign"


@rule(
    id="CONS-1",
    severity="rejection",
    category="consistency",
    description="annex2_toms.present == false, OR annex2_toms being omitted entirely, must "
                "never coexist with a positive outcome (compliant == true and/or "
                "recommendation == 'sign') — a DPA without a confirmed Annex 2 fails Art. "
                "28(3)(c) (+ Art. 32) per SKILL.md's hard rules, and an omitted annex2_toms "
                "cannot support a positive claim either (omission-bypass fix, "
                "break-it 2026-10-02).",
    spec_anchor=_CONS1_SPEC,
)
def annex2_absence_contradicts_compliant_outcome(sidecar, ctx):
    out = []
    if not _outcome_is_positive(sidecar):
        return out  # no positive claim to contradict
    annex2 = sidecar.get("annex2_toms")
    if not isinstance(annex2, dict):
        out.append(Finding(
            rule_id="CONS-1", category="consistency", severity="rejection",
            message="annex2_toms is missing from the sidecar but outcome.compliant is true "
                    "and/or recommendation is 'sign' — Annex 2 (TOMs) presence cannot be "
                    "confirmed, so a positive outcome claim is unsupported (Art. 28(3)(c) + "
                    "Art. 32).",
            spec_anchor=_CONS1_SPEC, field="annex2_toms",
            fix_hint="Record annex2_toms.present (and toms_art32_assessed) for this run, or "
                     "do not report compliant/sign without it.",
        ))
        return out
    if annex2.get("present") is False:
        out.append(Finding(
            rule_id="CONS-1", category="consistency", severity="rejection",
            message="annex2_toms.present is false but outcome.compliant is true and/or "
                    "recommendation is 'sign' — Annex 2 (TOMs) absence is a stated Art. "
                    "28(3)(c) failure and cannot coexist with a positive outcome.",
            spec_anchor=_CONS1_SPEC, field="annex2_toms.present",
            fix_hint="Either confirm Annex 2 is actually present (correct annex2_toms.present), "
                     "or set outcome.compliant to false / recommendation to "
                     "'do_not_sign_without_changes'.",
        ))
    return out


@rule(
    id="ANNEX2-2",
    severity="warning",
    category="consistency",
    description="annex2_toms.present == true but toms_art32_assessed == false, together with "
                "outcome.compliant == true, is NOT a CONS-1-grade contradiction: dpa-art28 "
                "certifies the INSTRUMENT's contractual sufficiency (the annex is specified), "
                "never the Annex 2 substance's Art. 32(1) appropriateness — that is "
                "toms-art32's job (SKILL.md 'Out of scope'). Flagged as a warning/open handoff "
                "so 'compliant' is not mistaken for substantively-assessed TOMs.",
    spec_anchor=_ANNEX2_2_SPEC,
)
def unassessed_toms_substance_with_compliant_outcome_is_an_open_handoff(sidecar, ctx):
    out = []
    annex2 = sidecar.get("annex2_toms")
    outcome = sidecar.get("outcome")
    if not isinstance(annex2, dict) or not isinstance(outcome, dict):
        return out
    if annex2.get("present") is True and annex2.get("toms_art32_assessed") is False \
            and outcome.get("compliant") is True:
        out.append(Finding(
            rule_id="ANNEX2-2", category="consistency", severity="warning", priority="medium",
            message="annex2_toms.present is true but toms_art32_assessed is false, while "
                    "outcome.compliant is true — the instrument is contractually sufficient on "
                    "Annex 2, but its substance has not been confirmed by a toms-art32 run. "
                    "'compliant' here reflects the instrument only; route the substance to "
                    "toms-art32 before relying on the TOMs as appropriate under Art. 32(1).",
            spec_anchor=_ANNEX2_2_SPEC, field="annex2_toms.toms_art32_assessed",
            fix_hint="Run toms-art32 on the Annex 2 substance, or note this as an open item in "
                     "the practitioner's note rather than treating 'compliant' as final.",
        ))
    return out


@rule(
    id="TIER-1",
    severity="rejection",
    category="consistency",
    description="tier == 3 requires Sections I, II AND III of the incorporated Clauses to "
                "remain intact (Clause 2(a) bars replacing any Section; v1.4 fixed a real "
                "shipped defect where the Tier 3 template dropped Section III). "
                "transfers.sections_intact being omitted entirely at tier 3, together with a "
                "positive outcome, is the same omission-bypass hole CONS-1 had "
                "(break-it 2026-10-02): Section integrity cannot be confirmed from no data.",
    spec_anchor=_TIER1_SPEC,
)
def tier3_requires_all_sections_intact(sidecar, ctx):
    out = []
    if sidecar.get("tier") != 3:
        return out
    transfers = sidecar.get("transfers")
    sections = transfers.get("sections_intact") if isinstance(transfers, dict) else None
    if not isinstance(sections, dict):
        if _outcome_is_positive(sidecar):
            out.append(Finding(
                rule_id="TIER-1", category="consistency", severity="rejection",
                message="tier is 3 (Hybrid) but transfers.sections_intact is missing — Section "
                        "I/II/III integrity cannot be confirmed, so a positive outcome "
                        "(compliant == true and/or recommendation == 'sign') is unsupported.",
                spec_anchor=_TIER1_SPEC, field="transfers.sections_intact",
                fix_hint="Record transfers.sections_intact.{I,II,III} for this run before "
                         "reporting compliant/sign, or recommend escalation instead.",
            ))
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


@rule(
    id="TRANSFER-1",
    severity="rejection",
    category="consistency",
    description="transfers.in_scope == true with no identified transfer mechanism (no "
                "non-empty scc_module, and no non-SCC transfers.mechanism) can never coexist "
                "with a positive outcome — at ANY tier, since the Art.28 tier and the Chapter V "
                "transfer mechanism are independent instruments. 'The Parties agree to use the "
                "SCCs' without specifying a module (or identifying DPF / adequacy / another "
                "mechanism) is not a binding instrument (SKILL.md hard rule).",
    spec_anchor=_TRANSFER1_SPEC,
)
def transfers_in_scope_without_mechanism_contradicts_positive_outcome(sidecar, ctx):
    out = []
    transfers = sidecar.get("transfers")
    if not isinstance(transfers, dict) or transfers.get("in_scope") is not True:
        return out
    if not _outcome_is_positive(sidecar):
        return out
    scc_module = transfers.get("scc_module")
    mechanism = transfers.get("mechanism")
    has_scc = isinstance(scc_module, str) and scc_module.strip() != ""
    has_other_mechanism = isinstance(mechanism, str) and mechanism in _NON_SCC_MECHANISMS
    if has_scc or has_other_mechanism:
        return out
    out.append(Finding(
        rule_id="TRANSFER-1", category="consistency", severity="rejection",
        message="transfers.in_scope is true but no transfer mechanism is identified "
                 "(scc_module is missing/empty and transfers.mechanism does not name a "
                 "non-SCC mechanism), while outcome.compliant is true and/or recommendation "
                 "is 'sign' — an unspecified transfer mechanism cannot be reported as "
                 "compliant/sign at any tier.",
        spec_anchor=_TRANSFER1_SPEC, field="transfers.scc_module",
        fix_hint="Identify the actual mechanism: set transfers.scc_module to the SCC module in "
                 "use, or transfers.mechanism to 'dpf' / 'adequacy_decision' / 'bcr' / "
                 "'art49_derogation' if SCCs are not the basis.",
    ))
    return out


@rule(
    id="COVERAGE-1",
    severity="rejection",
    category="consistency",
    description="art28_coverage[] is the evidence behind the sign/no-sign recommendation "
                "(review-quick.md Step 7 verdict-pattern table): a GAP or DEFECT entry "
                "anywhere, or the coverage table being missing/empty entirely, can never "
                "coexist with a positive outcome — only an all-PASS (or PASS/WEAK) coverage "
                "table ever reaches a bare 'sign' in that table.",
    spec_anchor=_COVERAGE1_SPEC,
)
def coverage_defects_or_omission_contradict_positive_outcome(sidecar, ctx):
    out = []
    if not _outcome_is_positive(sidecar):
        return out
    coverage = sidecar.get("art28_coverage")
    if not isinstance(coverage, list) or len(coverage) == 0:
        out.append(Finding(
            rule_id="COVERAGE-1", category="consistency", severity="rejection",
            message="art28_coverage is missing or empty but outcome.compliant is true and/or "
                    "recommendation is 'sign' — the Art. 28(3)(a)-(h) coverage table is the "
                    "evidence for that claim (review-quick.md Step 7); a positive outcome with "
                    "no recorded coverage is unsupported.",
            spec_anchor=_COVERAGE1_SPEC, field="art28_coverage",
            fix_hint="Record the full chapeau + (a)-(h) art28_coverage table for this run "
                     "before reporting compliant/sign.",
        ))
        return out
    for item in coverage:
        if not isinstance(item, dict) or item.get("status") not in ("GAP", "DEFECT"):
            continue
        obligation = item.get("obligation", "?")
        out.append(Finding(
            rule_id="COVERAGE-1", category="consistency", severity="rejection",
            message=f"art28_coverage entry '{obligation}' is {item.get('status')} but "
                     "outcome.compliant is true and/or recommendation is 'sign' — "
                     "review-quick.md's verdict-pattern table never reaches a bare 'sign' with "
                     "any GAP/DEFECT present.",
            spec_anchor=_COVERAGE1_SPEC, field="art28_coverage", entry_id=str(obligation),
            fix_hint="Either correct the obligation's status, or change "
                     "outcome.recommendation to 'sign_with_side_letter' / "
                     "'do_not_sign_without_changes' / 'escalate_to_review_neg' and set "
                     "compliant to false.",
        ))
    return out
