# Task A9 — Denomination Multiplier Table (1000x-prefixed symbols)

**Tier:** 🟢 LIGHTWEIGHT  
**Wave:** 3  
**Status:** 🛑 BLOCKED — Blocked on decision or dependency  
**Repo target:** oinkfarm  
**Branch:** —  
**PR:** [oink-sync#8](https://github.com/QuantisDevelopment/oink-sync/pull/8) + [oinkfarm#132](https://github.com/QuantisDevelopment/oinkfarm/pull/132)  
**Merge commit:** [27196487f966](https://github.com/QuantisDevelopment/oink-sync/commit/27196487f966fc6e24d2a412b7245ac8c9883c50) + [e7cfdb8e22ae](https://github.com/QuantisDevelopment/oinkfarm/commit/e7cfdb8e22aed4a3c41b33a126f9c58012f0bcf5)

## One-liner

Normalize entry + SL prices for `1000*USDT` symbols by dividing by 1000 at INSERT, and tag with `[A9: denomination_adjusted /1000]`.

## Timeline

| # | Phase | Actor | Verdict | Timestamp (CEST) | Artifact |
|---|---|---|---|---|---|
| 1 | OinkV audit | 👁️ OinkV | PASS | 15:29 CEST on 19 Apr 2026 | [OINKV-AUDIT-WAVE3-A9.md](../../raw-artifacts/forge/plans/OINKV-AUDIT-WAVE3-A9.md) |
| 2 | Phase 1 code | ⚒️ ANVIL | MERGED | — | [oink-sync#8](https://github.com/QuantisDevelopment/oink-sync/pull/8) + [oinkfarm#132](https://github.com/QuantisDevelopment/oinkfarm/pull/132) |

## Key Decisions

_(Pending — will be distilled after merge.)_

## Deferrals (Follow-up Tasks)

_None._

## Artifacts (Full Index)

- **OinkV audit:** [OINKV-AUDIT-WAVE3-A9.md](../../raw-artifacts/forge/plans/OINKV-AUDIT-WAVE3-A9.md) — 21.6 KB
- **Merge commit:** [`27196487f966`](https://github.com/QuantisDevelopment/oink-sync/commit/27196487f966fc6e24d2a412b7245ac8c9883c50) (oink-sync PR #8)
- **Merge commit:** [`e7cfdb8e22ae`](https://github.com/QuantisDevelopment/oinkfarm/commit/e7cfdb8e22aed4a3c41b33a126f9c58012f0bcf5) (oinkfarm PR #132)
- **PR(s):** [oink-sync#8](https://github.com/QuantisDevelopment/oink-sync/pull/8) · [oinkfarm#132](https://github.com/QuantisDevelopment/oinkfarm/pull/132)

## Lessons Learned

_(Written after canary verdict.)_

---

*[Live dashboard](https://quantisdevelopment.github.io/oinkfarm-sprint-checkpoint/) · [GitHub repo](https://github.com/QuantisDevelopment/oinkfarm-sprint-checkpoint) · [All raw artifacts](../../raw-artifacts/)*
