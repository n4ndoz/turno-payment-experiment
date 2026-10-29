# Turno — Payment Authorization Experiment

## Notebooks — complete source and saved outputs

All nine notebooks are version-controlled, including their Python source cells and saved outputs. Open them directly in GitHub or run them locally with the unchanged source CSVs in `data/raw/`:

- [A — Data structure](notebooks/00_data_foundation/00_A_structure.ipynb)
- [B — Conceptual integrity](notebooks/00_data_foundation/01_B_conceptual_integrity.ipynb)
- [C — Temporal integrity](notebooks/00_data_foundation/02_C_temporal_integrity.ipynb)
- [D — Payment journeys](notebooks/00_data_foundation/03_D_payment_journeys.ipynb)
- [E — Population coverage](notebooks/00_data_foundation/04_E_population_coverage.ipynb)
- [Sprint 1 — Experiment impact](notebooks/01_experiment/experiment_impact.ipynb)
- [EDA 1 — Payment reliability](notebooks/02_eda1/payment_reliability_deep_dive.ipynb)
- [Final inferential validation](notebooks/02_eda1/inferential_validation.ipynb)
- [Final decision-oriented checks](notebooks/02_eda1/final_decision_checks.ipynb)

Supporting Python modules are in [`src/`](src/), synthetic tests and independent audits in [`tests/`](tests/), and technical and executive reports in [`reports/`](reports/). The original CSVs are intentionally not tracked. The source-level payment and causal-identification limitations remain applicable.

**Status:** EDA 0 / **Checkpoint A (A01–A08)** committed on `analysis/eda0-data-foundation`; **Checkpoint B (B09–B17)** committed to the Foundation branch with Fernando's approval for technical review; **not yet signed off as analytically complete**. Checkpoints C and E are committed on the Foundation branch for review, including C21/C24 and C22 traceability corrections; Checkpoint D (D25–D34) was committed on the Foundation branch after explicit approval; technical review and methodological decisions remain separate. **V7 remains open for A and B.** Sprint 1 experimental contrasts are committed on the Foundation branch for review; no final KPI approval or Ship/Kill recommendation is included.

## Python version and local reproducibility

The original Python **3.12.10** target was expressly changed to **Python 3.13**. The execution environment used here is **Python 3.13.5**. Use a Python 3.13 interpreter on your machine; the Python 3.13 virtual environment is **local to each machine** and is never committed.

1. Clone the repository on its default `main` branch: `git clone https://github.com/n4ndoz/turno-payment-experiment.git`, then `cd turno-payment-experiment`.
2. Put the three *unchanged* CSV files in `data/raw/`, keeping their filenames:
   `experiment_exposures.csv`, `assignments.csv`, `payment_logs.csv`.
3. From the **repository root**, create the venv and install the project:

**Linux / macOS**

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m pytest -q
python -m jupyterlab
```

**Windows PowerShell**

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m pytest -q
python -m jupyterlab
```

If PowerShell activation is blocked, replace `python` with `.\.venv\Scripts\python.exe` in the commands above; do not bypass your machine's execution policy merely for this project. On Linux/macOS, use `.venv/bin/python` directly if desired.

Open `notebooks/00_data_foundation/00_A_structure.ipynb`, `01_B_conceptual_integrity.ipynb`, `02_C_temporal_integrity.ipynb` , `03_D_payment_journeys.ipynb`, and `04_E_population_coverage.ipynb`, choose the `.venv` Python 3.13 kernel, and **Restart Kernel and Run All Cells** for each notebook. C then E must be reviewed in this order. It also works with notebook working directory set to the repository root or the notebook folder, as long as `data/raw/` exists.

**Check the results:** compare the source SHA-256 checksums displayed in A01 with those in `reports/eda/eda0_checkpoint_A.md`, run `python -m pytest -q`, and verify **all notebook cells execute in order without errors**, with saved outputs matching freshly calculated results.

The dependencies are declared in `pyproject.toml`; use the local venv so they do not conflict with your system Python. The review environment could not install packages into an isolated `.venv` because the package index was inaccessible; it ran with the preinstalled Python 3.13 libraries. **Local venv installation and actual Jupyter clean-kernel execution remain acceptance checks (V7 OPEN for A and B; see `reports/eda/eda0_checkpoint_A.md` and `eda0_checkpoint_B.md`).** All code cells were nevertheless executed sequentially in a new Python process with genuine captured outputs and zero exceptions; this is not equivalent to a validated Jupyter kernel.

## Project layout

