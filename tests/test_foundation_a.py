"""Synthetic contract tests. Never use the Turno source CSVs in tests."""
import pandas as pd
import pytest
from src.foundation_a import (
    EXPECTED_COLUMNS, assert_conserved, audited_left_join, find_project_root,
    key_audit, load_raw,
)


def test_project_root_in_notebooks():
    root = find_project_root()
    assert find_project_root(root / "notebooks" / "00_data_foundation") == root


def test_key_audit_distinguishes_null_duplicate_and_full_row():
    frame = pd.DataFrame({"id": ["01", "01", "2", None, None], "x": ["a", "a", "b", "u", "v"]})
    assert key_audit(frame, "id") == {
        "rows": 5, "nonnull_keys": 3, "null_keys": 2, "distinct_nonnull_keys": 2,
        "repeated_key_rows": 2, "extra_key_occurrences": 1, "exact_duplicate_rows": 1,
    }


def test_join_keeps_unmatched_and_reconciles():
    left = pd.DataFrame({"host_id": ["h1", "h1", "h2", "h3"], "value": [1, 2, 3, 4]})
    right = pd.DataFrame({"host_id": ["h1", "h2"], "arm": ["test", "control"]})
    out, stats = audited_left_join(left, right, "host_id", relation="toy")
    assert len(out) == 4 and out.loc[3, "_match"] == "left_only"
    assert (stats["matched"], stats["unmatched"], stats["multiplied_rows"]) == (3, 1, 0)


def test_join_rejects_duplicate_right_keys():
    with pytest.raises(ValueError, match="duplicated"):
        audited_left_join(pd.DataFrame({"k": ["a"]}), pd.DataFrame({"k": ["a", "a"]}), "k", relation="toy")


def test_join_rejects_missing_right_keys():
    with pytest.raises(ValueError, match="missing"):
        audited_left_join(pd.DataFrame({"k": ["a"]}), pd.DataFrame({"k": ["a", None]}), "k", relation="toy")


def test_empty_source_file_is_missing(tmp_path):
    with pytest.raises(FileNotFoundError, match="Required source CSV absent"):
        load_raw(tmp_path)


def test_schema_validation_and_preserve_identifier_string(tmp_path):
    raw = tmp_path / "data" / "raw"
    raw.mkdir(parents=True)
    for name, filename in (("exposures", "experiment_exposures.csv"),
                           ("assignments", "assignments.csv"),
                           ("payments", "payment_logs.csv")):
        cols = EXPECTED_COLUMNS[name]
        data = {c: ["00" if c.endswith("_id") else ""] for c in cols}
        pd.DataFrame(data).to_csv(raw / filename, index=False)
    frames, provenance = load_raw(tmp_path)
    assert frames["exposures"].host_id.iloc[0] == "00"
    assert pd.isna(frames["payments"].captured_at.iloc[0])
    assert len(provenance) == 3


def test_csv_extra_column_is_not_removed(tmp_path):
    raw = tmp_path / "data" / "raw"; raw.mkdir(parents=True)
    for name, filename in (("exposures", "experiment_exposures.csv"),
                           ("assignments", "assignments.csv"),
                           ("payments", "payment_logs.csv")):
        cols = EXPECTED_COLUMNS[name]
        pd.DataFrame({**{c: ["x"] for c in cols}, **({"unexpected_field": ["z"]} if name == "exposures" else {})}).to_csv(raw / filename, index=False)
    frames, provenance = load_raw(tmp_path)
    assert "unexpected_field" in frames["exposures"].columns
    assert provenance.set_index("dataset").loc["exposures", "columns_unexpected"] == "unexpected_field"


def test_schema_missing_column_fails_loudly(tmp_path):
    raw = tmp_path / "data" / "raw"; raw.mkdir(parents=True)
    (raw / "experiment_exposures.csv").write_text("host_id,experiment_group\nh1,test\n")
    with pytest.raises(ValueError, match="Required columns missing"):
        load_raw(tmp_path)


def test_conservation_detects_bad_partition():
    assert_conserved(6, 0, 1, 5)
    with pytest.raises(AssertionError):
        assert_conserved(6, 1, 4)
