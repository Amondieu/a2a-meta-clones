# slot-b

> **Canonical policy (binding):** This slot is part of
> `a2a-meta-clones/`, orchestrated by A2A-Meta. See
> [`A2A-Meta/docs/repo_topology.md`](https://github.com/Amondieu/A2A-Meta/blob/master/docs/repo_topology.md).

## Clones hosted

| Canonical slug | Legacy source spec name | Description | Status |
|:--|:--|:--|:-:|
| `agent-fabric-oversight` | `agent-fabric__human-oversight-integration` | EU AI Act Art. 14 human oversight + interrupt (frozen at the v1 PATCH identity split) | `PENDING` |
| `agent-ledger` | `agent-ledger` | NIST AI RMF data governance | `PENDING` |

## Env contract

See `env.template`. The catalog in A2A-Meta is the source of
truth; the env vars must match the catalog entries for
`agent-fabric-oversight` and `agent-ledger`.

**Note on the slug split (v1 PATCH):** the public catalog
slug is `agent-fabric-oversight` (the EU AI Act
human-oversight variant). The original filename
`agent-fabric__human-oversight-integration` is preserved as
`legacy_source_spec_name` metadata only. The legacy name
`agent-fabric` (without suffix) is NEVER used in the URL
path, MCP server ID, or Stripe product ID. The token-aware
static check `scripts/check_no_legacy_slug.py` enforces this.

Full env contract: `docs/env_contract.md`.

## Deploy (Phase C/D)

- `railway.toml` sets `ROOT_DIRECTORY=services/slot-b`
- Railway uses the shared `Dockerfile` at the repo root
- Health check: `GET /health`
- Public domain: Railway-generated
