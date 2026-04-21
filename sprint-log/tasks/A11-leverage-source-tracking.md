# Task A11 — Leverage Source Tracking

**Tier:** 🟢 LIGHTWEIGHT  
**Wave:** 3  
**Status:** ✅ DONE — Shipped, canary PASS  
**Repo target:** oinkfarm  
**Branch:** —  
**PR:** [oinkfarm#133](https://github.com/QuantisDevelopment/oinkfarm/pull/133)  
**Merge commit:** [45a6931d4436](https://github.com/QuantisDevelopment/oinkfarm/commit/45a6931d44364fa68c9fd96779c58b20d69e01ae)

## In plain English

A11 persists a leverage_source column (EXPLICIT / DEFAULT / NULL) alongside the leverage value at INSERT-time. This gives us provenance for every leverage number — we can tell which came from the signal and which were filled from defaults.

## One-liner

Persist a `leverage_source` column (`EXPLICIT` / `DEFAULT` / NULL) alongside the leverage value at micro-gate INSERT.

## Timeline

| # | Phase | Actor | Verdict | Timestamp (CEST) | Artifact |
|---|---|---|---|---|---|
| 1 | OinkV audit | 👁️ OinkV | PASS | 15:28 CEST on 19 Apr 2026 | [OINKV-AUDIT-WAVE3-A11.md](../../raw-artifacts/forge/plans/OINKV-AUDIT-WAVE3-A11.md) |
| 2 | Phase 0 approval | 🪽 Hermes | ✅ APPROVED | 16:36 CEST on 19 Apr 2026 | [A11-PHASE0-APPROVED.marker](../../raw-artifacts/anvil/proposals/A11-PHASE0-APPROVED.marker) |
| 3 | Phase 1 code | ⚒️ ANVIL | MERGED | — | [oinkfarm#133](https://github.com/QuantisDevelopment/oinkfarm/pull/133) |
| 4 | Backfill | ⚒️ ANVIL | executed | 16:54 CEST on 19 Apr 2026 | [A11-BACKFILL-LOG.md](../../raw-artifacts/anvil/backfill-logs/A11-BACKFILL-LOG.md) |

## Key Decisions

_(No structured decision list extractable from merge artifacts — see the MERGED marker + FORGE plan for decision trail.)_

## Deferrals (Follow-up Tasks)

_None._

## Artifacts (Full Index)

- **OinkV audit:** [OINKV-AUDIT-WAVE3-A11.md](../../raw-artifacts/forge/plans/OINKV-AUDIT-WAVE3-A11.md) — 14.8 KB
- **Backfill log:** [A11-BACKFILL-LOG.md](../../raw-artifacts/anvil/backfill-logs/A11-BACKFILL-LOG.md)
- **Merge commit:** [`45a6931d4436`](https://github.com/QuantisDevelopment/oinkfarm/commit/45a6931d44364fa68c9fd96779c58b20d69e01ae) (oinkfarm PR #133)
- **PR(s):** [oinkfarm#133](https://github.com/QuantisDevelopment/oinkfarm/pull/133)

## Lessons Learned

- **🟢 LIGHTWEIGHT path** skipped Phase 0 and GUARDIAN review per SOUL.md §0 — shipped in one round with VIGIL PASS only.
- **Backfill `leverage IS NOT NULL → EXPLICIT`** cleanly populated the new column for the 98 non-NULL historical rows.
- **ANVIL spot-check** (10 organic INSERTs post-deploy) substituted for GUARDIAN canary on LIGHTWEIGHT tier.
- **Backfill pre-SELECT + abort-if-rowcount guard** caught a data-quality anomaly without failing the migration.

---

*[Live dashboard](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/) · [GitHub repo](https://github.com/QuantisDevelopment/oinkfarm-sprint-checkpoint) · [All raw artifacts](../../raw-artifacts/)*
