"""tests/test_check_no_legacy_slug.py — static check smoke tests."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _run():
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "check_no_legacy_slug.py")],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )


def test_check_returns_zero_violations_in_phase_a():
    """At Phase A (just scaffolded), the check passes (0 violations)."""
    r = _run()
    assert r.returncode == 0, f"unexpected violations: {r.stdout}\n{r.stderr}"
    assert "OK" in r.stdout
    assert "0 violations" in r.stdout
