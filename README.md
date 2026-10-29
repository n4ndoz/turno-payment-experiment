# Turno — Payment Authorization Experiment

**Status:** EDA 0 / **Checkpoint A (A01–A08)** committed on `analysis/eda0-data-foundation`; **Checkpoint B (B09–B17)** committed to the Foundation branch with Fernando's approval for technical review; **not yet signed off as analytically complete**. Checkpoints C–E have not been reimplemented. **V7 remains open for A and B.** No experiment-effect inference, KPI definition or Ship/Kill recommendation is included.

## Python version and local reproducibility

The original Python **3.12.10** target was expressly changed to **Python 3.13**. The execution environment used here is **Python 3.13.5**. Use a Python 3.13 interpreter on your machine; the Python 3.13 virtual environment is **local to each machine** and is never committed.

1. Clone the repository and check out the Checkpoint A review branch: `git clone https://github.com/n4ndoz/turno-payment-experiment.git`, `cd turno-payment-experiment`, then `git checkout analysis/eda0-data-foundation`.
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

Open `notebooks/00_data_foundation/00_A_structure.ipynb` and `01_B_conceptual_integrity.ipynb`, choose the `.venv` Python 3.13 kernel, then **Kernel → Restart Kernel and Run All Cells** for each. It also works with notebook working directory set to the repository root or the notebook folder, as long as `data/raw/` exists.

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

**Governance:** Data corrections, new business metrics, eligible populations, interpretations and decisions require separate approval. No source file is edited or excluded. Results about `payment_logs` refer to **attempts**, not completed project payment outcomes. **Commit A was explicitly authorized on the review branch; no pull request or merge is authorized yet.**
