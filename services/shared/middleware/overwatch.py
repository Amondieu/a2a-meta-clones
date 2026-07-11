"""Overwatch middleware (v0 stub).

The overwatch hook observes per-tool invocations. In v0 it is
a no-op; v1 will integrate with the A2A-Meta overwatch system.
"""
from __future__ import annotations

import logging
from typing import Any, Dict

log = logging.getLogger("a2a-meta-clones.overwatch")


async def observe_invocation(clone_id: str, tool_name: str, payload: Dict[str, Any]) -> None:
    """Stub: log the invocation. v1 forwards to A2A-Meta overwatch."""
    log.info("observe_invocation clone=%s tool=%s keys=%d", clone_id, tool_name, len(payload))
