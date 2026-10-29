# EDA 0 — Checkpoint A (A01–A08) — technical review

**Status:** Commit A authorized and published on `analysis/eda0-data-foundation` for Fernando + Jurandir review; **V7 remains OPEN**. This is a structural integrity diagnostic, not an experiment evaluation.

## Input provenance

| Original immutable file | File bytes | SHA-256 |
|---|---:|---|
| `experiment_exposures.csv` | 481,724 | `9cce67cd8d90d292c0703416b3c28c69783c56d10c2f997bf614b2bc84445327` |
| `assignments.csv` | 16,411,731 | `c66a6d5cb89b62bc3542ee9184e75c8ded41589e91dac9d726639acad0db0ff2` |
| `payment_logs.csv` | 24,857,672 | `ab6bf97f2ca216504058b5de1deb2f80641d783e8e23651d3efc2d595675879a` |

## A01–A08: principal evidence and independent reconciliation

| ID | Direct technical finding | Validation performed | Technical status |
|---|---|---|---|
| A01 | **14,708** host-exposure rows, **279,847** completed projects, **306,957** payment-attempt rows; 3/5/8 columns, respectively | `distinct primary keys + extra occurrences + missing keys = rows`, and direct `len()` checks | Answered for the supplied extract |
| A02 | Zero null or duplicate primary keys, and zero identical full rows in all three files | Separate `value_counts`, `.duplicated()` and direct full-row checks | Answered for file identifiers |
| A03 | All tested many-to-one joins preserve rows; zero project-to-multiple-host conflicts in both source tables | Explicit join `validate='many_to_one'`, input/output counts, 0 multiplied rows, groupby cardinality | Answered for observed associations |
| A04 | **0 projects** have hosts missing from the exposure table | Assignment↔exposure left join and independent host-set anti-join both equal zero | Answered |
| A05 | **0 payment logs** have orphan project IDs, orphan host IDs, or payment/project host mismatches | Left-join flags, independent key-set checks, and payment partition reconciling to 306,957 | Answered |
| A06 | **642 of 14,708 registered hosts** have no completed project recorded: Control **338**, Test **304** | Zero/one/multiple categories sum to exposure table; summed project counts reconcile to 279,847 | Answered within extract; cannot infer inactivity/churn |
| A07 | **239 of 279,847 completed projects** have no payment log; **279,608** have at least one. There are 306,957 matched attempts, **0** orphan attempts | 239 + 279,608 = 279,847; attempt counts sum to all 306,957 logs; independent project-ID set difference yields 239 | Answered as log absence only, not nonpayment |
| A08 | 16/16 PDF-described fields present; no unexpected fields; only `captured_at` has missing source values (**27,672**); 0 invalid non-null timestamps under UTC parsing | Schema membership, `null + nonnull = rows`, domain checks and derived UTC timestamp parse diagnostics | Answered for schema, not for business semantics |

### A06: all recorded hosts, including zeros

| Group | 0 completed projects | 1 project | 2+ projects | Total recorded hosts |
|---|---:|---:|---:|---:|
| Control | 338 | 702 | 6,337 | 7,377 |
| Test | 304 | 715 | 6,312 | 7,331 |
| **Both** | **642** | **1,417** | **12,649** | **14,708** |

### A07: projects lacking any payment log, by **project completion** window

| Completion period | Group | Projects with logs | Projects without logs | Total completed projects |
|---|---|---:|---:|---:|
| Baseline | Control | 38,710 | 21 | 38,731 |
| Baseline | Test | 39,756 | 58 | 39,814 |
| Experiment | Control | 98,820 | 35 | 98,855 |
| Experiment | Test | 102,322 | 125 | 102,447 |
| **Total** | | **279,608** | **239** | **279,847** |

The periods above use documented calendar boundaries at UTC midnight solely to **describe coverage**; they do not establish treatment-on-treatment timing, eligibility, observed errors, or causal differences. Project `created_at` and exposure timestamps must be analyzed in Checkpoint C before further assumptions.

