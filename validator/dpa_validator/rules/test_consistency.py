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
    # The contradiction is specifically present+false / compliant+true — an honest
    # non-compliant outcome with a missing annex must NOT trip CONS-1.
    sidecar = json.loads(
        (FIX / "must_fail" / "CONS-1__annex2-missing-but-compliant.json").read_text())
    sidecar["outcome"]["compliant"] = False
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
