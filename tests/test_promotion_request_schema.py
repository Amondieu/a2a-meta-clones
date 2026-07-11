"""tests/test_promotion_request_schema.py — assert the 9-field JSON schema
of promotion_request_<slug>.json.

Per the v1 PATCH promotion contract (architecture §8.1),
every promotion artifact must contain 9 fields. The child
repo's `pipeline.py promote` writes the file; the test
asserts the schema on a synthetic example.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _run_promote(slug, slot, output_path):
    """Run pipeline.py promote --live to write a real file, then return it."""
    r = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "pipeline.py"),
            "--live",
            "promote",
            "--slug", slug,
            "--slot", slot,
            "--reason", "test",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, f"promote failed: {r.stdout}\n{r.stderr}"
    return Path(REPO_ROOT / f"promotion_request_{slug}.json")


REQUIRED_FIELDS = {
    "slug",
    "slot",
    "git_sha",
    "image_digest",
    "railway_deployment_id",
    "public_base_url",
    "health_check",
    "mcp_check",
    "verified_at_utc",
    "verified_by",
    "promotion_state",
    "legacy_source_spec_name",  # v1 PATCH: added by the child repo
    "reason",
}


def test_promotion_request_has_all_required_fields():
    out_path = _run_promote("agent-fabric-oversight", "slot-b", None)
    try:
        data = json.loads(out_path.read_text(encoding="utf-8"))
    finally:
        out_path.unlink(missing_ok=True)

    missing = REQUIRED_FIELDS - set(data.keys())
    assert not missing, f"missing fields: {missing}"
    # Spot-check critical nested fields
    assert data["health_check"]["path"] == "/clone/agent-fabric-oversight/health"
    assert data["health_check"]["status"] == 200
    assert data["mcp_check"]["protocol"] == "json-rpc"
    assert data["promotion_state"] == "LIVE"
    # legacy_source_spec_name is the metadata for the v1 PATCH split
    assert data["legacy_source_spec_name"] == "agent-fabric__human-oversight-integration"
