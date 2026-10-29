# EDA 0 — Checkpoint B: Conceptual integrity (B09–B17)

**Status:** Implemented for Fernando and Jurandir's review. **Commit B was expressly authorized by Fernando and published on the Foundation branch. No pull request or merge is authorized.** Checkpoint A remains conditionally approved with open V7 validation. This checkpoint is a technical audit, **not** an experimental effect estimate, business KPI or financial-settlement assessment.

## Reproduction and source traceability

- Notebook: `notebooks/00_data_foundation/01_B_conceptual_integrity.ipynb` (nine explicit B question headings, source code, real saved outputs, source-independent cross-checks and limitations).
- Inputs (immutable, not committed): `data/raw/experiment_exposures.csv`, `data/raw/assignments.csv`, `data/raw/payment_logs.csv`.
- Python: **3.13**. Follow the Python 3.13 virtual environment instructions in the repository `README.md`, install `pip install -e ".[dev]"`, run `python -m pytest -q`, then open the B notebook and choose the `.venv` kernel. Run **Restart Kernel and Run All Cells**.
- No raw CSV or Parquet is tracked; no data transformation overwrites source values. Input SHA-256 checksums are printed in the first notebook cell and match Checkpoint A.

| Source file | SHA-256 |
|---|---|
| `experiment_exposures.csv` | `9cce67cd8d90d292c0703416b3c28c69783c56d10c2f997bf614b2bc84445327` |
| `assignments.csv` | `c66a6d5cb89b62bc3542ee9184e75c8ded41589e91dac9d726639acad0db0ff2` |
| `payment_logs.csv` | `ab6bf97f2ca216504058b5de1deb2f80641d783e8e23651d3efc2d595675879a` |

### Checkpoint-A population references

- 14,708 registered hosts, 279,847 completed projects, 306,957 payment-attempt records.
- 239 completed projects lack payment logs. They are retained at the project grain in B11 and B16.
- 27,672 attempts have a missing `captured_at` field.
- No key or parent-join anomalies previously detected in A were assumed away; B's reusable project check independently rejects duplicate keys, orphan attempts and host mismatches.

## Results and validations, by question

| ID | Direct technical evidence | Validation / interpretation boundary | Technical status |
|---|---|---|---|
| B09 | `captured_at` is missing in 27,672/306,957 attempts; all other documented fields are populated. Status × manual × capture-presence combinations are displayed. | `null + nonnull = dataset rows` for every field. Attempt null ≠ unpaid project. | Answered |
| B10 | Expected values appear for group, method, status and two booleans; **zero unexpected domain values**. Recorded timestamps are parse-tested to derived UTC values without changing source strings. | Every domain frequency plus missing count reconciles to its source grain. | Answered for recorded categories |
| B11 | **154 projects** have 2+ `succeeded` attempts; **652 projects** have 2+ populated `captured_at` rows and 2+ distinct capture timestamp strings; **200** have populated capture fields across 2+ methods. | Aggregation returns one row per project; 306,957 attempts and 279,285 populated captures are conserved. Neither complementarity nor duplicate charge can be established. | Answered for observable attempts |
| B12 | **2,316 discordant attempts** affecting **2,075 projects**. **595 affected projects** also have another concordant attempt. Full raw cross-tab appears below. | All four status totals, 27,672 missing and 279,285 present captures, and 306,957 attempts reconcile. Independent raw-mask and CSV-stream checks are in the notebook. | Answered for field inconsistencies; business truth unresolved |
| B13 | **2,755** true first-completion flags, each on a different host. **0** repeated true flags, **0** flagged projects later than the first completion observed in this extract. **7 hosts** have ties at the earliest observed completion timestamp. | Host and project totals reconcile; historical first completion is not provable with a partial extract. | Partially answerable |
| B14 | **0** duplicate `payment_log_id` occurrences, **0** exact duplicate rows, **0** rows whose every non-ID attribute exactly matches a different row. **17,986 rows** share project+method+status with at least another row (broader similarity only). | Full non-ID signature groups reconcile to 306,957 rows; similar attributes do not prove duplicate attempts. | Answered for source content |
| B15 | **7,125 projects** have both `succeeded` and `declined`/`failed` statuses; **6,662** have both `succeeded` and `voided`; **2,317** have logs without any `succeeded`; **1 project** has tied payment-record creation timestamps. | Status-set combinations plus 239 no-log projects sum to 279,847. Creation order does not prove payment-operation chronology. | Partially answerable |
| B16 | **277,291 projects** have any `succeeded` status; **278,559** have any populated capture field and a first valid observed capture timestamp; **277,115** have a concordant success+timestamp attempt; **2,075** have at least one discordant attempt; **652** have multiple capture rows; **239** have no logs. | Overlapping diagnostic flags and a separate mutually exclusive partition reconcile to all 279,847 projects; `csv.DictReader` independent set/count checks cover critical project categories. No payment rate is defined. | Answered for observed evidence, limited for financial interpretation |
| B17 | Matrix describes explicit columns, indirect signals and missing event fields for nine operational concepts (authorization, reauthorization, charge, automated/manual attempts, failure, recovery, method change, full settlement). | Absent event IDs, actual failure timestamps, payment amounts, amounts due, settlement ledger and CS event logs prohibit event-level conclusions. | Partially answerable |

