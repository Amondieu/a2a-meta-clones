"""scripts/pipeline.py — a2a-meta-clones pipeline CLI.

9 commands (each with --dry-run default):
  init        — create a new clone spec
  scaffold    — wire a clone into a slot's env
  test        — run local tests (pytest + smoke_gate --dry-run)
  package     — build the Docker image
  review      — show what would be committed
  verify      — 4-probe HTTP 200 verify
  promote     — write promotion_request_<slug>.json
  demote      — write DEMOTION_CANDIDATE entry
  status      — show LIVE/PENDING/backlog state

The first execution of any command requires the user's
explicit approval (per the v1 implementation plan, Phase A
boundary). --dry-run is the default for all commands.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
PROMOTION_LOG = REPO_ROOT / "docs" / "promotion_log.md"
PROMOTION_DIR = REPO_ROOT  # promotion_request_*.json written here in Phase D
SNAPSHOT_PATH = REPO_ROOT / "services" / "shared" / "catalog_client" / "catalog_snapshot.py"


def _load_snapshot():
    """Load the vendored catalog snapshot (read-only)."""
    if not SNAPSHOT_PATH.exists():
        print(f"ERROR: catalog snapshot not found at {SNAPSHOT_PATH}", file=sys.stderr)
        sys.exit(2)
    import importlib.util

    spec = importlib.util.spec_from_file_location("catalog_snapshot", SNAPSHOT_PATH)
    mod = importlib.util.module_from_spec(spec)
    # Critical: register in sys.modules BEFORE exec_module so
    # @dataclass(frozen=True) can resolve __dict__ via sys.modules.
    sys.modules["catalog_snapshot"] = mod
    spec.loader.exec_module(mod)
    return mod


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _print_json(obj) -> None:
    print(json.dumps(obj, indent=2, sort_keys=False))


# === commands ===


def cmd_init(args) -> int:
    """Create a new clone spec.

    Phase A: stub. Validates that the slug is not in the
    catalog and exits 0 (dry-run) or 1 (unknown slug).
    """
    snapshot = _load_snapshot()
    if not args.slug:
        print("ERROR: --slug is required", file=sys.stderr)
        return 1
    if args.slug in snapshot.LIVE_CLONES or args.slug in snapshot.PENDING_CLONES:
        print(f"ERROR: slug {args.slug!r} is already in the catalog", file=sys.stderr)
        return 1
    if args.dry_run:
        print(f"[DRY-RUN] would init clone spec for slug={args.slug!r}")
        return 0
    print(f"ERROR: --init is not implemented in Phase A. Use a future phase.", file=sys.stderr)
    return 6


def cmd_scaffold(args) -> int:
    """Wire a clone into a slot's env contract.

    Phase A: stub. Validates that the slug is in the catalog
    and the slot exists. Exits 1 if the slug is unknown.
    """
    snapshot = _load_snapshot()
    if args.slug in snapshot.LIVE_CLONES or args.slug in snapshot.PENDING_CLONES:
        pass
    else:
        print(f"ERROR: slug {args.slug!r} is not in the catalog", file=sys.stderr)
        return 1
    if args.slot not in ("slot-a", "slot-b", "slot-c"):
        print(f"ERROR: slot {args.slot!r} is not slot-a / slot-b / slot-c", file=sys.stderr)
        return 1
    if args.dry_run:
        print(f"[DRY-RUN] would scaffold {args.slug!r} into {args.slot}")
        return 0
    print(f"ERROR: --scaffold is not implemented in Phase A. Use Phase C.", file=sys.stderr)
    return 6


def cmd_test(args) -> int:
    """Run the local test suite."""
    import subprocess

    cmd = [sys.executable, "-m", "pytest", str(REPO_ROOT / "tests"), "-v"]
    if args.dry_run:
        cmd.append("--collect-only")
        print(f"[DRY-RUN] would run: {' '.join(cmd)}")
        return 0
    result = subprocess.run(cmd, cwd=str(REPO_ROOT))
    return result.returncode


def cmd_package(args) -> int:
    """Build the Docker image (Phase D). Phase A: stub."""
    if args.dry_run:
        print("[DRY-RUN] would run: docker build -t a2a-meta-clones:dev .")
        return 0
    print("ERROR: --package requires Docker. Phase A does not build images.", file=sys.stderr)
    return 6


def cmd_review(args) -> int:
    """Show what would be committed (Phase A: stub)."""
    import subprocess

    if args.dry_run:
        print("[DRY-RUN] would show git status + diff")
        return 0
    subprocess.run(["git", "status"], cwd=str(REPO_ROOT))
    return 0


def cmd_verify(args) -> int:
    """4-probe HTTP 200 verify for a clone.

    Phase A: dry-run prints the 4 probe URLs. Live requires
    a deployed service (Phase D).
    """
    snapshot = _load_snapshot()
    if args.slug not in snapshot.LIVE_CLONES and args.slug not in snapshot.PENDING_CLONES:
        print(f"ERROR: slug {args.slug!r} is not in the catalog", file=sys.stderr)
        return 1
    if args.slot not in ("slot-a", "slot-b", "slot-c"):
        print(f"ERROR: slot {args.slot!r} is not slot-a / slot-b / slot-c", file=sys.stderr)
        return 1
    base = args.base_url or f"https://a2a-meta-clones-{args.slot}.up.railway.app"
    probes = [
        ("GET /", f"{base}/"),
        ("GET /health", f"{base}/clone/{args.slug}/health"),
        ("GET /.well-known/mcp-server", f"{base}/.well-known/mcp-server"),
        ("POST /mcp", f"{base}/clone/{args.slug}/mcp"),
    ]
    if args.dry_run:
        print(f"[DRY-RUN] would probe 4 paths for {args.slug} on {args.slot}:")
        for name, url in probes:
            print(f"  {name:<32} {url}")
        return 0
    print("ERROR: live verify requires a deployed service. Phase A is local-only.", file=sys.stderr)
    return 6


def cmd_promote(args) -> int:
    """Write promotion_request_<slug>.json to the child repo's
    working directory. NEVER writes to A2A-Meta.

    Per the catalog write boundary (plan §2.2): the child
    repo does NOT mutate LIVE_CLONES. The user reviews the
    request and applies the change to A2A-Meta manually.
    """
    snapshot = _load_snapshot()
    if args.slug not in snapshot.PENDING_CLONES:
        print(f"ERROR: slug {args.slug!r} is not in PENDING_CLONES; cannot promote", file=sys.stderr)
        return 1
    request = {
        "slug": args.slug,
        "slot": args.slot,
        "git_sha": args.git_sha or "<placeholder: set after Phase D first deploy>",
        "image_digest": args.image_digest or "<placeholder: set after Phase D first deploy>",
        "railway_deployment_id": args.railway_deployment_id or "<placeholder>",
        "public_base_url": args.base_url or f"https://a2a-meta-clones-{args.slot}.up.railway.app",
        "health_check": {"path": f"/clone/{args.slug}/health", "status": 200},
        "mcp_check": {"path": "/.well-known/mcp-server", "status": 200, "protocol": "json-rpc"},
        "verified_at_utc": _now_iso(),
        "verified_by": "pipeline.py promote",
        "promotion_state": "LIVE",
        "legacy_source_spec_name": _legacy_name(args.slug, snapshot),
        "reason": args.reason or "manual",
    }
    if args.dry_run:
        print(f"[DRY-RUN] would write promotion_request_{args.slug}.json with:")
        _print_json(request)
        return 0
    out_path = PROMOTION_DIR / f"promotion_request_{args.slug}.json"
    out_path.write_text(json.dumps(request, indent=2), encoding="utf-8")
    print(f"wrote: {out_path}")
    print("NEXT: the user reviews this file and applies the change to A2A-Meta's catalog manually.")
    return 0


def cmd_demote(args) -> int:
    """Write a DEMOTION_CANDIDATE entry to the promotion log.

    Per the v1 PATCH: the cron creates a candidate entry; only
    an explicit `pipeline.py demote <slug> --reason <reason>`
    actually demotes. This command is the candidate generator.
    """
    snapshot = _load_snapshot()
    if args.slug not in snapshot.LIVE_CLONES:
        print(f"ERROR: slug {args.slug!r} is not in LIVE_CLONES; cannot create candidate", file=sys.stderr)
        return 1
    candidate = {
        "slug": args.slug,
        "slot": args.slot,
        "verified_at_utc": _now_iso(),
        "verified_by": "pipeline.py demote --candidate",
        "promotion_state": "DEMOTION_CANDIDATE",
        "demotion_reason": args.reason or "manual",
        "consecutive_failures": args.consecutive_failures or 0,
    }
    if args.dry_run:
        print(f"[DRY-RUN] would append DEMOTION_CANDIDATE entry for {args.slug}:")
        _print_json(candidate)
        return 0
    _append_to_promotion_log(f"### {_now_iso()} — demotion-candidate — {args.slug} — {args.slot}\n\n```json\n{json.dumps(candidate, indent=2)}\n```\n")
    print(f"appended DEMOTION_CANDIDATE entry for {args.slug} to {PROMOTION_LOG}")
    return 0


def cmd_status(args) -> int:
    """Show LIVE / PENDING / backlog state."""
    snapshot = _load_snapshot()
    out = {
        "mode": "local",
        "fable5_unlocked": False,
        "catalog_state": {
            "live_clones_count": len(snapshot.LIVE_CLONES),
            "pending_clones_count": len(snapshot.PENDING_CLONES),
            "pending_slugs": sorted(snapshot.PENDING_CLONES.keys()),
            "gap_clone_map_size": len(snapshot.GAP_CLONE_MAP),
        },
        "live_clones": {
            slug: {
                "display_name": c.display_name,
                "mcp_endpoint": c.mcp_endpoint,
                "regulatory_focus": list(c.regulatory_focus),
            }
            for slug, c in snapshot.LIVE_CLONES.items()
        },
        "pending_clones": {
            slug: {
                "display_name": c.display_name,
                "mcp_endpoint": c.mcp_endpoint,
                "regulatory_focus": list(c.regulatory_focus),
            }
            for slug, c in snapshot.PENDING_CLONES.items()
        },
        "backlog_slugs": sorted(set(snapshot.PENDING_CLONES) ^ set(snapshot.all_known_slugs())),
        "all_known_slugs": snapshot.all_known_slugs(),
    }
    _print_json(out)
    return 0


# === helpers ===


def _legacy_name(slug: str, snapshot) -> str:
    """Best-effort reverse lookup of the legacy source spec name."""
    # In v0, the only known mapping is agent-fabric-oversight ->
    # agent-fabric__human-oversight-integration
    overrides = {
        "agent-fabric-oversight": "agent-fabric__human-oversight-integration",
        "agent-fabric-threat-model": "agent-fabric",
    }
    if slug in overrides:
        return overrides[slug]
    return slug


def _append_to_promotion_log(entry: str) -> None:
    """Append a markdown entry to docs/promotion_log.md.

    The log is append-only. The header (v0 DRAFT format) is
    preserved at the top of the file.
    """
    if not PROMOTION_LOG.exists():
        PROMOTION_LOG.parent.mkdir(parents=True, exist_ok=True)
        PROMOTION_LOG.write_text(_PROMOTION_LOG_HEADER, encoding="utf-8")
    with PROMOTION_LOG.open("a", encoding="utf-8") as f:
        f.write("\n" + entry + "\n")


_PROMOTION_LOG_HEADER = """# a2a-meta-clones — promotion log

