"""Synthetic-only checks for technical evidence used in Checkpoint B."""
import pandas as pd
import pytest

from src.foundation_b import (
    first_completion_flag_audit,
    project_capture_evidence,
    status_capture_matrix,
)


def assignments(rows):
    return pd.DataFrame(rows, columns=["assignment_id", "host_id", "completed_at", "is_first_completed_project"])


def payments(rows):
    return pd.DataFrame(rows, columns=["payment_log_id", "assignment_id", "host_id", "payment_method", "payment_status", "captured_at"])


def test_status_cross_counts_success_without_timestamp_and_failure_with_timestamp():
    p = payments([
        ("1", "a", "h", "card", "succeeded", None),
        ("2", "a", "h", "card", "failed", "2025-10-01T10:00:00Z"),
        ("3", "a", "h", "card", "voided", None),
        ("4", "a", "h", "card", "succeeded", "2025-10-01T10:01:00Z"),
    ])
    matrix = status_capture_matrix(p)
    assert int(matrix.loc["succeeded", "captured_at_missing"]) == 1
    assert int(matrix.loc["failed", "captured_at_present"]) == 1
    assert matrix["all_attempts"].sum() == 4


def test_missing_status_is_visible_and_reconciles():
    p = payments([("p", "a", "h", "card", None, None)])
    assert status_capture_matrix(p).loc["<MISSING>", "captured_at_missing"] == 1


def test_capture_evidence_includes_no_logs_and_separates_attempts():
    a = assignments([("a", "h", "2025-10-01", "true"), ("b", "h", "2025-10-02", "false")])
    p = payments([("p", "a", "h", "card", "succeeded", None)])
    out = project_capture_evidence(a, p).set_index("assignment_id")
    assert out.loc["a", "any_success_status"] and not out.loc["a", "any_capture_field"]
    assert out.loc["a", "any_discordant"]
    assert out.loc["b", "attempt_rows"] == 0 and not out.loc["b", "has_logs"]
    assert out["attempt_rows"].sum() == 1


def test_multiple_captures_different_method_and_distinct_timestamps():
    a = assignments([("a", "h", "2025-10-01", "true")])
    p = payments([("p1", "a", "h", "card", "succeeded", "2025-10-01T10:00:00Z"),
                  ("p2", "a", "h", "credits", "succeeded", "2025-10-01T10:05:00Z")])
    x = project_capture_evidence(a, p).iloc[0]
    assert x.multiple_capture_rows and x.multiple_distinct_capture_times and x.capture_multiple_methods
    assert x.first_valid_capture_utc == pd.Timestamp("2025-10-01T10:00:00Z")


def test_two_captures_same_timestamp_are_not_two_distinct_times():
    a = assignments([("a", "h", "2025-10-01", "true")])
    p = payments([("p1", "a", "h", "card", "succeeded", "2025-10-01T10:00:00Z"),
                  ("p2", "a", "h", "card", "succeeded", "2025-10-01T10:00:00Z")])
    x = project_capture_evidence(a, p).iloc[0]
    assert x.multiple_capture_rows and not x.multiple_distinct_capture_times


def test_malformed_capture_timestamp_remains_visible_not_ignored():
    a = assignments([("a", "h", "2025-10-01", "true")])
    p = payments([("p", "a", "h", "card", "succeeded", "not-a-date")])
    x = project_capture_evidence(a, p).iloc[0]
    assert x.captured_field_rows == 1 and x.invalid_capture_timestamp_rows == 1
    assert not x.first_valid_capture_identifiable and x.any_capture_field and x.potentially_ambiguous


def test_mismatch_of_host_is_rejected():
    a = assignments([("a", "h", "2025-10-01", "true")])
    p = payments([("p", "a", "other", "card", "succeeded", None)])
    with pytest.raises(ValueError, match="host"):
        project_capture_evidence(a, p)


def test_orphan_log_is_rejected():
    a = assignments([("a", "h", "2025-10-01", "true")])
    p = payments([("p", "missing", "h", "card", "succeeded", None)])
    with pytest.raises(ValueError, match="Orphan"):
        project_capture_evidence(a, p)


def test_duplicate_primary_key_is_rejected():
    a = assignments([("a", "h", "2025-10-01", "true")])
    p = payments([("p", "a", "h", "card", "failed", None), ("p", "a", "h", "card", "failed", None)])
    with pytest.raises(ValueError, match="payment_log_id"):
        project_capture_evidence(a, p)


def test_first_flag_later_than_known_completion_detected():
    a = assignments([("early", "h", "2025-09-01T00:00:00Z", "false"),
                     ("late", "h", "2025-09-05T00:00:00Z", "true")])
    audit = first_completion_flag_audit(a).iloc[0]
    assert audit.flagged_later_than_observed_earliest == 1 and audit.positive_flags == 1


def test_first_flags_repeated_and_timestamp_ties_preserved():
    a = assignments([("p1", "h", "2025-09-01T00:00:00Z", "true"),
                     ("p2", "h", "2025-09-01T00:00:00Z", "true")])
    x = first_completion_flag_audit(a).iloc[0]
    assert x.positive_flags == 2 and x.earliest_observed_ties == 2
    assert x.flagged_later_than_observed_earliest == 0


def test_empty_data_no_payments_yields_all_no_logs():
    a = assignments([("p", "h", "2025-09-01T00:00:00Z", "false")])
    empty = payments([])
    out = project_capture_evidence(a, empty)
    assert len(out) == 1 and out.iloc[0].attempt_rows == 0


def test_similar_log_fields_do_not_collapse_distinct_ids():
    a = assignments([("a", "h", "2025-10-01", "true")])
    p = payments([("p1", "a", "h", "card", "failed", None), ("p2", "a", "h", "card", "failed", None)])
    out = project_capture_evidence(a, p)
    assert out.loc[0, "attempt_rows"] == 2
