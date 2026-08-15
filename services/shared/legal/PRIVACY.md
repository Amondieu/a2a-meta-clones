# Privacy Policy (operator-attested draft)

> **Status:** Operator fields filled from known product posture — **counsel / DPO review still required**. Not legal advice.  
> **Version:** `2026-08-15-operator-v1`  
> **Effective when:** published on the live branded hosts.  
> **Contact:** hallo@withkodex.com  

---

## 1. Who we are

**Controller (operator):** withkodex / A2A-Meta service operator (register details on request — see [IMPRESSUM.md](./IMPRESSUM.md))  
**Address:** see [IMPRESSUM.md](./IMPRESSUM.md)  
**Email:** hallo@withkodex.com  

Product surfaces covered:

- https://auditor.withkodex.com (discovery-auditor)
- https://slot-2.withkodex.com and related multiplexer hosts
- Related assessment / nurture funnel when enabled

---

## 2. What we process (current product posture)

| Category | Examples | Typical purpose | Notes |
|:--|:--|:--|:--|
| Account / contact | Email, name if you provide them | Inquiries, listing contact, transactional mail | Agent Card: `hallo@withkodex.com` |
| Assessment / funnel | Form answers, consent flags | Readiness / capture result | Explicit opt-in when enabled |
| Billing | Stripe customer / subscription identifiers | Checkout, entitlements, metered `scan_run` | Stripe as payment processor |
| Technical logs | Request metadata | Security, reliability, abuse prevention | Prefer hashed identifiers where feasible |
| Customer evidence inputs | Logs / sources you submit | Produce informational audit artifacts | You remain controller of that content |

We do **not** use the evidence path to train foundation models.

---

## 3. Legal bases (draft mapping — confirm with counsel)

| Processing | Draft basis (to confirm) |
|:--|:--|
| Email / listing contact | Art. 6(1)(b) and/or (f) GDPR |
| Assessment + nurture | Consent Art. 6(1)(a) when enabled |
| Stripe checkout / billing | Art. 6(1)(b) + legal obligation where applicable |
| Security / abuse logs | Art. 6(1)(f) |

---

## 4. Recipients / processors (as designed today)

| Party | Role |
|:--|:--|
| Railway | Hosting |
| Stripe | Payments / metering |
| Resend (when email pipeline enabled) | Transactional / nurture email |
| Cloudflare (DNS / optional proxy) | DNS for branded hosts |

A written DPA for enterprise customers is **available on request** via hallo@withkodex.com.

---

## 5. Your responsibilities (evidence / customer data)

If you submit materials containing personal data, you typically remain the controller of that content and must have a lawful basis to share it.

**Retention for customer evidence:** 90 days after last successful job unless a longer retention is agreed in writing, then deleted or anonymized.  
Deletion / access requests: hallo@withkodex.com (target response: 30 days).

---

## 6. Cookies / tracking

No marketing cookies on the discovery / multiplexer surface unless separately disclosed. Assessment attribution may store UTM parameters when the funnel is enabled.

---

## 7. International transfers

Prefer EU processing. Where a processor transfers data outside the EEA, we rely on **EU Standard Contractual Clauses (SCCs)** or an adequacy decision, as documented in that processor’s DPA.

---

## 8. Your rights

Subject to applicable law (GDPR): access, rectification, erasure, restriction, portability, objection, and withdrawal of consent.  
Complaint: your local supervisory authority (e.g. BfDI in Germany, CNIL in France, or your Member State DPA).

---

## 9. Changes

We bump `privacy_policy_version` on material changes. Re-consent where consent is the processing basis.

---

## 10. Not legal advice disclaimer

This policy describes product intent. It is **informational, not legal advice**.
Verify with your DPO, CISO, and qualified counsel before relying on service outputs or treating this draft as final.
