"""Project a native dpa-art28 sidecar into the portfolio core artefact.

A PROJECTION, not a rewrite: the native sidecar is never modified or
restructured. Structure/signature mirrors
skills/toms-art32/validator/toms_validator/core_artefact.py
(`to_core_artefact(sidecar, *, skill_version) -> dict`), but the mapping
logic is dpa-art28's own.

subject.type is "other": the subject here is a contract/instrument (a DPA,
AVV or JCA) being reviewed or drafted, which does not fit any of the more
specific skill-artefact-1.1 enum values (organisation | processing_activity |
transfer | assessment).

sources[]/handoffs[]/unknowns[] are deliberately NOT hard-coded empty
literals (the exact defect the portfolio standard calls out in ropa and
toms-art32) — each is driven by real fields the sidecar actually carries for
THIS run:

  - sources[]: which references/**/*.md files this run's mode/tier/transfers
    combination would actually have loaded, per SKILL.md's "Reference
    loading order" table, resolved against sources.lock.json for citation +
    last_verified. A run that used none of the conditional references still
    gets the one file SKILL.md loads unconditionally
    (references/art28-3-checklist.md); if even the lock entry is missing,
    that reference is skipped rather than fabricated.
  - handoffs[]: fires only when annex2_toms is present in the sidecar AND
    signals the Annex 2 substance has not been confirmed via toms-art32
    (SKILL.md 'Out of scope': "Producing the TOM content itself is the
    toms-art32 skill's job"). Silent when the sidecar carries no annex2_toms
    data at all (nothing to hand off).
  - unknowns[]: fires only when the sidecar's own optional `ropa_relevant`
    flag is true (SKILL.md 'Out of scope': RoPA record-keeping is "a
    separate task; reference the ropa skill") — this skill never assesses
    RoPA coverage itself, so a true flag is a genuinely open question with
    no sibling data available in this run.
"""
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ARTEFACT_SCHEMA_VERSION = "1.1"
SKILL_NAME = "dpa-art28"

_DATETIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")
_UNKNOWN_INSTRUMENT_ID = "unknown-instrument"

_OUTCOME_BY_VALIDATION_STATUS = {
    "passed": "complete",
    "passed_with_warnings": "provisional",
    "failed": "blocked",
}

# references/art28-3-checklist.md is loaded unconditionally in every mode
# (SKILL.md "Reference loading order" item 1). The rest are conditional on
# fields the sidecar itself carries.
_ALWAYS_LOADED = ["references/art28-3-checklist.md"]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _generated_at(sidecar: dict) -> str:
    value = sidecar.get("generated_at")
    if isinstance(value, str) and _DATETIME_RE.match(value):
        return value
    return _now_iso()


def _subject(sidecar: dict) -> dict:
    """`instrument` is untrusted input: a malformed sidecar can carry
    `instrument: 42` or an instrument missing `id`/`label`. Any non-dict
    shape, or a missing id/label, degrades to the unmistakable placeholder
    rather than crashing or fabricating a look-alike identifier."""
    instrument = sidecar.get("instrument")
    if not isinstance(instrument, dict):
        instrument = {}
    inst_id = instrument.get("id")
    label = instrument.get("label")
    return {
        "id": inst_id if isinstance(inst_id, str) and inst_id else _UNKNOWN_INSTRUMENT_ID,
        "label": label if isinstance(label, str) and label else "unknown instrument",
        "type": "other",
    }


def _art28_summary(sidecar: dict) -> str:
    mode = sidecar.get("mode", "unknown mode")
    coverage = sidecar.get("art28_coverage")
    recommendation = None
    outcome = sidecar.get("outcome")
    if isinstance(outcome, dict):
        recommendation = outcome.get("recommendation")
    parts = [f"mode={mode}"]
    if isinstance(coverage, list) and coverage:
        counts: dict = {}
        for item in coverage:
            if isinstance(item, dict):
                status = item.get("status", "unrated")
                counts[status] = counts.get(status, 0) + 1
        if counts:
            parts.append("Art.28(3) coverage: " +
                         ", ".join(f"{n} {s}" for s, n in sorted(counts.items())))
    if recommendation:
        parts.append(f"recommendation={recommendation}")
    return "; ".join(parts)


def _gap(f: dict) -> dict:
    return {
        "id": f.get("entry_id") or f.get("rule_id") or "gap",
        "severity": f.get("severity") or "rejection",
        "message": f.get("message") or "(no message on this finding)",
    }


def _load_lock(references_dir) -> dict:
    """Best-effort load of sources.lock.json next to references/; returns {}
    (never raises) if absent or malformed — sources[] then simply omits any
    reference this run would otherwise have cited."""
    if references_dir is None:
        return {}
    lock_path = Path(references_dir).parent / "sources.lock.json"
    if not lock_path.is_file():
        return {}
    try:
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    files = lock.get("files") if isinstance(lock, dict) else None
    return files if isinstance(files, dict) else {}


