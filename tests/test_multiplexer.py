"""tests/test_multiplexer.py — smoke tests for the vendored multiplexer.

Port of A2A-Meta/api/test_multiplexer.py. Phase A is a smoke
test: the vendored multiplexer imports and exposes the
expected routes. Deeper integration tests are added in
Phase B (after CI is wired).
"""
from __future__ import annotations

import pytest


EXPECTED_ROUTES = [
    "/",
    "/.well-known/mcp-server",
    "/health",
    "/clone/{clone_id}/mcp",
    "/clone/{clone_id}/health",
    "/clone/{clone_id}/tools",
]


def test_vendored_multiplexer_imports(project_root):
    """The vendored multiplexer at services/shared/multiplexer/app.py
    imports without error."""
    import importlib.util

    app_path = project_root / "services" / "shared" / "multiplexer" / "app.py"
    spec = importlib.util.spec_from_file_location("vendored_multiplexer", app_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert hasattr(mod, "app"), "vendored multiplexer must expose a FastAPI `app`"
    assert hasattr(mod, "MAX_CLONES_PER_SERVICE")
    assert mod.MAX_CLONES_PER_SERVICE == 3


def test_vendored_multiplexer_routes_present(project_root):
    """The vendored multiplexer registers the expected routes."""
    import importlib.util

    app_path = project_root / "services" / "shared" / "multiplexer" / "app.py"
    spec = importlib.util.spec_from_file_location("vendored_multiplexer", app_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    paths = {r.path for r in mod.app.routes}
    for expected in ("/", "/.well-known/mcp-server"):
        assert expected in paths, f"missing route: {expected}"


def test_clone_slot_module_re_exports(project_root):
    """clone_slot.py re-exports CloneSlot from app.py (v0 split)."""
    from services.shared.multiplexer import clone_slot

    assert hasattr(clone_slot, "CloneSlot")
