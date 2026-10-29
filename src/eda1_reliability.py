"""EDA 1: observable post-completion capture time and payment friction.

No evidence here verifies settlement, authorization operations, or a causal
payment-method subgroup effect. All timestamps use UTC and elapsed durations.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.experiment_impact import CS_START, CS_END, SEED
from src.foundation_ce import parse_utc

HORIZONS = (1, 7, 14, 30)
DOCUMENTED_LAST_DAY = pd.Timestamp("2025-12-19", tz="UTC")


def prepare_time_panel(project: pd.DataFrame) -> pd.DataFrame:
    """One experiment project per row, earliest observed capture, no exclusions.

    Incomplete D30 is *unknown extraction time* on final day. It cannot be
    assigned a defensible individual censoring instant, so complete-case
    diagnostic is used for that horizon instead of invented censor times.
    """
    q = project.loc[project.in_experiment].copy()
    if q.assignment_id.isna().any() or q.assignment_id.duplicated().any():
        raise ValueError("Project IDs must be unique and non-null")
    q["pre_completion"] = q.first_capture.notna() & q.first_capture.lt(q.completed_utc)
    delta = (q.first_capture - q.completed_utc).dt.total_seconds() / 3600.0
    q["signed_capture_hours"] = delta
    q["event_hours"] = delta.clip(lower=0)  # pre-completion captures at t=0
    q["has_capture_time"] = delta.notna()
    for h in HORIZONS:
        hh = 24*h
        q[f"covered_D{h}"] = q[f"coverage_D{h}"].eq("within_documented_horizon_conservative")
        q[f"event_D{h}"] = q.has_capture_time & q.event_hours.le(hh)
        q[f"restricted_uncaptured_hours_D{h}"] = q.event_hours.fillna(float(hh)).clip(upper=hh)
    assert q.pre_completion.sum() == (q.signed_capture_hours < 0).sum()
    assert q.event_hours.dropna().ge(0).all()
    assert q.event_D7.le(q.event_D14).all() and q.event_D14.le(q.event_D30).all()
    return q


def empirical_capture_curve(q: pd.DataFrame, times_hours: np.ndarray, cohort: str = "D30") -> pd.DataFrame:
    """Empirical cumulative incidence with conservative, common full-followup cohort."""
    times = np.asarray(times_hours, dtype=float)
    if np.any(times < 0) or np.any(np.diff(times) < 0) or np.any(times > 720):
        raise ValueError("Grid must be ordered in [0, 720] hours")
    eligible = q.loc[q[f"covered_{cohort}"]]
    rows=[]
    for group in ("control", "test"):
        g=eligible.loc[eligible.experiment_group.eq(group)]
        observed=np.sort(g.event_hours.dropna().to_numpy(dtype=float))
        rates=np.searchsorted(observed,times,side="right") / len(g)
        rows.extend({"group":group,"hours":float(x),"days":float(x)/24,
                     "captured_fraction":float(rate),"n_projects":len(g)} for x,rate in zip(times,rates))
    return pd.DataFrame(rows)


def aggregate_cluster_project_means(q: pd.DataFrame, hosts: pd.DataFrame,
                                    value_col: str, restrict_col: str | None = None) -> pd.DataFrame:
    """One row per registered host, with sum and project count in selected cohort."""
    x=q.loc[q[restrict_col]] if restrict_col else q
    totals=x.groupby("host_id").agg(total=(value_col,"sum"),denominator=(value_col,"size"))
    out=hosts[["host_id","experiment_group"]].join(totals,on="host_id")
    out[["total","denominator"]]=out[["total","denominator"]].fillna(0)
    assert out.host_id.is_unique and len(out)==len(hosts)
    assert out.denominator.sum()==len(x)
    return out


def cluster_ratio_ci(host_panel: pd.DataFrame, *, n_boot: int=2000, seed: int=SEED,
                     batch: int=64) -> dict:
    """Bootstrap difference of project-weighted means, resampling *whole hosts*.

    Host numerators and project denominators are sampled jointly. The ratio
    estimand differs from the unweighted average of host-specific rates.
    """
    if n_boot < 100 or batch < 1:raise ValueError("Insufficient bootstrap replicates")
    rng=np.random.default_rng(seed)
    estimates={};reps={};project_counts={};host_counts={}
    for group in ("control","test"):
        p=host_panel.loc[host_panel.experiment_group.eq(group)]
        mat=p[["total","denominator"]].to_numpy(dtype=float)
        if not len(p) or mat[:,1].sum()==0:raise ValueError("No projects in group")
        project_counts[group]=int(mat[:,1].sum());host_counts[group]=len(p)
        estimates[group]=float(mat[:,0].sum()/mat[:,1].sum())
        result=np.empty(n_boot)
        for j in range(0,n_boot,batch):
            k=min(batch,n_boot-j)
            ind=rng.integers(len(p),size=(k,len(p)))
            sums=mat[ind].sum(axis=1)
            result[j:j+k]=np.divide(sums[:,0],sums[:,1],out=np.full(k,np.nan),where=sums[:,1]!=0)
        reps[group]=result
    diff=reps["test"]-reps["control"]
    valid=np.isfinite(diff)
    if valid.sum() < n_boot//2:raise AssertionError("Too many bootstrap resamples with zero project denominators")
    return {"control":estimates["control"],"test":estimates["test"],
            "difference":estimates["test"]-estimates["control"],
            "ci_low":float(np.nanpercentile(diff,2.5)),"ci_high":float(np.nanpercentile(diff,97.5)),
            "valid_replicates":int(valid.sum()),
            "n_control":project_counts["control"],"n_test":project_counts["test"],
            "hosts_control":host_counts["control"],"hosts_test":host_counts["test"],
            "n_boot":n_boot,"seed":seed}


def metric_project_horizon(q: pd.DataFrame, hosts: pd.DataFrame, days: int, *,
                           criterion: str = "timestamp", subset: pd.Series | None = None,
                           restrict_to_D30: bool = False, n_boot: int=2000, seed: int=SEED) -> dict:
    """Project-level captured-by-horizon rate, host-cluster bootstrap."""
    if days not in HORIZONS and days != 1:raise ValueError("Unknown horizon")
    eligible = q[f"covered_D{days}"].copy()
    if restrict_to_D30:eligible &= q["covered_D30"]
    if subset is not None:eligible &= subset.reindex(q.index,fill_value=False)
    if criterion == "timestamp": value=f"event_D{days}"
    elif criterion == "concordant": value=f"concordant_D{days}"
    else:raise ValueError("Unsupported timed capture evidence")
    base=aggregate_cluster_project_means(q.loc[eligible],hosts,value)
    result=cluster_ratio_ci(base,n_boot=n_boot,seed=seed)
    result.update({"horizon":f"D{days}","criterion":criterion,
                   "excluded_projects":len(q)-int(eligible.sum())})
    return result


def rmst_horizon(q: pd.DataFrame,hosts:pd.DataFrame,days:int, *,common_D30: bool=False,
                 n_boot:int=2000,seed:int=SEED) -> dict:
    if days not in (7,14,30):raise ValueError("RMST horizon must be D7, D14 or D30")
    eligible=q[f"covered_D{days}"] & (q.covered_D30 if common_D30 else True)
    col=f"restricted_uncaptured_hours_D{days}"
    panel=aggregate_cluster_project_means(q.loc[eligible],hosts,col)
    result=cluster_ratio_ci(panel,n_boot=n_boot,seed=seed)
    result.update({"measure":f"RMST D{days}" + (" (D30 cohort)" if common_D30 else ""),
                   "hours":days*24,"excluded_projects":len(q)-int(eligible.sum())})
    return result


def label_incident_overlap(q:pd.DataFrame, days:int=1)->pd.Series:
    """Completion D1 window [completed, completed+24h] overlaps CS interval."""
    return q.completed_utc.lt(CS_END) & (q.completed_utc + pd.Timedelta(days=days)).gt(CS_START)


def build_discordance_flags(logs:pd.DataFrame, project:pd.DataFrame)->pd.DataFrame:
    """Status/capture disagreement per attempt; same vs distinct timestamp is descriptive."""
    l=logs[["assignment_id","payment_method","payment_status","captured_at","created_at"]].copy()
    l["capture_utc"]=parse_utc(l.captured_at)
    l["creation_utc"]=parse_utc(l.created_at)
    l["succeeded"]=l.payment_status.eq("succeeded")
    l["discordant"]=l.succeeded.ne(l.capture_utc.notna())
    l["concordant"]=l.succeeded & l.capture_utc.notna()
    g=l.groupby("assignment_id",sort=False).agg(any_discordance=("discordant","any"),
         discordant_attempts=("discordant","sum"),any_concordance=("concordant","any"))
    # Equal captures, distinct captures, and no concordant capture can coexist across attempts.
    a=l.loc[l.discordant & l.capture_utc.notna(),["assignment_id","capture_utc"]]
    b=l.loc[l.concordant,["assignment_id","capture_utc"]]
    both=a.merge(b,on="assignment_id",suffixes=("_discordant","_concordant"),how="left")
    equal=(both.capture_utc_discordant.eq(both.capture_utc_concordant) & both.capture_utc_concordant.notna())
    uneq=(both.capture_utc_concordant.notna() & ~equal)
    eqids=set(both.loc[equal,"assignment_id"])
    diffids=set(both.loc[uneq,"assignment_id"])
    g["discordant_capture_same_time_as_concordant"]=g.index.isin(eqids)
    g["discordant_capture_distinct_time_from_concordant"]=g.index.isin(diffids)
    p=project[["assignment_id","experiment_group","completed_utc","in_experiment"]].merge(g,on="assignment_id",how="left",validate="one_to_one")
    for k in ("any_discordance","any_concordance","discordant_capture_same_time_as_concordant","discordant_capture_distinct_time_from_concordant"):
        p[k]=p[k].astype("boolean").fillna(False).astype(bool)
    p["discordant_attempts"]=p.discordant_attempts.fillna(0).astype(int)
    assert p.discordant_attempts.sum()==l.discordant.sum()
    return p


def friction_tables(logs:pd.DataFrame, project:pd.DataFrame)->tuple[pd.DataFrame,pd.DataFrame,pd.DataFrame]:
    """Attempt, project-method and overall project friction, no method exclusivity."""
    p=project[["assignment_id","experiment_group","baseline","in_experiment"]]
    l=logs.merge(p,on="assignment_id",how="left",validate="many_to_one")
    if l.experiment_group.isna().any() or len(l)!=len(logs):raise ValueError("Attempt join failed")
    l=l.loc[l.baseline|l.in_experiment].copy()
    l["period"]=np.where(l.in_experiment,"experiment","baseline")
    l["capture_flag"]=l.captured_at.notna()
    for k in ("succeeded","failed","declined","voided"):
        l[k]=l.payment_status.eq(k)
    l["failed_or_declined"]=l.failed|l.declined
    fields=["succeeded","failed","declined","voided","failed_or_declined","capture_flag"]
    attempts=l.groupby(["period","experiment_group","payment_method"],observed=True).agg(total_attempts=("payment_status","size"),**{k:(k,"sum") for k in fields}).reset_index()
    for k in fields:attempts[k+"_pct"]=100*attempts[k]/attempts.total_attempts
    proj_method=l.groupby(["period","experiment_group","payment_method","assignment_id"],sort=False,observed=True).agg(attempts=("payment_status","size"),**{k:(k,"any") for k in fields}).reset_index()
    per_method=proj_method.groupby(["period","experiment_group","payment_method"],observed=True).agg(projects_with_method=("assignment_id","size"),projects_multi_attempts=("attempts",lambda s:int((s>1).sum())),**{f"projects_{k}":(k,"sum") for k in fields}).reset_index()
    experiment=project.loc[project.in_experiment,["assignment_id","experiment_group"]]
    all_counts=l.loc[l.in_experiment].groupby("assignment_id",sort=False).agg(any_failed_or_declined=("failed_or_declined","any"),n_methods=("payment_method","nunique"),n_attempts=("payment_status","size"))
    exp=experiment.join(all_counts,on="assignment_id")
    exp["any_failed_or_declined"]=exp.any_failed_or_declined.astype("boolean").fillna(False).astype(bool)
    exp["n_methods"]=exp.n_methods.fillna(0).astype(int)
    exp["n_attempts"]=exp.n_attempts.fillna(0).astype(int)
    summary=exp.groupby("experiment_group").agg(completed_projects=("assignment_id","size"),with_failed_or_declined=("any_failed_or_declined","sum"),multiple_methods=("n_methods",lambda s:int((s>1).sum())),multiple_attempts=("n_attempts",lambda s:int((s>1).sum()))).reset_index()
    for k in ("with_failed_or_declined","multiple_methods","multiple_attempts"):
        summary[k+"_percent"]=100*summary[k]/summary.completed_projects
    return attempts,per_method,summary


def card_alternative_journeys(logs:pd.DataFrame, project:pd.DataFrame)->tuple[pd.DataFrame,pd.DataFrame]:
    """Card failure + alternative-method records; chronology refers only to log creation."""
    q=project.loc[project.in_experiment,["assignment_id","experiment_group"]]
    l=logs.merge(q,on="assignment_id",how="inner",validate="many_to_one")
    l["log_time"]=parse_utc(l.created_at)
    l["capture"]=l.captured_at.notna()
    cardfail=l.loc[l.payment_method.eq("card") & l.payment_status.isin(["failed","declined"])]
    cardmin=cardfail.groupby("assignment_id").log_time.min().rename("card_fail_log_created")
    out=[]
    for method in ("bank_account","credits"):
        alt=l.loc[l.payment_method.eq(method)]
        altproj=alt.groupby("assignment_id").agg(alt_present=("payment_method","size"),
           alt_success=("payment_status",lambda s:int(s.eq("succeeded").any())),
           alt_capture=("capture",lambda s:int(s.any())),
           alt_first_created=("log_time","min"))
        pair=cardmin.to_frame().join(altproj,how="inner").reset_index()
        pair=pair.merge(q,on="assignment_id",how="left",validate="one_to_one")
        pair["alternative_method"]=method
        pair["later_alt_record"]=(pair.alt_first_created>pair.card_fail_log_created)
        pair["tied_alt_record"]=(pair.alt_first_created==pair.card_fail_log_created)
        pair["earlier_alt_record"]=(pair.alt_first_created<pair.card_fail_log_created)
        out.append(pair)
    details=pd.concat(out,ignore_index=True)
    summary=details.groupby(["experiment_group","alternative_method"],observed=True).agg(
       projects_card_fail_and_alt=("assignment_id","size"),
       projects_alt_succeeded=("alt_success","sum"),
       projects_alt_captured=("alt_capture","sum"),
       alt_created_after_first_card_fail=("later_alt_record","sum"),
       ties=("tied_alt_record","sum"),
       alt_created_before_first_card_fail=("earlier_alt_record","sum")).reset_index()
    return details,summary
