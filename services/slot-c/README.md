# slot-c

> **Canonical policy (binding):** This slot is part of
> `a2a-meta-clones/`, orchestrated by A2A-Meta. See
> [`A2A-Meta/docs/repo_topology.md`](https://github.com/Amondieu/A2A-Meta/blob/master/docs/repo_topology.md).

## Clones hosted (current)

| Canonical slug | Description | Status |
|:--|:--|:-:|
| `compliance-lens` | NIST AI RMF / ISO 42001 / SOC 2 | `PENDING` |

## Capacity

Slot-c is intentionally under-provisioned (1 clone + 2 free
slots) so the 5 backlog clones from
`A2A-Meta/docs/clone_repo_architecture_v0_DRAFT.md` §10 can
be added here without redistributing other slots.

The 5 backlog clones (NOT in this slot, NOT in any slot today):

| Reserved canonical slug | Legacy source spec | Why not in catalog |
|:--|:--|:--|
| `agent-catalog` | `agent-catalog` | service-d not provisioned |
| `agent-fabric-threat-model` | `agent-fabric` | name-collision with the human-oversight variant |
| `agent-vault` | `agent-vault` | not yet promoted |
| `audit-workbench` | `audit-workbench` | not yet promoted |
| `policy-hub` | `policy-hub` | not yet promoted |

## Env contract

See `env.template`. The catalog in A2A-Meta is the source of
truth; the env vars must match the catalog entry for
`compliance-lens`.

Full env contract: `docs/env_contract.md`.

## Deploy (Phase C/D)

- `railway.toml` sets `ROOT_DIRECTORY=services/slot-c`
- Railway uses the shared `Dockerfile` at the repo root
- Health check: `GET /health`
- Public domain: Railway-generated
