# Turno — Payment Authorization Experiment

Reproducible analytical project for the Turno payment authorization experiment take-home assignment.

## Project status

Initial scaffolding only. No datasets have been read, transformed, or analyzed; no metrics have been implemented.

## Environment

- Python 3.12.10
- Dependencies will be declared when their use is approved and implemented.

## Local data

Place the three original, unmodified CSV files under `data/raw/`:

- `experiment_exposures.csv`
- `assignments.csv`
- `payment_logs.csv`

The source CSVs are not committed to Git. Neither are generated Parquet files. Preserve the original filenames and contents.

## Directory layout

- `data/raw/`: original CSVs (not versioned)
- `data/processed/`: reusable treated data, when needed
- `data/analytical/`: reusable analytical datasets, when needed
- `notebooks/`: exploratory notebooks, organized by stage
- `src/`: reusable Python functions/modules, added as needed
- `tests/`: automated tests, added alongside implementation
- `reports/`: reproducible analysis reports
- `docs/`: data definitions and decision records, populated progressively

The target architecture may expand incrementally as tasks are approved. Use paths relative to the repository root when running notebooks.

## Governance

Metric definitions require approval before implementation. Technical integrity checks may precede metric definitions. Changes must be reviewed before commit; pull requests and merges require explicit authorization.
