# EDA 0 — Checkpoint D: Payment attempt records and observable journeys (D25–D34)

**Status:** Committed to `analysis/eda0-data-foundation` after explicit approval; ready for technical review. No PR/merge, business KPI or experimental inference. Analysis is in `notebooks/00_data_foundation/03_D_payment_journeys.ipynb` with 11 executed code cells and saved outputs. Python 3.13.5, Pandas 2.2.3, UTC. Results pertain strictly to the provided, immutable extracts, not to financial settlement.

## Source provenance, grain, and reproducibility

| Original CSV | SHA-256 |
|---|---|
| `experiment_exposures.csv` | `9cce67cd8d90d292c0703416b3c28c69783c56d10c2f997bf614b2bc84445327` |
| `assignments.csv` | `c66a6d5cb89b62bc3542ee9184e75c8ded41589e91dac9d726639acad0db0ff2` |
| `payment_logs.csv` | `ab6bf97f2ca216504058b5de1deb2f80641d783e8e23651d3efc2d595675879a` |

The starting universes are **14,708 registered hosts, 279,847 completed projects and 306,957 payment-attempt records**. The 239 completed projects with no payment log are retained by an audited left join from the complete project table. Payment logs are joined many-to-one to projects and hosts, with uniqueness, membership, host agreement and cardinality checks. Captured-field and status-based evidence remain **distinct**; source records are never removed, rewritten, imputed or reclassified into presumed financial outcomes.

## Questions and evidence map

| ID | Investigation / key evidence | Validation and interpretation boundary | Status |
|---|---|---|---|
| D25 | Recorded attempts per project: **239 zero, 265,501 one, 14,107 multiple; max 37**. Detailed frequency, quantiles and extreme examples appear in the notebook. | Complete histogram closes to 279,847 projects and its weighted sum to 306,957 attempts. Attempt rows are not proven retries. | Answered for records |
| D26 | **207,031 card**, **99,293 bank_account**, **633 credits** attempts. **3,410 projects** use multiple recorded methods (3,405 have two; five have three). | Attempt-method totals reconcile; project-method counts are distinct and nonadditive across individual methods. Method choice may occur after treatment. | Answered for records |
| D27 | First and last record-created methods tabulated for **279,607** projects with unambiguous timestamps; earliest capture-associated method identified for **278,559** projects; **zero tied earliest capture timestamp cases**. | Excludes one tied-creation project and 239 zero-log projects from first/last method tables. A first record is not a first financial operation or host selection. | Partially identifiable |
| D28 | **27,347** adjacent creation-ordered record pairs among unambiguous projects; **5,815** contain a change of recorded method. Frequent method paths and transition matrix displayed. | Transition buckets sum to the number of adjacent pairs. Record transitions cannot prove retries or payment-method switching intent. | Record sequences observed |
| D29 | **One project** has a tie in creation timestamps; **zero** projects have missing/invalid log creation timestamps. | 279,607 orderable log-bearing projects + one ambiguous = 279,608 with logs. No artificial tie ordering. | Answered for ordering |
| D30 | **9,362 manually flagged attempts**, spanning **5,348 projects**; 5,153 projects have both manual and automatic records. Full method × status × manual table and group counts displayed. | Every attempt belongs to one status × method × manual cell, with capture/discrepancy totals reconciled. Flag is not a complete CS intervention log. | Answered for records |
| D31 | **4,836 projects** contain a failure-status record created before a first manual record, among 5,348 projects with manual records. Manual-record creation is broken out before/during/after **2025-09-17 through 2025-09-30 UTC**. | Classification uses `payment_logs.created_at`, not actual failure/contact/alert timestamps; no causal claim about the CS incident. | Partially identifiable |
| D32 | **7,125 projects** have both `failed`/`declined` and `succeeded` statuses; **7,108** have a failure-status record created earlier than the earliest success-status record; **16** have the reverse, and one has ambiguous ordering. **7,248** projects show both a failure-status row and a capture timestamp somewhere. | Co-occurrence and record-creation ordering are not verified financial recovery; actual failure, retry and recovery events are unobserved. | Record patterns observed; recovery unproven |
| D33 | **154 projects** have multiple `succeeded` records, **652** have multiple populated capture timestamps, **200** have capture timestamps associated with more than one method, and **140** have success and capture evidence only on different attempts. **2,075** projects contain status/capture discordances. | A capture timestamp is not a payment amount or proof of full settlement. Multiple records do not establish duplicate or complementary charges. | Observable configurations only |
| D34 | Five-way **exclusive evidence partition**, separate overlapping flags, candidate-rule cross-tab and group × completion-period measurement sensitivity. | 279,847 projects are conserved; all candidate totals reconcile by group and UTC completion period. No metric/causal estimand chosen. | Evidence answered, outcome interpretation limited |

