"""Resolve shared portfolio schemas (docs/standards/schemas/) for
dpa_validator's own tests, by walking UP from this file's location.

Works identically in both layouts: inside the monorepo, where
docs/standards/schemas/ lives at the repo root (an ancestor of
skills/dpa-art28/validator/dpa_validator/); and inside a flat public copy
(built by scripts/stage-public-copy.sh), where the same schemas are staged at
docs/standards/schemas/ relative to the public repo root (also an ancestor
of this file there).
"""
from pathlib import Path


def find_schema(name: str) -> Path:
    here = Path(__file__).resolve()
    for ancestor in here.parents:
        candidate = ancestor / "docs" / "standards" / "schemas" / name
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(
        f"schema {name!r} not found in any ancestor of {here} — expected at "
        "docs/standards/schemas/ at the monorepo root or the public repo root"
    )
