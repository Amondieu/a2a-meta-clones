"""tests/conftest.py — pytest fixtures for a2a-meta-clones.

Port of A2A-Meta/tests/conftest_aug2_fakes.py (the standard
pytest conftest name; the source conftest_aug2_fakes.py is
ported under this standard name per the v1 PATCH).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure the project root is on sys.path so `import services.*` works
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def project_root() -> Path:
    """The a2a-meta-clones repo root."""
    return PROJECT_ROOT


@pytest.fixture
def snapshot_path() -> Path:
    """Path to the vendored catalog snapshot."""
    return PROJECT_ROOT / "services" / "shared" / "catalog_client" / "catalog_snapshot.py"


@pytest.fixture
def catalog_snapshot(snapshot_path):
    """Load the vendored catalog snapshot as a module."""
    import importlib.util
    import sys

    spec = importlib.util.spec_from_file_location("catalog_snapshot", snapshot_path)
    mod = importlib.util.module_from_spec(spec)
    # Critical: register in sys.modules BEFORE exec_module so that
    # @dataclass(frozen=True) can resolve the module's __dict__ via
    # sys.modules.get(cls.__module__).
    sys.modules["catalog_snapshot"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def a2a_meta_catalog_path():
    """Path to the A2A-Meta catalog source (read-only)."""
    return Path(r"C:\Users\Shadow\ShadowDrive\0.1.Ai\A2A-Meta\api\middleware\live_clone_catalog.py")
