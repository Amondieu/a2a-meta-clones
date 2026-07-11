"""services.shared.multiplexer - vendored from A2A-Meta/api/multiplexer.py.

This package hosts up to 3 clones per Railway service slot.
The router paths and env contract are frozen at the v1 PATCH
level. See A2A-Meta/docs/clone_repo_architecture_v0_DRAFT.md §6.

v0: app.py contains the full multiplexer logic. The split into
clone_slot / env_loader / routes is a v1 follow-up.
"""
