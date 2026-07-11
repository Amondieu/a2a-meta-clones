"""api/middleware/live_clone_catalog.py — server-side authority for live clones.

The Aug 2 assessment funnel (and any future tool that emits clone references)
MUST consult this catalog before sending an email, report, Stripe CTA, or
MCP link. The browser-side CLONES object in the assessment HTML is
presentation; THIS file is the source of truth.

Catalog state (a2a-meta-070, post v1 PATCH):
  LIVE_CLONES     — only entries with a timestamped, HTTP-verified endpoint.
                    Empty until the user provisions real infrastructure and
                    each clone passes /, /health, /.well-known/mcp-server,
                    /clone/{slug}/mcp (POST initialize) HTTP 200 probes.
  PENDING_CLONES  — entries known to the catalog (per clone_specs/*.json and
                    deploy_state_v2.json) but not yet HTTP-verified. Excluded
                    from every recommendation, capture, email, and Stripe path.

This is a Phase A snapshot. It is a one-way copy of the A2A-Meta source
(api/middleware/live_clone_catalog.py) with the v1 PATCH slug split
applied. The user mutates A2A-Meta's source to match this snapshot in
Phase D; sync_catalog.py is the re-sync path.

v1 PATCH (applied here, not yet in A2A-Meta's source):
  - agent-fabric (bare) split into:
      * agent-fabric-oversight  (canonical, EU AI Act human oversight)
      * agent-fabric-threat-model (reserved backlog, MCP threat modeling)
  - legacy_source_spec_name="agent-fabric__human-oversight-integration"
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class LiveClone:
    """Canonical record for a live A2A-Meta clone.

    Frozen because LIVE_CLONES entries are by definition HTTP-verified and
    must not mutate at runtime. PENDING_CLONES entries are mutable via
    `with_*` factories below.
    """

    slug: str
    display_name: str
    railway_url: str
    stripe_product_id: str
    regulatory_focus: List[str]
    mcp_manifest_path: str
    primary_service: str
    service_url: str
    legacy_source_spec_name: Optional[str] = None  # v1 PATCH: original filename for traceability

    def __post_init__(self) -> None:
        # Normalize trailing slashes (frozen dataclass: use object.__setattr__).
        object.__setattr__(self, "railway_url", self.railway_url.rstrip("/"))
        object.__setattr__(self, "service_url", self.service_url.rstrip("/"))

    @property
    def mcp_endpoint(self) -> str:
        return f"{self.railway_url}/clone/{self.slug}/mcp"

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
            "legacy_source_spec_name": self.legacy_source_spec_name,
        }


# CANONICAL LIVE CLONE CATALOG — verified only
# ----------------------------------------------------------------------
# Every entry here MUST have: live Railway URL + Stripe product ID +
# MCP manifest + a timestamped HTTP 200 probe recorded in docs/infra_status.md.
# Promotion from PENDING_CLONES is a code change, not a runtime mutation.
#
# Phase A state (2026-07-11, a2a-meta-070 + v1 PATCH): empty. The 5
# catalogued clones (agent-fabric-oversight, agent-ledger, audit-bazaar,
# agent-lens, compliance-lens) are in PENDING_CLONES. Until the user
# provisions the dedicated A2A-Meta Postgres, the 8 missing env vars,
# and 5 HTTP-verified endpoints, `available_live_slugs()` returns [].
LIVE_CLONES: Dict[str, LiveClone] = {}


# PENDING_CLONES — deployed/known but not yet HTTP-verified
# ----------------------------------------------------------------------
# Excluded from every recommendation, capture, email, and Stripe path.
# A test asserts that resolve_recommended_clones() never surfaces a
# PENDING_CLONES slug, even if the frontend payload contains it.
#
# Sources of these entries:
#   - clone_specs/*.json (PromptGenerator/research/examples/clone_specs/)
#   - deploy_state_v2.json (PromptGenerator/research/examples/)
#   - server_manifests/*/server.json (10 manifests with §0.9 metadata)
#
# v1 PATCH: agent-fabric (bare) is split into:
#   - agent-fabric-oversight  (in PENDING_CLONES; canonical EU AI Act clone)
#   - agent-fabric-threat-model (in BACKLOG, NOT in PENDING_CLONES;
#     reserved for separate promotion via the same promotion contract)
PENDING_CLONES: Dict[str, LiveClone] = {
    "agent-fabric-oversight": LiveClone(
        slug="agent-fabric-oversight",
        display_name="Agent Fabric (Oversight)",
        # legacy_source_spec_name records the original filename for traceability
        legacy_source_spec_name="agent-fabric__human-oversight-integration",
        railway_url="https://service-c-production.up.railway.app",
        stripe_product_id="prod_Urd5xIglJAwvk8",  # service-c/agent-fabric (EU AI Act)
        regulatory_focus=["EU AI Act"],
        mcp_manifest_path="clone_specs/agent-fabric__human-oversight-integration.json",
        primary_service="service-c",
        service_url="https://service-c-production.up.railway.app",
    ),
    "agent-lens": LiveClone(
        slug="agent-lens",
        display_name="Agent Lens",
        legacy_source_spec_name="agent-lens",
        railway_url="https://service-a-production-9303.up.railway.app",
        stripe_product_id="prod_Urd5zf6oLeOqOL",
        regulatory_focus=["NIST AI RMF"],
        mcp_manifest_path="clone_specs/agent-lens.json",
        primary_service="service-a",
        service_url="https://service-a-production-9303.up.railway.app",
    ),
    "audit-bazaar": LiveClone(
        slug="audit-bazaar",
        display_name="Audit Bazaar",
        legacy_source_spec_name="audit-bazaar",
        railway_url="https://service-a-production-9303.up.railway.app",
        stripe_product_id="prod_Urd5dOMlFZ5yvg",
        regulatory_focus=["SOC 2"],
        mcp_manifest_path="clone_specs/audit-bazaar.json",
        primary_service="service-a",
        service_url="https://service-a-production-9303.up.railway.app",
    ),
    "agent-ledger": LiveClone(
        slug="agent-ledger",
        display_name="Agent Ledger",
        legacy_source_spec_name="agent-ledger",
        railway_url="https://service-c-production.up.railway.app",
        stripe_product_id="prod_Urd5I0snDVnaR8",
        regulatory_focus=["NIST AI RMF"],
        mcp_manifest_path="clone_specs/agent-ledger.json",
        primary_service="service-c",
        service_url="https://service-c-production.up.railway.app",
    ),
    "compliance-lens": LiveClone(
        slug="compliance-lens",
        display_name="Compliance Lens",
        legacy_source_spec_name="compliance-lens",
        railway_url="https://service-c-production.up.railway.app",
        stripe_product_id="prod_Urd5kHvd7Fn9sA",
        regulatory_focus=["NIST AI RMF", "ISO 42001", "SOC 2"],
        mcp_manifest_path="clone_specs/compliance-lens.json",
        primary_service="service-c",
        service_url="https://service-c-production.up.railway.app",
    ),
}


# BACKLOG — 5 clones with valid specs/manifests but not in PENDING_CLONES.
# Per the v1 PATCH backlog register (architecture §10), these are
# real, full-spec clones that have no deployment slot and no
# recommendation rights. They do not appear in assessment, MCP
# discovery, Stripe products, payment links, or nurture email.
#
# Phase A: documented here so the child repo's tests can verify
# the 5+5 split (5 PENDING_CLONES + 5 BACKLOG).
BACKLOG_CLONES: Dict[str, LiveClone] = {
    "agent-catalog": LiveClone(
        slug="agent-catalog",
        display_name="Agent Catalog",
        legacy_source_spec_name="agent-catalog",
        railway_url="https://service-d-production.up.railway.app",  # placeholder
        stripe_product_id="",
        regulatory_focus=["EU AI Act"],
        mcp_manifest_path="clone_specs/agent-catalog.json",
        primary_service="service-d",  # service-d not yet provisioned
        service_url="",
    ),
    "agent-fabric-threat-model": LiveClone(
        slug="agent-fabric-threat-model",
        display_name="Agent Fabric (Threat Model)",
        legacy_source_spec_name="agent-fabric",
        railway_url="https://service-b-production-3133.up.railway.app",
        stripe_product_id="",
        regulatory_focus=["NIST AI RMF"],
        mcp_manifest_path="clone_specs/agent-fabric.json",
        primary_service="service-b",
        service_url="",
    ),
    "agent-vault": LiveClone(
        slug="agent-vault",
        display_name="Agent Vault",
        legacy_source_spec_name="agent-vault",
        railway_url="https://service-b-production-3133.up.railway.app",
        stripe_product_id="",
        regulatory_focus=["ISO 42001"],
        mcp_manifest_path="clone_specs/agent-vault.json",
        primary_service="service-b",
        service_url="",
    ),
    "audit-workbench": LiveClone(
        slug="audit-workbench",
        display_name="Audit Workbench",
        legacy_source_spec_name="audit-workbench",
        railway_url="https://service-a-production-9303.up.railway.app",
        stripe_product_id="",
        regulatory_focus=["EU AI Act", "ISO 42001", "SOC 2"],
        mcp_manifest_path="clone_specs/audit-workbench.json",
        primary_service="service-a",
        service_url="",
    ),
    "policy-hub": LiveClone(
        slug="policy-hub",
        display_name="Policy Hub",
        legacy_source_spec_name="policy-hub",
        railway_url="https://service-b-production-3133.up.railway.app",
        stripe_product_id="",
        regulatory_focus=["NIST AI RMF", "ISO 42001"],
        mcp_manifest_path="clone_specs/policy-hub.json",
        primary_service="service-b",
        service_url="",
    ),
}


def available_live_slugs() -> List[str]:
    """Return only the slugs that are currently HTTP-verified (LIVE_CLONES).

    Use this in the capture endpoint and nurture service. Until a
    PENDING_CLONES entry is promoted to LIVE_CLONES with a timestamped
    HTTP 200 probe, the recommended_clones emitted to leads MUST
    exclude that clone.
    """
    return sorted(LIVE_CLONES.keys())


def all_known_slugs() -> List[str]:
    """Return all known slugs (live + pending + backlog), for diagnostics."""
    return sorted(set(LIVE_CLONES) | set(PENDING_CLONES) | set(BACKLOG_CLONES))


def backlog_slugs() -> List[str]:
    """Return the 5 backlog slugs (NOT in PENDING_CLONES, no slot)."""
    return sorted(BACKLOG_CLONES.keys())


# Canonical gap → recommended-clones map.
# Mirrors the GAP_CATALOG clone arrays in the assessment HTML.
# v1 PATCH: uses agent-fabric-oversight (not the bare agent-fabric).
GAP_CLONE_MAP: Dict[str, List[str]] = {
    "technical_documentation": ["agent-fabric-oversight"],
    "human_oversight": ["agent-fabric-oversight"],
    "interrupt_mechanism": ["agent-fabric-oversight"],
    "logging": ["audit-bazaar", "agent-fabric-oversight"],
    "risk_assessment": ["agent-lens", "compliance-lens"],
    "data_governance": ["agent-ledger"],
    "vendor_chain": ["audit-bazaar"],
}


class UnknownCloneError(ValueError):
    """Raised when an assessment references a slug not in LIVE_CLONES.

    Includes the PENDING_CLONES case: a clone that exists in the catalog
    source but has not been HTTP-verified yet. PENDING_CLONES is
    deliberately excluded from every recommendation path.
    """


def is_live(slug: str) -> bool:
    """True if `slug` is in LIVE_CLONES (HTTP-verified)."""
    return slug in LIVE_CLONES


def is_pending(slug: str) -> bool:
    """True if `slug` is in PENDING_CLONES (deployed but unverified)."""
    return slug in PENDING_CLONES


def is_backlog(slug: str) -> bool:
    """True if `slug` is in BACKLOG_CLONES (no slot, not yet promoted)."""
    return slug in BACKLOG_CLONES


def get_clone(slug: str) -> LiveClone:
    """Return the LiveClone for `slug`, or raise UnknownCloneError.

    Only LIVE_CLONES is consulted by this function. PENDING_CLONES
    and BACKLOG_CLONES are treated as unknown/stale from the
    perspective of any runtime path.
    """
    if slug not in LIVE_CLONES:
        raise UnknownCloneError(
            f"clone slug {slug!r} is not in LIVE_CLONES. "
            f"Live slugs: {sorted(LIVE_CLONES)}. "
            f"Pending slugs (excluded): {sorted(PENDING_CLONES)}. "
            f"Backlog slugs (excluded): {sorted(BACKLOG_CLONES)}. "
            f"Update LIVE_CLONES (with a fresh HTTP 200 verification) "
            f"or reject the assessment."
        )
    return LIVE_CLONES[slug]


def resolve_recommended_clones(
    gap_id: str,
    max_results: int = 2,
) -> List[LiveClone]:
    """Server-side authority for 'what clones should we recommend for this gap?'

    The frontend is NOT consulted. This function regenerates from
    GAP_CLONE_MAP[gap_id] ∩ LIVE_CLONES. PENDING_CLONES, unknown, and
    stale entries are silently dropped. Any gap_id not in GAP_CLONE_MAP
    returns [].

    Per docs/aug2_opus_spec.md §4.1 step 6: the frontend's
    `recommended_clones[]` is never trusted; the server regenerates
    from canonical gap_ids.
    """
    if gap_id not in GAP_CLONE_MAP:
        return []
    candidates = GAP_CLONE_MAP[gap_id]
    resolved = [LIVE_CLONES[s] for s in candidates if s in LIVE_CLONES]
    return resolved[:max_results]


def validate_frontend_clones(frontend_slugs: List[str]) -> List[str]:
    """Canonicalize a frontend-supplied slug list against LIVE_CLONES.

    Used to reject any frontend payload containing fictional, stale,
    or PENDING_CLONES slugs. The capture endpoint MUST call this on
    any frontend-supplied `recommended_clones[]` and treat the result
    as advisory only — the canonical response is regenerated by
    `resolve_recommended_clones(gap_id)`.
    """
    canonical: List[str] = []
    for slug in frontend_slugs:
        if slug not in LIVE_CLONES:
            raise UnknownCloneError(
                f"frontend-supplied slug {slug!r} is not in LIVE_CLONES. "
                f"Live slugs: {sorted(LIVE_CLONES)}. "
                f"Pending slugs (excluded by design): {sorted(PENDING_CLONES)}. "
                f"Backlog slugs (excluded by design): {sorted(BACKLOG_CLONES)}. "
                f"Frontend must not surface clones that are not HTTP-verified."
            )
        canonical.append(slug)
    return canonical
