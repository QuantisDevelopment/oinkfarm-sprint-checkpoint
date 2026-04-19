# Deferred: oinkdb-api.py Event Instrumentation

**Source:** A1 Phase 0 Proposal — DQ-2
**Deferred From:** Task A1 (signal_events extension + lifecycle instrumentation)
**Deferred To:** A1b or A4
**Date:** 2026-04-19

## What Was Deferred

Three event types that should be emitted from oinkdb-api.py (FastAPI REST application):

1. **ENTRY_CORRECTED** — When entry price is corrected via API
2. **FIELD_CORRECTED** — When any signal field is corrected via API
3. **NOTE_ADDED** — When a note is added to a signal via API

## Why Deferred

- oinkdb-api.py is a FastAPI app with async connection pooling — different lifecycle pattern from synchronous oink-sync
- Thread safety and connection handling need separate review
- A1 is already 🔴 CRITICAL scope — adding async FastAPI instrumentation increases review surface unnecessarily
- These 3 event types are low-frequency correction events — deferring won't block the Phase A >95% coverage gate

## Reviewer Endorsement

- **VIGIL:** "The oinkdb-api.py deferral is sound. FastAPI's async connection pooling is a genuinely different integration pattern."
- **GUARDIAN:** "oinkdb-api.py deferral is acceptable. The FastAPI async context is genuinely different from the synchronous lifecycle.py pattern."

## Implementation Notes

- EventStore uses synchronous sqlite3.Connection — may need async wrapper or thread-local for FastAPI
- oinkdb-api.py currently has NO event_store import
- Correction endpoints are at `/signals/{id}` (field updates)
- Consider whether EventStore needs an async variant or if sync calls are acceptable in FastAPI endpoints

## Key Files

- `/home/oinkv/.openclaw/workspace/api/oinkdb-api.py` (1,748 LOC)
- `/home/oinkv/.openclaw/workspace/scripts/event_store.py` (209 LOC)
