"""Offline tests for Pay2Go Stripe checkout/webhook helpers."""
from __future__ import annotations

import hashlib
import hmac
import json
import time

import pytest

from services.shared.multiplexer import pay2go_stripe as pay2go


def test_verify_signature_ok(tmp_path, monkeypatch):
    monkeypatch.setenv("PAY2GO_STATE_DIR", str(tmp_path))
    secret = "whsec_test"
    body = b'{"id":"evt_1","type":"checkout.session.completed"}'
    t = int(time.time())
    signed = f"{t}.".encode() + body
    sig = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    header = f"t={t},v1={sig}"
    assert pay2go.verify_signature(body, header, secret) is True
    assert pay2go.verify_signature(body, "t=1,v1=dead", secret) is False


def test_resolve_price_id_fallback(monkeypatch, tmp_path):
    monkeypatch.setenv("PAY2GO_STATE_DIR", str(tmp_path))
    monkeypatch.delenv("SOLO_PRICE_ID", raising=False)
    assert pay2go.resolve_price_id("solo").startswith("price_")
    with pytest.raises(ValueError):
        pay2go.resolve_price_id("nope")


def test_handle_checkout_completed_idempotent(tmp_path, monkeypatch):
    monkeypatch.setenv("PAY2GO_STATE_DIR", str(tmp_path))
    event = {
        "id": "evt_checkout_1",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "object": "checkout.session",
                "customer": "cus_x",
                "customer_email": "buyer@example.com",
                "subscription": "sub_x",
                "metadata": {"tier": "solo"},
            }
        },
    }
    r1 = pay2go.handle_webhook_event(event)
    r2 = pay2go.handle_webhook_event(event)
    assert r1["result"] == "ok"
    assert r2["result"] == "ok_duplicate"
    ent = pay2go.get_entitlement(email="buyer@example.com")
    assert ent is not None
    assert ent["tier"] == "solo"


def test_checkout_routes_registered():
    from services.shared.multiplexer.app import app

    paths = {getattr(r, "path", None) for r in app.routes}
    assert "/api/stripe/checkout" in paths
    assert "/api/stripe/webhook" in paths
    assert "/api/stripe/team-webhook" in paths
