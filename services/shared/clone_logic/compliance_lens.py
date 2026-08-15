"""compliance-lens — compliance-grade system card builder (deterministic)."""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional


def _canon(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


REQUIRED_FIELDS = (
    "agent_name",
    "underlying_model",
    "intended_use",
    "performance_metrics",
)


def build_compliance_system_card(
    agent_name: str | None = None,
    underlying_model: str | None = None,
    training_data_summary: str | None = None,
    intended_use: str | None = None,
    performance_metrics: Dict[str, Any] | None = None,
    gpai_systemic_risk: bool | None = None,
    frameworks: List[str] | None = None,
) -> Dict[str, Any]:
    gaps: List[str] = []
    if not agent_name:
        gaps.append("agent_name")
    if not underlying_model:
        gaps.append("underlying_model")
    if not intended_use:
        gaps.append("intended_use")
    if not isinstance(performance_metrics, dict) or not performance_metrics:
        gaps.append("performance_metrics")
    if training_data_summary is None or training_data_summary == "":
        gaps.append("training_data_summary")
    if gpai_systemic_risk is None:
        gaps.append("gpai_systemic_risk")

    completeness = max(0, 100 - 15 * len(gaps))
    grade = (
        "A"
        if completeness >= 90
        else "B"
        if completeness >= 75
        else "C"
        if completeness >= 50
        else "D"
    )
    frameworks = frameworks or ["NIST AI RMF", "ISO 42001", "SOC 2"]

    card = {
        "loop": "compliance_system_card",
        "loop_version": "1.0.0",
        "agent_name": agent_name,
        "underlying_model": underlying_model,
        "training_data_summary": training_data_summary,
        "intended_use": intended_use,
        "performance_metrics": performance_metrics or {},
        "gpai_systemic_risk": gpai_systemic_risk,
        "frameworks_mapped": frameworks,
        "completeness_score": completeness,
        "grade": grade,
        "missing_fields": gaps,
        "status": "complete" if not gaps else "incomplete",
    }
    card["reproducibility_hash"] = "sha256:" + hashlib.sha256(
        _canon(card).encode()
    ).hexdigest()
    return card


def handle(args: Dict[str, Any]) -> Dict[str, Any]:
    return build_compliance_system_card(
        agent_name=args.get("agent_name"),
        underlying_model=args.get("underlying_model"),
        training_data_summary=args.get("training_data_summary"),
        intended_use=args.get("intended_use"),
        performance_metrics=args.get("performance_metrics"),
        gpai_systemic_risk=args.get("gpai_systemic_risk"),
        frameworks=args.get("frameworks"),
    )