The inventory question labels above are technical paraphrases of the approved D25–D34 subjects; the notebook preserves their IDs and investigations rather than asserting verbatim quotations from an unavailable master inventory.

## D34 — Exclusive fundamental project-evidence partition

This is a **partition by whether evidence exists anywhere among a project's attempts**, not a classification of the project's true payment outcome. The categories are exhaustive and mutually exclusive, with no priority-based suppression of discordances:

| Exclusive fundamental evidence | Completed projects |
|---|---:|
| Both a `succeeded` status somewhere and a populated `captured_at` somewhere | **277,255** |
| Populated `captured_at` only; no `succeeded` attempt | **1,304** |
| Has logs, neither a `succeeded` status nor a populated capture timestamp | **1,013** |
| No logs in the provided extract | **239** |
| Has `succeeded` status only; no populated capture timestamp | **36** |
| **Total** | **279,847** |

**Importantly:** 140 of the 277,255 projects with both evidence types have them only on **different attempts**: there is **no same-attempt success-and-capture concordance** for those projects. They remain in the combined fundamental-evidence bucket and are additionally flagged.

### Nonexclusive diagnostic flags — do not sum

| Flag | Projects |
|---|---:|
| At least one `succeeded` status | 277,291 |
| At least one non-null `captured_at` | 278,559 |
| At least one same-attempt `succeeded` plus non-null `captured_at` | 277,115 |
| Status/capture discordance in at least one attempt | 2,075 |
| More than one populated capture timestamp row | 652 |
| Capture-associated records use more than one payment method | 200 |
| More than one method across any recorded attempts | 3,410 |
| Success and timestamp exist only in different attempts | 140 |
| Any manual attempt | 5,348 |
| Manual and automatic records both present | 5,153 |
| Both failure and success status somewhere | 7,125 |
| Record-evidence flags meriting further review (limited technical triage union) | 2,402 |

The technical triage union is **not** a final list of excluded, unpaid or financially ambiguous projects; without amounts, full settlement is not verifiable for any of them.

## Measurement sensitivity of three *candidate evidence rules*

| Candidate rule at completed-project grain | Projects |
|---|---:|
| Any attempt has `payment_status = succeeded` | **277,291** |
| Any attempt has populated `captured_at` | **278,559** |
| Any single attempt has **both** `succeeded` and populated `captured_at` | **277,115** |

The mutually exclusive three-rule patterns are:

| Status evidence | Capture field evidence | Same-attempt concordance | Completed projects |
|---|---|---|---:|
| No | No | No | 1,252 (includes 239 without logs) |
| No | Yes | No | 1,304 |
| Yes | No | No | 36 |
| Yes | Yes | No | 140 |
| Yes | Yes | Yes | 277,115 |
| **Total** | | | **279,847** |

Candidate classifications change for **1,340 projects** (status versus timestamp), **176** (status versus same-attempt concordance), and **1,444** (timestamp versus same-attempt concordance). These are XOR differences at project grain, **not** a payment-loss count or a treatment-effect estimate.

### Descriptive sensitivity by group and completion period

Group labels are as recorded (`control` / `test`) and denominators are **all completed projects with the stated completion period**, including those with no log. Periods are half-open in UTC: baseline `[2025-07-18, 2025-08-18)` and experiment `[2025-08-18, 2025-11-20)`. Comparisons are *measurement coverage diagnostics only*, not inferential treatment comparisons.

