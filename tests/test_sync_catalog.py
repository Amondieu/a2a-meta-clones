"""tests/test_sync_catalog.py — sync_catalog dry-run smoke test."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _run():
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "sync_catalog.py")],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )


def test_sync_catalog_dry_run_prints_source_and_target():
    r = _run()
    assert r.returncode == 0
    assert "DRY-RUN" in r.stdout
    assert "live_clone_catalog.py" in r.stdout  # source
    assert "catalog_snapshot.py" in r.stdout  # target
