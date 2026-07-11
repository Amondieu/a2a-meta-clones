"""tests/test_catalog_write_boundary.py — assert the catalog write boundary.

Per the v1 PATCH (§2.2 of the plan), the child repo MUST NOT
mutate the A2A-Meta catalog. The test snapshots the A2A-Meta
catalog's mtime + content hash before and after running
pipeline.py promote; the hash must be unchanged.
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

import pytest

A2A_META_CATALOG = Path(r"C:\Users\Shadow\ShadowDrive\0.1.Ai\A2A-Meta\api\middleware\live_clone_catalog.py")
REPO_ROOT = Path(__file__).resolve().parent.parent


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_pipeline_promote_does_not_modify_a2a_meta_catalog():
    """Running `pipeline.py promote` does not modify the A2A-Meta catalog."""
    if not A2A_META_CATALOG.is_file():
        pytest.skip("A2A-Meta catalog not present in this environment")

    before = _hash(A2A_META_CATALOG)
    r = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "pipeline.py"),
            "--live",
            "promote",
            "--slug", "agent-lens",
            "--slot", "slot-a",
            "--reason", "catalog-boundary-test",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, f"promote failed: {r.stdout}\n{r.stderr}"
    after = _hash(A2A_META_CATALOG)
    assert before == after, (
        f"catalog write boundary violated: A2A-Meta catalog hash changed. "
        f"Before: {before}, After: {after}. The child repo MUST NOT modify "
        f"A2A-Meta/api/middleware/live_clone_catalog.py."
    )

    # Also verify no promotion_request_*.json was created in A2A-Meta
    a2a_meta_root = A2A_META_CATALOG.parent.parent.parent
    bad_files = list(a2a_meta_root.rglob("promotion_request_*.json"))
    # The test created one in the child repo, not in A2A-Meta
    assert not any(str(f).startswith(str(a2a_meta_root)) for f in bad_files), (
        f"child repo wrote to A2A-Meta: {bad_files}"
    )

    # Cleanup: remove the promotion_request_*.json from the child repo
    for f in REPO_ROOT.glob("promotion_request_*.json"):
        f.unlink()


def test_pipeline_demote_does_not_modify_a2a_meta_catalog():
    """Running `pipeline.py demote --candidate` (which writes to docs/promotion_log.md)
    does not modify the A2A-Meta catalog."""
    if not A2A_META_CATALOG.is_file():
        pytest.skip("A2A-Meta catalog not present in this environment")

    before = _hash(A2A_META_CATALOG)
    r = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "pipeline.py"),
            "--live",
            "demote",
            "--slug", "agent-lens",
            "--slot", "slot-a",
            "--reason", "catalog-boundary-test",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    # demote --candidate against a non-LIVE slug exits 1; the catalog
    # must not be modified regardless
    assert before == _hash(A2A_META_CATALOG), "catalog hash changed (it must not)"
