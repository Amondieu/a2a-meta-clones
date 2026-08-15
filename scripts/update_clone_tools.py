"""Update clone_specs exposed_tools to clone-specific logic tools."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "http://json-schema.org/draft-07/schema#"

TOOLS = {
    "audit-bazaar": [
        {
            "name": "run_eu_ai_act_deployer_evidence",
            "description": (
                "Evaluate deployer obligations Art. 26(4)-(7) + Art. 50 against "
                "operational evidence sources. Deterministic; zero LLM."
            ),
            "tier": "logic",
            "parameters": {
                "deployment_id": {"type": "string", "required": True},
                "scope": {"type": "string", "description": "YYYY-MM", "required": True},
                "sources": {"type": "array", "required": True},
            },
            "input_schema": {
                "$schema": SCHEMA,
                "type": "object",
                "properties": {
                    "deployment_id": {"type": "string"},
                    "scope": {"type": "string"},
                    "sources": {"type": "array", "items": {"type": "object"}},
                },
                "required": ["deployment_id", "scope", "sources"],
            },
        },
        {
            "name": "get_compliance_posture",
            "description": "Project evidence.json to compliance_posture.json (deterministic).",
            "tier": "logic",
            "parameters": {"evidence": {"type": "object", "required": True}},
            "input_schema": {
                "$schema": SCHEMA,
                "type": "object",
                "properties": {"evidence": {"type": "object"}},
                "required": ["evidence"],
            },
        },
    ],
    "agent-fabric": [
        {
            "name": "assess_mcp_threat_posture",
            "description": (
                "Score MCP tool surfaces for agent-native security risks "
                "(dangerous tools, secrets, overbroad perms, open egress). "
                "Deterministic; NIST AI RMF aligned."
            ),
            "tier": "logic",
            "parameters": {
                "tools": {"type": "array", "required": False},
                "permissions": {"type": "array", "required": False},
                "network_egress": {"type": "string", "required": False},
            },
            "input_schema": {
                "$schema": SCHEMA,
                "type": "object",
                "properties": {
                    "tools": {"type": "array"},
                    "permissions": {"type": "array", "items": {"type": "string"}},
                    "network_egress": {"type": "string"},
                },
            },
        }
    ],
    "agent-lens": [
        {
            "name": "assess_agent_identity",
            "description": (
                "Assess agent identity and least-agency authorization "
                "(distinct ID, shared accounts, scopes, owners). Deterministic."
            ),
            "tier": "logic",
            "parameters": {
                "agent_id": {"type": "string"},
                "roles": {"type": "array"},
                "scopes": {"type": "array"},
                "shared_account": {"type": "boolean"},
                "human_owner": {"type": "string"},
            },
            "input_schema": {
                "$schema": SCHEMA,
                "type": "object",
                "properties": {
                    "agent_id": {"type": "string"},
                    "roles": {"type": "array", "items": {"type": "string"}},
                    "scopes": {"type": "array", "items": {"type": "string"}},
                    "shared_account": {"type": "boolean"},
                    "human_owner": {"type": "string"},
                },
            },
        }
    ],
    "agent-ledger": [
        {
            "name": "scan_shadow_ai_inventory",
            "description": (
                "Scan discovered agents for shadow AI / unvetted MCP servers "
                "and models vs approved allowlists. Deterministic."
            ),
            "tier": "logic",
            "parameters": {
                "discovered_agents": {"type": "array"},
                "approved_mcp_servers": {"type": "array"},
                "approved_models": {"type": "array"},
            },
            "input_schema": {
                "$schema": SCHEMA,
                "type": "object",
                "properties": {
                    "discovered_agents": {"type": "array"},
                    "approved_mcp_servers": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "approved_models": {"type": "array", "items": {"type": "string"}},
                },
            },
        }
    ],
    "compliance-lens": [
        {
            "name": "build_compliance_system_card",
            "description": (
                "Build a compliance-grade agent system card (model, training "
                "summary, metrics, GPAI systemic risk) mapped to NIST/ISO/SOC2. "
                "Deterministic."
            ),
            "tier": "logic",
            "parameters": {
                "agent_name": {"type": "string"},
                "underlying_model": {"type": "string"},
                "training_data_summary": {"type": "string"},
                "intended_use": {"type": "string"},
                "performance_metrics": {"type": "object"},
                "gpai_systemic_risk": {"type": "boolean"},
                "frameworks": {"type": "array"},
            },
            "input_schema": {
                "$schema": SCHEMA,
                "type": "object",
                "properties": {
                    "agent_name": {"type": "string"},
                    "underlying_model": {"type": "string"},
                    "training_data_summary": {"type": "string"},
                    "intended_use": {"type": "string"},
                    "performance_metrics": {"type": "object"},
                    "gpai_systemic_risk": {"type": "boolean"},
                    "frameworks": {"type": "array", "items": {"type": "string"}},
                },
            },
        }
    ],
}


def main() -> None:
    for slug, tools in TOOLS.items():
        path = ROOT / "clone_specs" / f"{slug}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["exposed_tools"] = tools
        body = {k: v for k, v in data.items() if k != "checksum"}
        data["checksum"] = hashlib.sha256(
            json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        print(slug, [t["name"] for t in tools])


if __name__ == "__main__":
    main()
