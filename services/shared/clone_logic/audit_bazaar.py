"""audit-bazaar — EU AI Act deployer evidence (deterministic, zero LLM)."""
from __future__ import annotations

import calendar
import hashlib
import json
import re
from typing import Any, Dict, List

LOOP_NAME = "eu_ai_act_deployer_evidence"
LOOP_VERSION = "1.0.0"

EVIDENCE_ARTIFACTS = [
    "evidence.json",
    "evidence.pdf",
    "evidence.sha256",
    "compliance_posture.json",
    "replay_command.json",
]

OBLIGATION_KINDS: Dict[str, frozenset] = {
    "art_26_4_transparency": frozenset(
        {"instructions_for_use_ack", "transparency_notice"}
    ),
    "art_26_5_human_oversight": frozenset({"oversight_review", "override_event"}),
    "art_26_6_incident_monitoring": frozenset(
        {"incident_report", "monitoring_heartbeat"}
    ),
    "art_26_7_input_data_quality": frozenset({"input_data_check"}),
    "art_50_user_notification": frozenset({"user_notification"}),
}

_SCOPE_RE = re.compile(r"^(\d{4})-(0[1-9]|1[0-2])$")


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _normalize_scope(scope: str) -> Dict[str, Any]:
    if not isinstance(scope, str):
        raise ValueError(
            f"SCOPE_INVALID: scope must be a 'YYYY-MM' string, got {type(scope).__name__}"
        )
    m = _SCOPE_RE.match(scope)
    if not m:
        raise ValueError(f"SCOPE_INVALID: scope must match 'YYYY-MM', got {scope!r}")
    year, month = int(m.group(1)), int(m.group(2))
    last_day = calendar.monthrange(year, month)[1]
    return {
        "period_start": f"{year:04d}-{month:02d}-01T00:00:00Z",
        "period_end": f"{year:04d}-{month:02d}-{last_day:02d}T23:59:59Z",
        "month": scope,
    }


def _validate_sources(sources: Any) -> List[Dict[str, Any]]:
    if not isinstance(sources, list):
        raise ValueError(
            f"SOURCES_INVALID: sources must be a list, got {type(sources).__name__}"
        )
    for i, src in enumerate(sources):
        if not isinstance(src, dict) or not isinstance(src.get("uri"), str):
            raise ValueError(f"SOURCES_INVALID: sources[{i}] needs a string 'uri'")
        records = src.get("records", [])
        if not isinstance(records, list):
            raise ValueError(f"SOURCES_INVALID: sources[{i}].records must be a list")
    return sources


def _evaluate_obligation(kinds: frozenset, records: List[Dict[str, Any]]) -> Dict[str, Any]:
    matching = [r for r in records if r.get("kind") in kinds]
    if any(r.get("result") == "fail" for r in matching):
        status = "fail"
    elif matching:
        status = "pass"
    else:
        status = "attention"
    return {"status": status, "controls": len(matching)}


def run_eu_ai_act_deployer_evidence(
    deployment_id: str,
    scope: str,
    sources: List[Dict[str, Any]],
) -> Dict[str, Any]:
    if not isinstance(deployment_id, str) or not deployment_id:
        raise ValueError("DEPLOYMENT_ID_INVALID: deployment_id must be a non-empty string")
    period = _normalize_scope(scope)
    sources = _validate_sources(sources)

    all_records: List[Dict[str, Any]] = []
    for src in sources:
        all_records.extend(src.get("records", []))

    obligations = {
        name: _evaluate_obligation(kinds, all_records)
        for name, kinds in OBLIGATION_KINDS.items()
    }
    controls_evaluated = sum(o["controls"] for o in obligations.values())

    input_fingerprint = _sha256(
        canonical_json(
            {
                "deployment_id": deployment_id,
                "scope": scope,
                "sources": sources,
                "loop": LOOP_NAME,
                "loop_version": LOOP_VERSION,
            }
        )
    )
    audit_id = f"aud_{period['month'].replace('-', '_')}_{input_fingerprint[:8]}"

    evidence: Dict[str, Any] = {
        "audit_id": audit_id,
        "loop": LOOP_NAME,
        "loop_version": LOOP_VERSION,
        "deployment_id": deployment_id,
        "scope": {
            "period_start": period["period_start"],
            "period_end": period["period_end"],
            "evidence_uris": [src["uri"] for src in sources],
        },
        "obligations": obligations,
        "controls_evaluated": controls_evaluated,
        "evidence_artifacts": list(EVIDENCE_ARTIFACTS),
    }
    evidence["reproducibility_hash"] = "sha256:" + _sha256(canonical_json(evidence))
    evidence["replay_command"] = (
        f"mcp call run_eu_ai_act_deployer_evidence --replay --audit-id {audit_id}"
    )
    return evidence


def get_compliance_posture(evidence: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(evidence, dict) or evidence.get("loop") != LOOP_NAME:
        raise ValueError(
            "EVIDENCE_INVALID: expected the payload returned by run_eu_ai_act_deployer_evidence"
        )
    obligations = evidence.get("obligations")
    if not isinstance(obligations, dict) or set(obligations) != set(OBLIGATION_KINDS):
        raise ValueError("EVIDENCE_INVALID: obligations block is missing or incomplete")

    statuses = {name: o["status"] for name, o in sorted(obligations.items())}
    if any(s == "fail" for s in statuses.values()):
        posture = "non_compliant"
    elif any(s == "attention" for s in statuses.values()):
        posture = "compliant_with_findings"
    else:
        posture = "compliant"

    return {
        "audit_id": evidence["audit_id"],
        "loop": LOOP_NAME,
        "loop_version": evidence["loop_version"],
        "deployment_id": evidence["deployment_id"],
        "scope": evidence["scope"],
        "posture": posture,
        "obligations": statuses,
        "controls_evaluated": evidence["controls_evaluated"],
        "evidence_artifacts": len(evidence["evidence_artifacts"]),
        "reproducibility_hash": evidence["reproducibility_hash"],
        "replay_command": evidence["replay_command"],
    }


def handle_evidence(args: Dict[str, Any]) -> Dict[str, Any]:
    return run_eu_ai_act_deployer_evidence(
        deployment_id=str(args.get("deployment_id") or ""),
        scope=str(args.get("scope") or ""),
        sources=args.get("sources") or [],
    )


def handle_posture(args: Dict[str, Any]) -> Dict[str, Any]:
    evidence = args.get("evidence")
    if not isinstance(evidence, dict):
        raise ValueError("EVIDENCE_INVALID: 'evidence' object required")
    return get_compliance_posture(evidence)
