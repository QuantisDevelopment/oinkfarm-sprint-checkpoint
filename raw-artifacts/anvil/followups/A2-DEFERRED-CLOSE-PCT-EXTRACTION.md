# Deferred: Provider Text close_pct Extraction

**Task:** A2 follow-up
**Created:** 2026-04-19
**Priority:** HIGH — directly improves PnL accuracy

## What
Extract actual `close_pct` from provider TP hit notifications (e.g., "TP1 (25%) hit", "Closed 25% at TP1") in signal_router.py or reconciler.

## Why deferred
- Requires changes to signal_router.py (4,366 LOC God Object) or reconciler — separate review surface from lifecycle.py
- A2 establishes the infrastructure (remaining_pct column, TP_HIT event with close_pct field, alloc_source tracking)
- Extraction accuracy for various text formats needs its own test suite

## When to implement
After A2 is merged and canary-verified. Can be a standalone 🟡 STANDARD task since calculate_blended_pnl() already handles the "extracted" path after A2.

## Acceptance criteria
- Cornix TP hit messages: extract close_pct from "TP1 (25%)" format
- WG TP hit messages: extract close_pct from embed fields
- alloc_source changes from "assumed" to "extracted" for signals with provider data
- FET #1159 ROI changes to 1.68% if provider sent 25% close (verify actual message)