- `data/raw/`: three **immutable, unversioned** original CSVs.
- `data/processed/`, `data/analytical/`: reserved for approved derived datasets; **unused** in Checkpoint A.
- `notebooks/00_data_foundation/00_A_structure.ipynb`: A01–A08, with code, tables, reconciliations, outputs and limitations.
- `src/foundation_a.py`: small, reusable, synthetic-testable file loading and guarded-join utilities.
- `notebooks/00_data_foundation/01_B_conceptual_integrity.ipynb`: B09–B17, with full field-discrepancy matrix and independent CSV-source verification.
- `src/foundation_b.py`: reusable project-grain evidence and first-completion-flag checks (no KPI definitions).
- `tests/test_foundation_b.py`: synthetic checks of discordance, multiple captures, ties and missing logs.
- `reports/eda/eda0_checkpoint_B.md`, `eda0_anomalies_B.md`, `eda0_coverage_B.md`: B evidence and open issues for review.
- `tests/test_foundation_a.py`: ten synthetic tests; no Turno records.
- `docs/data_dictionary.md`: documented-vs-observed schema; each field's meaning originates from the four-page assignment PDF.
- `reports/eda/eda0_checkpoint_A.md`: principal technical checkpoint and review notes.
- `reports/eda/eda0_anomalies_A.md`: anomaly and limitation inventory.
- `reports/eda/eda0_coverage.md`: question coverage and acceptance status.

**Governance:** Data corrections, new business metrics, eligible populations, interpretations and decisions require separate approval. No source file is edited or excluded. Results about `payment_logs` refer to **attempts**, not completed project payment outcomes. **The initial Checkpoint A authorization applied only to its review branch; later, integration of the full reviewed project into `main` was expressly authorized.**

## Checkpoints C + E (committed for technical review)

- `notebooks/00_data_foundation/02_C_temporal_integrity.ipynb`: C18–C24, actual event chronology, preliminary D0/D1/D7/D14/D30 horizon bounds and September incident observability.
- `notebooks/00_data_foundation/04_E_population_coverage.ipynb`: E35–E43, registered hosts including zero experiment completions, recorded exposure opportunity and technical answerability matrix; interactive Plotly descriptions.
- `src/foundation_ce.py`, `tests/test_foundation_ce.py`: small reusable UTC, elapsed-horizon and zero-host helpers with synthetic checks.
- `tests/check_ce_source_reconciliations.py`: independent CSV-stdlib verification of critical horizon/population numbers. Run `python tests/check_ce_source_reconciliations.py` after placing originals in `data/raw/`.
- `reports/eda/eda0_checkpoint_C.md`, `eda0_checkpoint_E.md`: independent checkpoint reports; `eda0_anomalies_CE.md` and `eda0_coverage_combined.md` consolidate technical status without deciding business KPIs.

**Validation:** 36 synthetic tests passed across A/B/C/E. Revised Checkpoint C (10 code cells) and E (10 code cells) successfully executed with `nbclient` from a **clean Python 3.13.5 Jupyter kernel** in the authoring environment; outputs were saved. The user-local Python 3.13 `.venv` remains to be tested; earlier A/B V7 kernel errors remain unresolved.

**Git:** Checkpoints C, D and E and Sprint 1 were explicitly approved and versioned. Full project integration into `main` was subsequently authorized; historical review-stage limitations remain documented.


## Checkpoint D (committed for technical review)

- `notebooks/00_data_foundation/03_D_payment_journeys.ipynb`: D25–D34, 11 executed Jupyter code cells, project-evidence partition, attempt method / sequence diagnostics and candidate-capture measurement sensitivity (not approved KPIs).
- `src/foundation_d.py`: guarded project/host joins, overlapping project evidence, exclusive fundamental partition, and tie-aware record chronology.
- `tests/test_foundation_d.py`: synthetic D edge cases and invariants.
- `tests/check_d_source_reconciliations.py`: independent source-stream verification using standard-library `csv.DictReader` (no Pandas or shared helpers). Run `python tests/check_d_source_reconciliations.py`.
- `reports/eda/eda0_checkpoint_D.md`, `eda0_anomalies_D.md`: complete English technical evidence and caveats; `eda0_coverage_combined.md` is updated for all 43 questions.

**Validation:** 52 synthetic pytest cases passed across A/B/C/E/D; 11/11 D notebook code cells passed in a fresh Python 3.13.5 Jupyter kernel via `nbclient` after vectorizing performance bottlenecks, with outputs saved. Independent D source audit passed. Historical A/B V7 exceptions and local-user `.venv` verification remain open. Commit D and subsequent experimental analysis were separately authorized; historical validation and local-environment caveats remain open.


## Sprint 1 — Experimental Impact (committed for technical review)

- `notebooks/01_experiment/experiment_impact.ipynb`: six registered-host candidate metrics, 2,000 host-stratified bootstrap CIs, D1/D7/D14/D30 capture timing, S1–S4 sensitivities, two decision-relevant charts, and saved outputs.
- `reports/experiment_impact.md`: English executive results table, payment reliability, host behavior, robustness, eight original case questions, and decision evidence without a Ship/Kill recommendation.
- `src/experiment_impact.py`: reusable validated project/host panels, elapsed capture windows, host-clustered bootstrap and baseline HC3 adjustment. Does not modify the approved foundation.
- `tests/test_experiment_impact.py`: synthetic endpoint, no-log, zero-host, bootstrap, source-key and baseline-robustness tests.
- `tests/check_experiment_source_reconciliations.py`: independent standard-library source audit.

