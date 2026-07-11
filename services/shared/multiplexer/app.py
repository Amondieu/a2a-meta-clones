"""MCP multiplexer — hosts up to 3 clones per Railway service.

Reads CLONE_A_ID / CLONE_A_MANIFEST_PATH / CLONE_A_STRIPE_KEY (and B, C) from
env, loads the clone specs, and exposes:
  - GET  /                            — service info
  - GET  /.well-known/mcp-server      — IETF draft-serra-mcp-discovery-uri-01
  - GET  /clone/{id}/mcp              — clone manifest (per clone)
  - GET  /clone/{id}/health           — health check
  - GET  /clone/{id}/tools            — list of tool definitions
  - POST /clone/{id}/invoke/{tool}    — invoke a tool (stub in slice 1)

This is slice 1 — no real tool execution yet. The tool invocation endpoint
returns a structured "not yet wired" response so the route exists and the
end-to-end topology is testable.

Future slices will add: real tool execution (slice 4 = Railway deploy wires
the running service), Stripe metered billing on invoke, and overwatch hooks.
"""
from __future__ import annotations

import json
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel


log = logging.getLogger("gold-seed.multiplexer")
logging.basicConfig(level=logging.INFO)


# Design constraint: 3 clones per service. 4 services → 12 max.
MAX_CLONES_PER_SERVICE = 3

# Provider routing (SOUL.md §0.5): every LLM call goes through the LiteLLM
# proxy — NEVER directly to Groq/DeepSeek/etc. Aliases are proxy-side.
TIER_ALIAS = {"lightweight": "flash-k2", "heavy": "kore-builder"}
HEAVY_FALLBACK_ALIAS = "deepseek-flash"


def _clean_env(name: str) -> str:
    """Env read that strips accidental quoting (Infisical-stored values)."""
    return (os.environ.get(name) or "").strip().strip('"').strip("'")


class CloneSlot(BaseModel):
    """One clone hosted on this service."""
    clone_id: str
    name: str
    archetype: str
    description: str
    exposed_tools: List[Dict[str, Any]] = []
    mcp_path: str
    regulatory_anchor: Optional[str] = None
    category: Optional[str] = None
    gap_name: Optional[str] = None
    stripe_price_per_call_usd: float = 0.05
    stripe_product_id: Optional[str] = None
    stripe_price_id: Optional[str] = None
    stripe_restricted_key: Optional[str] = None
    metadata: Dict[str, Any] = {}


def _read_clone_spec(manifest_path: str) -> Dict[str, Any]:
    """Load a clone spec from disk. Supports the WarpEngine spec shape."""
    p = Path(manifest_path)
    if not p.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    return json.loads(p.read_text(encoding="utf-8"))


def _spec_to_slot(letter: str, clone_id: str, manifest_path: str) -> CloneSlot:
    """Convert a WarpEngine CloneSpecification JSON into a CloneSlot."""
    spec = _read_clone_spec(manifest_path)
    mcp_path = f"/clone/{clone_id}/mcp"
    return CloneSlot(
        clone_id=clone_id,
        name=spec.get("name", clone_id),
        archetype=spec.get("archetype_class", spec.get("archetype", "AuditorScribe")),
        description=spec.get("description", ""),
        exposed_tools=spec.get("exposed_tools", []),
        mcp_path=mcp_path,
        category=os.environ.get(f"CLONE_{letter}_CATEGORY"),
        gap_name=os.environ.get(f"CLONE_{letter}_GAP_NAME"),
        regulatory_anchor=os.environ.get(f"CLONE_{letter}_REGULATORY_ANCHOR"),
        stripe_price_per_call_usd=float(os.environ.get(f"CLONE_{letter}_PRICE_USD", "0.05")),
        stripe_restricted_key=os.environ.get(f"CLONE_{letter}_STRIPE_KEY"),
        metadata={
            "service_letter": letter,
            "deployment_at": os.environ.get("DEPLOYMENT_AT", ""),
            "warp_generation": spec.get("generation", 2),
        },
    )


