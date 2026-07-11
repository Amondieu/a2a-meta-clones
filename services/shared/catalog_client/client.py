"""HTTP client for the A2A-Meta catalog API.

v0: stub. Reads from the vendored snapshot. The live HTTP
client is a v1 task (gated on the preflight being GREEN; the
catalog endpoint at A2A-Meta/api/ is not yet exposed).

The catalog is the single source of truth. This client MUST
NOT mutate LIVE_CLONES — the catalog write boundary (§2.2 of
the plan) reserves that for the A2A-Meta control plane.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class CatalogEntry:
    """One entry in the catalog (LIVE or PENDING).

    Mirrors the LiveClone dataclass in the A2A-Meta catalog.
    Frozen because the snapshot is read-only.
    """

    slug: str
    display_name: str
    railway_url: str
    stripe_product_id: str
    regulatory_focus: List[str]
    mcp_manifest_path: str
    primary_service: str
    service_url: str
    promotion_state: str  # "LIVE" or "PENDING"

    @property
    def mcp_endpoint(self) -> str:
        return f"{self.railway_url.rstrip('/')}/clone/{self.slug}/mcp"

    def to_dict(self) -> Dict[str, object]:
        return {
            "slug": self.slug,
            "display_name": self.display_name,
            "railway_url": self.railway_url,
            "stripe_product_id": self.stripe_product_id,
            "regulatory_focus": list(self.regulatory_focus),
            "mcp_manifest_path": self.mcp_manifest_path,
            "primary_service": self.primary_service,
            "service_url": self.service_url,
            "mcp_endpoint": self.mcp_endpoint,
            "promotion_state": self.promotion_state,
        }


class CatalogClient:
    """Read-only client for the A2A-Meta catalog.

    v0 reads from the vendored snapshot (services/shared/catalog_client/catalog_snapshot.py).
    v1 migrates to live HTTP.
    """

    def __init__(self, snapshot_module_path: Optional[str] = None) -> None:
        if snapshot_module_path is None:
            from services.shared.catalog_client import catalog_snapshot

            self._snapshot = catalog_snapshot
        else:
            import importlib

            self._snapshot = importlib.import_module(snapshot_module_path)

    def live_clones(self) -> Dict[str, CatalogEntry]:
        """Return all LIVE clones from the snapshot."""
        result: Dict[str, CatalogEntry] = {}
        for slug, clone in self._snapshot.LIVE_CLONES.items():
            result[slug] = self._to_entry(clone, "LIVE")
        return result

    def pending_clones(self) -> Dict[str, CatalogEntry]:
        """Return all PENDING clones from the snapshot."""
        result: Dict[str, CatalogEntry] = {}
        for slug, clone in self._snapshot.PENDING_CLONES.items():
            result[slug] = self._to_entry(clone, "PENDING")
        return result

    def all_known_slugs(self) -> List[str]:
        return self._snapshot.all_known_slugs()

    def available_live_slugs(self) -> List[str]:
        return self._snapshot.available_live_slugs()

    def resolve_for_gap(self, gap_id: str) -> List[CatalogEntry]:
        result: List[CatalogEntry] = []
        for clone in self._snapshot.resolve_recommended_clones(gap_id):
            result.append(self._to_entry(clone, "LIVE"))
        return result

    def get_clone(self, slug: str) -> Optional[CatalogEntry]:
        try:
            clone = self._snapshot.get_clone(slug)
        except Exception:
            return None
        return self._to_entry(clone, "LIVE")

    @staticmethod
    def _to_entry(clone, state: str) -> CatalogEntry:
        return CatalogEntry(
            slug=clone.slug,
            display_name=clone.display_name,
            railway_url=clone.railway_url,
            stripe_product_id=clone.stripe_product_id,
            regulatory_focus=list(clone.regulatory_focus),
            mcp_manifest_path=clone.mcp_manifest_path,
            primary_service=clone.primary_service,
            service_url=clone.service_url,
            promotion_state=state,
        )
