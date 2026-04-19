# Deferred: Reconciler GHOST_CLOSURE Instrumentation

**Source:** A1 Phase 0 Proposal — DQ-3
**Deferred From:** Task A1 (signal_events extension + lifecycle instrumentation)
**Deferred To:** A1b or follow-up task
**Date:** 2026-04-19

## What Was Deferred

GHOST_CLOSURE event emission from the standalone reconciler service.

## Why Deferred

- Reconciler is a standalone service at a separate import path (`/home/oinkv/signal-gateway/scripts/signal_gateway/reconciler.py`, 924 LOC)
- Has its own process context and state management (`reconciler-state.json`)
- micro-gate already has `_log_event` calls in its closure path — once the zero-event bug is fixed, closure events from reconciler-triggered closes will flow through micro-gate's `_process_closure()`
- The reconciler's CLOSE_ACTIONS set (CLOSE, CLOSE_WIN, CLOSE_LOSS, SL_HIT, etc.) maps to existing TRADE_CLOSED_* event types

## Reviewer Endorsement

- **VIGIL:** Created follow-up tracking file per DQ-3 recommendation
- **GUARDIAN:** "Reconciler deferral is acceptable. micro-gate's existing `_log_event` calls in the closure path should capture most closure events once the zero-event bug is fixed."

## Implementation Notes

- Reconciler processes WealthGroup lifecycle signals (board/alert reconciliation)
- State persisted to `/home/oinkv/signal-gateway/status/reconciler-state.json`
- Close events flow: reconciler detects → triggers micro-gate `_process_closure()` → micro-gate emits TRADE_CLOSED_* event
- Direct reconciler instrumentation would add GHOST_CLOSURE for reconciler-initiated closes not routed through micro-gate
- Need to assess whether ANY close path bypasses micro-gate entirely

## Key Files

- `/home/oinkv/signal-gateway/scripts/signal_gateway/reconciler.py` (924 LOC)
- `/home/oinkv/signal-gateway/status/reconciler-state.json`
- `/home/oinkv/.openclaw/workspace/scripts/micro-gate-v3.py` — `_process_closure()` function
