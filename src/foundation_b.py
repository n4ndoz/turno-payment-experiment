"""Technical evidence helpers for EDA 0 Checkpoint B (not business KPIs).

Never decide whether a project's total due was paid; records have no amounts.
Input frames are not modified. Missing capture timestamp is not proof of
non-payment at the completed-project grain.
"""
from __future__ import annotations

import pandas as pd

from src.foundation_a import assert_conserved


def status_capture_matrix(payment_logs: pd.DataFrame) -> pd.DataFrame:
    """Attempt-level raw-status vs present-captured_at matrix, including unknown status."""
    status = payment_logs["payment_status"].fillna("<MISSING>")
    has_capture = payment_logs["captured_at"].notna()
    matrix = pd.crosstab(status, has_capture)
    matrix = matrix.reindex(columns=[False, True], fill_value=0)
    matrix.columns = ["captured_at_missing", "captured_at_present"]
    matrix["all_attempts"] = matrix.sum(axis=1)
    assert_conserved(len(payment_logs), int(matrix["all_attempts"].sum()))
    assert_conserved(len(payment_logs), int(matrix["captured_at_missing"].sum()), int(matrix["captured_at_present"].sum()))
    return matrix


def project_capture_evidence(assignments: pd.DataFrame, payment_logs: pd.DataFrame) -> pd.DataFrame:
    """One-row-per-project overlapping diagnostic evidence (not payment classification).

    Requires unique, non-null assignment IDs and payment log IDs; rejects
    orphan logs and host mismatch rather than losing or duplicating records.
    Captured timestamps are counted if populated; parsed UTC timestamps used
    solely to report the earliest valid observed timestamp.
    """
    for df, key in [(assignments, "assignment_id"), (payment_logs, "payment_log_id")]:
        if df[key].isna().any() or df[key].duplicated().any():
            raise ValueError(f"Unusable or duplicate key: {key}")
    ids = assignments[["assignment_id", "host_id"]].rename(columns={"host_id": "assignment_host_id"})
    logs = payment_logs.merge(ids, on="assignment_id", how="left", validate="many_to_one", indicator=True)
    if len(logs) != len(payment_logs) or not logs["_merge"].eq("both").all():
        raise ValueError("Orphan payment logs or multiplied rows")
    if not logs["host_id"].eq(logs["assignment_host_id"]).all():
        raise ValueError("Payment host does not match assignment host")
    logs = logs.copy()
    logs["_is_success"] = logs["payment_status"].eq("succeeded").fillna(False)
    logs["_has_capture"] = logs["captured_at"].notna()
    logs["_concordant"] = logs["_is_success"] & logs["_has_capture"]
    logs["_discordant"] = logs["_is_success"] ^ logs["_has_capture"]
    logs["_parsed_capture"] = pd.to_datetime(logs["captured_at"], format="mixed", utc=True, errors="coerce")
    logs["_invalid_capture"] = logs["_has_capture"] & logs["_parsed_capture"].isna()
    gp = logs.groupby("assignment_id", sort=False, dropna=False)
    grouped = gp.agg(
        attempt_rows=("payment_log_id", "size"),
        success_status_rows=("_is_success", "sum"),
        captured_field_rows=("_has_capture", "sum"),
        concordant_rows=("_concordant", "sum"),
        discordant_rows=("_discordant", "sum"),
        invalid_capture_timestamp_rows=("_invalid_capture", "sum"),
        first_valid_capture_utc=("_parsed_capture", "min"),
        distinct_capture_timestamps=("captured_at", "nunique"),
    )
    captured_methods = logs.loc[logs["_has_capture"]].groupby("assignment_id")["payment_method"].nunique(dropna=True)
    grouped["distinct_capture_methods"] = captured_methods.reindex(grouped.index, fill_value=0)
    if int(grouped["attempt_rows"].sum()) != len(payment_logs):
        raise AssertionError("Attempt totals differ after per-project grouping")
    if int(grouped["captured_field_rows"].sum()) != int(payment_logs["captured_at"].notna().sum()):
        raise AssertionError("Capture totals differ after per-project grouping")
    # Left join from *all* projects; projects without logs must survive.
    project = assignments[["assignment_id"]].merge(grouped, left_on="assignment_id", right_index=True,
                                                      how="left", validate="one_to_one", indicator=True)
    if len(project) != len(assignments):
        raise AssertionError("Project universe changed")
    project["has_logs"] = project["_merge"].eq("both")
    project = project.drop(columns="_merge")
    numeric = ["attempt_rows", "success_status_rows", "captured_field_rows", "concordant_rows",
               "discordant_rows", "invalid_capture_timestamp_rows", "distinct_capture_timestamps",
               "distinct_capture_methods"]
    project[numeric] = project[numeric].fillna(0).astype("int64")
    project["any_success_status"] = project["success_status_rows"].gt(0)
    project["any_capture_field"] = project["captured_field_rows"].gt(0)
    project["any_concordant"] = project["concordant_rows"].gt(0)
    project["any_discordant"] = project["discordant_rows"].gt(0)
    project["multiple_capture_rows"] = project["captured_field_rows"].gt(1)
    project["multiple_distinct_capture_times"] = project["distinct_capture_timestamps"].gt(1)
    project["capture_multiple_methods"] = project["distinct_capture_methods"].gt(1)
    project["first_valid_capture_identifiable"] = project["first_valid_capture_utc"].notna()
    # These are overlapping observations, not exclusive classifications.
    project["potentially_ambiguous"] = project["any_discordant"] | project["multiple_capture_rows"] | ~project["has_logs"] | project["invalid_capture_timestamp_rows"].gt(0)
    assert_conserved(len(assignments), int(project["has_logs"].sum()), int((~project["has_logs"]).sum()))
    return project


def first_completion_flag_audit(assignments: pd.DataFrame) -> pd.DataFrame:
    """Per-host flag/chronology check in the *observed extract only*."""
    if assignments["assignment_id"].isna().any() or assignments["assignment_id"].duplicated().any():
        raise ValueError("Duplicate or missing project IDs")
    a = assignments[["assignment_id", "host_id", "completed_at", "is_first_completed_project"]].copy()
    a["_flag"] = a["is_first_completed_project"].eq("true").fillna(False)
    a["_completion"] = pd.to_datetime(a["completed_at"], format="mixed", utc=True, errors="coerce")
    minimum = a.groupby("host_id")["_completion"].transform("min")
    a["_earliest_observed"] = a["_completion"].eq(minimum) & a["_completion"].notna()
    a["_flag_later_than_observed_earliest"] = a["_flag"] & a["_completion"].gt(minimum)
    a["_flag_timestamp_invalid"] = a["_flag"] & a["_completion"].isna()
    per_host = a.groupby("host_id", dropna=False).agg(
        observed_projects=("assignment_id", "size"), positive_flags=("_flag", "sum"),
        flagged_later_than_observed_earliest=("_flag_later_than_observed_earliest", "sum"),
        flagged_timestamp_invalid=("_flag_timestamp_invalid", "sum"),
        earliest_observed_ties=("_earliest_observed", "sum"),
    ).reset_index()
    if int(per_host["observed_projects"].sum()) != len(assignments):
        raise AssertionError("Flag audit lost projects")
    return per_host
