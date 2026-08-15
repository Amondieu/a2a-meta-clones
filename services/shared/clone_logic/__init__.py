"""Per-clone pure-logic tool handlers (tier=logic, zero LLM)."""
from __future__ import annotations

from typing import Any, Callable, Dict, Tuple

from . import agent_fabric, agent_ledger, agent_lens, audit_bazaar, compliance_lens, human_oversight

Handler = Callable[[Dict[str, Any]], Dict[str, Any]]

# (clone_id, tool_name) → handler
# Live Railway maps CLONE_B agent-fabric → agent-fabric__human-oversight-integration.json
REGISTRY: Dict[Tuple[str, str], Handler] = {
    ("audit-bazaar", "run_eu_ai_act_deployer_evidence"): audit_bazaar.handle_evidence,
    ("audit-bazaar", "get_compliance_posture"): audit_bazaar.handle_posture,
    ("agent-fabric", "assess_human_oversight"): human_oversight.handle,
    # Backlog slug agent-fabric-threat-model uses agent-fabric.json when promoted
    ("agent-fabric-threat-model", "assess_mcp_threat_posture"): agent_fabric.handle,
    ("agent-lens", "assess_agent_identity"): agent_lens.handle,
    ("agent-ledger", "scan_shadow_ai_inventory"): agent_ledger.handle,
    ("compliance-lens", "build_compliance_system_card"): compliance_lens.handle,
}


def normalize_args(payload: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    args = payload.get("arguments")
    if isinstance(args, dict):
        return args
    return payload


def dispatch(clone_id: str, tool_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    key = (clone_id, tool_name)
    handler = REGISTRY.get(key)
    if not handler:
        raise KeyError(f"no logic handler for {clone_id}/{tool_name}")
    return handler(normalize_args(payload))


def known_tools(clone_id: str) -> list[str]:
    return [t for (c, t) in REGISTRY if c == clone_id]
