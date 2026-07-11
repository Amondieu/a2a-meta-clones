"""scripts/sync_catalog.py — one-way copy of the A2A-Meta catalog.

Reads A2A-Meta/api/middleware/live_clone_catalog.py and writes
a snapshot to services/shared/catalog_client/catalog_snapshot.py.

The snapshot is what the child repo's runtime reads (v0).
The catalog itself is the single source of truth and is
NEVER modified by the child repo (catalog write boundary §2.2).

In Phase A this is a stub. Phase B/D re-introduces the real
sync (HTTP fetch from the A2A-Meta catalog API, once that API
exists in the A2A-Meta Opus build).
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE = Path(r"C:\Users\Shadow\ShadowDrive\0.1.Ai\A2A-Meta\api\middleware\live_clone_catalog.py")
TARGET = REPO_ROOT / "services" / "shared" / "catalog_client" / "catalog_snapshot.py"


def main() -> int:
    parser = argparse.ArgumentParser(description="One-way copy of the A2A-Meta catalog into the child repo.")
    parser.add_argument("--source", default=str(SOURCE))
    parser.add_argument("--target", default=str(TARGET))
    parser.add_argument("--dry-run", action="store_true", default=True)
    args = parser.parse_args()

    if args.dry_run:
        print(f"[DRY-RUN] would copy:")
        print(f"  source: {args.source}")
        print(f"  target: {args.target}")
        return 0
    src = Path(args.source)
    tgt = Path(args.target)
    if not src.is_file():
        print(f"ERROR: source not found: {src}", file=sys.stderr)
        return 2
    tgt.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, tgt)
    print(f"synced: {src} -> {tgt}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
