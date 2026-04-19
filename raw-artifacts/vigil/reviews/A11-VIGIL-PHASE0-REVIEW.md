# VIGIL Proposal Review — A11: Leverage Source Tracking

**Verdict:** APPROVE

**Tier:** 🟢 LIGHTWEIGHT
**Note:** Per SOUL.md §0, LIGHTWEIGHT tasks skip Phase 0 entirely. ANVIL submitted a proposal anyway — reviewing as courtesy since it's here. No Financial Hotpath files are touched; tier confirmed LIGHTWEIGHT.

---

**Spec Alignment:** The FORGE plan's core decision — track leverage provenance rather than manufacture defaults — aligns with Arbiter-Oink Phase 3 §ADAPT/leverage-model. The approach correctly identifies that NULL is informationally accurate for 80.1% of signals and that defaulting leverage manufactures false precision for PnL. Schema change (`ALTER TABLE ADD COLUMN leverage_source VARCHAR(20) DEFAULT NULL`) is additive and non-destructive. Only `EXPLICIT` and `NULL` written today per §4a; `EXTRACTED`/`DEFAULT` reserved for future — this is the correct scoping.

**Acceptance Criteria Coverage:** 5 tests mapped to 5 acceptance criteria:
1. Explicit numeric leverage → EXPLICIT ✅
2. No leverage → NULL ✅
3. String "10x" parse → EXPLICIT ✅
4. Unparseable "5x-10x" → NULL ✅
5. Backfill correctness (98 rows) ✅

All 4 MUST tests cover the two primary code paths (EXPLICIT vs NULL). SHOULD test covers the backfill. Adequate for LIGHTWEIGHT.

**Concerns:** None blocking.

**Suggestions:**
1. OinkV audit notes the INSERT line reference is stale (plan says 855, actual ~922). ANVIL will grep anyway — non-blocking.
2. OinkV found the leverage distribution table is stale (non-NULL values have redistributed). The aggregate 395/493 NULL count is still exact. Non-blocking.
3. Confirm `ext.get("leverage")` is checked BEFORE the normalization block mutates `leverage` — the source determination must use the raw extraction value, not the post-normalization float. The proposal's placement ("after the existing leverage normalization block") is correct only if `ext.get("leverage")` is read before the block overwrites the local variable. Verify during Phase 1.

---

**Review Date:** 2026-04-19
