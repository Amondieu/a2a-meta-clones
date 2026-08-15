"""agent-fabric (live) — EU AI Act Art. 14 human oversight assessment."""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List


def _canon(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


REQUIRED_CONTROLS = (
    "human_can_interrupt",
    "human_can_override",
    "oversight_ui",
    "decision_logging",
    "escalation_path",
)


def assess_human_oversight(
    agent_name: str | None = None,
    controls: Dict[str, Any] | None = None,
    decision_points: List[str] | None = None,
) -> Dict[str, Any]:
    controls = controls or {}
    decision_points = decision_points or []
    findings: List[Dict[str, Any]] = []
    score = 100

    for key in REQUIRED_CONTROLS:
        val = controls.get(key)
        if val is True or val == "yes" or val == "present":
            continue
        findings.append(
            {
                "severity": "high" if key.startswith("human_can_") else "medium",
                "code": f"MISSING_{key.upper()}",
                "detail": f"Art. 14 control '{key}' not evidenced as present",
            }
        )
        score -= 15 if key.startswith("human_can_") else 10

    if not decision_points:
        findings.append(
            {
                "severity": "medium",
                "code": "NO_DECISION_POINTS",
                "detail": "No meaningful decision points listed for human review",
            }
        )
        score -= 10

    score = max(0, min(100, score))
    grade = "A" if score >= 85 else "B" if score >= 70 else "C" if score >= 50 else "D"
    body = {
        "loop": "eu_ai_act_art14_human_oversight",
        "loop_version": "1.0.0",
        "agent_name": agent_name,
        "score": score,
        "grade": grade,
        "findings": findings,
        "controls_checked": list(REQUIRED_CONTROLS),
        "decision_points": decision_points,
        "framework": "EU AI Act Article 14 — human oversight",
    }
    body["reproducibility_hash"] = "sha256:" + hashlib.sha256(
        _canon(body).encode()
    ).hexdigest()
    return body


def handle(args: Dict[str, Any]) -> Dict[str, Any]:
    return assess_human_oversight(
        agent_name=args.get("agent_name"),
        controls=args.get("controls"),
        decision_points=args.get("decision_points"),
    )
