# EDA 0 — Checkpoint C: Temporal integrity (C18–C24)

**Status:** Checkpoint C committed to `analysis/eda0-data-foundation` after explicit authorization, with both C21/C24 and C22 traceability corrections incorporated; pending further review. No pull request, merge, KPI or treatment-effect assessment is authorized. Checkpoints A/B retain historical V7/local-validation caveats.

## Reproduction and inputs

- Notebook: `notebooks/00_data_foundation/02_C_temporal_integrity.ipynb` (all seven C IDs; executable checks and recorded Jupyter outputs).
- Source: immutable CSVs in `data/raw/`; Python 3.13.5 with Pandas 2.2.3; all timestamps parsed as UTC without modifying source strings.
- Source SHA-256: exposures `9cce67cd8d90d292c0703416b3c28c69783c56d10c2f997bf614b2bc84445327`; assignments `c66a6d5cb89b62bc3542ee9184e75c8ded41589e91dac9d726639acad0db0ff2`; logs `ab6bf97f2ca216504058b5de1deb2f80641d783e8e23651d3efc2d595675879a`.
- Prior references verified: 14,708 registered hosts; 279,847 completed assignments; 306,957 logged payment attempts; 2,316 status/timestamp disagreements in B12.

## Findings by question

| ID | Directly observed evidence | Validation | Technical limit / status |
|---|---|---|---|
| C18 | First-exposure dates 2025-08-18 to 2025-11-19; project completion 2025-07-18 to 2025-11-19; payment creation as early as 2022-02-13 and as late as 2025-12-19; captures from 2024-10-08 through 2025-12-19. All source temporal strings parse as UTC when present. | Valid + missing + invalid reconcile to each source grain. | Observed maxima are **not** independently verified export cutoffs. Answered for observed coverage. |
| C19 | **9** projects have `completed_at` before `created_at`; **1,821** attempts have `captured_at` preceding log `created_at` (1–6 seconds before, median 2 seconds); 3,175 share the same timestamp. | All timestamped/untimestamped log comparisons reconcile to 306,957 attempts; examples in notebook. | A small negative delta is not automatically financial fraud or invalid settlement. Answered as technical chronology. |
| C20 | **284,113** payment logs created before project completion; **22,843** after and **1** at the same instant. | One-to-many joins checked; all attempts preserved. | Log creation is not a verified failure, charge or CS alert time. Answered descriptively. |
| C21 | Of 279,285 populated capture timestamps, **156** occur before completion and **279,129** after; no same-instant captures in the extract. **New:** status/capture discordance tables by project completion time and payment-log creation time, with explicit UTC periods and group counts. | Attempt categories total 306,957 including 27,672 missing timestamps; project-level counts shown separately and overlapping. | Early capture records are preserved, not silently discarded. Answered for timestamp evidence, not full settlement. |
| C22 | **65,294** projects were booked before first recorded exposure and completed afterward; **5,091** experiment-period projects were completed **before** first recorded exposure (Control 2,573; Test 2,518). **New:** reproducible group table, data-derived reconciliation assertions, independent host lookup and reported-vs-recomputed comparison. | Full-extract cross-tab totals 279,847; experiment-period partition independently checked. | `first_exposed_at` does not prove randomization instant or treatment application. Answered for recorded chronology. |
| C23 | Candidate D0, D1, D7, D14 follow-up deadlines are strictly before Dec 19 00:00 UTC for all 279,847 projects. For D30, **278,595** deadlines are strictly before Dec 19 and **1,252** fall on Dec 19, where completeness depends on the unknown exact export cutoff time. | Exhaustive project partitions; elapsed-time bounds rather than calendar dates; independent standard-library CSV verification. | Documentation says tracking *through* Dec 19 without a precise final UTC observation instant or a completeness guarantee. These categories are **potential documented-horizon coverage**, not verified extraction completeness or payment outcomes. Partially answerable. |
| C24 | Before/during/after incident event distributions are in the notebook for completion, payment record creation, capture time and manual-flagged record creation. **New:** linked C21/C24 discordance distributions based separately on project completion and log creation dates. **1,245** manual-flagged payment records were *created* during Sept 17–30 (Control 354; Test 891). | Each source-time distribution reconciles within its event grain and recorded group. | This **does not** contradict the documented missing Test CS alerts for failures in that incident: log `created_at` does not prove the actual failure/manual-recovery date or alert eligibility. No alert stream exists. Partially answerable. |

