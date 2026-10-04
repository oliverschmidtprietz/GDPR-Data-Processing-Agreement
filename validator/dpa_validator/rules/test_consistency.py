import json
from pathlib import Path

from dpa_validator.runner import validate, Context

HERE = Path(__file__).resolve()
VALIDATOR = HERE.parents[2]                    # .../validator
SCHEMA = VALIDATOR.parent / "references" / "dpa-art28-sidecar-schema.json"
FIX = VALIDATOR / "fixtures"


def _ctx():
    return Context(mode="internal", schema_path=SCHEMA,
                   references_dir=VALIDATOR.parent / "references")


def _assert_only_rule_rejects(sidecar, rule_id):
    result = validate(sidecar, _ctx())
    assert result.status == "failed"
    rejecting = {f.rule_id for f in result.findings if f.severity == "rejection"}
    assert rejecting == {rule_id}, [f.to_dict() for f in result.findings]
    return result


def test_annex2_absent_but_compliant_is_rejected():
    sidecar = json.loads(
        (FIX / "must_fail" / "CONS-1__annex2-missing-but-compliant.json").read_text())
    _assert_only_rule_rejects(sidecar, "CONS-1")


def test_annex2_absent_but_not_compliant_is_fine():
    # The contradiction is specifically present+false / (compliant+true or sign) — an
    # honest non-positive outcome (neither compliant nor "sign") with a missing annex
    # must NOT trip CONS-1.
    sidecar = json.loads(
        (FIX / "must_fail" / "CONS-1__annex2-missing-but-compliant.json").read_text())
    sidecar["outcome"] = {"compliant": False, "recommendation": "do_not_sign_without_changes"}
    result = validate(sidecar, _ctx())
    assert not any(f.rule_id == "CONS-1" for f in result.findings), \
        [f.to_dict() for f in result.findings]


def test_tier3_section_iii_dropped_is_rejected():
    sidecar = json.loads(
        (FIX / "must_fail" / "TIER-1__section-iii-dropped.json").read_text())
    _assert_only_rule_rejects(sidecar, "TIER-1")


def test_tier3_all_sections_intact_is_fine():
    sidecar = json.loads(
        (FIX / "must_pass" / "tier3-transfer-with-handoffs.json").read_text())
    result = validate(sidecar, _ctx())
    assert not any(f.rule_id == "TIER-1" for f in result.findings), \
        [f.to_dict() for f in result.findings]


def test_tier1_only_examines_tier3():
    # tier 2 with a dropped Section III is a different (uncovered) legal question —
    # TIER-1 must not fire outside tier == 3.
    sidecar = json.loads(
        (FIX / "must_fail" / "TIER-1__section-iii-dropped.json").read_text())
    sidecar["tier"] = 2
    result = validate(sidecar, _ctx())
    assert not any(f.rule_id == "TIER-1" for f in result.findings), \
        [f.to_dict() for f in result.findings]


# --- break-it fix 2026-10-02: omission bypasses + new consistency rules --------------


def test_cons1_fires_when_annex2_toms_key_is_omitted_entirely_and_compliant():
    # Previously CONS-1 only looked at annex2_toms.present == False; a sidecar that
    # omits annex2_toms entirely (no data at all) sailed through uncaught.
    sidecar = json.loads(
        (FIX / "must_fail" / "CONS-1__annex2-key-omitted-entirely.json").read_text())
    _assert_only_rule_rejects(sidecar, "CONS-1")


def test_cons1_omission_variant_does_not_fire_without_a_positive_claim():
    sidecar = json.loads(
        (FIX / "must_fail" / "CONS-1__annex2-key-omitted-entirely.json").read_text())
    sidecar["outcome"] = {"compliant": False, "recommendation": "escalate_to_review_neg"}
    result = validate(sidecar, _ctx())
    assert not any(f.rule_id == "CONS-1" for f in result.findings), \
        [f.to_dict() for f in result.findings]


def test_annex2_not_yet_assessed_honest_escalation_is_fine():
    sidecar = json.loads(
        (FIX / "must_pass" / "annex2-not-yet-assessed-honest-escalation.json").read_text())
    result = validate(sidecar, _ctx())
    assert result.status in {"passed", "passed_with_warnings"}, \
        [f.to_dict() for f in result.findings]
    assert not any(f.severity == "rejection" for f in result.findings), \
        [f.to_dict() for f in result.findings]


def test_tier1_fires_when_sections_intact_is_omitted_entirely_and_compliant():
    sidecar = json.loads(
        (FIX / "must_fail" / "TIER-1__sections-intact-omitted-entirely.json").read_text())
    _assert_only_rule_rejects(sidecar, "TIER-1")


def test_tier3_sections_not_yet_confirmed_honest_escalation_is_fine():
    sidecar = json.loads(
        (FIX / "must_pass" / "tier3-sections-not-yet-confirmed-honest-escalation.json")
        .read_text())
    result = validate(sidecar, _ctx())
    assert not any(f.severity == "rejection" for f in result.findings), \
        [f.to_dict() for f in result.findings]


