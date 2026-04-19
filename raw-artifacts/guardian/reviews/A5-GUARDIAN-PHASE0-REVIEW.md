## GUARDIAN Proposal Review — A5

**Verdict:** APPROVE

**Data Safety:**
The proposed change is metadata-only and additive. It updates how `signals.confidence` is assigned at INSERT time for new rows when the extractor did not provide an explicit confidence. It does not change any financial fields, lifecycle state, PnL logic, or dedup keys. Existing explicit extractor confidence values are preserved if the implementation follows the proposed `ext.get("confidence") is None` guard before defaulting.

**Migration Risk:**
Safe. No DDL, no schema migration, no backfill, no rewrite of the existing 492 rows. I agree with the forward-only approach here. Confidence is descriptive metadata, not a financial calculation input, so historical backfill is not required for safety and would create unnecessary mixed-era reinterpretation risk.

**Query Performance:**
No query-path risk introduced. This is a Python-side constant lookup (`PARSER_CONFIDENCE_MAP.get(method, 0.8)`) on the ingest path. No new indexes, joins, scans, or write amplification beyond the existing INSERT.

**Regression Risk:**
Low, but real at the downstream filtering layer. Any consumer using numeric thresholds on `signals.confidence` will see a distribution shift for newly inserted rows only. In practice:
- thresholds at or below `0.70` will admit more `llm_nl` / `qwen_v3` / `inline_fallback` signals than before only if they were previously relying on the blunt 0.80 default
- thresholds at or above `0.80` will now exclude these lower-confidence parser paths
This is acceptable because the proposal correctly frames the change as improving metadata fidelity, and the downstream audit indicates no financial or lifecycle consumer depends on this field.

**Concerns:**
1. The `oinxtractor_agent = 0.75` value is still an estimate, not a measured production-backed calibration. The proposal does address this by explicitly flagging it for Mike's validation. I do not consider that a Phase 0 blocker because the change is metadata-only and the fallback behavior is safe, but the PR should preserve that note clearly.
2. The implementation must use the explicit `is None` detection before normalization. A post-normalization equality check against `0.8` would be unsafe because it would overwrite legitimate extractor-supplied `0.8` values.
3. Downstream analytics or filters that compare old and new signals by raw confidence should expect a forward-only regime change. That is a reporting interpretation issue, not a data integrity issue.

**Suggestions:**
- Keep the change strictly forward-only, no historical backfill.
- In the PR description, explicitly restate that this is a metadata distribution change for new rows only.
- Keep `oinxtractor_agent` called out as Mike-validated / provisional so later recalibration is straightforward if production evidence suggests a different score.
- For post-deploy verification, sample recent inserts by extraction method and confirm explicit extractor confidences remain untouched.
