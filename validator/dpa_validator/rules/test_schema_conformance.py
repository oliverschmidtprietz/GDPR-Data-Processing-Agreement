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


def test_minimal_clean_passes():
    sidecar = json.loads((FIX / "must_pass" / "minimal-clean.json").read_text())
    result = validate(sidecar, _ctx())
    assert result.status in {"passed", "passed_with_warnings"}, \
        [f.to_dict() for f in result.findings]


def test_tier3_transfer_fixture_passes():
    sidecar = json.loads((FIX / "must_pass" / "tier3-transfer-with-handoffs.json").read_text())
    result = validate(sidecar, _ctx())
    assert result.status in {"passed", "passed_with_warnings"}, \
        [f.to_dict() for f in result.findings]


def test_bad_mode_enum_is_a_rejection_finding_not_an_exception():
    sidecar = json.loads((FIX / "must_fail" / "SCHEMA-1__bad-mode-enum.json").read_text())
    result = validate(sidecar, _ctx())   # MUST NOT raise — findings-based
    _assert_only_rule_rejects(sidecar, "SCHEMA-1")


def test_missing_required_outcome_is_a_rejection_finding_not_an_exception():
    sidecar = json.loads((FIX / "must_pass" / "minimal-clean.json").read_text())
    del sidecar["outcome"]
    result = validate(sidecar, _ctx())
    assert result.status == "failed"
    assert any(f.severity == "rejection" and f.rule_id == "SCHEMA-1" for f in result.findings)


def test_non_dict_sidecar_root_does_not_crash():
    # A stray non-object root must be reported, never raised (A9-style discipline).
    result = validate({"not": "a valid sidecar"}, _ctx())
    assert result.status == "failed"
    assert any(f.severity == "rejection" for f in result.findings)