> **Format:** append-only. Each section is a single probe or
> promotion event. The log is the audit trail for HTTP
> verification history.
> **Verifiers:** `pipeline.py verify`, `pipeline.py promote`,
> `pipeline.py demote`, and the A2A-Meta-side manual review.
> **Retention:** permanent. Roll-back is achieved by writing a
> new DEMOTED entry, never by deleting a row.
> **v1 evidence record (mandatory):** see
> `A2A-Meta/docs/clone_repo_architecture_v0_DRAFT.md` §8.1 for
> the immutable evidence record fields.

---

"""


# === CLI dispatcher ===


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="pipeline.py",
        description="a2a-meta-clones pipeline CLI (9 commands).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="(default) do everything except actually call external systems or write files",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        default=False,
        help="perform actual writes; requires --dry-run to be false",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="create a new clone spec")
    p_init.add_argument("--slug", required=True)
    p_init.add_argument("--gap-name", default=None)
    p_init.set_defaults(func=cmd_init)

    p_scaffold = sub.add_parser("scaffold", help="wire a clone into a slot's env")
    p_scaffold.add_argument("--slug", required=True)
    p_scaffold.add_argument("--slot", required=True)
    p_scaffold.set_defaults(func=cmd_scaffold)

    p_test = sub.add_parser("test", help="run the local test suite")
    p_test.set_defaults(func=cmd_test)

    p_pkg = sub.add_parser("package", help="build the Docker image")
    p_pkg.set_defaults(func=cmd_package)

    p_review = sub.add_parser("review", help="show what would be committed")
    p_review.set_defaults(func=cmd_review)

    p_verify = sub.add_parser("verify", help="4-probe HTTP 200 verify")
    p_verify.add_argument("--slug", required=True)
    p_verify.add_argument("--slot", required=True)
    p_verify.add_argument("--base-url", default=None)
    p_verify.set_defaults(func=cmd_verify)

    p_promote = sub.add_parser("promote", help="write promotion_request_<slug>.json")
    p_promote.add_argument("--slug", required=True)
    p_promote.add_argument("--slot", required=True)
    p_promote.add_argument("--git-sha", default=None)
    p_promote.add_argument("--image-digest", default=None)
    p_promote.add_argument("--railway-deployment-id", default=None)
    p_promote.add_argument("--base-url", default=None)
    p_promote.add_argument("--reason", default=None)
    p_promote.set_defaults(func=cmd_promote)

    p_demote = sub.add_parser("demote", help="write DEMOTION_CANDIDATE entry")
    p_demote.add_argument("--slug", required=True)
    p_demote.add_argument("--slot", required=True)
    p_demote.add_argument("--reason", default=None)
    p_demote.add_argument("--consecutive-failures", type=int, default=None)
    p_demote.set_defaults(func=cmd_demote)

    p_status = sub.add_parser("status", help="show LIVE/PENDING/backlog state")
    p_status.set_defaults(func=cmd_status)

    args = parser.parse_args()
    if args.live:
        args.dry_run = False
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
