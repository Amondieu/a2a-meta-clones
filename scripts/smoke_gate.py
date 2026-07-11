"""scripts/smoke_gate.py — a2a-meta-clones smoke gate (8 BLOCKED checks).

Port of A2A-Meta/scripts/smoke_gate.py with the same 8 checks
but adapted for the a2a-meta-clones surface. --dry-run is the
default; it performs no network calls and produces 8/8 BLOCKED
with exact prerequisites.

Live mode is not implemented in this offline harness; the
A2A-Meta Opus build (per A2A-Meta/docs/opus_build_prompt_v1.md)
is the only place that runs live probes once the preflight
gate is GREEN.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

# === Required environment variables (mirrors A2A-Meta) ===

REQUIRED_VARS: Dict[str, str] = {
    "DATABASE_URL": "Postgres connection string (Railway, NOT localhost/litellm)",
    "REDIS_URL": "Redis for rate limit + dedupe + queue state",
    "RESEND_API_KEY": "Resend transactional + marketing email",
    "EMAIL_FROM": "From address, e.g. 'Aug 2 Readiness <no-reply@a2a-meta.dev>'",
    "PUBLIC_BASE_URL": "Public URL of the assessment site",
    "PRIVACY_URL": "Full URL of PRIVACY.md",
    "UNSUBSCRIBE_BASE_URL": "Base URL for unsubscribe tokens",
    "UNSUBSCRIBE_SECRET": "HMAC secret for unsubscribe token signing",
    "STRIPE_SECRET_KEY": "Stripe API key (live or test per ASSESSMENT_WEBHOOK_ENABLED)",
    "STRIPE_WEBHOOK_SECRET": "Stripe webhook signing secret",
    "TEAM_PRICE_ID": "Stripe price_... for the €249/mo Team plan",
}


# === Check model ===

@dataclass
class CheckResult:
    number: int
    title: str
    status: str  # 'BLOCKED' | 'PASS' | 'FAIL' | 'SKIP'
    prereq: str
    detail: str = ""


@dataclass
class GateResult:
    mode: str
    fable5_unlocked: bool
    checks: List[CheckResult] = field(default_factory=list)
    env: Dict[str, bool] = field(default_factory=dict)
    catalog_state: Dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(
            {
                "mode": self.mode,
                "fable5_unlocked": self.fable5_unlocked,
                "checks": [
                    {
                        "number": c.number,
                        "title": c.title,
                        "status": c.status,
                        "prereq": c.prereq,
                        "detail": c.detail,
                    }
                    for c in self.checks
                ],
                "env": self.env,
                "catalog_state": self.catalog_state,
            },
            indent=2,
            sort_keys=False,
        )


# === Check definitions (mirrors A2A-Meta) ===

def _env_check() -> Tuple[Dict[str, bool], List[str]]:
    presence: Dict[str, bool] = {}
    missing: List[str] = []
    for var in REQUIRED_VARS:
        present = bool(os.environ.get(var))
        presence[var] = present
        if not present:
            missing.append(var)
    return presence, missing


def _check_1_postgres(env):
    if not env.get("DATABASE_URL"):
        return CheckResult(
            1, "Postgres reachable from API service", "BLOCKED",
            "DATABASE_URL must be set in env and the value must be the new Railway Postgres URL (NOT postgresql://localhost:5432/litellm).",
        )
    return CheckResult(1, "Postgres reachable from API service", "BLOCKED",
                       "Manual: `psql $DATABASE_URL -c 'SELECT 1;'` against the new A2A-Meta Railway Postgres.")


def _check_2_resend(env):
    missing = [v for v in ("RESEND_API_KEY", "EMAIL_FROM") if not env.get(v)]
    if missing:
        return CheckResult(
            2, "Resend send-email probe", "BLOCKED",
            f"Set env vars: {', '.join(missing)}.",
        )
    return CheckResult(2, "Resend send-email probe", "BLOCKED",
                       "Manual: trigger a test send.")


def _check_3_public_url(env):
    missing = [v for v in ("PUBLIC_BASE_URL", "PRIVACY_URL",
                            "UNSUBSCRIBE_BASE_URL", "UNSUBSCRIBE_SECRET") if not env.get(v)]
    if missing:
        return CheckResult(
            3, "Public URL + privacy + unsubscribe config", "BLOCKED",
            f"Set env vars: {', '.join(missing)}.",
        )
    return CheckResult(3, "Public URL + privacy + unsubscribe config", "BLOCKED",
                       "Manual: inspect a test capture response for the URL fields.")


def _check_4_clone_availability(env):
    # Read the vendored catalog snapshot
    try:
        snapshot = _load_vendored_snapshot()
        if not snapshot.LIVE_CLONES:
            return CheckResult(
                4, "Live clone catalog (5 verified endpoints)", "BLOCKED",
                "LIVE_CLONES is empty. The 5 catalogued clones are in PENDING_CLONES. Each must pass a fresh timestamped HTTP 200 probe of /, /health, /.well-known/mcp-server, and POST /clone/{slug}/mcp (initialize). After all 5 pass, promote them in A2A-Meta/api/middleware/live_clone_catalog.py and record the verification in docs/infra_status.md.",
            )
    except Exception as e:
        return CheckResult(4, "Live clone catalog (5 verified endpoints)", "BLOCKED",
                           f"Could not load catalog snapshot: {e}")

    return CheckResult(4, "Live clone catalog (5 verified endpoints)", "BLOCKED",
                       "Manual: re-run preflight HTTP probes for all 5 clones; ensure each returns 200.")


def _load_vendored_snapshot():
    """Load the vendored catalog snapshot (handles @dataclass(frozen=True)
    which requires the module to be in sys.modules before exec_module)."""
    snapshot_path = Path(__file__).resolve().parent.parent / "services" / "shared" / "catalog_client" / "catalog_snapshot.py"
    spec = importlib.util.spec_from_file_location("catalog_snapshot", snapshot_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["catalog_snapshot"] = mod
    spec.loader.exec_module(mod)
    return mod


def _check_5_capture_endpoint(env):
    if not env.get("DATABASE_URL"):
        return CheckResult(
            5, "POST /api/assessment-capture returns 201 with real data", "BLOCKED",
            "Requires DATABASE_URL reachable AND at least 1 clone in LIVE_CLONES. The Aug 2 capture endpoint does not exist yet; it is part of the A2A-Meta Opus build.",
        )
    return CheckResult(5, "POST /api/assessment-capture returns 201 with real data", "BLOCKED",
                       "Manual: the Aug 2 capture endpoint is built in the A2A-Meta Opus build (gated on this preflight).")


def _check_6_stripe_webhook(env):
    missing = [v for v in ("STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET",
                            "TEAM_PRICE_ID") if not env.get(v)]
    if missing:
        return CheckResult(
            6, "Stripe Team webhook signature + entitlement flow", "BLOCKED",
            f"Set env vars: {', '.join(missing)}.",
        )
    return CheckResult(6, "Stripe Team webhook signature + entitlement flow", "BLOCKED",
                       "Manual: use `stripe trigger checkout.session.completed` against the webhook endpoint.")


def _check_7_unsubscribe_flow(env):
    if not env.get("UNSUBSCRIBE_SECRET"):
        return CheckResult(
            7, "POST /api/assessment-unsubscribe idempotency", "BLOCKED",
            "UNSUBSCRIBE_SECRET must be set.",
        )
    return CheckResult(7, "POST /api/assessment-unsubscribe idempotency", "BLOCKED",
                       "Manual: POST with a known token, then POST again — second is 204.")


def _check_8_runlog(env):
    return CheckResult(
        8, "docs/aug2_opus_spec.md §11 run log filled in", "BLOCKED",
        "After checks 1-7 PASS, fill in the §11 table with PASS/FAIL + timestamp + assessment_id for each row. Fable 5 gate opens only when all 8 rows are PASS.",
    )


CHECKS = [
    _check_1_postgres, _check_2_resend, _check_3_public_url,
    _check_4_clone_availability, _check_5_capture_endpoint,
    _check_6_stripe_webhook, _check_7_unsubscribe_flow, _check_8_runlog,
]

# === Mode dispatch ===

def run_dry_run() -> GateResult:
    env, _ = _env_check()
    # Try to load the catalog snapshot
    catalog_state = {
        "live_clones_count": 0,
        "pending_clones_count": 0,
        "pending_slugs": [],
        "gap_clone_map_size": 0,
    }
    try:
        mod = _load_vendored_snapshot()
        catalog_state = {
            "live_clones_count": len(mod.LIVE_CLONES),
            "pending_clones_count": len(mod.PENDING_CLONES),
            "pending_slugs": sorted(mod.PENDING_CLONES.keys()),
            "gap_clone_map_size": len(mod.GAP_CLONE_MAP),
        }
    except Exception as e:
        catalog_state["error"] = f"could not load catalog snapshot: {e}"

    result = GateResult(
        mode="dry-run",
        fable5_unlocked=False,
        env=env,
        catalog_state=catalog_state,
    )
    for check_fn in CHECKS:
        result.checks.append(check_fn(env))
    return result


def run_live():
    raise SystemExit(
        "ERROR: --live mode is not implemented in this offline harness. "
        "Live mode is the A2A-Meta Opus build's responsibility once the "
        "preflight gate is GREEN."
    )


# === Output rendering ===

def render_table(result: GateResult) -> str:
    lines = []
    lines.append(f"Smoke gate ({result.mode}) — Fable 5 unlocked: {result.fable5_unlocked}")
    lines.append("")
    lines.append(f"Catalog state: LIVE={result.catalog_state.get('live_clones_count', 0)} "
                 f"PENDING={result.catalog_state.get('pending_clones_count', 0)} "
                 f"GAPS={result.catalog_state.get('gap_clone_map_size', 0)}")
    lines.append("")
    lines.append("Checks:")
    lines.append(f"  {'#':<3} {'Status':<8} Title")
    lines.append(f"  {'-'*3} {'-'*8} {'-'*60}")
    for c in result.checks:
        lines.append(f"  {c.number:<3} {c.status:<8} {c.title}")
    lines.append("")
    lines.append("Env vars (presence only, never values):")
    for var, present in sorted(result.env.items()):
        marker = "[x]" if present else "[ ]"
        lines.append(f"  {marker} {var}")
    lines.append("")
    for c in result.checks:
        if c.detail:
            lines.append(f"  [{c.number}] {c.detail}")
    return "\n".join(lines)


# === CLI ===

def main() -> int:
    from pathlib import Path
    parser = argparse.ArgumentParser(
        description="a2a-meta-clones smoke gate (8/8 BLOCKED in --dry-run).",
    )
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--live", action="store_true", default=False)
    parser.add_argument("--json-out", default=None)
    parser.add_argument("--table-out", default=None)
    args = parser.parse_args()

    if args.live:
        result = run_live()
    else:
        result = run_dry_run()

    json_blob = result.to_json()
    table_blob = render_table(result)

    if args.json_out:
        Path(args.json_out).write_text(json_blob, encoding="utf-8")
    else:
        print(json_blob)

    if args.table_out:
        Path(args.table_out).write_text(table_blob, encoding="utf-8")
    else:
        print(table_blob, file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
