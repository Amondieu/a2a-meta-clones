# a2a-meta-clones — promotion log

> **Format:** append-only. Each section is a single probe or
> promotion event. The log is the audit trail for HTTP
> verification history.
> **Verifiers:** `pipeline.py verify`, `pipeline.py promote`,
> `pipeline.py demote`, and the A2A-Meta-side manual review.
> **Retention:** permanent. Roll-back is achieved by writing a
> new DEMOTED entry, never by deleting a row.
> **v1 evidence record (mandatory):** see
> `A2A-Meta/docs/clone_repo_architecture_v0_DRAFT.md` §8.1 for
> the immutable evidence record fields.

---

<!-- Entries are appended below this line by `pipeline.py`. Do NOT edit existing rows. -->
