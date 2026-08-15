"""agent-lens — agent identity & least-agency authorization (deterministic)."""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List


def _canon(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def assess_agent_identity(
    agent_id: str | None = None,
    roles: List[str] | None = None,
    scopes: List[str] | None = None,
    shared_account: bool | None = None,
    human_owner: str | None = None,
) -> Dict[str, Any]:
    roles = roles or []
    scopes = scopes or []
    findings: List[Dict[str, Any]] = []
    score = 100

    if not agent_id or not str(agent_id).strip():
        findings.append(
            {
                "severity": "critical",
                "code": "NO_AGENT_ID",
                "detail": "Agent lacks a distinct identity",
            }
        )
        score -= 40
    if shared_account is True:
        findings.append(
            {
                "severity": "high",
                "code": "SHARED_ACCOUNT",
                "detail": "Agent runs under a shared service account",
            }
        )
        score -= 25
    if not human_owner:
        findings.append(
            {
                "severity": "medium",
                "code": "NO_HUMAN_OWNER",
                "detail": "No accountable human owner recorded",
            }
        )
        score -= 10
    if any(str(r).lower() in ("admin", "root", "*", "owner") for r in roles):
        findings.append(
            {
                "severity": "high",
                "code": "ROLE_TOO_BROAD",
                "detail": "Roles include admin/root-class privileges",
            }
        )
        score -= 20
    if not scopes:
        findings.append(
            {
                "severity": "medium",
                "code": "NO_SCOPES",
                "detail": "No least-agency scopes declared",
            }
        )
        score -= 15
    if any(str(s) in ("*", "all") for s in scopes):
        findings.append(
            {
                "severity": "high",
                "code": "WILDCARD_SCOPE",
                "detail": "Wildcard scope defeats least agency",
            }
        )
        score -= 20

    score = max(0, min(100, score))
    grade = "A" if score >= 85 else "B" if score >= 70 else "C" if score >= 50 else "D"
    body = {
        "loop": "agent_identity_least_agency",
        "loop_version": "1.0.0",
        "agent_id": agent_id,
        "score": score,
        "grade": grade,
        "findings": findings,
        "roles": roles,
        "scopes": scopes,
        "shared_account": bool(shared_account),
        "human_owner": human_owner,
        "framework": "NIST AI RMF — identity & least agency",
    }
    body["reproducibility_hash"] = "sha256:" + hashlib.sha256(
        _canon(body).encode()
    ).hexdigest()
    return body


def handle(args: Dict[str, Any]) -> Dict[str, Any]:
    return assess_agent_identity(
        agent_id=args.get("agent_id"),
        roles=args.get("roles"),
        scopes=args.get("scopes"),
        shared_account=args.get("shared_account"),
        human_owner=args.get("human_owner"),
    )