**Additional dependencies:** `statsmodels`, `scipy`, and `matplotlib` are declared in `pyproject.toml` for inference and the two plots. The main inference is on **registered hosts**, not proven full-population ITT; captured-at timestamps are not ledger settlement verification. The all-host D14 window is inside the conservatively documented observation horizon, but the completeness of source logs cannot be proven independently. D30 excludes final-day uncertain windows.

**Sprint 1 validation:** 65/65 project pytest checks passed, independent CSV audit passed, and the Sprint notebook executed 11/11 code cells in a clean Jupyter Python 3.13.5 kernel with saved outputs. Historical A/B V7 issues remain separate; local `.venv` validation is still required. **Sprint 1 was committed with explicit authorization; its later integration into `main` was also authorized.**


## EDA 1 — Payment Reliability & Experiment Impact (committed for technical review)

**Branch:** `analysis/eda1-experiment-impact`, created from approved Sprint 1 commit `84e25e5ac410f72c971292b4ed7ea0945f77d266`.

- `notebooks/02_eda1/payment_reliability_deep_dive.ipynb`: D0–D30 empirical capture curve, first-day zoom, full-cohort **RMST D7/D14**, conservatively covered **RMST D30**, common D30-cohort RMST D7/D14, and diagnostic last-day sensitivity; 2,000 host-stratified bootstrap draws with fixed seed.
- `reports/eda1_payment_reliability.md`: single English executive report, including D1 robustness, experiment-period method friction, and mixed-method journeys.
- `src/eda1_reliability.py`: reusable project-grain time-to-capture, RMST, cluster inference, status-discordance and method-friction operations.
- `tests/test_eda1_reliability.py`: synthetic validation for exact D1/D7/D14/D30 boundaries, t=0 and pre-completion captures, uncertain final-day D30 coverage, bootstrap reproducibility and denominator preservation.
- `tests/check_eda1_source_reconciliations.py`: independent CSV and UTC datetime audit using only the Python standard library.

**Status:** 88/88 Pytest tests passed and independent source audit reconciled. The 10 EDA 1 notebook code cells were executed sequentially in one fresh Python process with outputs saved. **V7 Jupyter clean-kernel validation for EDA 1 remains OPEN** after a `ZMQError` / `DeadKernelError` in the authoring environment; do not mistake the alternative Python run for a clean Jupyter kernel. The historical A/B V7 pending items also remain open.

With unchanged original source CSVs in `data/raw/` and the local Python 3.13 environment installed, run `python -m pytest -q`, `python tests/check_eda1_source_reconciliations.py`, and **Restart Kernel and Run All Cells** in the EDA 1 notebook.

**Governance:** EDA 1 was committed after explicit authorization. Integration of the reviewed project into `main` was separately authorized. No causal within-method inference, final capture definition, financial-settlement claim or product recommendation is made.

## Final inferential validation (approved for publication)

- `notebooks/02_eda1/inferential_validation.ipynb`: baseline-vs-experiment D1, HC3-adjusted host metrics, host-label permutation tests, Holm multiplicity, and sensitivity of M1 to high-activity hosts; 6/6 Jupyter code cells executed with outputs saved.
- `reports/inferential_validation.md`: final concise English decision-evidence report; no Ship/Kill recommendation.
- `src/inferential_validation.py`, `tests/test_inferential_validation.py`: focused reusable estimators and 8 new synthetic tests (96/96 tests in the full project suite).

**Validation:** The final inferential notebook passed a clean Python 3.13.5 Jupyter execution. The separate EDA 1 payment-reliability notebook's V7 issue and the historical A/B V7 caveats remain open. No original CSVs or local virtual environments are committed.

## Final decision-oriented checks (approved for integration)

- `notebooks/02_eda1/final_decision_checks.ipynb`: recorded post-exposure M2 chronology, second completion within 30 days and its pre-booked share, plus a project-weighted D1 baseline-activity sensitivity. Six code cells ran in a clean Jupyter kernel with saved outputs.
- `reports/final_decision_checks.md`: concise English technical interpretation and decision limitations.
- `src/final_decision_checks.py`, `tests/test_final_decision_checks.py`: deterministic helpers and 10 targeted synthetic checks. The full suite passed **106/106** tests in Python 3.13.5 before integration.

Historical A/B and EDA 1 payment-reliability Jupyter V7 exceptions remain open. No raw CSV files, Python caches or local virtual environments are versioned. No final Ship/Kill/Modified Ship recommendation is made.
