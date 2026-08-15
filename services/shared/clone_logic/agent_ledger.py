"""agent-ledger — shadow AI / supply-chain inventory scan (deterministic)."""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List


def _canon(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def scan_shadow_ai_inventory(
    discovered_agents: List[Dict[str, Any]] | None = None,
    approved_mcp_servers: List[str] | None = None,
    approved_models: List[str] | None = None,
) -> Dict[str, Any]:
    discovered_agents = discovered_agents or []
    approved_mcp = {str(x).lower() for x in (approved_mcp_servers or [])}
    approved_models = {str(x).lower() for x in (approved_models or [])}
    findings: List[Dict[str, Any]] = []
    shadow = []
    score = 100

    for agent in discovered_agents:
        if not isinstance(agent, dict):
            continue
        name = str(agent.get("name") or agent.get("id") or "unknown")
        approved = bool(agent.get("approved"))
        mcp = str(agent.get("mcp_server") or agent.get("mcp") or "")
        model = str(agent.get("model") or "")
        issues = []
        if not approved:
            issues.append("unapproved_channel")
            score -= 15
        if mcp and approved_mcp and mcp.lower() not in approved_mcp:
            issues.append("unvetted_mcp")
            score -= 15
        if model and approved_models and model.lower() not in approved_models:
            issues.append("unvetted_model")
            score -= 10
        if issues:
            shadow.append({"agent": name, "issues": issues, "mcp": mcp, "model": model})
            findings.append(
                {
                    "severity": "high" if "unapproved_channel" in issues else "medium",
                    "code": "SHADOW_AI",
                    "agent": name,
                    "issues": issues,
                }
            )

    score = max(0, min(100, score))
    grade = "A" if score >= 85 else "B" if score >= 70 else "C" if score >= 50 else "D"
    body = {
        "loop": "shadow_ai_supply_chain",
        "loop_version": "1.0.0",
        "score": score,
        "grade": grade,
        "agents_scanned": len(discovered_agents),
        "shadow_count": len(shadow),
        "shadow_agents": shadow,
        "findings": findings,
        "framework": "NIST AI RMF — shadow AI & supply chain",
    }
    body["reproducibility_hash"] = "sha256:" + hashlib.sha256(
        _canon(body).encode()
    ).hexdigest()
    return body


def handle(args: Dict[str, Any]) -> Dict[str, Any]:
    return scan_shadow_ai_inventory(
        discovered_agents=args.get("discovered_agents"),
        approved_mcp_servers=args.get("approved_mcp_servers"),
        approved_models=args.get("approved_models"),
    )
