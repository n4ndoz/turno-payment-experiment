"""Narrow, deterministic decision checks after the approved inferential validation.

All times are UTC, and completion observation ends strictly before
2025-11-20 00:00 UTC. The source event flag, not a reconstructed first
project, defines the candidate M2 cohort. No causal retention is identified.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm

from src.experiment_impact import EXPERIMENT_END


GROUPS = ("control", "test")


def m2_recorded_exposure(project: pd.DataFrame, hosts: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Preserve registered-host denominators and flagged-event chronology."""
    if hosts.host_id.isna().any() or not hosts.host_id.is_unique:
        raise ValueError("Registered host IDs must be unique and non-null")
    if not project.assignment_id.is_unique or project.assignment_id.isna().any():
        raise ValueError("Duplicate/null project ID")
    if not project.host_id.isin(hosts.host_id).all():
        raise ValueError("Unregistered project host")
    q = project.loc[project.in_experiment & project.is_first_true].copy()
    if q.host_id.duplicated().any():
        raise ValueError("More than one flagged experiment first project for a host")
    if q.exposed_utc.isna().any() or q.completed_utc.isna().any():
        raise ValueError("Missing first-event or exposure time")
    q["recorded_pre_exposure"] = q.completed_utc.lt(q.exposed_utc)
    q["recorded_post_exposure"] = ~q.recorded_pre_exposure
    group_counts = hosts.experiment_group.value_counts()
    rows = []
    for grp in GROUPS:
        sub = q.loc[q.experiment_group.eq(grp)]
        base = int(len(sub))
        pre = int(sub.recorded_pre_exposure.sum())
        post = int(sub.recorded_post_exposure.sum())
        n_hosts = int(group_counts.get(grp, 0))
        if n_hosts == 0 or pre + post != base:
            raise AssertionError("Invalid group or nonexhaustive chronology")
        rows.append(dict(group=grp, registered_hosts=n_hosts, flagged_first=base,
                         pre_recorded_exposure=pre, post_or_at_recorded_exposure=post,
                         pre_share_of_flagged=pre/base if base else np.nan,
                         post_share_of_flagged=post/base if base else np.nan,
                         original_M2_per_host=base/n_hosts,
                         post_recorded_exposure_per_host=post/n_hosts))
    return pd.DataFrame(rows), q


def second_within_30_days(project: pd.DataFrame, *, observation_end: pd.Timestamp = EXPERIMENT_END) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """First flagged experiment project -> earliest strictly later completion.

    Eligibility requires first + 30 days STRICTLY before the exclusive end.
    This guarantees an exact inclusive 30-day right endpoint is observable
    within the documented completion window. Same-time completions do not
    establish a *later* second project and are flagged diagnostically.
    """
    if not project.assignment_id.is_unique or project.assignment_id.isna().any():
        raise ValueError("Invalid assignment IDs")
    if observation_end.tzinfo is None:
        raise ValueError("Observation end must be timezone-aware")
    if project.completed_utc.isna().any() or project.created_utc.isna().any():
        raise ValueError("Missing project timestamps")
    first = project.loc[project.in_experiment & project.is_first_true,
        ["host_id", "assignment_id", "experiment_group", "completed_utc", "created_utc"]].copy()
    if first.host_id.duplicated().any():
        raise ValueError("Multiple first-ever flagged projects per host")
    first = first.rename(columns={"assignment_id":"first_assignment_id", "completed_utc":"first_completed_at", "created_utc":"first_created_at"})
    first["followup_complete"] = first.first_completed_at.add(pd.Timedelta(days=30)).lt(observation_end)
    first["deadline_30d"] = first.first_completed_at.add(pd.Timedelta(days=30))
    elig = first.loc[first.followup_complete].copy()

    # Do not lose events in hosts with 0 subsequent completions.
    seq = project[["host_id", "assignment_id", "completed_utc", "created_utc"]].merge(
        elig[["host_id", "first_assignment_id", "first_completed_at", "deadline_30d"]],
        on="host_id", how="inner", validate="many_to_one")
    distinct = seq.assignment_id.ne(seq.first_assignment_id)
    before_or_equal = distinct & seq.completed_utc.le(seq.first_completed_at)
    strictly_after = distinct & seq.completed_utc.gt(seq.first_completed_at)
    seq["within_30d"] = strictly_after & seq.completed_utc.le(seq.deadline_30d)
    # Deterministic tie-breaking for the earliest distinct strictly-later completion.
    nexts = (seq.loc[seq.within_30d].sort_values(["host_id", "completed_utc", "assignment_id"],kind="stable")
             .drop_duplicates("host_id",keep="first")
             [["host_id", "assignment_id", "completed_utc", "created_utc"]]
             .rename(columns={"assignment_id":"second_assignment_id", "completed_utc":"second_completed_at", "created_utc":"second_created_at"}))
    result = elig.merge(nexts,on="host_id",how="left",validate="one_to_one")
    result["has_second_30d"] = result.second_assignment_id.notna()
    result["second_created_before_first_completion"] = (result.has_second_30d & result.second_created_at.lt(result.first_completed_at))
    result["second_created_simultaneous_first_completion"] = result.has_second_30d & result.second_created_at.eq(result.first_completed_at)
    result["second_created_after_first_completion"] = result.has_second_30d & result.second_created_at.gt(result.first_completed_at)
    # Diagnostic temporal inconsistencies; keep them rather than silently repairing.
    inconsistency = seq.loc[before_or_equal].groupby("host_id").agg(
        earlier_or_tied_project_count=("assignment_id", "size"),
        exactly_tied_project_count=("completed_utc",lambda x: int(x.eq(seq.loc[x.index,"first_completed_at"]).sum())),
    )
    result["earlier_or_tied_project_count"] = pd.to_numeric(result.host_id.map(inconsistency.earlier_or_tied_project_count),errors="coerce").astype(float).fillna(0).astype(int)
    result["exactly_tied_project_count"] = pd.to_numeric(result.host_id.map(inconsistency.exactly_tied_project_count),errors="coerce").astype(float).fillna(0).astype(int)
    rows=[]
    for grp in GROUPS:
        q=result.loc[result.experiment_group.eq(grp)]
        n=len(q);with_second=int(q.has_second_30d.sum())
        earlier=int(q.second_created_before_first_completion.sum())
        same=int(q.second_created_simultaneous_first_completion.sum())
        after=int(q.second_created_after_first_completion.sum())
        if earlier+same+after!=with_second:raise AssertionError("Second booking split mismatch")
        rows.append(dict(group=grp,eligible_hosts=n,second_within_30d=with_second,
                         second_rate=with_second/n if n else np.nan,
                         second_created_before_first=earlier,
                         second_created_simultaneously=same,
                         second_created_after_first=after,
                         flagged_first_earlier_or_tied_hosts=int(q.earlier_or_tied_project_count.gt(0).sum()),
                         exactly_tied_second_candidate_hosts=int(q.exactly_tied_project_count.gt(0).sum())))
    summary=pd.DataFrame(rows)
    diagnostics=dict(flagged_experiment_firsts=len(first),eligible_firsts=len(elig),
                     censored_firsts=int((~first.followup_complete).sum()),
                     earlier_or_tied_hosts=int(result.earlier_or_tied_project_count.gt(0).sum()),
                     tied_hosts=int(result.exactly_tied_project_count.gt(0).sum()),
                     strict_followup_end=str(observation_end))
    if summary.eligible_hosts.sum() != len(result):raise AssertionError("Cohort mismatch")
    return summary,result,diagnostics