| Group | Completion period | Completed projects (denominator) | Candidate status | Candidate timestamp | Candidate same-attempt concordance | No logs |
|---|---|---:|---:|---:|---:|---:|
| `control` | baseline | 38,731 | 38,473 | 38,638 | 38,456 | 21 |
| `control` | experiment | 98,855 | 97,948 | 98,405 | 97,880 | 35 |
| `test` | baseline | 39,814 | 39,498 | 39,618 | 39,460 | 58 |
| `test` | experiment | 102,447 | 101,372 | 101,898 | 101,319 | 125 |
| **All** | **Both periods** | **279,847** | **277,291** | **278,559** | **277,115** | **239** |

All four rows and all candidate columns reconcile to the independent overall totals. Different project populations across groups/periods, documented pre-exposure completions in C and unequal observation horizons in E require future explicit eligibility and censoring decisions. No denominator or effect estimand has been selected.

## Methodological implications — compact technical synthesis

**1. Population and recorded exposure.** Assignments were included exactly as supplied. C found 5,091 completions in the experiment period before the host's recorded first exposure; D does not remove or recode them. The original randomization population and actual treatment application are not established by these CSVs. Payment method and manual actions can be post-treatment observations.

**2. Observed capture definition.** Three plausible evidence indicators select different project sets, including 1,304 timestamp-only projects, 36 success-only projects, and 140 split-evidence projects. Multiple captures and discordant statuses require interpretation without amounts; no evidence source is declared authoritative.

**3. Potential experiment measurement architecture.** Completed projects per recorded host are directly aggregatable (with E's full registered-host universe). Projects with status/capture evidence per host are aggregatable under each *candidate* definition. Projects without such evidence and elapsed time to a timestamped capture require horizon/censoring assumptions from C; a status-only success has no observable capture time. A proportion of completed projects with a capture timestamp could be *calculated* after choosing a denominator and event definition but **none is approved here**. Full settlement, gross loss, financial recovery and treatment effects are not identifiable from these data alone.

**4. Recovery-like sequences versus proof.** A failed-status record may precede a later-created success or manual record, but `created_at` is the creation of a log, not the exact failed-payment/CS-alert/authorization time. The absent financial-operation event IDs and monetary amounts mean the existence, completeness, and timing of actual recovery cannot be proved.

**5. Additional data required.** Payment/authorization event taxonomy and IDs, capture amount and due amount, settlement/refund ledger, exact failure/retry event timestamps, complete CS action and alert logs, original randomization logs, treatment-application events and verified extract cutoffs.

## Validation and reproducibility

- **V1/V3:** exclusive classes sum to 279,847, attempts sum to 306,957, counts by group/completion period reconcile, and overlapping flags are never summed.
- **V2:** validated many-to-one joins prevent unmatched or duplicated attempts; all projects including the 239 with no logs survive.
- **V4:** status, timestamp and same-attempt concordance are separate; no authoritative financial-capture rule was selected.
- **V5:** UTC parsing and timestamp ties are explicit; the single tied creation-time project is excluded **only from sequence-order calculations**, not the source universe.
- **V6:** **52 synthetic pytest cases passed** across A/B/C/E and D, including the new partition, split-attempt evidence, capture-only case, ties, missing creation time, joins and UTC boundaries. `python -m pytest -q`.
- **V7 for D: PASS in the authoring environment.** **11/11 notebook code cells** completed from a *fresh Jupyter Python 3.13.5 kernel* via `nbclient` with outputs saved and no cell errors, in **17.5 seconds**. A prior pre-optimization attempt failed with `ZMQError: Socket operation on non-socket` and `DeadKernelError`, and its traceback was retained separately; the successful fresh-kernel run supersedes that attempt **only for this D notebook**. Historical A/B V7 remains OPEN; user-local Python 3.13 `.venv` remains untested.
- **V8:** `python tests/check_d_source_reconciliations.py` independently reads raw CSVs with standard-library `csv.DictReader`, **without importing Pandas or any `src` helpers**, and reconciles all five exclusive classes, candidate counts, method counts, manual-project counts, 2,316 discordant attempts / 2,075 affected projects, 652 multiple-capture projects, 200 cross-method capture projects, and 140 split-evidence projects. **PASS.**

**Review and governance:** These findings are ready for technical review by Fernando and Jurandir, not business approval. No data repair, exclusion, KPI, hypothesis test, causal estimate, A1 modification, PR, merge or subsequent experiment analysis was performed. Commit D was explicitly approved and published on the Foundation branch. No local raw CSV or virtual-environment files should be versioned.
