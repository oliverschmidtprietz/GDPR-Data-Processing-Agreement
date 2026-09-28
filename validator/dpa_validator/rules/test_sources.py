import json
from pathlib import Path

from dpa_validator.runner import validate, Context

HERE = Path(__file__).resolve()
VALIDATOR = HERE.parents[2]                    # .../validator
SCHEMA = VALIDATOR.parent / "references" / "dpa-art28-sidecar-schema.json"
REFS = VALIDATOR.parent / "references"
FIX = VALIDATOR / "fixtures"


def _ctx(sources_lock_override=None):
    return Context(mode="internal", schema_path=SCHEMA, references_dir=REFS,
                   sources_lock_override=sources_lock_override)


def test_real_sources_lock_covers_every_on_disk_reference_with_no_warnings():
    # The real, committed sources.lock.json must cover every references/**/*.md
    # file dpa-art28 actually ships, with no SRC-1 warnings at all.
    sidecar = json.loads((FIX / "must_pass" / "minimal-clean.json").read_text())
    result = validate(sidecar, _ctx())
    src_findings = [f for f in result.findings if f.rule_id == "SRC-1"]
    assert src_findings == [], [f.to_dict() for f in src_findings]


def test_missing_manifest_entry_is_a_warning_not_a_rejection():
    sidecar = json.loads((FIX / "must_pass" / "minimal-clean.json").read_text())
    result = validate(sidecar, _ctx(sources_lock_override={"files": {}}))
    src_findings = [f for f in result.findings if f.rule_id == "SRC-1"]
    assert src_findings, "expected SRC-1 to report every on-disk reference as undeclared"
    assert all(f.severity == "warning" for f in src_findings)
    assert result.status != "failed"


def test_stale_entry_is_flagged():
    override = {"files": {
        "references/art28-3-checklist.md": {
            "source_type": "template", "jurisdiction": "EU", "url": None,
            "last_verified": "2000-01-01", "confidence": "high",
            "owner": "oliverschmidtprietz",
        },
    }}
    sidecar = json.loads((FIX / "must_pass" / "minimal-clean.json").read_text())
    result = validate(sidecar, _ctx(sources_lock_override=override))
    stale = [f for f in result.findings
             if f.rule_id == "SRC-1" and f.entry_id == "references/art28-3-checklist.md"
             and f.field == "last_verified"]
    assert stale, [f.to_dict() for f in result.findings]


def test_missing_manifest_file_is_reported_not_raised(tmp_path):
    sidecar = json.loads((FIX / "must_pass" / "minimal-clean.json").read_text())
    ctx = Context(mode="internal", schema_path=SCHEMA, references_dir=tmp_path / "references")
    result = validate(sidecar, ctx)   # MUST NOT raise even though the dir doesn't exist
    assert any(f.rule_id == "SRC-1" and "could not be loaded" in f.message
               for f in result.findings), [f.to_dict() for f in result.findings]
