"""CLI fail-closed tests (break-it test 2026-10-02).

The validate.py file-read/parse step must never crash with a raw traceback on
malformed input: missing file, unreadable file, invalid UTF-8, invalid JSON
syntax, or a non-object top-level JSON value (which previously also crashed
--emit-core-artefact with a TypeError at the `{**sidecar, ...}` literal,
since dict-unpacking a list/str/etc. raises). Probe files reused from
scratchpad/breakit/dpa-art28/c1-c4 (copied into fixtures/malformed_input/,
never referenced from the scratchpad path per the break-it fix brief).

Invocation mirrors the sibling convention (skills/ropa/validator/tests/
test_pack_end_to_end.py): subprocess.run(["uv", "run", str(VALIDATE_PY), ...]).
"""
import json
import subprocess
from pathlib import Path

VALIDATOR_DIR = Path(__file__).resolve().parent
VALIDATE_PY = VALIDATOR_DIR / "validate.py"
MALFORMED = VALIDATOR_DIR / "fixtures" / "malformed_input"


def _run(*args):
    return subprocess.run(
        ["uv", "run", str(VALIDATE_PY), *args],
        capture_output=True, text=True, cwd=VALIDATOR_DIR,
    )


def _assert_clean_failure(proc, expect_substring=None):
    assert "Traceback (most recent call last)" not in proc.stdout, proc.stdout
    assert "Traceback (most recent call last)" not in proc.stderr, proc.stderr
    assert proc.returncode == 1, (proc.returncode, proc.stdout, proc.stderr)
    assert "status: failed" in proc.stdout, proc.stdout
    if expect_substring:
        assert expect_substring in proc.stdout, proc.stdout


def test_invalid_json_syntax_fails_closed():
    proc = _run(str(MALFORMED / "c1-invalid-json-syntax.json"))
    _assert_clean_failure(proc, "not valid JSON")


def test_top_level_array_fails_closed():
    proc = _run(str(MALFORMED / "c2-top-level-array.json"))
    _assert_clean_failure(proc, "JSON object")


def test_empty_file_fails_closed():
    proc = _run(str(MALFORMED / "c3-empty-file.json"))
    _assert_clean_failure(proc, "not valid JSON")


def test_bare_string_fails_closed():
    proc = _run(str(MALFORMED / "c4-bare-string.json"))
    _assert_clean_failure(proc, "JSON object")


def test_missing_file_fails_closed(tmp_path):
    missing = tmp_path / "does-not-exist.json"
    proc = _run(str(missing))
    _assert_clean_failure(proc, "not found")


def test_directory_as_sidecar_path_fails_closed(tmp_path):
    a_directory = tmp_path / "a-directory.json"
    a_directory.mkdir()
    proc = _run(str(a_directory))
    _assert_clean_failure(proc)


def test_invalid_utf8_fails_closed(tmp_path):
    bad = tmp_path / "bad-utf8.json"
    bad.write_bytes(b"\xff\xfe\x00{")
    proc = _run(str(bad))
    _assert_clean_failure(proc, "UTF-8")


def test_emit_core_artefact_with_top_level_array_does_not_crash(tmp_path):
    out = tmp_path / "artefact.json"
    proc = _run(str(MALFORMED / "c2-top-level-array.json"),
                "--emit-core-artefact", str(out))
    _assert_clean_failure(proc)
    assert out.exists()
    artefact = json.loads(out.read_text(encoding="utf-8"))
    assert artefact["outcome"]["status"] == "blocked"
    assert any(g["severity"] == "rejection" for g in artefact["gaps"])


def test_emit_core_artefact_with_bare_string_does_not_crash(tmp_path):
    out = tmp_path / "artefact.json"
    proc = _run(str(MALFORMED / "c4-bare-string.json"),
                "--emit-core-artefact", str(out))
    _assert_clean_failure(proc)
    assert out.exists()
    artefact = json.loads(out.read_text(encoding="utf-8"))
    assert artefact["outcome"]["status"] == "blocked"


def test_emit_core_artefact_with_invalid_json_does_not_crash(tmp_path):
    out = tmp_path / "artefact.json"
    proc = _run(str(MALFORMED / "c1-invalid-json-syntax.json"),
                "--emit-core-artefact", str(out))
    _assert_clean_failure(proc)
    assert out.exists()
    artefact = json.loads(out.read_text(encoding="utf-8"))
    assert artefact["outcome"]["status"] == "blocked"


def test_json_format_fails_closed_cleanly_too():
    proc = _run(str(MALFORMED / "c1-invalid-json-syntax.json"), "--format", "json")
    assert "Traceback" not in proc.stdout, proc.stdout
    assert proc.returncode == 1
    report = json.loads(proc.stdout)
    assert report["status"] == "failed"
    assert report["findings"][0]["severity"] == "rejection"


def test_well_formed_clean_sidecar_still_passes():
    clean = VALIDATOR_DIR / "fixtures" / "must_pass" / "minimal-clean.json"
    proc = _run(str(clean))
    assert proc.returncode == 0, proc.stdout
    assert "Traceback" not in proc.stdout
