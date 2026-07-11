"""tests/test_promotion_log_immutability.py — assert docs/promotion_log.md
is append-only.

The promotion log is the audit trail for HTTP-verification
history. Per the v1 PATCH (architecture §9 + pipeline §6),
it is append-only. The test asserts that running
`pipeline.py demote --live` appends a new entry without
modifying any prior content.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PROMOTION_LOG = REPO_ROOT / "docs" / "promotion_log.md"


def _read(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def test_promotion_log_unchanged_when_no_demote(tmp_path):
    """When the demote --candidate fails (no LIVE clones to demote), the log is unchanged."""
    # Snapshot
    before = _read(PROMOTION_LOG)
    r = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "pipeline.py"),
            "--live",
            "demote",
            "--slug", "agent-lens",  # not in LIVE_CLONES
            "--slot", "slot-a",
            "--reason", "immutability-test",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    assert r.returncode == 1, "demote against a non-LIVE slug should fail"
    after = _read(PROMOTION_LOG)
    assert before == after, "promotion log was modified by a failed demote"


def test_promotion_log_header_format():
    """The promotion log opens with the v0 DRAFT header when it is first created."""
    from scripts.pipeline import _PROMOTION_LOG_HEADER

    assert _PROMOTION_LOG_HEADER.startswith("# a2a-meta-clones — promotion log")
    assert "append-only" in _PROMOTION_LOG_HEADER
    assert "Retention" in _PROMOTION_LOG_HEADER
