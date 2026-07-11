# a2a-meta-clones

> **Canonical policy (binding):** This repo is orchestrated by
> **A2A-Meta** (sibling of `!A2A-Meta-Repos/`). See
> [`A2A-Meta/docs/repo_topology.md`](https://github.com/Amondieu/A2A-Meta/blob/master/docs/repo_topology.md)
> for the relationship, and
> [`A2A-Meta/docs/clone_repo_architecture_v0_DRAFT.md`](https://github.com/Amondieu/A2A-Meta/blob/master/docs/clone_repo_architecture_v0_DRAFT.md)
> for the spec this repo implements.
>
> `A2A-Meta/docs/repo_topology.md` is the canonical policy
> document. This README is a convenience mirror, not a
> second authority. If they conflict, the root side wins.

Deployable MCP clone services for A2A-Meta. Hosts 3 Railway
service slots (`slot-a`, `slot-b`, `slot-c`) for the 5
PENDING_CLONES MCP clones catalogued in
`A2A-Meta/api/middleware/live_clone_catalog.py`.

The catalog in A2A-Meta is the single source of truth for
which clones are LIVE. This repo vendors a snapshot (via
`sync_catalog.py`) and serves the clones via the multiplexer
vendored from `A2A-Meta/api/multiplexer.py`.

## Status (Phase A — local scaffold)

- **Phase A (local scaffold):** in progress, see
  `docs/parallel_prep_runlog.md` (mirror) and
  `A2A-Meta/docs/a2a_meta_clones_v1_implementation_plan_v0_DRAFT.md`
  (canonical plan)
- **Phase B (GitHub + CI):** not started
- **Phase C (Railway provisioning):** not started
- **Phase D (deploy + promotion):** not started

## Local layout

```
a2a-meta-clones/
├── README.md                        # this file
├── LICENSE                          # MIT
├── .gitignore
├── .env.example                     # shows expected env vars
├── pyproject.toml                   # package metadata
├── Dockerfile                       # shared, used by all 3 slots
├── railway.toml                     # shared template
├── requirements.txt
├── services/
│   ├── slot-a/                      # 2 clones: agent-lens, audit-bazaar
│   ├── slot-b/                      # 2 clones: agent-fabric-oversight, agent-ledger
│   ├── slot-c/                      # 1 clone: compliance-lens (+ 2 free capacity)
│   └── shared/
│       ├── multiplexer/             # vendored from A2A-Meta/api/multiplexer.py
│       ├── catalog_client/          # HTTP client for the A2A-Meta catalog
│       └── middleware/              # shared middleware
├── clone_specs/                     # 10 files: 5 PENDING + 5 backlog
├── server_manifests/                # 10 directories
├── scripts/
│   ├── pipeline.py                  # 9 commands: init / scaffold / test / package / review / verify / promote / demote / status
│   ├── smoke_gate.py                # 8 BLOCKED checks (--dry-run safe)
│   ├── check_no_legacy_slug.py      # token-aware static check
│   ├── verify_endpoint.py           # 4-probe HTTP 200 verify
│   └── sync_catalog.py              # one-way copy of A2A-Meta catalog
├── tests/                           # 9 test files + conftest
└── docs/
    ├── README.md
    ├── env_contract.md
    ├── promotion_log.md
    └── rollback_runbook.md
```

## Quick start (Phase A only)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run local tests
python -m pytest tests/ -v

# 3. Run the 8 smoke checks (--dry-run is safe; no network)
python scripts/smoke_gate.py --dry-run

# 4. Verify the legacy-slug static check
python scripts/check_no_legacy_slug.py

# 5. Show pipeline status
python scripts/pipeline.py status
```

## What is NOT here

- No `git init` in this folder (Phase B's responsibility)
- No GitHub remote (Phase B)
- No Railway services (Phase C)
- No deploys (Phase D)
- No promotion_request_*.json (Phase D)

This folder is a local scaffold. It will become a Git repo
in Phase B.

## Cross-references

- **Topology:** [A2A-Meta/docs/repo_topology.md](https://github.com/Amondieu/A2A-Meta/blob/master/docs/repo_topology.md)
- **Spec:** [A2A-Meta/docs/clone_repo_architecture_v0_DRAFT.md](https://github.com/Amondieu/A2A-Meta/blob/master/docs/clone_repo_architecture_v0_DRAFT.md)
- **Pipeline:** [A2A-Meta/docs/clone_pipeline_v0_DRAFT.md](https://github.com/Amondieu/A2A-Meta/blob/master/docs/clone_pipeline_v0_DRAFT.md)
- **Plan:** [A2A-Meta/docs/a2a_meta_clones_v1_implementation_plan_v0_DRAFT.md](https://github.com/Amondieu/A2A-Meta/blob/master/docs/a2a_meta_clones_v1_implementation_plan_v0_DRAFT.md)
- **Catalog:** [A2A-Meta/api/middleware/live_clone_catalog.py](https://github.com/Amondieu/A2A-Meta/blob/master/api/middleware/live_clone_catalog.py)
- **Aug 2 capture backend:** [A2A-Meta/docs/aug2_opus_spec.md](https://github.com/Amondieu/A2A-Meta/blob/master/docs/aug2_opus_spec.md)
