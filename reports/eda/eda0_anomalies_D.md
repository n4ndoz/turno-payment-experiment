# EDA 0 — Checkpoint D: Technical anomaly and interpretation-dependency inventory

**Scope:** observed raw-record patterns and their technical implications. All counts are for the immutable provided extract; each row preserves the distinction between evidence and financial truth. `created_at` is the payment **record creation** timestamp, not necessarily the financial event time.

| ID | Evidence and grain | Technical limitation / decision dependency | Status |
|---|---|---|---|
| D25-Z | 239 completed projects (project grain) have zero payment logs. | Neither paid nor unpaid can be inferred; retain in future denominators unless explicitly approved otherwise. | Open interpretation |
| D25-T | 14,107 projects have >1 logged attempt, maximum 37. | Attempt rows are not necessarily new charges or retries. | Observed; operation identity unknown |
| D26-M | 3,410 projects contain >1 payment method; five contain all three recorded methods. | Method selection may change following treatment; cannot infer host's independently chosen/default method. | Observed; causal use undecided |
| D29-T | One project has two attempt records with the same creation timestamp. | Their order cannot be established; no arbitrary ordering was used. | Handled for technical sequence calculations |
| D31-M | 5,348 projects have a manual flag, with 4,836 having a failure-status record created before the earliest manual record. | Manual attempt flag is not a complete CS intervention log; creation time is not failure/alert time. | Observed; actual CS sequence unknown |
| D32-R | 7,125 projects contain both failure and success statuses; 7,108 have earlier-created failure-status record than success-status record; 16 reverse; one is creation-time ambiguous. | Compatible with follow-up activity, not verified recovery or time-to-recovery. | Observed; operation timeline unavailable |
| D33-X | 2,316 status/timestamp-discordant attempts affect 2,075 projects. | Any automatic source-of-truth choice changes financial-evidence classification. | Decision pending |
| D33-C | 652 projects have >1 populated capture timestamp row; 200 span >1 captured-method category. | Without transaction IDs, amounts and ledger, cannot identify double charge or complementary settlement. | Observed; financial interpretation unknown |
| D34-S | 140 projects have both success-status and capture evidence, but never within the same attempt. | Same-attempt concordance selects a stricter set than project-level coexistence; status/capture data provenance required. | Decision pending |
| D34-U | 1,304 timestamp-only projects; 36 status-only projects; 1,013 have logged attempts but neither evidence; 239 have no logs. | These are evidence classes, **not** financial payment states or exclusions. | Decision pending |
| D34-H | Experiment-period pre-exposure projects identified in C and unknown exact extraction end-of-day affect downstream definitions. | See C/E follow-up windows and registered/exposed populations; D does not recode eligibility or censoring. | Deferred methodology |

**No anomaly is repaired, imputed, dropped or automatically classified as a monetary loss.** The technical triage union of 2,402 projects is not an approved exclusion or exhaustive ambiguity population. Business/methodological decisions remain with Fernando and Jurandir (with Adelaide when authorized).
