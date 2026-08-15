"""Pay2Go Stripe rail (P1): Checkout Sessions + signed webhook intake.

No stripe SDK — urllib + stdlib HMAC (same pattern as api/services/stripe_webhook.py).
Entitlements are file-backed JSON (Railway ephemeral OK for v0; Postgres later).

Env:
  STRIPE_SECRET_KEY | STRIPE_LIVE_KEY | STRIPE_TEST_KEY
  STRIPE_MODE = test|live (default live if sk_live present else test)
  STRIPE_WEBHOOK_SECRET_LIVE | STRIPE_WEBHOOK_SECRET_TEST | STRIPE_WEBHOOK_SECRET
  SOLO_PRICE_ID | PRO_PRICE_ID | TEAM_PRICE_ID | EARLY_ACCESS_PRICE_ID
  PUBLIC_BASE_URL (optional; default production clones URL)
  PAY2GO_STATE_DIR (optional; default /tmp/a2a-pay2go)
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger("gold-seed.pay2go_stripe")

DEFAULT_TOLERANCE_SECONDS = 300
ALLOWLISTED_EVENTS = frozenset(
    {
        "checkout.session.completed",
        "customer.subscription.created",
        "customer.subscription.updated",
        "customer.subscription.deleted",
        "invoice.payment_failed",
    }
)

DEFAULT_PUBLIC_BASE = "https://a2a-meta-clones-production.up.railway.app"

TIER_ENV = {
    "solo": ("SOLO_PRICE_ID",),
    "pro": ("PRO_PRICE_ID", "EARLY_ACCESS_PRICE_ID"),
    "team": ("TEAM_PRICE_ID",),
}

# Fallback to known LIVE ids if Infisical not yet synced into Railway
TIER_FALLBACK_PRICE = {
    "solo": "price_1U4fJxGpyUjJ8qvea7BUGNKH",
    "pro": "price_1U4fJxGpyUjJ8qvecos5yTMV",
    "team": "price_1U4dWxGpyUjJ8qveBgYFkG5y",
}


def verify_signature(
    raw_body: bytes,
    sig_header: Optional[str],
    secret: str,
    *,
    now_epoch: Optional[int] = None,
    tolerance: int = DEFAULT_TOLERANCE_SECONDS,
) -> bool:
    if not sig_header or not secret:
        return False
    parts: Dict[str, List[str]] = {}
    for chunk in sig_header.split(","):
        if "=" not in chunk:
            continue
        k, v = chunk.split("=", 1)
        parts.setdefault(k.strip(), []).append(v.strip())
    t_vals, v1_vals = parts.get("t"), parts.get("v1")
    if not t_vals or not v1_vals:
        return False
    try:
        t = int(t_vals[0])
    except ValueError:
        return False
    now = now_epoch if now_epoch is not None else int(time.time())
    if abs(now - t) > tolerance:
        return False
    signed = f"{t}.".encode("utf-8") + raw_body
    expected = hmac.new(secret.encode("utf-8"), signed, hashlib.sha256).hexdigest()
    return any(hmac.compare_digest(expected, cand) for cand in v1_vals)


def stripe_mode() -> str:
    mode = (os.environ.get("STRIPE_MODE") or "").strip().lower()
    if mode in ("test", "live"):
        return mode
    key = _stripe_secret_key()
    if key.startswith("sk_live_"):
        return "live"
    return "test"


def _stripe_secret_key() -> str:
    mode_hint = (os.environ.get("STRIPE_MODE") or "").strip().lower()
    if mode_hint == "test":
        return (
            os.environ.get("STRIPE_TEST_KEY")
            or os.environ.get("STRIPE_SECRET_KEY")
            or ""
        ).strip()
    return (
        os.environ.get("STRIPE_SECRET_KEY")
        or os.environ.get("STRIPE_LIVE_KEY")
        or os.environ.get("STRIPE_TEST_KEY")
        or ""
    ).strip()


def webhook_secret() -> str:
    if stripe_mode() == "live":
        return (
            os.environ.get("STRIPE_WEBHOOK_SECRET_LIVE")
            or os.environ.get("STRIPE_WEBHOOK_SECRET")
            or ""
        ).strip()
    return (
        os.environ.get("STRIPE_WEBHOOK_SECRET_TEST")
        or os.environ.get("STRIPE_WEBHOOK_SECRET")
        or ""
    ).strip()


def public_base_url() -> str:
    explicit = (os.environ.get("PUBLIC_BASE_URL") or "").strip().rstrip("/")
    if explicit:
        return explicit
    domain = (os.environ.get("RAILWAY_PUBLIC_DOMAIN") or "").strip()
    if domain:
        return f"https://{domain}"
    return DEFAULT_PUBLIC_BASE


def resolve_price_id(tier: str) -> str:
    tier = tier.strip().lower()
    if tier not in TIER_ENV:
        raise ValueError(f"unknown tier {tier!r}; use solo|pro|team")
    for env_name in TIER_ENV[tier]:
        val = (os.environ.get(env_name) or "").strip()
        if val.startswith("price_"):
            return val
    fb = TIER_FALLBACK_PRICE.get(tier)
    if fb:
        return fb
    raise ValueError(f"no Stripe price id configured for tier={tier}")


def _state_dir() -> Path:
    root = Path(os.environ.get("PAY2GO_STATE_DIR") or "/tmp/a2a-pay2go")
    root.mkdir(parents=True, exist_ok=True)
    return root


def _load_json(path: Path, default: Any) -> Any:
    if not path.is_file():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _atomic_write(path: Path, data: Any) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(tmp, path)


def _stripe_form(path: str, fields: Dict[str, str]) -> Dict[str, Any]:
    key = _stripe_secret_key()
    if not key.startswith("sk_"):
        raise RuntimeError("STRIPE_SECRET_KEY / STRIPE_TEST_KEY not configured")
    body = urllib.parse.urlencode(fields).encode("utf-8")
    auth = base64.b64encode(f"{key}:".encode()).decode()
    req = urllib.request.Request(
        f"https://api.stripe.com/v1/{path}",
        data=body,
        headers={
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Stripe HTTP {e.code}: {detail}") from e


def create_checkout_session(
    tier: str,
    *,
    customer_email: Optional[str] = None,
    success_url: Optional[str] = None,
    cancel_url: Optional[str] = None,
    client_reference_id: Optional[str] = None,
) -> Dict[str, Any]:
    price_id = resolve_price_id(tier)
    base = public_base_url()
    success = success_url or f"{base}/static/audit-bazaar.html?checkout=success&tier={tier}"
    cancel = cancel_url or f"{base}/static/audit-bazaar.html?checkout=cancel&tier={tier}"
    fields: Dict[str, str] = {
        "mode": "subscription",
        "success_url": success,
        "cancel_url": cancel,
        "line_items[0][price]": price_id,
        "line_items[0][quantity]": "1",
        "allow_promotion_codes": "true",
        "metadata[tier]": tier.lower(),
        "metadata[service]": "audit-bazaar",
        "subscription_data[metadata][tier]": tier.lower(),
        "subscription_data[metadata][service]": "audit-bazaar",
    }
    if customer_email:
        fields["customer_email"] = customer_email
    if client_reference_id:
        fields["client_reference_id"] = client_reference_id
    session = _stripe_form("checkout/sessions", fields)
    return {
        "id": session.get("id"),
        "url": session.get("url"),
        "tier": tier.lower(),
        "price_id": price_id,
        "mode": stripe_mode(),
    }


def record_entitlement(
    *,
    customer_id: Optional[str],
    email: Optional[str],
    tier: str,
    subscription_id: Optional[str],
    event_id: str,
    status: str = "active",
) -> None:
    path = _state_dir() / "entitlements.json"
    data = _load_json(path, {"by_customer": {}, "by_email": {}, "events": []})
    entry = {
        "tier": tier,
        "status": status,
        "subscription_id": subscription_id,
        "customer_id": customer_id,
        "email": email,
        "updated_at": int(time.time()),
        "last_event_id": event_id,
    }
    if customer_id:
        data["by_customer"][customer_id] = entry
    if email:
        data["by_email"][email.lower()] = entry
    data["events"] = ([{"event_id": event_id, "ts": int(time.time()), "tier": tier}] + data.get("events", []))[
        :200
    ]
    _atomic_write(path, data)


def claim_event(event_id: str) -> bool:
    """Return True if this is the first time we see event_id (claim)."""
    path = _state_dir() / "processed_events.json"
    data = _load_json(path, {"ids": []})
    ids: List[str] = list(data.get("ids") or [])
    if event_id in ids:
        return False
    ids.insert(0, event_id)
    data["ids"] = ids[:5000]
    _atomic_write(path, data)
    return True


def _tier_from_obj(obj: Dict[str, Any]) -> str:
    md = obj.get("metadata") or {}
    tier = (md.get("tier") or "").strip().lower()
    if tier in TIER_ENV:
        return tier
    # Match price id
    price = None
    if obj.get("object") == "checkout.session":
        # line items not expanded — use metadata only; fallback pro
        return tier if tier in TIER_ENV else "pro"
    items = ((obj.get("items") or {}).get("data")) or []
    if items:
        price = ((items[0].get("price") or {}).get("id")) or None
    if isinstance(price, str):
        for t, envs in TIER_ENV.items():
            for e in envs:
                if os.environ.get(e) == price:
                    return t
            if TIER_FALLBACK_PRICE.get(t) == price:
                return t
    return "pro"


def handle_webhook_event(event: Dict[str, Any]) -> Dict[str, Any]:
    etype = event.get("type") or ""
    eid = event.get("id") or ""
    if etype not in ALLOWLISTED_EVENTS:
        return {"result": "ignored_unallowlisted", "type": etype}
    if not eid or not claim_event(eid):
        return {"result": "ok_duplicate", "type": etype, "event_id": eid}

    obj = (event.get("data") or {}).get("object") or {}
    if etype == "checkout.session.completed":
        tier = _tier_from_obj(obj)
        record_entitlement(
            customer_id=obj.get("customer"),
            email=obj.get("customer_details", {}).get("email")
            or obj.get("customer_email"),
            tier=tier,
            subscription_id=obj.get("subscription"),
            event_id=eid,
            status="active",
        )
        return {"result": "ok", "type": etype, "tier": tier, "event_id": eid}

    if etype == "customer.subscription.created":
        tier = _tier_from_obj(obj)
        record_entitlement(
            customer_id=obj.get("customer"),
            email=None,
            tier=tier,
            subscription_id=obj.get("id"),
            event_id=eid,
            status=obj.get("status") or "active",
        )
        return {"result": "ok", "type": etype, "tier": tier, "event_id": eid}

    if etype == "customer.subscription.updated":
        tier = _tier_from_obj(obj)
        record_entitlement(
            customer_id=obj.get("customer"),
            email=None,
            tier=tier,
            subscription_id=obj.get("id"),
            event_id=eid,
            status=obj.get("status") or "active",
        )
        return {"result": "ok", "type": etype, "tier": tier, "event_id": eid}

    if etype == "customer.subscription.deleted":
        tier = _tier_from_obj(obj)
        record_entitlement(
            customer_id=obj.get("customer"),
            email=None,
            tier=tier,
            subscription_id=obj.get("id"),
            event_id=eid,
            status="canceled",
        )
        return {"result": "ok", "type": etype, "tier": tier, "event_id": eid}

    if etype == "invoice.payment_failed":
        return {"result": "recorded_for_dunning_review", "type": etype, "event_id": eid}

    return {"result": "ignored_unallowlisted", "type": etype}


def get_entitlement(
    *, customer_id: Optional[str] = None, email: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    data = _load_json(_state_dir() / "entitlements.json", {"by_customer": {}, "by_email": {}})
    if customer_id and customer_id in data.get("by_customer", {}):
        return data["by_customer"][customer_id]
    if email and email.lower() in data.get("by_email", {}):
        return data["by_email"][email.lower()]
    return None


def agent_key_lookup(agent_key: str) -> Optional[Dict[str, Any]]:
    """MPP stub: map X-Agent-Key → entitlement via PAY2GO_AGENT_KEYS JSON env.

    Format: {"wlt_xxx": {"customer_id": "cus_...", "email": "a@b.c"}}
    """
    raw = (os.environ.get("PAY2GO_AGENT_KEYS") or "").strip()
    if not raw or not agent_key:
        return None
    try:
        mapping = json.loads(raw)
    except json.JSONDecodeError:
        return None
    entry = mapping.get(agent_key)
    if not isinstance(entry, dict):
        return None
    return get_entitlement(
        customer_id=entry.get("customer_id"), email=entry.get("email")
    )
