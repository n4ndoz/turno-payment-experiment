# EDA 0 / Checkpoint A — Initial data dictionary

**Source:** *Turno Data Analyst Take-Home: Payment Authorization Experiment*, pp. 2–3. The "meaning" column below reflects the PDF, not a newly approved business definition. Counts are computed from the three CSVs supplied for this checkpoint. All fields were read as **source strings** to avoid silent conversion of IDs, categories, dates and booleans. UTC parsing is only diagnostic, on derived arrays.

| File / effective row grain | Field | PDF-documented meaning | Observed diagnostic |
|---|---|---|---|
| `experiment_exposures.csv` / host | `host_id` | Host identifier | 14,708 distinct, zero nulls, unique |
| | `experiment_group` | Control or Test | `control` 7,377; `test` 7,331, zero nulls |
| | `first_exposed_at` | When first exposed | Zero nulls; all non-null fields parsed as UTC |
| `assignments.csv` / **completed** project | `assignment_id` | Completed marketplace cleaning project | 279,847 distinct, zero nulls, unique |
| | `host_id` | Host who booked project | Zero nulls; all match exposures |
| | `created_at` | When project was booked | Zero nulls; all parsed as UTC |
| | `completed_at` | When cleaner completed project | Zero nulls; all parsed as UTC |
| | `is_first_completed_project` | First project host ever completed in marketplace | `true` 2,755; `false` 277,092; zero nulls; **historical assertion, not independently proven** |
| `payment_logs.csv` / payment attempt | `payment_log_id` | Payment attempt identifier | 306,957 distinct, zero nulls, unique |
| | `assignment_id` | Project being paid | Zero nulls; all match assignment IDs |
| | `host_id` | Host being charged | Zero nulls; all match the project host ID |
| | `payment_method` | Card, bank account/ACH, Turno credits | `card` 207,031; `bank_account` 99,293; `credits` 633 |
| | `payment_status` | Final status of this *attempt* | `succeeded` 277,447; `declined` 17,231; `voided` 10,769; `failed` 1,510 |
| | `is_manual_attempt` | Triggered manually (e.g., CS) rather than automatically | `true` 9,362; `false` 297,595 |
| | `created_at` | Payment log record created, possibly before completion | Zero nulls; all parsed as UTC |
| | `captured_at` | When money moved, NULL if never captured | 27,672 nulls; all other values parse as UTC; **not evidence of full payment** |

**Coverage checks:** exactly 3+5+8 = **16 expected columns**, no unexpected columns observed, and zero *non-null unparseable* timestamps in the source extract. The only observed null field is `payment_logs.captured_at`, consistent with the source definition at the schema level. No null/format repair or filtering has been performed.

**Interpretation guardrails:** A payment attempt is not a completed project. Multiple attempts may belong to one project. `succeeded` cannot be equated to full financial settlement without amounts, and the current data cannot establish the operational time of a failure or authorization event. `first_exposed_at` is not documented as a randomization timestamp. The extract does not contain unfinished marketplace projects or the full Turno host population. Data format conformance is **not** confirmation of operational semantics. Checkpoint B will specifically investigate status/capture disagreement and multiple capture records before any payment classification is approved.

**Evidence source:** `notebooks/00_data_foundation/00_A_structure.ipynb`, sections A01–A08 (especially A08), with 10 synthetic tests in `tests/test_foundation_a.py`.