## Targeted traceability corrections — C21/C24 and C22

These two additions respond only to the technical review; no records were recoded, removed or excluded, no capture rule or experimental outcome was defined, and Checkpoint E is unchanged. The tables below are reproducible from the executed Checkpoint C notebook. All timestamps use **UTC** and these **non-overlapping, half-open periods**:

| Period code | UTC interval |
|---|---|
| `before_baseline` | before `2025-07-18T00:00:00Z` |
| `baseline` | `[2025-07-18T00:00:00Z, 2025-08-18T00:00:00Z)` |
| `experiment_pre_incident` | `[2025-08-18T00:00:00Z, 2025-09-17T00:00:00Z)` |
| `CS_incident` | `[2025-09-17T00:00:00Z, 2025-10-01T00:00:00Z)` (September 17–30, inclusive) |
| `experiment_post_incident` | `[2025-10-01T00:00:00Z, 2025-11-20T00:00:00Z)` |
| `after_experiment` | from `2025-11-20T00:00:00Z` onward |
| `unknown_timestamp` | null or unparseable timestamp |

### C21/C24 — B12 discordances by **project completion timestamp**

Each payment **attempt** is assigned to the completion period of its recorded project. Each project has one recorded completion timestamp and one registered experiment group, so distinct project counts **can be summed** in this table.

| Group | UTC period | Discordant attempts | Distinct projects within period |
|---|---|---:|---:|
| Control | `baseline` | 271 | 244 |
| Control | `experiment_pre_incident` | 268 | 238 |
| Control | `CS_incident` | 112 | 100 |
| Control | `experiment_post_incident` | 484 | 417 |
| Test | `baseline` | 285 | 259 |
| Test | `experiment_pre_incident` | 349 | 321 |
| Test | `CS_incident` | 92 | 88 |
| Test | `experiment_post_incident` | 455 | 408 |
| **Total** | **All periods (distinct projects additive)** | **2,316** | **2,075** |

**Reconciliation:** 2,316 discordant attempts; **2,075 unique affected projects**, equal to the sum of the project-count column. `before_baseline`, `after_experiment` and `unknown_timestamp` had zero discordant attempts in this completion-time view.

### C21/C24 — B12 discordances by **payment-log creation timestamp**

The grouping timestamp is **`payment_logs.created_at`**, not `assignments.completed_at` and **not** the timestamp of the actual payment failure, capture, missing CS alert, or support intervention.

| Group | UTC period | Discordant attempts | Distinct projects within period |
|---|---|---:|---:|
| Control | `before_baseline` | 13 | 13 |
| Control | `baseline` | 275 | 256 |
| Control | `experiment_pre_incident` | 260 | 237 |
| Control | `CS_incident` | 126 | 117 |
| Control | `experiment_post_incident` | 443 | 396 |
| Control | `after_experiment` | 18 | 14 |
| Test | `before_baseline` | 15 | 15 |
| Test | `baseline` | 280 | 261 |
| Test | `experiment_pre_incident` | 340 | 316 |
| Test | `CS_incident` | 116 | 112 |
| Test | `experiment_post_incident` | 425 | 382 |
| Test | `after_experiment` | 5 | 4 |
| **Total** | **All periods (distinct projects not additive)** | **2,316** | **2,123** |

**Reconciliation:** 2,316 attempts; **2,075 globally unique projects** across all rows. The project column sums to **2,123 project-period memberships**, exceeding the global unique count by **48 memberships** because the same project can have discordant logs created in more than one period. Summing these per-period distinct-project figures as though they were unique would be incorrect. There were zero discordant attempts with an unknown creation timestamp.

**Interpretation constraint:** temporal coincidence with the CS incident does **not** establish causation or identify which alert should have been sent. No status-vs-timestamp precedence was chosen and neither table is an experimental outcome comparison.

### C22 — Experiment completions **strictly before** recorded first exposure

