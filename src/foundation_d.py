"""Checkpoint D: observable payment-log journeys, not payment outcomes.

Every measurement is derived from immutable attempt records. No classification
in this module implies financial settlement, recovery, duplicate charges,
preauthorization, or treatment effects.
"""
from __future__ import annotations

import pandas as pd

from src.foundation_a import assert_conserved
from src.foundation_ce import parse_utc, utc_timestamp

FAILURE_STATUSES = frozenset({"declined", "failed"})


def checked_attempts(assignments: pd.DataFrame, logs: pd.DataFrame, hosts: pd.DataFrame) -> pd.DataFrame:
    """Attach project metadata to attempts, validating all join cardinalities."""
    for df, col in [(assignments, "assignment_id"), (logs, "payment_log_id"), (hosts, "host_id")]:
        if df[col].isna().any() or df[col].duplicated().any():
            raise ValueError(f"Missing/duplicate keys: {col}")
    a = assignments[["assignment_id", "host_id", "completed_at"]].rename(columns={"host_id": "assignment_host_id"})
    h = hosts[["host_id", "experiment_group", "first_exposed_at"]]
    t = logs.merge(a, on="assignment_id", how="left", validate="many_to_one", indicator="_project_match")
    if len(t) != len(logs) or not t["_project_match"].eq("both").all():
        raise ValueError("Orphan/multiplied payment logs")
    if not t["host_id"].eq(t["assignment_host_id"]).all():
        raise ValueError("Payment host does not match project host")
    t = t.drop(columns="_project_match").merge(h, on="host_id", how="left", validate="many_to_one", indicator="_host_match")
    if len(t) != len(logs) or not t["_host_match"].eq("both").all():
        raise ValueError("Orphan/multiplied experiment hosts")
    t = t.drop(columns="_host_match")
    t["_created_utc"] = parse_utc(t["created_at"])
    t["_captured_utc"] = parse_utc(t["captured_at"])
    t["_completion_utc"] = parse_utc(t["completed_at"])
    t["_success"] = t["payment_status"].eq("succeeded").fillna(False)
    t["_capture"] = t["captured_at"].notna()
    t["_concordant"] = t["_success"] & t["_capture"]
    t["_discordant"] = t["_success"] ^ t["_capture"]
    t["_failure_status"] = t["payment_status"].isin(FAILURE_STATUSES)
    t["_manual"] = t["is_manual_attempt"].eq("true").fillna(False)
    t["_invalid_created"] = t["created_at"].notna() & t["_created_utc"].isna()
    t["_invalid_capture"] = t["_capture"] & t["_captured_utc"].isna()
    assert_conserved(len(logs), int(t["_discordant"].sum()), int((~t["_discordant"]).sum()))
    return t


def project_journeys(assignments: pd.DataFrame, attempts: pd.DataFrame) -> pd.DataFrame:
    """Full-project evidence partition plus nonexclusive flags, with zero-log rows.

    Only five mutually exclusive evidence categories are used. Additional
    diagnostics are overlapping and MUST NOT be summed as a partition.
    """
    keys = assignments["assignment_id"]
    if keys.isna().any() or keys.duplicated().any():
        raise ValueError("Invalid project keys")
    if attempts["payment_log_id"].isna().any() or attempts["payment_log_id"].duplicated().any():
        raise ValueError("Invalid attempt keys")
    gp = attempts.groupby("assignment_id", sort=False)
    measures = gp.agg(
        attempts=("payment_log_id", "size"),
        success_rows=("_success", "sum"),
        capture_rows=("_capture", "sum"),
        concordant_rows=("_concordant", "sum"),
        discordant_rows=("_discordant", "sum"),
        failed_rows=("_failure_status", "sum"),
        manual_rows=("_manual", "sum"),
        invalid_created_rows=("_invalid_created", "sum"),
        invalid_capture_rows=("_invalid_capture", "sum"),
        distinct_methods=("payment_method", "nunique"),
    )
    measures["capture_methods"] = attempts.loc[attempts["_capture"]].groupby("assignment_id")["payment_method"].nunique().reindex(measures.index, fill_value=0)
    measures["distinct_capture_timestamps"] = attempts.loc[attempts["_capture"]].groupby("assignment_id")["captured_at"].nunique().reindex(measures.index, fill_value=0)
    measures["first_capture_utc"] = gp["_captured_utc"].min()
    if not set(attempts["assignment_id"]).issubset(set(keys)):
        raise ValueError("Orphan attempts")
    project = assignments[["assignment_id", "host_id", "completed_at"]].merge(measures, on="assignment_id", how="left", validate="one_to_one", indicator="_join")
    if len(project) != len(assignments):
        raise AssertionError("Project multiplication")
    project["has_logs"] = project["_join"].eq("both")
    project = project.drop(columns="_join")
    number_cols = measures.columns.drop("first_capture_utc")
    project[number_cols] = project[number_cols].fillna(0).astype("int64")
    any_s, any_c = project["success_rows"].gt(0), project["capture_rows"].gt(0)
    project["financial_evidence_partition"] = "unclassified"
    project.loc[~project["has_logs"], "financial_evidence_partition"] = "no_logs"
    project.loc[project["has_logs"] & ~any_s & ~any_c, "financial_evidence_partition"] = "logs_no_success_or_capture"
    project.loc[project["has_logs"] & any_s & ~any_c, "financial_evidence_partition"] = "success_status_only"
    project.loc[project["has_logs"] & ~any_s & any_c, "financial_evidence_partition"] = "capture_timestamp_only"
    project.loc[project["has_logs"] & any_s & any_c, "financial_evidence_partition"] = "both_evidence_types"
    if project["financial_evidence_partition"].eq("unclassified").any():
        raise AssertionError("Financial partition not exhaustive")
    project["has_success_status"] = any_s
    project["has_capture_timestamp"] = any_c
    project["has_concordant_attempt"] = project["concordant_rows"].gt(0)
    project["split_evidence_attempts_only"] = any_s & any_c & ~project["has_concordant_attempt"]
    project["has_discordance"] = project["discordant_rows"].gt(0)
    project["multiple_capture_rows"] = project["capture_rows"].gt(1)
    project["multiple_capture_methods"] = project["capture_methods"].gt(1)
    project["multiple_methods"] = project["distinct_methods"].gt(1)
    project["has_manual"] = project["manual_rows"].gt(0)
    project["has_automatic"] = (project["attempts"] - project["manual_rows"]).gt(0)
    project["mixed_manual_auto"] = project["has_manual"] & project["has_automatic"]
    project["has_failure_status"] = project["failed_rows"].gt(0)
    project["has_both_failure_and_success"] = project["has_failure_status"] & any_s
    project["has_both_failure_and_capture"] = project["has_failure_status"] & any_c
    project["materially_ambiguous_record_evidence"] = (~project["has_logs"] | project["has_discordance"] | project["multiple_capture_rows"] | project["split_evidence_attempts_only"] | project["invalid_created_rows"].gt(0) | project["invalid_capture_rows"].gt(0))
    assert_conserved(len(project), *[int(x) for x in project["financial_evidence_partition"].value_counts().values])
    assert_conserved(len(attempts), int(project["attempts"].sum()))
    assert_conserved(int(attempts["_capture"].sum()), int(project["capture_rows"].sum()))
    return project