def _referenced_files(sidecar: dict) -> list:
    """Which references/**/*.md files THIS run's own mode/tier/transfers/
    language fields would have loaded, per SKILL.md's reference loading
    order — not every file the skill owns."""
    keys = list(_ALWAYS_LOADED)
    mode = sidecar.get("mode")
    tier = sidecar.get("tier")
    transfers = sidecar.get("transfers")
    instrument = sidecar.get("instrument")
    language = instrument.get("language") if isinstance(instrument, dict) else None

    if mode == "REVIEW_NEG":
        keys += ["references/common-defects.md", "references/negotiation-fallbacks.md"]
    if mode == "JOINT_CONTROLLER":
        keys.append("references/art26-joint-controller.md")
    if mode in ("DRAFT", "REDLINE"):
        keys.append("references/tier-selection.md")
    if tier in (2, 3):
        if language == "DE":
            keys.append("references/2021-915-commission-text-de.md")
        elif language == "bilingual":
            keys += ["references/2021-915-commission-text-en.md",
                     "references/2021-915-commission-text-de.md"]
        else:
            keys.append("references/2021-915-commission-text-en.md")
    if isinstance(transfers, dict) and transfers.get("in_scope") is True:
        keys.append("references/sccs-module-guide.md")
    # de-duplicate, preserve first-seen order
    seen = set()
    out = []
    for k in keys:
        if k not in seen:
            seen.add(k)
            out.append(k)
    return out


def _sources(sidecar: dict, references_dir) -> list:
    lock_files = _load_lock(references_dir)
    out = []
    for key in _referenced_files(sidecar):
        entry = lock_files.get(key)
        if not isinstance(entry, dict):
            continue  # not in the lock — nothing honest to cite, so omit rather than fabricate
        last_verified = entry.get("last_verified")
        if not isinstance(last_verified, str):
            continue
        source_type = entry.get("source_type", "reference")
        url = entry.get("url")
        citation = f"{key} ({source_type}{', ' + url if url else ''})"
        out.append({"id": key, "citation": citation, "last_verified": last_verified})
    return out


def _handoffs(sidecar: dict) -> list:
    annex2 = sidecar.get("annex2_toms")
    if not isinstance(annex2, dict):
        return []  # no annex2_toms data in this run — nothing to hand off
    present = annex2.get("present")
    assessed = annex2.get("toms_art32_assessed")
    if present is False or assessed is False:
        return [{
            "sibling_skill": "toms-art32",
            "reason": "Annex 2 (TOM) substance — Art. 32(1) appropriateness, implementation "
                      "status, evidence and effectiveness — is toms-art32's assessment, not "
                      f"this skill's. This run recorded annex2_toms.present={present!r}, "
                      f"toms_art32_assessed={assessed!r}.",
        }]
    return []


def _unknowns(sidecar: dict) -> list:
    if sidecar.get("ropa_relevant") is True:
        return [{
            "id": "ropa-records-not-assessed",
            "question": "Are the processing activities under this instrument reflected in "
                        "the organisation's Records of Processing (Art. 30)? dpa-art28 does "
                        "not assess this — route to the ropa skill.",
            "blocking": False,
        }]
    return []


def to_core_artefact(sidecar: dict, *, skill_version: str, references_dir=None) -> dict:
    validation = sidecar.get("validation")
    if not isinstance(validation, dict):
        validation = {}
    validation_findings = validation.get("findings")
    if not isinstance(validation_findings, list):
        validation_findings = []
    return {
        "artefact_schema_version": ARTEFACT_SCHEMA_VERSION,
        "skill": SKILL_NAME,
        "skill_version": skill_version,
        "generated_at": _generated_at(sidecar),
        "subject": _subject(sidecar),
        "outcome": {
            "status": _OUTCOME_BY_VALIDATION_STATUS.get(
                validation.get("status", "passed"), "provisional"),
            "summary": _art28_summary(sidecar),
        },
        "gaps": [_gap(f) for f in validation_findings if isinstance(f, dict)],
        "sources": _sources(sidecar, references_dir),
        "handoffs": _handoffs(sidecar),
        "unknowns": _unknowns(sidecar),
    }


def blocked_artefact(*, skill_version: str, reason: str) -> dict:
    """Minimal, always schema-valid artefact for when `to_core_artefact`
    itself raises despite the guards above (mirrors
    dpa_validator.runner.validate()'s per-rule exception handler)."""
    return {
        "artefact_schema_version": ARTEFACT_SCHEMA_VERSION,
        "skill": SKILL_NAME,
        "skill_version": skill_version,
        "generated_at": _now_iso(),
        "subject": {"id": _UNKNOWN_INSTRUMENT_ID, "label": "unknown instrument", "type": "other"},
        "outcome": {
            "status": "blocked",
            "summary": f"Core artefact adapter failed: {reason}",
        },
        "gaps": [{
            "id": "core-artefact-adapter-error",
            "severity": "rejection",
            "message": f"to_core_artefact raised: {reason}",
        }],
        "sources": [],
        "handoffs": [],
        "unknowns": [],
    }
