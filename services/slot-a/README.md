# slot-a

> **Canonical policy (binding):** This slot is part of
> `a2a-meta-clones/`, orchestrated by A2A-Meta. See
> [`A2A-Meta/docs/repo_topology.md`](https://github.com/Amondieu/A2A-Meta/blob/master/docs/repo_topology.md).

## Clones hosted

| Canonical slug | Source spec file | Description | Status |
|:--|:--|:--|:-:|
| `agent-lens` | `clone_specs/agent-lens.json` | Risk assessment (NIST AI RMF) | `PENDING` |
| `audit-bazaar` | `clone_specs/audit-bazaar.json` | SOC 2 audit | `PENDING` |

## Env contract

See `env.template` for the per-slot env vars. The catalog in
A2A-Meta is the source of truth; this slot's env vars must
match the catalog entries for `agent-lens` and `audit-bazaar`.

Full env contract: `docs/env_contract.md`.

## Deploy (Phase C/D)

- `railway.toml` sets `ROOT_DIRECTORY=services/slot-a`
- Railway uses the shared `Dockerfile` at the repo root
- Health check: `GET /health`
- Public domain: Railway-generated (e.g.
  `a2a-meta-clones-slot-a.up.railway.app`)
