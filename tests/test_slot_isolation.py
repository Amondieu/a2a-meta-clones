"""tests/test_slot_isolation.py — slot env vars are independent."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_vendored_multiplexer(project_root):
    app_path = project_root / "services" / "shared" / "multiplexer" / "app.py"
    spec = importlib.util.spec_from_file_location("vendored_multiplexer", app_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["vendored_multiplexer"] = mod
    spec.loader.exec_module(mod)
    # Force pydantic forward-reference resolution for the vendored CloneSlot
    if hasattr(mod, "CloneSlot"):
        try:
            mod.CloneSlot.model_rebuild()
        except Exception:
            pass
    return mod


def test_max_clones_per_service_is_3(project_root):
    mod = _load_vendored_multiplexer(project_root)
    assert mod.MAX_CLONES_PER_SERVICE == 3


def test_clones_from_env_returns_empty_when_no_env(project_root, monkeypatch):
    """With no CLONE_X_ID env vars, load_clones_from_env returns []."""
    monkeypatch.chdir(project_root)
    mod = _load_vendored_multiplexer(project_root)
    for letter in ("A", "B", "C"):
        monkeypatch.delenv(f"CLONE_{letter}_ID", raising=False)
        monkeypatch.delenv(f"CLONE_{letter}_MANIFEST_PATH", raising=False)
    assert mod.load_clones_from_env() == []


def test_clones_from_env_does_not_mix_slots(project_root, monkeypatch):
    """slot-a's CLONE_A_ID and slot-b's CLONE_A_ID are independent env vars."""
    monkeypatch.chdir(project_root)
    mod = _load_vendored_multiplexer(project_root)
    monkeypatch.setenv("CLONE_A_ID", "agent-lens")
    monkeypatch.setenv("CLONE_A_MANIFEST_PATH", "clone_specs/agent-lens.json")
    monkeypatch.delenv("CLONE_B_ID", raising=False)
    monkeypatch.delenv("CLONE_B_MANIFEST_PATH", raising=False)
    monkeypatch.delenv("CLONE_C_ID", raising=False)
    monkeypatch.delenv("CLONE_C_MANIFEST_PATH", raising=False)
    clones = mod.load_clones_from_env()
    assert len(clones) == 1
    assert clones[0].clone_id == "agent-lens"
