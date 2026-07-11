"""Env loading helpers.

v0: placeholders. The actual env-reading logic is currently in
app.py (vendored from A2A-Meta/api/multiplexer.py). The split
into this file is a v1 follow-up.
"""
# Re-export from app.py for forward-compat
from services.shared.multiplexer.app import _clean_env, load_clones_from_env  # noqa: F401
