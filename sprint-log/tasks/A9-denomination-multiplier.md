# Task A9 — Denomination Multiplier Table (1000x-prefixed symbols)

**Tier:** 🟢 LIGHTWEIGHT  
**Wave:** 3  
**Status:** ✅ DONE — Shipped, canary PASS  
**Repo target:** oinkfarm  
**Branch:** —  
**PR:** [oink-sync#8](https://github.com/QuantisDevelopment/oink-sync/pull/8) + [oinkfarm#132](https://github.com/QuantisDevelopment/oinkfarm/pull/132)  
**Merge commit:** [27196487f966](https://github.com/QuantisDevelopment/oink-sync/commit/27196487f966fc6e24d2a412b7245ac8c9883c50)

## In plain English

A9 normalizes entry + SL prices for 1000x-prefixed symbols (1000SHIB, 1000PEPE, …) by dividing by 1000 at INSERT. Before this, ~7% of signals had off-by-1000 prices and the SL_DEVIATION guard incorrectly rejected valid signals.

## One-liner

Normalize entry + SL prices for `1000*USDT` symbols by dividing by 1000 at INSERT, and tag with `[A9: denomination_adjusted /1000]`.

## Timeline

| # | Phase | Actor | Verdict | Timestamp (CEST) | Artifact |
|---|---|---|---|---|---|
| 1 | OinkV audit | 👁️ OinkV | PASS | 15:29 CEST on 19 Apr 2026 | [OINKV-AUDIT-WAVE3-A9.md](../../raw-artifacts/forge/plans/OINKV-AUDIT-WAVE3-A9.md) |
| 2 | Phase 1 code | ⚒️ ANVIL | MERGED | — | [oink-sync#8](https://github.com/QuantisDevelopment/oink-sync/pull/8) + [oinkfarm#132](https://github.com/QuantisDevelopment/oinkfarm/pull/132) |

## Key Decisions

_(No structured decision list extractable from merge artifacts — see the MERGED marker + FORGE plan for decision trail.)_

## Deferrals (Follow-up Tasks)

_None._

## Artifacts (Full Index)

- **OinkV audit:** [OINKV-AUDIT-WAVE3-A9.md](../../raw-artifacts/forge/plans/OINKV-AUDIT-WAVE3-A9.md) — 21.6 KB
- **Merge commit:** [`27196487f966`](https://github.com/QuantisDevelopment/oink-sync/commit/27196487f966fc6e24d2a412b7245ac8c9883c50) (oink-sync PR #8)
- **PR(s):** [oink-sync#8](https://github.com/QuantisDevelopment/oink-sync/pull/8) · [oinkfarm#132](https://github.com/QuantisDevelopment/oinkfarm/pull/132)

## Lessons Learned

- **Normalize early, dedup after** — entry-price normalization had to move to §3b (before all guards) so the snowflake dedup probe at §4 + §4b matched stored values (GUARDIAN P2 fix).
- **SL normalization in §8a-A9** (before B11 deviation guard) prevented valid 1000x signals with SL from being rejected by the SL_DEVIATION guard (GUARDIAN P1 fix).
- **R2 delta review** converged all three reviewers (VIGIL 9.40 · GUARDIAN 9.80 · Hermes LGTM) after 2 rounds.
- **INSERT-time-only scope** deliberately left UPDATE and CLOSURE normalization for A9.1 follow-up — avoided blast-radius creep.

---

*[Live dashboard](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/) · [GitHub repo](https://github.com/QuantisDevelopment/oinkfarm-sprint-checkpoint) · [All raw artifacts](../../raw-artifacts/)*
