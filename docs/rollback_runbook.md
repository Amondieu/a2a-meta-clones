# rollback_runbook.md — what to do when something breaks

> **Status:** v0 DRAFT (a2a-meta-070, Phase A)
> **Applies to:** the deployed a2a-meta-clones slots (post-Phase D)

## 1. Slot-level rollback (Railway dashboard)

Each slot is its own Railway service. To roll back `slot-a`:

1. Open Railway dashboard → `a2a-meta-clones-slot-a` → **Deployments**.
2. Select the previous successful deployment.
3. Click **Rollback** — Railway swaps the active deployment.

The roll-back does **not** auto-demote any clone in the
catalog. The catalog promotion state is independent of the
running deploy. The next `pipeline.py verify` re-probes the
rolled-back version. Per §2, a verify failure writes a
`DEMOTION_CANDIDATE` entry — it does not auto-demote.

## 2. Clone-level demote (v1 PATCH: candidate-only)

The pipeline distinguishes between `DEMOTION_CANDIDATE` (a
flag indicating a clone *should* be demoted) and an actual
demotion (a code change to the A2A-Meta catalog).

### 2.1 DEMOTION_CANDIDATE — auto

A `DEMOTION_CANDIDATE` is auto-created in any of these cases:

- `pipeline.py verify` fails 3 times in a row for a clone
- A `customer.subscription.deleted` webhook for a Team
  subscriber whose assessment referenced the clone
- A slot-level rollback (§1) leaves a clone in a state
  where its last deploy SHA does not match any
  `docs/promotion_log.md` evidence record

A `DEMOTION_CANDIDATE` is **not** a demotion. The clone stays
`LIVE` in the catalog. A human must then explicitly invoke:

```bash
python scripts/pipeline.py demote <slug> --reason <reason>
```

For compliance-grade products, the user is the only one
authorized to make the final demotion decision. The cron
(`--auto-failures` flag) is a *triage tool*, not a
decision-maker.

### 2.2 Actual demote — manual

The `pipeline.py demote` command writes a new
`docs/promotion_log.md` entry with `promotion_state =
"DEMOTED"` and the demoter (always `human` via this command),
reason, and timestamp. The clone's catalog entry is moved
from `LIVE_CLONES` to `PENDING_CLONES` only at this point —
and that mutation is performed by the user (or an
A2A-Meta-side automation) on `A2A-Meta/api/middleware/live_clone_catalog.py`,
**not** by the child repo.

## 3. Repo-level rollback (catastrophic)

If the entire repo must be rolled back:

1. `git revert <bad-sha>` on a fresh branch in
   `Amondieu/a2a-meta-clones`.
2. Open a PR; CI runs the full test suite.
3. After merge, GitHub Actions deploys to all 3 slots
   (only the changed slot, due to path filters).
4. Run `python scripts/pipeline.py verify --all` (or per
   clone) to re-probe every clone.
5. Results recorded in `docs/promotion_log.md`.

The user is the only one authorized to merge to `main`.

## 4. Recovery from catalog write boundary violation

If a child-repo change ever writes to
`A2A-Meta/api/middleware/live_clone_catalog.py` (the catalog
write boundary §2.2 of the plan is violated):

1. **STOP** the offending operation immediately.
2. `git diff` A2A-Meta to identify the unintended change.
3. `git checkout` to revert the file.
4. Identify the root cause in the child-repo code.
5. Add a regression test (`tests/test_catalog_write_boundary.py`
   already exists; expand it).
6. Re-run the test suite.
7. Document the incident in `docs/promotion_log.md`.

This is the most serious category of error; the catalog is
the single source of truth for which clones are LIVE.
