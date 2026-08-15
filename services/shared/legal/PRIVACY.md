# Privacy Policy (DRAFT stub)

> **Status:** DRAFT for operator / counsel review — **not legal advice**.  
> **Version:** `2026-08-15-draft`  
> **Effective when:** published to a live URL and `PRIVACY_URL` is set.  
> **Contact:** hallo@withkodex.com  

Do not treat this file as a finished GDPR Art. 12–13 notice until a qualified
person reviews it and the `[OPERATOR FILL]` fields are completed.

---

## 1. Who we are

**Controller (operator):** `[OPERATOR FILL: legal entity name]`  
**Address:** see [IMPRESSUM.md](./IMPRESSUM.md)  
**Email:** hallo@withkodex.com  

Product surface covered by this draft:

- Live multiplexer / discovery host: `https://a2a-meta-clones-production.up.railway.app`
- Related assessment / nurture funnel when enabled (Aug2 capture)

---

## 2. What we process (current product posture)

| Category | Examples | Typical purpose | Notes from current product design |
|:--|:--|:--|:--|
| Account / contact | Email, name if you provide them | Respond to inquiries, listing contact, transactional mail | Contact on Agent Card: `hallo@withkodex.com` |
| Assessment / funnel | Form answers, consent flags, recommended clones | Provide readiness / capture result | Requires explicit opt-in (default off) per Aug2 spec |
| Billing | Stripe customer / subscription identifiers | Pay2Go / team checkout | Processed by Stripe as payment provider |
| Technical logs | Request metadata on our hosts | Security, reliability, abuse prevention | Raw IP/UA are **not** stored for assessments unless a documented legal basis exists (hashes only, columns may stay NULL) |
| Customer evidence inputs | Agent-run logs / evidence `sources` you upload or send to the API | Produce deterministic evidence artifacts | May contain personal data **you** control — see §5 |

We do **not** use the evidence path to train foundation models. The EU AI Act
deployer evidence loop is designed as a deterministic, zero-LLM path for the
artifact itself.

---

## 3. Legal bases (draft mapping — confirm with counsel)

| Processing | Draft basis (to confirm) |
|:--|:--|
| Responding to your email / listing contact | Contract / steps prior to contract (Art. 6(1)(b)) or legitimate interest (Art. 6(1)(f)) |
| Assessment capture + nurture emails | **Consent** (Art. 6(1)(a)) — versioned privacy policy binding; one-click unsubscribe |
| Stripe checkout / billing | Contract (Art. 6(1)(b)) + legal obligation where applicable |
| Security / abuse logs | Legitimate interest (Art. 6(1)(f)) |

---

## 4. Recipients / processors (as designed today)

| Party | Role |
|:--|:--|
| Railway | Hosting (EU-oriented residency goal stated on Agent Card; confirm region with operator) |
| Stripe | Payments |
| Resend (when email pipeline is enabled) | Transactional / nurture email |
| `[OPERATOR FILL: other subprocessors]` | — |

A written DPA with customers who send personal data in evidence logs is
**planned but not published** in this stub.

---

## 5. Your responsibilities (evidence / customer data)

If you submit agent logs or other materials that contain personal data, you
are typically the controller of that content. You must have a lawful basis to
share it with us. We process it to provide the service (evidence / posture
artifacts) under the terms you accept and any DPA you sign with us.

Retention for customer evidence: `[OPERATOR FILL: retention period]`.  
Deletion / access requests: email hallo@withkodex.com (target response: 30 days).

---

## 6. Cookies / tracking

This stub assumes **no marketing cookies** on the discovery / multiplexer
surface unless separately disclosed. Assessment attribution may store UTM
parameters on the assessment record when the funnel is enabled — not full
referrer URLs (per Aug2 “explicitly do not store” list).

---

## 7. International transfers

Draft posture: prefer EU processing. If a processor transfers data outside the
EEA, `[OPERATOR FILL: SCC / transfer tool]`.

---

## 8. Your rights

Subject to applicable law (GDPR): access, rectification, erasure, restriction,
portability, objection, and withdrawal of consent.  
Complaint: your local supervisory authority (`[OPERATOR FILL: e.g. CNIL / BfDI]`).

---

## 9. Changes

We will bump `privacy_policy_version` (e.g. `2026-08-15-draft` → dated release)
when this becomes live. Material changes require re-consent where consent is
the basis for processing.

---

## 10. Not legal advice disclaimer

This policy describes product intent. It is **informational, not legal advice**.
Verify with your DPO, CISO, and a qualified legal or compliance professional
before relying on outputs of the service or before treating this stub as final.
