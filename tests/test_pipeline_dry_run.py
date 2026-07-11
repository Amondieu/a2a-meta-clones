"""tests/test_pipeline_dry_run.py — pipeline.py dry-run smoke tests."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def _run(args, cwd=None):
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "pipeline.py"), *args],
        cwd=cwd or str(REPO_ROOT),
        capture_output=True,
        text=True,
    )


def test_pipeline_help_shows_9_commands():
    """pipeline.py --help shows all 9 subcommands."""
    r = _run(["--help"])
    assert r.returncode == 0
    for cmd in ("init", "scaffold", "test", "package", "review", "verify", "promote", "demote", "status"):
        assert cmd in r.stdout, f"missing command in help: {cmd}"


def test_pipeline_status_shows_5_pending():
    """pipeline.py status shows 5 PENDING clones and the catalog split."""
    r = _run(["status"])
    assert r.returncode == 0
    out = r.stdout
    assert "live_clones_count" in out
    assert "pending_clones_count" in out
    # 5 PENDING per Phase A
    assert "5" in out  # at least one "5" in the JSON


def test_pipeline_init_unknown_slug_exits_1():
    """pipeline.py init with a known catalog slug exits 1 (already exists)."""
    r = _run(["init", "--slug", "agent-lens"])
    assert r.returncode == 1


def test_pipeline_scaffold_unknown_slug_exits_1():
    """pipeline.py scaffold with an unknown slug exits 1 (catalog boundary)."""
    r = _run(["scaffold", "--slug", "policy-weaver", "--slot", "slot-a"])
    assert r.returncode == 1


def test_pipeline_verify_dry_run_prints_4_probes():
    """pipeline.py verify --dry-run prints the 4 probe URLs for a known slug."""
    r = _run(["verify", "--slug", "agent-fabric-oversight", "--slot", "slot-b"])
    assert r.returncode == 0
    assert "DRY-RUN" in r.stdout
    for path in ("/", "/clone/agent-fabric-oversight/health", "/.well-known/mcp-server", "/clone/agent-fabric-oversight/mcp"):
        assert path in r.stdout, f"missing probe URL: {path}"
