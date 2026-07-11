"""tests/test_catalog_client.py — smoke tests for the catalog client."""
from __future__ import annotations

from services.shared.catalog_client.client import CatalogClient, CatalogEntry


def test_catalog_client_live_clones_is_empty(catalog_snapshot):
    """At Phase A, LIVE_CLONES is empty (no verified clones yet)."""
    client = CatalogClient()
    assert client.live_clones() == {}


def test_catalog_client_pending_clones_has_5(catalog_snapshot):
    """At Phase A, PENDING_CLONES has 5 entries (5 catalogued clones)."""
    client = CatalogClient()
    pending = client.pending_clones()
    assert len(pending) == 5
    assert set(pending.keys()) == {
        "agent-lens",
        "audit-bazaar",
        "agent-fabric-oversight",
        "agent-ledger",
        "compliance-lens",
    }


def test_catalog_entry_mcp_endpoint_format():
    """CatalogEntry.mcp_endpoint is railway_url + /clone/<slug>/mcp."""
    entry = CatalogEntry(
        slug="x",
        display_name="X",
        railway_url="https://example.com/",
        stripe_product_id="prod_x",
        regulatory_focus=[],
        mcp_manifest_path="x.json",
        primary_service="service-x",
        service_url="https://example.com",
        promotion_state="PENDING",
    )
    # Trailing slash is stripped
    assert entry.mcp_endpoint == "https://example.com/clone/x/mcp"