The reproducible filter is `completed_at >= 2025-08-18T00:00:00Z AND completed_at < 2025-11-20T00:00:00Z AND completed_at < first_exposed_at`, with both timestamps parsed as UTC and matched by `host_id`. The project group is taken from `experiment_exposures.csv`, and each completed project appears once.

| Recorded group | Recomputed projects | Previously reported projects | Difference |
|---|---:|---:|---:|
| Control | 2,573 | 2,573 | +0 |
| Test | 2,518 | 2,518 | +0 |
| **Total** | **5,091** | **5,091** | **+0** |

The group sum is asserted against the **data-derived mask count**, not the reference numbers. A second project-to-host mapping independently reproduces the same group counts; the one-off `csv.DictReader` verification also independently reproduces **2,573 + 2,518 = 5,091**. **No discrepancy with the prior report was found.** These projects remain included; no experimental eligibility rule has been changed.

### Validation of these changes

- **36 existing pytest tests passed**, without adding unnecessary helper modules or changing Checkpoint E.
- The C notebook completed **10/10 code cells from a clean Python 3.13.5 Jupyter kernel**, with no cell exceptions and saved outputs. **V7 for this C revision: PASSED in the authoring environment.** Historical A/B V7 and the user's local reproduction remain separate.
- Synthetic assertions inside the new notebook section cover each half-open UTC boundary (including incident start and end), missing timestamps, all category sums, cross-grain distinct-project counts, and an independent recomputation of the C22 mask.
- A **standard-library CSV-only** cross-check (no Pandas or notebook code) independently confirmed both period tables, 2,316 discordant attempts, 2,075 global projects, 2,123 creation-period memberships, and C22 group/total counts.
- The only residual constraints are those already established: `created_at` cannot locate the actual failure or CS alert; temporal association is not causal; `first_exposed_at` does not prove randomization or treatment activation; B12's status/capture contradictions remain unresolved.

## Follow-up diagnostic: time-of-day uncertainty

| Candidate elapsed window | Conservative documented-horizon coverage* | Deadline on unverified final day | Beyond documented calendar-day horizon | Projects with a timestamped capture at/before deadline** |
|---|---:|---:|---:|---:|
| D0 (instant of completion) | 279,847 | 0 | 0 | 156 |
| D1 (24 h) | 279,847 | 0 | 0 | 275,697 |
| D7 (7 days) | 279,847 | 0 | 0 | 277,977 |
| D14 (14 days) | 279,847 | 0 | 0 | 278,279 |
| D30 (30 days) | 278,595 | 1,252 | 0 | 278,471 |

*Strictly earlier than `2025-12-19T00:00:00Z`, assuming the stated follow-up period is complete up to that instant. Completeness itself is not independently verified. **Includes valid recorded captures preceding project completion, because this is a timestamp-only observation check, not an approved capture-within-window KPI. The notebook also reports within-[completion, deadline] captures separately. A missing captured timestamp, an insufficient horizon, or a status-only success is **not** a definitive failed payment.

## Verification, dependencies and limitations

- **V1/V3:** project/attempt denominators and all exhaustive categories reconcile. Overlapping project categories are identified.
- **V2:** payment-to-project joins are many-to-one and row-preserving; original host associations checked.
- **V4:** capture timestamps used only for event placement. B12 discordance remains; no authoritative payment-success rule adopted.
- **V5/V6:** UTC and exact elapsed-day boundaries, ties, unknown timestamps and endpoint cases covered by synthetic tests and explicit checks.
- **V7 (C): passed in the current author's Python 3.13.5 Jupyter kernel via `nbclient`,** from a clean kernel, ten code cells, no exceptions, outputs saved. Reproducing in the user's local `.venv` remains a separate acceptance activity. **Historical A/B V7 remains OPEN.**
- **V8:** a separate `csv.DictReader` stream in `tests/check_ce_source_reconciliations.py` independently checked negative project duration, capture-before-log timestamps, D30 final-day boundaries, period totals and host population intersections.

**Block-dependent caveat for E:** no fatal population-key or temporal coverage failure prevents E35–E43 descriptions. However, any *future* rate involving a payment deadline or exposure-defined denominator must resolve the missing export cutoff time, B12 status/capture discordance and the 5,091 experiment-period completions before recorded first exposure. No further C-based business interpretation is authorized.
