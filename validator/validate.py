#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = ["jsonschema>=4.21"]
# ///
"""dpa-art28 validator CLI — v1.1.0.

  uv run skills/dpa-art28/validator/validate.py <dpa-art28-sidecar.json> [--mode internal|submission] [--format human|json]
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from dpa_validator.runner import validate, Context, Result, to_findings_json  # noqa: E402
from dpa_validator.core_artefact import to_core_artefact, blocked_artefact  # noqa: E402
from dpa_validator.findings import Finding  # noqa: E402
from dpa_validator import rules  # noqa: E402,F401  (populates the registry)

DEFAULT_SCHEMA = HERE.parent / "references" / "dpa-art28-sidecar-schema.json"
DEFAULT_REFS = HERE.parent / "references"


def _skill_version() -> str:
    """Read the live version from SKILL.md frontmatter — never hard-code it (CLAUDE.md)."""
    skill_md = Path(__file__).resolve().parents[1] / "SKILL.md"
    for line in skill_md.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("version:"):
            return line.split(":", 1)[1].strip()
    raise SystemExit("SKILL.md has no version: field")


def _input_error_result(mode: str, sidecar_path: Path, message: str) -> Result:
    """Build a Result for input that couldn't even be loaded/parsed — a file-read or
    JSON-parse failure, or a well-formed-but-non-object top-level JSON value.

    This is a fail-closed path, not a rule: it never raises, always reports
    status "failed" with exactly one INPUT-0 rejection finding, and is run
    through the exact same --format human/json and --emit-core-artefact
    machinery as a normal result, so the CLI never prints a raw traceback for
    malformed input (break-it fix 2026-10-02; no exit code is defined in this
    skill's own docs for bad input, so per the controller's fallback this
    exits 1 with status "failed", consistent with the runner's own
    failed-status exit code — not a distinct operational exit code)."""
    finding = Finding(
        rule_id="INPUT-0", category="input", severity="rejection",
        message=message, spec_anchor="validator/README.md#fail-closed",
        fix_hint="Fix the sidecar file itself (valid UTF-8 JSON, top-level object) and re-run.",
    )
    return Result(
        status="failed",
        summary={"rejections": 1, "warnings": 0, "info": 0, "rules_evaluated": 0},
        findings=[finding],
        mode=mode,
        artefact_path=str(sidecar_path),
        validated_at=datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
    )


def main(argv=None):
    p = argparse.ArgumentParser(prog="dpa-art28-validator")
    p.add_argument("sidecar", type=Path)
    p.add_argument("--mode", choices=["internal", "submission"], default="internal")
    p.add_argument("--format", choices=["human", "json"], default="human")
    p.add_argument("--schema-path", type=Path, default=DEFAULT_SCHEMA)
    p.add_argument("--references-dir", type=Path, default=DEFAULT_REFS)
    p.add_argument(
        "--emit-core-artefact",
        type=Path,
        default=None,
        metavar="PATH",
        help=(
            "After validation, write the portfolio core artefact "
            "(skill-artefact-1.1 schema) projection of THIS run's result to PATH. "
            "Built from the live validation result, never the sidecar's "
            "embedded validation block. Report and exit code unchanged."
        ),
    )
    args = p.parse_args(argv)

    # --- fail-closed file-read/parse step --------------------------------------------
    # Every branch below reports a clean one-line INPUT-0 rejection instead of letting
    # a raw traceback reach the terminal: missing file, unreadable file (permissions,
    # a directory given as the path, ...), invalid UTF-8, invalid JSON syntax, and a
    # well-formed-but-non-object top level (list / string / number / bool / null) —
    # the last of which previously crashed `--emit-core-artefact` with a TypeError at
    # `{**sidecar, ...}` (dict-unpacking a non-mapping), since that line sat outside
    # the adapter's own try/except (break-it fix 2026-10-02).
    sidecar = None
    result = None
    try:
        raw_text = args.sidecar.read_text(encoding="utf-8")
    except FileNotFoundError:
        result = _input_error_result(args.mode, args.sidecar,
                                      f"sidecar not found: {args.sidecar}")
    except UnicodeDecodeError as exc:
        result = _input_error_result(args.mode, args.sidecar,
                                      f"sidecar is not valid UTF-8: {args.sidecar} ({exc})")
    except OSError as exc:
        result = _input_error_result(args.mode, args.sidecar,
                                      f"sidecar could not be read: {args.sidecar} ({exc})")

    if result is None:
        try:
            sidecar = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            result = _input_error_result(args.mode, args.sidecar,
                                          f"sidecar is not valid JSON: {args.sidecar} ({exc})")

    if result is None and not isinstance(sidecar, dict):
        result = _input_error_result(
            args.mode, args.sidecar,
            f"sidecar top level must be a JSON object, got {type(sidecar).__name__}: "
            f"{args.sidecar}")
        sidecar = None  # nothing structured left to project into a core artefact

    # --- normal validation ------------------------------------------------------------
    if result is None:
        ctx = Context(mode=args.mode, schema_path=args.schema_path,
                      references_dir=args.references_dir)
        result = validate(sidecar, ctx)
        result.artefact_path = str(args.sidecar)

    if args.emit_core_artefact is not None:
        if sidecar is not None:
            live_sidecar = {**sidecar, "validation": {
                "status": result.status,
                "findings": [f.to_dict() for f in result.findings],
            }}
            try:
                artefact = to_core_artefact(live_sidecar,
                                            skill_version=_skill_version(),
                                            references_dir=args.references_dir)
            except Exception as exc:  # adapter must never crash the run: the report on stdout
                # and the exit code stay exactly as they would be without this flag, and a
                # minimal, schema-valid, blocked artefact is written instead of a traceback.
                artefact = blocked_artefact(
                    skill_version=_skill_version(),
                    reason=f"{type(exc).__name__}: {exc}")
        else:
            # Input couldn't even be loaded into a structured sidecar — write the same
            # minimal, always-schema-valid blocked artefact rather than skip the file.
            reason = result.findings[0].message if result.findings else "sidecar could not be loaded"
            artefact = blocked_artefact(skill_version=_skill_version(), reason=reason)
        args.emit_core_artefact.write_text(
            json.dumps(artefact, indent=2) + "\n", encoding="utf-8")

    if args.format == "json":
        print(json.dumps(to_findings_json(result, skill_version=_skill_version()), indent=2))
    else:
        print(f"status: {result.status}  ({len(result.findings)} findings)")
        for f in result.findings:
            print(f"  [{f.severity}] {f.rule_id}: {f.message}")
    return 1 if result.status == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