## Integrity assessment and dependencies

- **No structural blocker** detected in the tested project, host and payment-log key relationships. This result does **not** validate payment outcomes.
- **239 completed projects without logs** are an observation gap, not evidence of unpaid projects; do not discard them.
- **642 hosts without completed projects in the extract** remain in the registered-host universe; they cannot be treated as churned or as never-active hosts.
- **27,672 missing `captured_at`** are compatible with a not-captured attempt but cannot establish an unpaid project, because multiple attempts may exist.
- The earlier EDA implementation and any provisional payment anomalies are **not** treated as verified by this new Checkpoint A. The status/capture and multi-capture investigations belong to Checkpoint B, subject to the current contract and review.

## Technical validation status

- V1 / V3: all host, project and attempt partitions and their aggregates reconcile in the same universes.
- V2 / V8: joins are guarded by parent-key uniqueness, row-conservation checks and independent set-difference checks.
- V5: completion timestamps are parsed to derived UTC series, with exclusive end bounds. Comprehensive temporal validation awaits C18–C24.
- V6: **10/10 synthetic pytest checks passed**, including duplicate/missing keys, unexpected/missing columns, join multiplication prevention, unknown hosts and partition mismatch.
- V7: **all 10 notebook code cells executed sequentially without exceptions in a fresh Python interpreter**, and the resulting real outputs were saved. **An actual complete Jupyter clean-kernel execution did not complete reliably in this authoring container**, so **V7 remains OPEN**. A local `Restart Kernel and Run All Cells` pass must be verified before approval. Dependency installation into an isolated `.venv` was also blocked by the executor's package-index access; local venv installation remains unverified.

### Open V7 issue — Jupyter execution

The notebook was executed as **10 code cells in sequence in a fresh Python interpreter** without exceptions, and those outputs are saved in the notebook. However, the required **full clean Jupyter kernel run with `nbclient` was not successfully completed** in the authoring environment.

A previously recorded **abbreviated diagnostic** from the unsuccessful Jupyter attempt was:

```text
ipykernel.kernelbase.dispatch_shell -> ipykernel.ipkernel.execute_request
-> jupyter_client.session.send -> zmq.sugar.socket.send_multipart
zmq.error.ZMQError: Socket operation on non-socket
nbclient.exceptions.DeadKernelError: Kernel died
```

This is an excerpt of an earlier reported traceback, **not a retained full raw execution log**. It identifies a kernel communication failure, **not its proven root cause**. Separate attempts also encountered environment timeouts or permission-related errors; these cannot be established as the cause of the ZeroMQ failure. There is no demonstrated connection between the kernel termination and incorrect Pandas calculations, but the failure means Jupyter reproducibility is **unverified**.

**V7 status: OPEN.** In a Python 3.13 virtual environment, install the declared dependencies, select the matching Jupyter kernel, run **Restart Kernel and Run All Cells**, confirm current outputs and zero errors, and preserve the error logs if execution fails. Only mark V7 passed after that check. The isolated `.venv` installation itself was not verified in the authoring environment because access to its package index was unavailable.

## Files included in Commit A for review

- `notebooks/00_data_foundation/00_A_structure.ipynb`
- `src/foundation_a.py`; `src/__init__.py`
- `tests/test_foundation_a.py`
- `docs/data_dictionary.md`
- `reports/eda/eda0_checkpoint_A.md`, `eda0_anomalies_A.md`, `eda0_coverage.md`
- `README.md`, `pyproject.toml` (Python 3.13 and local setup)

**Checkpoint decision requested:** confirm the A01–A08 evidence and whether the observed 239 no-log projects / 642 zero-project hosts require any special treatment in the *next* technical block. They have not been removed or relabeled. Commit A was explicitly authorized; do not open a PR or merge without further authorization.
