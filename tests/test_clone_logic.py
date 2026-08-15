"""Minimal tests for clone_logic handlers."""
from services.shared.clone_logic import dispatch


def test_audit_bazaar_evidence():
    ev = dispatch(
        "audit-bazaar",
        "run_eu_ai_act_deployer_evidence",
        {
            "deployment_id": "dep-1",
            "scope": "2026-08",
            "sources": [
                {
                    "uri": "s3://bucket/x",
                    "records": [{"kind": "transparency_notice"}],
                }
            ],
        },
    )
    assert ev["obligations"]["art_26_4_transparency"]["status"] == "pass"
    posture = dispatch(
        "audit-bazaar", "get_compliance_posture", {"evidence": ev}
    )
    assert posture["posture"] in (
        "compliant",
        "compliant_with_findings",
        "non_compliant",
    )


def test_agent_fabric_flags_shell():
    out = dispatch(
        "agent-fabric",
        "assess_mcp_threat_posture",
        {"tools": [{"name": "shell_exec"}], "permissions": ["admin"]},
    )
    assert out["grade"] in ("C", "D")
    assert out["findings"]


def test_each_clone_has_handler():
    samples = {
        "agent-lens": ("assess_agent_identity", {"agent_id": "a1", "scopes": ["read"]}),
        "agent-ledger": (
            "scan_shadow_ai_inventory",
            {"discovered_agents": [{"name": "x", "approved": False}]},
        ),
        "compliance-lens": (
            "build_compliance_system_card",
            {
                "agent_name": "n",
                "underlying_model": "m",
                "intended_use": "u",
                "performance_metrics": {"f1": 0.9},
                "training_data_summary": "public",
                "gpai_systemic_risk": False,
            },
        ),
    }
    for cid, (tool, args) in samples.items():
        out = dispatch(cid, tool, args)
        assert "reproducibility_hash" in out
