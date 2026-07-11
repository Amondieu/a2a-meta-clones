"""CloneSlot and related pydantic models.

v0: placeholders. The actual CloneSlot class is currently in
app.py (vendored from A2A-Meta/api/multiplexer.py). The split
into this file is a v1 follow-up.
"""
# Re-export from app.py for forward-compat
from services.shared.multiplexer.app import CloneSlot  # noqa: F401