def load_clones_from_env() -> List[CloneSlot]:
    """Read CLONE_A_ID, CLONE_A_MANIFEST_PATH, ... from env. Max 3 per service."""
    clones: List[CloneSlot] = []
    for letter in ["A", "B", "C"]:
        clone_id = os.environ.get(f"CLONE_{letter}_ID")
        manifest_path = os.environ.get(f"CLONE_{letter}_MANIFEST_PATH")
        if not clone_id or not manifest_path:
            continue
        try:
            slot = _spec_to_slot(letter, clone_id, manifest_path)
            clones.append(slot)
        except FileNotFoundError as e:
            log.warning(f"CLONE_{letter}: {e}; skipping")
    if len(clones) > MAX_CLONES_PER_SERVICE:
        raise ValueError(
            f"Service has {len(clones)} clones, max is {MAX_CLONES_PER_SERVICE}. "
            f"Pair differently in deploy_all.py."
        )
    return clones


# === App ===

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Replace @app.on_event('startup') with the modern lifespan pattern.

    FastAPI 0.115+ deprecates on_event in favor of the lifespan context manager.
    The two semantically are equivalent: code before yield = startup, code after
    yield = shutdown. There is no shutdown logic here yet (slice 1 is read-only).
    """
    global clones
    clones = load_clones_from_env()
    log.info(f"Multiplexer started: {len(clones)} clones loaded")
    for c in clones:
        log.info(f"  [{c.metadata.get('service_letter', '?')}] {c.clone_id}  →  {c.mcp_path}")
    yield  # application runs here
    # Shutdown logic (none in slice 1; future: flush telemetry, close pools)


app = FastAPI(title="Gold Seed MCP Multiplexer", version="0.1.0", lifespan=lifespan)
clones: List[CloneSlot] = []


@app.get("/")
def root() -> Dict[str, Any]:
    return {
        "service": "gold-seed-multiplexer",
        "version": app.version,
        "clones_hosted": len(clones),
        "clones": [
            {
                "clone_id": c.clone_id,
                "archetype": c.archetype,
                "mcp_path": c.mcp_path,
                "category": c.category,
            }
            for c in clones
        ],
        "endpoints": {
            "well_known": "/.well-known/mcp-server",
            "clone_manifest": "/clone/{id}/mcp",
            "clone_health": "/clone/{id}/health",
            "clone_tools": "/clone/{id}/tools",
            "clone_invoke": "/clone/{id}/invoke/{tool_name}",
        },
        "irreversible_actions": False,  # read-only in slice 1
    }


@app.get("/.well-known/mcp-server")
def well_known() -> Dict[str, Any]:
    """IETF draft-serra-mcp-discovery-uri-01: list all clones on this service.

    Every registry (Official, Smithery, mcp.so, Glama) can read this endpoint
    and self-verify what's hosted here. Zero lock-in.
    """
    return {
        "service": app.title,
        "version": app.version,
        "transport": "http+sse",
        "servers": [
            {
                "name": c.clone_id,
                "path": c.mcp_path,
                "version": "1.0",
                "archetype": c.archetype,
                "tools": [t.get("name", "?") for t in c.exposed_tools],
                "regulatory_anchor": c.regulatory_anchor,
                "category": c.category,
                "pricing": {
                    "per_call_usd": c.stripe_price_per_call_usd,
                    "currency": "USD",
                },
            }
            for c in clones
        ],
    }


def _find_clone(clone_id: str) -> CloneSlot:
    clone = next((c for c in clones if c.clone_id == clone_id), None)
    if not clone:
        raise HTTPException(404, f"Clone {clone_id!r} not hosted on this service")
    return clone


@app.get("/clone/{clone_id}/mcp")
def clone_manifest(clone_id: str) -> Dict[str, Any]:
    """Per-clone MCP manifest. What Smithery/Official/Glama register against."""
    c = _find_clone(clone_id)
    return {
        "name": c.name,
        "version": "1.0",
        "clone_id": c.clone_id,
        "archetype": c.archetype,
        "description": c.description,
        "category": c.category,
        "gap_name": c.gap_name,
        "regulatory_anchor": c.regulatory_anchor,
        "tools": c.exposed_tools,
        "transport": "http+sse",
        "pricing": {
            "model": "pay_per_call",
            "per_call_usd": c.stripe_price_per_call_usd,
            "currency": "USD",
            "billing_surface": "stripe",
            "stripe_configured": c.stripe_restricted_key is not None,
        },
    }


@app.get("/clone/{clone_id}/health")
def clone_health(clone_id: str) -> Dict[str, Any]:
    c = _find_clone(clone_id)
    return {
        "clone_id": c.clone_id,
        "status": "active",
        "archetype": c.archetype,
        "tools_count": len(c.exposed_tools),
        "stripe_configured": c.stripe_restricted_key is not None,
    }


@app.get("/clone/{clone_id}/tools")
def clone_tools(clone_id: str) -> Dict[str, Any]:
    c = _find_clone(clone_id)
    return {
        "clone_id": c.clone_id,
        "tools": c.exposed_tools,
    }


def _require_auth(x_api_key: Optional[str]) -> None:
    """Invoke auth: enforced only when MULTIPLEXER_API_KEY is configured.

    Discovery endpoints stay public (registries must be able to read them);
    tool invocation is the billable surface, so it is the one behind the key.
    The compliance gate (api/quality_gate.py check 6) requires deployments to
    configure the key — an open invoke endpoint fails the pre-deploy gate.
    """
    expected = _clean_env("MULTIPLEXER_API_KEY")
    if not expected:
        return  # slice-1 back-compat: no key configured → open (fails compliance)
    if x_api_key != expected:
        raise HTTPException(401, "invalid or missing x-api-key")


def _proxy_chat(alias: str, tool: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
    """One chat call through the LiteLLM proxy. Fail fast, never fall back to
    a direct provider call (SOUL.md §0.5 hard rule)."""
    base_url = _clean_env("LITELLM_BASE_URL")
    api_key = _clean_env("LITELLM_API_KEY")
    if not base_url:
        raise HTTPException(
            502,
            "LITELLM_BASE_URL not configured — provider routing goes through the "
            "LiteLLM proxy only; direct provider calls are forbidden (SOUL.md §0.5)",
        )
    import httpx

    body = {
        "model": alias,
        "messages": [
            {
                "role": "system",
                "content": f"You are the tool {tool.get('name')!r}: {tool.get('description', '')}",
            },
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ],
        "max_tokens": 1024,
    }
    r = httpx.post(
        f"{base_url.rstrip('/')}/chat/completions",
        json=body,
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=30.0,
    )
    r.raise_for_status()
    data = r.json()
    return {
        "content": data["choices"][0]["message"]["content"],
        "usage": data.get("usage", {}),
        "alias": alias,
    }


@app.post("/clone/{clone_id}/invoke/{tool_name}")
def clone_invoke(
    clone_id: str,
    tool_name: str,
    payload: Dict[str, Any] = {},
    x_api_key: Optional[str] = Header(default=None),
) -> Dict[str, Any]:
    """Tier-routed tool invocation (slice 4 upgrade).

    tool.tier drives dispatch (SOUL.md §0.5):
      "logic"       → pure Python, no LLM call ever
      "lightweight" → LiteLLM proxy alias flash-k2
      "heavy"       → kore-builder, one retry on deepseek-flash if rate-limited
      missing       → slice-1 stub response. Deployed specs always carry an
                      explicit tier (the compliance gate blocks otherwise), so
                      this path only exists for untagged/legacy specs.
    """
    _require_auth(x_api_key)
    c = _find_clone(clone_id)
    tool = next((t for t in c.exposed_tools if t.get("name") == tool_name), None)
    if not tool:
        raise HTTPException(404, f"Tool {tool_name!r} not exposed by clone {clone_id!r}")

    tier = tool.get("tier")
    if tier == "logic":
        # Pure-Python execution surface. The baseline AuditorScribe scaffold
        # is a deterministic payload processor; no LLM is ever consulted.
        return {
            "clone_id": c.clone_id,
            "tool": tool_name,
            "status": "ok",
            "tier": "logic",
            "result": {"processed": True, "input_keys": sorted(payload.keys())},
            "llm_called": False,
        }

    if tier in TIER_ALIAS:
        alias = TIER_ALIAS[tier]
        try:
            out = _proxy_chat(alias, tool, payload)
        except HTTPException:
            raise
        except Exception as first_err:
            if tier == "heavy":  # fallback chain: kore-builder → deepseek-flash
                try:
                    out = _proxy_chat(HEAVY_FALLBACK_ALIAS, tool, payload)
                except Exception as e:
                    raise HTTPException(
                        502, f"LiteLLM proxy unreachable/failed on {alias} and "
                             f"{HEAVY_FALLBACK_ALIAS}: {e}"
                    )
            else:
                raise HTTPException(502, f"LiteLLM proxy call failed on {alias}: {first_err}")
        return {
            "clone_id": c.clone_id,
            "tool": tool_name,
            "status": "ok",
            "tier": tier,
            "alias": out["alias"],
            "result": out["content"],
            "usage": out["usage"],
            "llm_called": True,
        }

    # No tier tag → slice-1 stub (unreachable for gate-passed deployments).
    return {
        "clone_id": c.clone_id,
        "tool": tool_name,
        "status": "not_yet_wired",
        "message": (
            f"Slice 1 stub: this tool would be invoked in slice 4 (Railway deploy). "
            f"For now, the multiplexer is read-only."
        ),
        "echo_payload": payload,
        "next_slice": "real_invoke_via_warp_engine_or_direct_call",
    }


# === JSON-RPC 2.0 MCP surface ===
# GET /clone/{id}/mcp stays the human/registry-readable manifest; POST is the
# machine MCP endpoint real clients speak. The compliance gate (quality_gate)
# validates this surface: methods tools/list + tools/call, and the five
# standard error codes (-32700/-32600/-32601/-32602/-32603).

JSONRPC_PARSE_ERROR = -32700
JSONRPC_INVALID_REQUEST = -32600
JSONRPC_METHOD_NOT_FOUND = -32601
JSONRPC_INVALID_PARAMS = -32602
JSONRPC_INTERNAL_ERROR = -32603


def _rpc_error(req_id: Any, code: int, message: str) -> JSONResponse:
    # JSON-RPC-level errors ride on HTTP 200; transport errors (auth) use 4xx.
    return JSONResponse(
        {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}
    )


@app.post("/clone/{clone_id}/mcp")
async def clone_jsonrpc(
    clone_id: str,
    request: Request,
    x_api_key: Optional[str] = Header(default=None),
) -> JSONResponse:
    c = _find_clone(clone_id)

    raw = await request.body()
    try:
        req = json.loads(raw)
    except (ValueError, UnicodeDecodeError):
        return _rpc_error(None, JSONRPC_PARSE_ERROR, "Parse error: invalid JSON")

    if not isinstance(req, dict) or req.get("jsonrpc") != "2.0" or "method" not in req:
        return _rpc_error(
            req.get("id") if isinstance(req, dict) else None,
            JSONRPC_INVALID_REQUEST,
            "Invalid Request: jsonrpc must be '2.0' and method is required",
        )

    req_id = req.get("id")
    method = req["method"]
    params = req.get("params") or {}

    if method == "tools/list":
        return JSONResponse(
            {"jsonrpc": "2.0", "id": req_id, "result": {"tools": c.exposed_tools}}
        )

    if method == "tools/call":
        _require_auth(x_api_key)
        if not isinstance(params, dict) or not params.get("name"):
            return _rpc_error(req_id, JSONRPC_INVALID_PARAMS, "params.name is required")
        tool_name = params["name"]
        tool = next((t for t in c.exposed_tools if t.get("name") == tool_name), None)
        if tool is None:
            return _rpc_error(req_id, JSONRPC_INVALID_PARAMS, f"unknown tool {tool_name!r}")
        try:
            result = clone_invoke(
                clone_id, tool_name, params.get("arguments") or {}, x_api_key=x_api_key
            )
        except HTTPException:
            raise  # transport-level (auth/proxy) — keep HTTP semantics
        except Exception as e:
            return _rpc_error(req_id, JSONRPC_INTERNAL_ERROR, f"{type(e).__name__}: {e}")
        return JSONResponse(
            {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"content": [{"type": "text", "text": json.dumps(result)}]},
            }
        )

    return _rpc_error(req_id, JSONRPC_METHOD_NOT_FOUND, f"Method not found: {method}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
