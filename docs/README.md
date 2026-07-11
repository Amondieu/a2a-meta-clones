# a2a-meta-clones docs

> **Canonical policy:** these docs are written in the child
> repo but reference the A2A-Meta control plane for any
> cross-cutting rule. See
> [A2A-Meta/docs/repo_topology.md](https://github.com/Amondieu/A2A-Meta/blob/master/docs/repo_topology.md).

## Contents

| File | Purpose |
|:--|:--|
| [env_contract.md](./env_contract.md) | Exact env vars per slot, derived from the A2A-Meta multiplexer contract. Source of truth for the per-slot `env.template` files. |
| [promotion_log.md](./promotion_log.md) | Append-only audit log of HTTP verifications, promotions, and demotion candidates. |
| [rollback_runbook.md](./rollback_runbook.md) | What to do when a slot breaks, a clone must be demoted, or a repo-level rollback is required. |

## Cross-references

- **Architecture spec:** [A2A-Meta/docs/clone_repo_architecture_v0_DRAFT.md](https://github.com/Amondieu/A2A-Meta/blob/master/docs/clone_repo_architecture_v0_DRAFT.md)
- **Pipeline spec:** [A2A-Meta/docs/clone_pipeline_v0_DRAFT.md](https://github.com/Amondieu/A2A-Meta/blob/master/docs/clone_pipeline_v0_DRAFT.md)
- **Plan:** [A2A-Meta/docs/a2a_meta_clones_v1_implementation_plan_v0_DRAFT.md](https://github.com/Amondieu/A2A-Meta/blob/master/docs/a2a_meta_clones_v1_implementation_plan_v0_DRAFT.md)
- **Catalog:** [A2A-Meta/api/middleware/live_clone_catalog.py](https://github.com/Amondieu/A2A-Meta/blob/master/api/middleware/live_clone_catalog.py)
- **Aug 2 capture backend:** [A2A-Meta/docs/aug2_opus_spec.md](https://github.com/Amondieu/A2A-Meta/blob/master/docs/aug2_opus_spec.md)
