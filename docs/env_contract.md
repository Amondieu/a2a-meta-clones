# env_contract.md — exact env vars per slot

> **Source of truth:** A2A-Meta multiplexer contract, in
> [A2A-Meta/docs/clone_repo_architecture_v0_DRAFT.md §6.1](https://github.com/Amondieu/A2A-Meta/blob/master/docs/clone_repo_architecture_v0_DRAFT.md).
>
> This file is a **mirror** for the child repo. If the
> contract changes in A2A-Meta, sync via
> `scripts/sync_catalog.py` (Phase B+) or manual edit.

## Multiplexer env vars (per clone)

Each clone hosted by a slot requires **6 env vars** read by
`load_clones_from_env()` in `services/shared/multiplexer/app.py`:

| Variable | Type | Required | Source |
|:--|:--|:-:|:--|
| `CLONE_{X}_ID` | string | yes | canonical slug (e.g. `agent-lens`) |
| `CLONE_{X}_MANIFEST_PATH` | path | yes | repo-relative path to the spec JSON (e.g. `clone_specs/agent-lens.json`) |
| `CLONE_{X}_CATEGORY` | string | no (default empty) | e.g. `agent_devtools`, `agent_marketplace` |
| `CLONE_{X}_GAP_NAME` | string | no (default empty) | human-readable gap name |
| `CLONE_{X}_REGULATORY_ANCHOR` | string | no (default empty) | e.g. `EU AI Act`, `NIST AI RMF` |
| `CLONE_{X}_PRICE_USD` | float | no (default `0.05`) | per-call price |

`X` is `A`, `B`, or `C` — up to 3 clones per slot. Slots
hosting fewer clones simply leave the unused letters unset.

## Per-slot env vars

| Variable | Required | Notes |
|:--|:-:|:--|
| `ROOT_DIRECTORY` | yes (set by Railway) | `services/slot-a` / `services/slot-b` / `services/slot-c` |
| `DEPLOYMENT_AT` | no | ISO timestamp, set by CI |
| `RAILWAY_TOKEN` | yes (GitHub secret) | used by `railway up` in CI |
| `PORT` | no (default `8080`) | Railway injects automatically |

## Per-slot allocation (v1 PATCH)

| Slot | Clone A | Clone B | Clone C (capacity) |
|:-:|:--|:--|:--|
| **slot-a** | `agent-lens` | `audit-bazaar` | (capacity for 1 more) |
| **slot-b** | `agent-fabric-oversight` | `agent-ledger` | (capacity for 1 more) |
| **slot-c** | `compliance-lens` | (free) | (capacity for 2 more) |

The 5 backlog clones (NOT in any slot today) are listed in
[A2A-Meta/docs/clone_repo_architecture_v0_DRAFT.md §10](https://github.com/Amondieu/A2A-Meta/blob/master/docs/clone_repo_architecture_v0_DRAFT.md).

## Per-slot env templates

| Slot | File |
|:--|:--|
| slot-a | `services/slot-a/env.template` |
| slot-b | `services/slot-b/env.template` |
| slot-c | `services/slot-c/env.template` |

These files are the source of truth for Phase C Railway
Variables. The actual env values applied to each Railway
service are generated from these templates in Phase C.