### B12: Actual payment-status × capture-field matrix (attempts)

| `payment_status` | `captured_at` missing | `captured_at` present | All attempts |
|---|---:|---:|---:|
| `declined` | 17,191 | 40 | 17,231 |
| `failed` | 850 | 660 | 1,510 |
| `succeeded` | 239 | 277,208 | 277,447 |
| `voided` | 9,392 | 1,377 | 10,769 |
| **Total** | **27,672** | **279,285** | **306,957** |

**Interpretation of the previously observed 1,838 marginal difference:** 2,077 attempts with a populated capture field and a non-`succeeded` status minus 239 `succeeded` attempts without a capture field = **1,838**; the total number of discordant attempts is **2,316**, not 1,838. No source-of-truth precedence has been chosen.

Discordant attempts by method: **1,326 card**, **976 bank_account**, **14 credits**. This is an attempt-level characterization, not treatment-effect analysis.

### B16: Overlapping evidence versus exclusive technical review groups

The flags above overlap, and must not be summed as project partitions. For a **separate, exclusive technical review workload partition**, we used the following explicit order: no log → any discordant attempt → multiple capture rows → any concordant capture → other capture → success without capture → remaining logs. The source project universe is reconciled below:

| Technical review category (not financial outcome) | Projects |
|---|---:|
| Concordant capture; no higher-priority flags | 276,432 |
| At least one discordant attempt | 2,075 |
| Logs, no success status and no capture field | 1,013 |
| No payment log | 239 |
| Multiple captures without discordant attempt | 88 |
| **Total** | **279,847** |

A separate overlapping helper flag labels **2,402 projects as needing additional technical review** because of no logs, discordant attempts, multiple capture records or unparseable capture timestamps. This flag is **not an exhaustive inventory of financial ambiguity** (without monetary values, all full-settlement interpretations are limited), and is not an approved KPI exclusion rule.

## Test and execution evidence

- **V1/V3:** source attempt and completed-project universes reconcile; overlapping groups are explicitly labeled; the exclusive technical partition totals 279,847.
- **V2:** the project helper rejects duplicate/missing primary keys, orphan payment logs and payment/project host mismatches; group totals are checked independently.
- **V4:** competing `succeeded` versus `captured_at` evidence is maintained separately, including discordant and multiple-capture cases.
- **V5:** record-creation timestamp ties are reported rather than arbitrarily ordered; no payment-failure moment is inferred.
- **V6:** 23 synthetic tests in `tests/test_foundation_a.py` and `tests/test_foundation_b.py` passed in this build environment. Each covers observable technical behavior, not presumed cleanliness of the real extract.
- **V8:** the notebook independently streams the original payment CSV using standard-library `csv.DictReader` and reconciles the B12 status-by-timestamp cells, project membership and multiple-capture counts against the Pandas calculations.
- **V7: OPEN.** A new `nbclient` full-kernel attempt in this container failed with `zmq.error.ZMQError: Socket operation on non-socket`, followed by `nbclient.exceptions.DeadKernelError: Kernel died`. The kernel-client cleanup also reported `AssertionError` within `nbclient`. **The cause of the socket loss is unproven.** In a separate clean Python interpreter, all code cells were executed in source order without exceptions and their real outputs saved. **This does not constitute a full Jupyter Restart & Run All pass.** A local Python 3.13 `.venv` execution remains mandatory before V7 can be closed. Full current trace is retained locally as `_checkpoint_b_nbclient.log` and a shortened technical excerpt is included in `eda0_anomalies_B.md`.

## Pending decisions and boundaries

1. Future source-of-truth or hierarchy between success status and capture timestamp requires explicit Fernando/Jurandir approval; **not decided in B**.
2. Multiple populated capture timestamps and multiple methods cannot establish full payment, financial double charges or complementarity without amounts and a ledger.
3. Exact failure/recovery times, CS interventions, temporal censoring and incident alignment belong to Checkpoint C/D and additional operational data.
4. No control/test impact estimates, causal interpretations, experimental KPIs or payment recovery rates have been implemented.
5. Checkpoint B was committed after Fernando's explicit authorization; no PR or merge is authorized. Stop for review; proceed to Checkpoint C only with subsequent approval.
