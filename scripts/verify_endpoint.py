"""scripts/verify_endpoint.py — 4-probe HTTP 200 verify for one clone.

Per the v1 PATCH promotion contract (architecture §8.1):
  1. GET /                          — service info
  2. GET /clone/{slug}/health       — per-clone health
  3. GET /.well-known/mcp-server    — IETF discovery URI
  4. POST /clone/{slug}/mcp         — JSON-RPC initialize

In Phase A (no deployed service), this is a dry-run stub.
Phase D uses the real implementation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT_PATH = REPO_ROOT / "services" / "shared" / "catalog_client" / "catalog_snapshot.py"
PROMOTION_LOG = REPO_ROOT / "docs" / "promotion_log.md"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _probe_urls(base: str, slug: str) -> List[Tuple[str, str]]:
    return [
        ("GET /", f"{base}/"),
        ("GET /health", f"{base}/clone/{slug}/health"),
        ("GET /.well-known/mcp-server", f"{base}/.well-known/mcp-server"),
        ("POST /mcp", f"{base}/clone/{slug}/mcp"),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="4-probe HTTP 200 verify for one clone.")
    parser.add_argument("--slug", required=True)
    parser.add_argument("--slot", required=True)
    parser.add_argument("--base-url", default=None)
    parser.add_argument("--dry-run", action="store_true", default=True)
    args = parser.parse_args()

    base = args.base_url or f"https://a2a-meta-clones-{args.slot}.up.railway.app"
    if args.dry_run:
        print(f"[DRY-RUN] would probe 4 paths for {args.slug} on {args.slot}:")
        for name, url in _probe_urls(base, args.slug):
            print(f"  {name:<32} {url}")
        return 0
    print("ERROR: live verify requires a deployed service. Phase A is local-only.", file=sys.stderr)
    return 6


if __name__ == "__main__":
    sys.exit(main())
