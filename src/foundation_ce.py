"""Shared technical utilities for EDA 0 temporal and population checks.

Strictly diagnostic: no business KPI, causal estimand, or financial outcome.
"""
from __future__ import annotations
import pandas as pd


def utc_timestamp(value: str) -> pd.Timestamp:
    """Return timezone-aware UTC timestamp for an explicitly documented boundary."""
    return pd.Timestamp(value, tz="UTC")


def parse_utc(series: pd.Series) -> pd.Series:
    """Derive UTC datetimes without changing immutable source strings."""
    return pd.to_datetime(series, format="mixed", utc=True, errors="coerce")


def compare_times(left: pd.Series, right: pd.Series) -> pd.Series:
    """Exhaustive temporal buckets; no synthetic tie-breaking or null dropping."""
    if len(left) != len(right) or not left.index.equals(right.index):
        raise ValueError("Temporal series must share length and index")
    result = pd.Series("unknown", index=left.index, dtype="string")
    known = left.notna() & right.notna()
    result.loc[known & left.lt(right)] = "before"
    result.loc[known & left.eq(right)] = "same_instant"
    result.loc[known & left.gt(right)] = "after"
    assert len(result) == sum((result == cat).sum() for cat in ["before", "same_instant", "after", "unknown"])
    return result


def potential_window_coverage(completed: pd.Series, days: int, cutoff_day: str = "2025-12-19") -> pd.Series:
    """Candidate follow-up classification with unknown exact closing time.

    If observation through calendar day cutoff_day is documented but the last
    captured instant is not, deadlines strictly before 00:00 on that day are
    *conservatively covered under the documented continuous-follow-up premise*.
    Deadlines within that date are time-of-day uncertain. Later are beyond the
    documented horizon. This is never proof that the export contains all events.
    """
    if days < 0: raise ValueError("Follow-up days cannot be negative")
    boundary = utc_timestamp(cutoff_day)
    end_day = boundary + pd.Timedelta(days=1)
    deadline = completed + pd.Timedelta(days=days)
    result = pd.Series("unknown_completion", index=completed.index, dtype="string")
    result.loc[completed.notna() & deadline.lt(boundary)] = "within_documented_horizon_conservative"
    result.loc[completed.notna() & deadline.ge(boundary) & deadline.lt(end_day)] = "last_day_time_uncertain"
    result.loc[completed.notna() & deadline.ge(end_day)] = "beyond_documented_horizon"
    return result


def host_experiment_counts(hosts: pd.DataFrame, projects: pd.DataFrame,
                           start: str="2025-08-18", end_exclusive: str="2025-11-20") -> pd.DataFrame:
    """Start from all registered hosts, including those with zero observed completions."""
    if hosts.host_id.isna().any() or hosts.host_id.duplicated().any():
        raise ValueError("Host keys must be unique and not missing")
    if projects.assignment_id.isna().any() or projects.assignment_id.duplicated().any():
        raise ValueError("Project keys must be unique and not missing")
    completion = parse_utc(projects.completed_at)
    in_window = completion.ge(utc_timestamp(start)) & completion.lt(utc_timestamp(end_exclusive))
    counts = projects.loc[in_window].groupby("host_id").size()
    if not set(projects.host_id.dropna()).issubset(set(hosts.host_id)):
        raise ValueError("Projects with unregistered hosts")
    answer = hosts[["host_id", "experiment_group", "first_exposed_at"]].copy()
    answer["experiment_completions"] = answer.host_id.map(counts).fillna(0).astype("int64")
    if int(answer.experiment_completions.sum()) != int(in_window.sum()):
        raise AssertionError("Experiment completion totals did not reconcile")
    return answer
