"""Small, reusable *technical* checks for EDA 0 / Checkpoint A.

No metrics, eligibility rules, deduplication, coercive key parsing or data repair.
Raw CSVs are loaded as strings so that identifiers and source values are preserved.
"""
from __future__ import annotations

import csv
import hashlib
from pathlib import Path

import pandas as pd

RAW_FILES = {
    "exposures": "experiment_exposures.csv",
    "assignments": "assignments.csv",
    "payments": "payment_logs.csv",
}
EXPECTED_COLUMNS = {
    "exposures": ["host_id", "experiment_group", "first_exposed_at"],
    "assignments": ["assignment_id", "host_id", "created_at", "completed_at", "is_first_completed_project"],
    "payments": ["payment_log_id", "assignment_id", "host_id", "payment_method", "payment_status", "is_manual_attempt", "created_at", "captured_at"],
}
PRIMARY_KEYS = {"exposures": "host_id", "assignments": "assignment_id", "payments": "payment_log_id"}


def find_project_root(start: Path | None = None) -> Path:
    """Find root from notebook working directory or any child folder."""
    path = (Path(start) if start is not None else Path.cwd()).resolve()
    for candidate in (path, *path.parents):
        if (candidate / "pyproject.toml").is_file() and (candidate / "data" / "raw").is_dir():
            return candidate
    raise FileNotFoundError("Project root not found: need pyproject.toml and data/raw/")


def sha256_file(path: Path) -> str:
    checksum = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            checksum.update(chunk)
    return checksum.hexdigest()


def load_raw(root: Path) -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    """Load source CSVs without retyping keys or masking anomalies.

    A true empty CSV field becomes pandas <NA>; other literal strings are preserved.
    Header duplicates/missing fields cause an explicit error; extra fields are reported.
    """
    root = Path(root)
    frames = {}
    provenance = []
    for name, filename in RAW_FILES.items():
        path = root / "data" / "raw" / filename
        if not path.is_file():
            raise FileNotFoundError(f"Required source CSV absent: {path}")
        with path.open(encoding="utf-8-sig", newline="") as handle:
            header = next(csv.reader(handle))
        if len(header) != len(set(header)):
            raise ValueError(f"Duplicate CSV header(s) in {filename}: {header}")
        missing = sorted(set(EXPECTED_COLUMNS[name]) - set(header))
        if missing:
            raise ValueError(f"Required columns missing from {filename}: {missing}")
        # Keep exact nonempty strings; don't default-convert 'NULL', 'NA', etc. to missing.
        df = pd.read_csv(path, dtype="string", keep_default_na=False, na_values=[""], low_memory=False)
        frames[name] = df
        provenance.append({"dataset": name, "file": filename, "bytes": path.stat().st_size,
                           "sha256": sha256_file(path), "columns_unexpected": ", ".join(sorted(set(header) - set(EXPECTED_COLUMNS[name])))})
    return frames, pd.DataFrame(provenance)


def key_audit(df: pd.DataFrame, key: str) -> dict[str, int]:
    """Count duplicated key *rows* separately from redundant extra occurrences."""
    series = df[key]
    nonnull = series.dropna()
    return {
        "rows": len(df),
        "nonnull_keys": int(nonnull.size),
        "null_keys": int(series.isna().sum()),
        "distinct_nonnull_keys": int(nonnull.nunique()),
        "repeated_key_rows": int(nonnull.duplicated(keep=False).sum()),
        "extra_key_occurrences": int(nonnull.duplicated().sum()),
        "exact_duplicate_rows": int(df.duplicated().sum()),
    }


def audited_left_join(left: pd.DataFrame, right: pd.DataFrame, on: str, *, relation: str) -> tuple[pd.DataFrame, dict]:
    """A guarded many-to-one LEFT JOIN with explicit row conservation and match counts.

    Raises for duplicate nonnull right keys rather than hiding row multiplication.
    """
    if right[on].isna().any() or right[on].dropna().duplicated().any():
        raise ValueError(f"{relation}: invalid right-side key {on} (missing or duplicated)")
    right_renamed = right.copy()
    # Keep only supplied columns. The caller controls field overlap / suffix semantics.
    result = left.merge(right_renamed, on=on, how="left", indicator="_match", validate="many_to_one")
    if len(result) != len(left):
        raise AssertionError(f"{relation}: unexpected row multiplication")
    counts = result["_match"].value_counts()
    audit = {"relation": relation, "left_rows": len(left), "output_rows": len(result),
             "matched": int(counts.get("both", 0)), "unmatched": int(counts.get("left_only", 0)),
             "multiplied_rows": len(result) - len(left)}
    if audit["matched"] + audit["unmatched"] != audit["left_rows"]:
        raise AssertionError(f"{relation}: match buckets do not reconcile")
    return result, audit


def assert_conserved(universe: int, *counts: int) -> None:
    if sum(int(x) for x in counts) != int(universe):
        raise AssertionError(f"Expected {universe}, got partition total {sum(counts)} for {counts}")