def d1_project_weighted_baseline_sensitivity(paired: pd.DataFrame) -> dict:
    """Simple optional host-level project-weighted linear probability model.

    Response: experiment D1 successes / experiment completed projects.
    WLS weight: experiment completed projects, reproducing project weighting.
    Predetermined control: log1p(baseline completed project count). This
    avoids baseline D1 outcomes whose 24-hour window could cross into the
    experimental treatment period. No invented historical rates.

    HC3 is heteroskedasticity-robust at independent host rows (one per host).
    The Test coefficient is a common-slope *conditional association* over
    observed completed projects, not an ITT or causally standardized effect.
    """
    if not paired.host_id.is_unique or paired.host_id.isna().any():
        raise ValueError("Duplicate host in paired panel")
    if not paired.experiment_group.isin(GROUPS).all():
        raise ValueError("Unknown host group")
    if (paired[["baseline_projects", "baseline_captured", "experiment_projects", "experiment_captured"]] < 0).any().any():
        raise ValueError("Negative project count")
    for p in ("baseline", "experiment"):
        if (paired[f"{p}_captured"] > paired[f"{p}_projects"]).any():
            raise ValueError("Captured projects exceed denominator")
    usable = paired.experiment_projects.gt(0)
    active = paired.loc[usable].copy()
    if active.experiment_group.nunique()!=2:raise ValueError("Both groups required")
    test=active.experiment_group.eq("test").astype(float)
    x = pd.DataFrame({"intercept":1.,"test":test,
                      "log1p_baseline_projects":np.log1p(active.baseline_projects.astype(float))})
    y=active.experiment_captured.to_numpy(dtype=float)/active.experiment_projects.to_numpy(dtype=float)
    w=active.experiment_projects.to_numpy(dtype=float)
    full = sm.WLS(y,x,weights=w).fit(cov_type="HC3")
    b=float(full.params["test"]);lo,hi=map(float,full.conf_int().loc["test"])
    control=paired.loc[paired.experiment_group.eq("control")]
    treatment=paired.loc[paired.experiment_group.eq("test")]
    raw=treatment.experiment_captured.sum()/treatment.experiment_projects.sum()-control.experiment_captured.sum()/control.experiment_projects.sum()
    if abs(raw - (active.loc[test.eq(1),"experiment_captured"].sum()/active.loc[test.eq(1),"experiment_projects"].sum()-active.loc[test.eq(0),"experiment_captured"].sum()/active.loc[test.eq(0),"experiment_projects"].sum()))>1e-12:
        raise AssertionError("Weighted response did not preserve raw D1 contrast")
    return dict(raw_diff=float(raw),adjusted_diff=b,ci95_low=lo,ci95_high=hi,
                pvalue=float(full.pvalues["test"]),hosts_total=len(paired),hosts_with_experiment=len(active),
                hosts_with_zero_experiment=int((~usable).sum()),hosts_without_baseline=int(paired.baseline_projects.eq(0).sum()),
                projects_experiment=int(active.experiment_projects.sum()),
                weighted_residual_sumsq=float(np.sum(w*np.square(y-full.predict(x)))),
                covariates=["log1p(baseline completed projects)"],
                model="Host-level WLS of experimental D1 project fraction, weighted by experiment projects; HC3 robust covariance")