def ordered_record_diagnostics(attempts: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Chronology of *record creation*, excluding ties/invalid timestamps.

    Returns per-project flags and adjacent record transitions. Does not infer
    chronology of financial operations, failure notification or recovery.
    """
    groups = attempts.groupby("assignment_id", sort=False)
    ties = attempts.loc[attempts["_created_utc"].notna()].duplicated(["assignment_id", "_created_utc"], keep=False)
    tied_ids = set(attempts.loc[attempts["_created_utc"].notna()].loc[ties, "assignment_id"])
    missing_ids = set(attempts.loc[attempts["_created_utc"].isna(), "assignment_id"])
    sorted_at = attempts.sort_values(["assignment_id", "_created_utc"], kind="mergesort")
    prev = sorted_at.groupby("assignment_id", sort=False)
    sorted_at = sorted_at.copy()
    sorted_at["_prev_method"] = prev["payment_method"].shift()
    sorted_at["_prev_status"] = prev["payment_status"].shift()
    sorted_at["_prev_created"] = prev["_created_utc"].shift()
    sorted_at["_time_order_clear"] = ~sorted_at["assignment_id"].isin(tied_ids | missing_ids)
    transitions = sorted_at.loc[sorted_at["_time_order_clear"] & sorted_at["_prev_method"].notna()].copy()
    # Explicitly require strictly increasing timestamps for each adjacent pair.
    if not transitions["_created_utc"].gt(transitions["_prev_created"]).all():
        raise AssertionError("Ambiguous transitions included")
    safe = sorted_at.loc[sorted_at["_time_order_clear"]].copy()
    gp = safe.groupby("assignment_id", sort=False)
    first = gp.first()
    last = gp.last()
    j = pd.DataFrame(index=groups.size().index)
    j["tied_created_timestamp"] = j.index.isin(tied_ids)
    j["missing_or_invalid_created"] = j.index.isin(missing_ids)
    j["sequence_order_clear"] = ~(j["tied_created_timestamp"] | j["missing_or_invalid_created"])
    j["first_record_method"] = first["payment_method"].reindex(j.index)
    j["last_record_method"] = last["payment_method"].reindex(j.index)
    # Groupwise earliest *record creation* time by status, not failure event time.
    for name, cond in [("failure", "_failure_status"), ("success", "_success"), ("manual", "_manual")]:
        time = safe.loc[safe[cond]].groupby("assignment_id")["_created_utc"].min()
        j[f"first_{name}_record_created"] = time.reindex(j.index)
    j["failure_record_before_success_record"] = j["sequence_order_clear"] & j["first_failure_record_created"].lt(j["first_success_record_created"])
    j["success_record_before_failure_record"] = j["sequence_order_clear"] & j["first_success_record_created"].lt(j["first_failure_record_created"])
    j["failure_record_before_manual_record"] = j["sequence_order_clear"] & j["first_failure_record_created"].lt(j["first_manual_record_created"])
    # Failure status and capture timestamp on separate attempts may be compared
    # as recorded timestamps but NOT construed as verified failure-before-recovery.
    return j.reset_index(), transitions


def completion_period(completed: pd.Series) -> pd.Series:
    """Half-open UTC periods, including explicit unknown and out-of-scope."""
    dt = parse_utc(completed)
    out = pd.Series("out_of_documented_completion_periods", index=completed.index, dtype="string")
    out.loc[dt.isna()] = "unknown_completion"
    out.loc[dt.ge(utc_timestamp("2025-07-18")) & dt.lt(utc_timestamp("2025-08-18"))] = "baseline"
    out.loc[dt.ge(utc_timestamp("2025-08-18")) & dt.lt(utc_timestamp("2025-11-20"))] = "experiment"
    return out
