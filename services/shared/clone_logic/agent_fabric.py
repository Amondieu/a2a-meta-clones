"""agent-fabric — MCP threat / agent-native security posture (deterministic)."""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Dict, List

DANGEROUS_NAME = re.compile(
    r"(shell|exec|eval|subprocess|os\.system|rm\s+-rf|drop\s+table|exfiltrat)",
    re.I,
)
SECRET_HINT = re.compile(r"(password|secret|api[_-]?key|token|credential|private[_-]?key)", re.I)


def _canon(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def assess_mcp_threat_posture(
    tools: List[Dict[str, Any]] | None = None,
    permissions: List[str] | None = None,
    network_egress: str | None = None,
) -> Dict[str, Any]:
    tools = tools or []
    permissions = permissions or []
    findings: List[Dict[str, Any]] = []
    score = 100

    for t in tools:
        if not isinstance(t, dict):
            continue
        name = str(t.get("name") or "")
        desc = str(t.get("description") or "")
        blob = f"{name} {desc}"
        if DANGEROUS_NAME.search(blob):
            findings.append(
                {
                    "severity": "high",
                    "code": "DANGEROUS_TOOL",
                    "tool": name,
                    "detail": "Tool name/description suggests code execution or destructive ops",
                }
            )
            score -= 25
        if SECRET_HINT.search(blob):
            findings.append(
                {
                    "severity": "medium",
                    "code": "SECRET_SURFACE",
                    "tool": name,
                    "detail": "Tool may handle secrets — require redaction + audit log",
                }
            )
            score -= 10
        if t.get("unrestricted") is True or t.get("network") == "*":
            findings.append(
                {
                    "severity": "high",
                    "code": "UNRESTRICTED_NETWORK",
                    "tool": name,
                    "detail": "Unrestricted network egress on tool",
                }
            )
            score -= 20

    for p in permissions:
        pl = str(p).lower()
        if pl in ("*", "admin", "root", "owner") or "write_all" in pl:
            findings.append(
                {
                    "severity": "critical",
                    "code": "OVERPRIVILEGED",
                    "permission": p,
                    "detail": "Permission is overly broad for agent workloads",
                }
            )
            score -= 30

    egress = (network_egress or "unknown").lower()
    if egress in ("*", "unrestricted", "any"):
        findings.append(
            {
                "severity": "high",
                "code": "EGRESS_OPEN",
                "detail": "Network egress is unrestricted",
            }
        )
        score -= 15

    score = max(0, min(100, score))
    if score >= 85:
        grade = "A"
    elif score >= 70:
        grade = "B"
    elif score >= 50:
        grade = "C"
    else:
        grade = "D"

    body = {
        "loop": "mcp_threat_posture",
        "loop_version": "1.0.0",
        "score": score,
        "grade": grade,
        "findings": findings,
        "tools_reviewed": len(tools),
        "permissions_reviewed": len(permissions),
        "network_egress": egress,
        "framework": "NIST AI RMF — agent-native security / MCP threat modeling",
    }
    body["reproducibility_hash"] = "sha256:" + hashlib.sha256(
        _canon(body).encode()
    ).hexdigest()
    return body


def handle(args: Dict[str, Any]) -> Dict[str, Any]:
    return assess_mcp_threat_posture(
        tools=args.get("tools"),
        permissions=args.get("permissions"),
        network_egress=args.get("network_egress"),
    )