def test_annex2_2_warns_when_toms_substance_unassessed_but_compliant():
    sidecar = json.loads(
        (FIX / "must_warn" / "ANNEX2-2__unassessed-toms-but-compliant.json").read_text())
    result = validate(sidecar, _ctx())
    assert result.status == "passed_with_warnings", [f.to_dict() for f in result.findings]
    warning_rules = {f.rule_id for f in result.findings if f.severity == "warning"}
    assert "ANNEX2-2" in warning_rules
    assert not any(f.severity == "rejection" for f in result.findings), \
        [f.to_dict() for f in result.findings]


def test_annex2_2_silent_when_compliant_is_false():
    sidecar = json.loads(
        (FIX / "must_warn" / "ANNEX2-2__unassessed-toms-but-compliant.json").read_text())
    sidecar["outcome"]["compliant"] = False
    sidecar["outcome"]["recommendation"] = "escalate_to_review_neg"
    result = validate(sidecar, _ctx())
    assert not any(f.rule_id == "ANNEX2-2" for f in result.findings), \
        [f.to_dict() for f in result.findings]


def test_transfer1_fires_when_in_scope_with_no_mechanism_but_compliant():
    sidecar = json.loads(
        (FIX / "must_fail" / "TRANSFER-1__in-scope-no-mechanism-but-compliant.json")
        .read_text())
    _assert_only_rule_rejects(sidecar, "TRANSFER-1")


def test_transfer1_fires_at_any_tier_not_just_tiers_with_sccs():
    sidecar = json.loads(
        (FIX / "must_fail" / "TRANSFER-1__in-scope-no-mechanism-but-compliant.json")
        .read_text())
    assert sidecar["tier"] == 1
    _assert_only_rule_rejects(sidecar, "TRANSFER-1")


def test_transfer1_does_not_false_positive_on_a_legitimate_dpf_mechanism():
    sidecar = json.loads(
        (FIX / "must_pass" / "transfer-dpf-mechanism-no-sccs-needed.json").read_text())
    result = validate(sidecar, _ctx())
    assert not any(f.rule_id == "TRANSFER-1" for f in result.findings), \
        [f.to_dict() for f in result.findings]


def test_coverage1_fires_on_defect_entries_with_compliant_outcome():
    sidecar = json.loads(
        (FIX / "must_fail" / "COVERAGE-1__defect-entries-but-compliant.json").read_text())
    _assert_only_rule_rejects(sidecar, "COVERAGE-1")


def test_coverage1_fires_on_missing_coverage_array_with_sign_recommendation():
    sidecar = json.loads(
        (FIX / "must_fail" / "COVERAGE-1__no-coverage-array-but-sign.json").read_text())
    _assert_only_rule_rejects(sidecar, "COVERAGE-1")


def test_coverage1_fires_regardless_of_mode_including_joint_controller():
    sidecar = json.loads(
        (FIX / "must_fail" / "COVERAGE-1__jc-mode-with-defect-coverage.json").read_text())
    _assert_only_rule_rejects(sidecar, "COVERAGE-1")


def test_coverage1_does_not_false_positive_on_gap_with_side_letter_recommendation():
    sidecar = json.loads(
        (FIX / "must_pass" / "coverage-gap-with-side-letter-recommendation.json").read_text())
    result = validate(sidecar, _ctx())
    assert not any(f.rule_id == "COVERAGE-1" for f in result.findings), \
        [f.to_dict() for f in result.findings]


def test_schema1_rejects_empty_scc_module_and_transfer1_also_fires():
    # scc_module "" now violates the schema's minLength: 1 (SCHEMA-1), and separately
    # carries no usable mechanism for TRANSFER-1 — both legitimately fire together.
    sidecar = json.loads(
        (FIX / "must_fail" / "SCHEMA-1__empty-scc-module.json").read_text())
    result = validate(sidecar, _ctx())
    assert result.status == "failed"
    rejecting = {f.rule_id for f in result.findings if f.severity == "rejection"}
    assert rejecting == {"SCHEMA-1", "TRANSFER-1"}, [f.to_dict() for f in result.findings]


def test_known_limitation_per_clause_substance_is_not_machine_checked():
    # Documents an intentional, disclosed gap (validator/README.md): a PASS verdict on
    # (d)/(h) is trusted at face value even when its own note says the clause-level
    # substance (an objection right, real audit rights) is absent. This is a
    # regression lock on the documented limitation, not an endorsement of the outcome.
    sidecar = json.loads(
        (FIX / "must_pass" / "known-limitation-per-clause-substance-not-checked.json")
        .read_text())
    result = validate(sidecar, _ctx())
    assert not any(f.severity == "rejection" for f in result.findings), \
        [f.to_dict() for f in result.findings]
