"""Tests for dpa_validator.core_artefact.to_core_artefact.

Verifies the projection against the real skill-artefact-1.1 schema, and
specifically that sources[]/handoffs[]/unknowns[] are driven by the
sidecar's own fields rather than hard-coded empty (the defect the portfolio
standard calls out in ropa and toms-art32).
"""
import json
from pathlib import Path

import jsonschema
import pytest

from dpa_validator.core_artefact import to_core_artefact, blocked_artefact

_ARTEFACT_SCHEMA = json.loads(
    (Path(__file__).resolve().parents[4] / "docs" / "standards" / "schemas"
     / "skill-artefact-1.1.schema.json").read_text(encoding="utf-8")
)
REFS = Path(__file__).resolve().parents[1].parent / "references"


def _validate(artefact):
    jsonschema.validate(artefact, _ARTEFACT_SCHEMA, format_checker=jsonschema.FormatChecker())


def _minimal_sidecar(**overrides):
    sidecar = {
        "schema_version": "1.0",
        "generated_at": "2026-09-24T10:00:00Z",
        "instrument": {"id": "acme-dpa", "label": "Acme DPA", "type": "DPA", "language": "EN"},
        "mode": "REVIEW_QUICK",
        "annex2_toms": {"present": True, "toms_art32_assessed": True},
        "outcome": {"compliant": True, "recommendation": "sign"},
        "validation": {"status": "passed", "findings": []},
    }
    sidecar.update(overrides)
    return sidecar


def test_minimal_projection_validates_against_the_portfolio_schema():
    artefact = to_core_artefact(_minimal_sidecar(), skill_version="1.5", references_dir=REFS)
    _validate(artefact)


def test_subject_uses_instrument_id_and_label_and_type_other():
    artefact = to_core_artefact(_minimal_sidecar(), skill_version="1.5", references_dir=REFS)
    assert artefact["subject"] == {"id": "acme-dpa", "label": "Acme DPA", "type": "other"}


def test_malformed_instrument_degrades_to_placeholder_not_a_crash():
    sidecar = _minimal_sidecar(instrument="not-a-dict")
    artefact = to_core_artefact(sidecar, skill_version="1.5", references_dir=REFS)
    _validate(artefact)
    assert artefact["subject"]["id"] == "unknown-instrument"


@pytest.mark.parametrize("validation_status,outcome_status", [
    ("passed", "complete"),
    ("passed_with_warnings", "provisional"),
    ("failed", "blocked"),
])
def test_outcome_status_maps_from_validation_status(validation_status, outcome_status):
    sidecar = _minimal_sidecar(validation={"status": validation_status, "findings": []})
    artefact = to_core_artefact(sidecar, skill_version="1.5", references_dir=REFS)
    assert artefact["outcome"]["status"] == outcome_status


def test_gaps_come_from_the_live_validation_findings_not_a_constant():
    sidecar = _minimal_sidecar(validation={
        "status": "failed",
        "findings": [{"rule_id": "CONS-1", "severity": "rejection", "message": "boom"}],
    })
    artefact = to_core_artefact(sidecar, skill_version="1.5", references_dir=REFS)
    assert artefact["gaps"] == [{"id": "CONS-1", "severity": "rejection", "message": "boom"}]


# --- sources[] --------------------------------------------------------------

def test_sources_includes_the_always_loaded_checklist():
    artefact = to_core_artefact(_minimal_sidecar(), skill_version="1.5", references_dir=REFS)
    ids = {s["id"] for s in artefact["sources"]}
    assert "references/art28-3-checklist.md" in ids
    for s in artefact["sources"]:
        assert s["last_verified"]  # real date from sources.lock.json, never fabricated


def test_sources_adds_tier_and_transfer_references_when_relevant():
    sidecar = _minimal_sidecar(
        mode="DRAFT", tier=3,
        transfers={"in_scope": True, "sections_intact": {"I": True, "II": True, "III": True}},
    )
    artefact = to_core_artefact(sidecar, skill_version="1.5", references_dir=REFS)
    ids = {s["id"] for s in artefact["sources"]}
    assert "references/2021-915-commission-text-en.md" in ids
    assert "references/sccs-module-guide.md" in ids
    assert "references/tier-selection.md" in ids


def test_sources_is_empty_list_not_omitted_when_references_dir_unavailable():
    artefact = to_core_artefact(_minimal_sidecar(), skill_version="1.5", references_dir=None)
    assert artefact["sources"] == []
    _validate(artefact)


# --- handoffs[] / unknowns[] -------------------------------------------------

def test_no_handoff_when_annex2_toms_absent_from_this_run():
    sidecar = _minimal_sidecar()
    del sidecar["annex2_toms"]
    artefact = to_core_artefact(sidecar, skill_version="1.5", references_dir=REFS)
    assert artefact["handoffs"] == []


def test_handoff_to_toms_art32_when_annex2_not_substantively_assessed():
    sidecar = _minimal_sidecar(annex2_toms={"present": True, "toms_art32_assessed": False})
    artefact = to_core_artefact(sidecar, skill_version="1.5", references_dir=REFS)
    assert len(artefact["handoffs"]) == 1
    assert artefact["handoffs"][0]["sibling_skill"] == "toms-art32"


def test_handoff_to_toms_art32_when_annex2_absent():
    sidecar = _minimal_sidecar(annex2_toms={"present": False, "toms_art32_assessed": False})
    artefact = to_core_artefact(sidecar, skill_version="1.5", references_dir=REFS)
    assert artefact["handoffs"][0]["sibling_skill"] == "toms-art32"


def test_no_handoff_when_annex2_fully_assessed():
    sidecar = _minimal_sidecar(annex2_toms={"present": True, "toms_art32_assessed": True})
    artefact = to_core_artefact(sidecar, skill_version="1.5", references_dir=REFS)
    assert artefact["handoffs"] == []


def test_no_unknown_when_ropa_relevant_absent():
    artefact = to_core_artefact(_minimal_sidecar(), skill_version="1.5", references_dir=REFS)
    assert artefact["unknowns"] == []


def test_unknown_emitted_when_ropa_relevant_true():
    sidecar = _minimal_sidecar(ropa_relevant=True)
    artefact = to_core_artefact(sidecar, skill_version="1.5", references_dir=REFS)
    assert len(artefact["unknowns"]) == 1
    assert artefact["unknowns"][0]["id"] == "ropa-records-not-assessed"
    assert artefact["unknowns"][0]["blocking"] is False


def test_no_unknown_when_ropa_relevant_false():
    sidecar = _minimal_sidecar(ropa_relevant=False)
    artefact = to_core_artefact(sidecar, skill_version="1.5", references_dir=REFS)
    assert artefact["unknowns"] == []


# --- blocked_artefact fallback -----------------------------------------------

def test_blocked_artefact_validates_against_the_portfolio_schema():
    artefact = blocked_artefact(skill_version="1.5", reason="KeyError: 'instrument'")
    _validate(artefact)
    assert artefact["outcome"]["status"] == "blocked"
