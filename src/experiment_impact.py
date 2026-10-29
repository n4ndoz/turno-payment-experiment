"""Sprint 1 registered-host experimental comparisons (not proven randomization ITT).

Inputs remain unchanged. Capture timestamps are *observed evidence*, never a
verification of settlement or the total amount owed. Jupyter notebook is the
primary presentation; these helpers only encode shared, testable operations.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm

from src.foundation_ce import parse_utc, utc_timestamp, potential_window_coverage

BASELINE_START = utc_timestamp("2025-07-18")
EXPERIMENT_START = utc_timestamp("2025-08-18")
EXPERIMENT_END = utc_timestamp("2025-11-20")
CS_START = utc_timestamp("2025-09-17")
CS_END = utc_timestamp("2025-10-01")
FOLLOWUP_DAY = "2025-12-19"
SEED = 20261029
METRICS = ("M1_completed_per_host", "M2_first_ever_per_host", "M3_hosts_2plus", "M4_captured_D14_per_host", "M5_not_captured_D14_per_host", "M6_capture_D14_project_rate")


def build_project_panel(hosts: pd.DataFrame, assignments: pd.DataFrame, logs: pd.DataFrame) -> pd.DataFrame:
    """One row per completed project, strict source keys and log-host match."""
    for d, col in ((hosts, "host_id"), (assignments, "assignment_id"), (logs, "payment_log_id")):
        if d[col].isna().any() or d[col].duplicated().any():
            raise ValueError(f"Null or duplicate key: {col}")
    if not set(assignments.host_id).issubset(set(hosts.host_id)):
        raise ValueError("Project hosts absent from exposure register")
    if not set(logs.assignment_id).issubset(set(assignments.assignment_id)):
        raise ValueError("Orphan attempt")
    project_host = assignments.set_index("assignment_id")["host_id"]
    if not logs.host_id.eq(logs.assignment_id.map(project_host)).all():
        raise ValueError("Payment attempt host differs from project host")

    l = logs[["assignment_id", "payment_status", "captured_at"]].copy()
    l["capture_time"] = parse_utc(l["captured_at"])
    if (l["captured_at"].notna() & l["capture_time"].isna()).any():
        raise ValueError("Unparseable non-null captured_at")
    l["success"] = l.payment_status.eq("succeeded")
    l["concordant"] = l.success & l.capture_time.notna()
    grouped = l.groupby("assignment_id", sort=False).agg(
        log_rows=("payment_status", "size"),
        has_success=("success", "any"),
        has_concordant=("concordant", "any"),
        first_capture=("capture_time", "min"),
    )
    a = assignments[["assignment_id", "host_id", "created_at", "completed_at", "is_first_completed_project"]].copy()
    a["completed_utc"] = parse_utc(a.completed_at)
    a["created_utc"] = parse_utc(a.created_at)
    if a["completed_utc"].isna().any() or a["created_utc"].isna().any():
        raise ValueError("Missing/invalid project timestamps")
    a = a.merge(hosts[["host_id", "experiment_group", "first_exposed_at"]],on="host_id",how="left",validate="many_to_one")
    a["exposed_utc"] = parse_utc(a.first_exposed_at)
    if a.experiment_group.isna().any() or a.exposed_utc.isna().any():
        raise ValueError("Unassigned or invalid exposure")
    a = a.merge(grouped,on="assignment_id",how="left",validate="one_to_one")
    if len(a)!=len(assignments) or a.assignment_id.duplicated().any():
        raise AssertionError("Project rows multiplied")
    a["log_rows"] = a.log_rows.fillna(0).astype(int)
    for col in ("has_success", "has_concordant"):
        a[col] = a[col].fillna(False).astype(bool)
    a["has_capture"] = a.first_capture.notna()
    a["is_first_true"] = a.is_first_completed_project.eq("true")
    a["baseline"] = a.completed_utc.ge(BASELINE_START) & a.completed_utc.lt(EXPERIMENT_START)
    a["in_experiment"] = a.completed_utc.ge(EXPERIMENT_START) & a.completed_utc.lt(EXPERIMENT_END)
    a["completed_pre_exposure"] = a.completed_utc.lt(a.exposed_utc)
    a["created_pre_exposure"] = a.created_utc.lt(a.exposed_utc)
    a["incident_completed"] = a.completed_utc.ge(CS_START) & a.completed_utc.lt(CS_END)
    a["captured_before_completion"] = a.has_capture & a.first_capture.lt(a.completed_utc)
    for d in (1,7,14,30):
        a[f"coverage_D{d}"] = potential_window_coverage(a.completed_utc, d, FOLLOWUP_DAY)
        a[f"capture_D{d}"] = a.has_capture & a.first_capture.le(a.completed_utc+pd.Timedelta(days=d))
    assert a.log_rows.sum()==len(logs)
    return a


def build_host_panel(hosts: pd.DataFrame, project: pd.DataFrame, *, omit_incident: bool=False, restrict_after_exposure: bool=False) -> pd.DataFrame:
    """Preserve every registered host; absent projects map to zero, never NA."""
    if hosts.host_id.duplicated().any() or hosts.host_id.isna().any():
        raise ValueError("Invalid host register keys")
    q=project.loc[project.in_experiment]
    if omit_incident:
        q=q.loc[~q.incident_completed]
    if restrict_after_exposure:
        q=q.loc[~q.completed_pre_exposure]
    if not q.coverage_D14.eq("within_documented_horizon_conservative").all():
        raise ValueError("D14 projects with unproven documented coverage; stratify explicitly")
    summary=q.groupby("host_id",sort=False).agg(
        completed=("assignment_id","size"),
        first_ever=("is_first_true","sum"),
        captured_D14=("capture_D14","sum"),
    )
    result=hosts[["host_id","experiment_group","first_exposed_at"]].copy()
    result=result.join(summary,on="host_id")
    for col in ("completed","first_ever","captured_D14"):
        result[col]=result[col].fillna(0).astype("int64")
    result["not_captured_D14"]=result.completed-result.captured_D14
    result["two_plus"]=result.completed.ge(2).astype(int)
    baseline=project.loc[project.baseline].groupby("host_id").size()
    result["baseline_completions"]=result.host_id.map(baseline).fillna(0).astype("int64")
    result["test"]=result.experiment_group.eq("test").astype(int)
    if not result.experiment_group.isin(["control","test"]).all():
        raise ValueError("Unexpected experimental group")
    if len(result)!=len(hosts) or result.host_id.duplicated().any():
        raise AssertionError("Host rows changed")
    if result.completed.sum()!=len(q) or result.captured_D14.sum()!=int(q.capture_D14.sum()):
        raise AssertionError("Project-to-host totals mismatch")
    if not result.completed.eq(result.captured_D14+result.not_captured_D14).all():
        raise AssertionError("M1 != M4 + M5 at host grain")
    return result


def _metric_arrays(panel: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    vals=panel[["completed","first_ever","two_plus","captured_D14","not_captured_D14"]].to_numpy(dtype=float)
    denom=panel["completed"].to_numpy(dtype=float)
    return vals,denom


def point_estimates(panel: pd.DataFrame) -> pd.DataFrame:
    """Six group estimates; M6 is a project-weighted ratio, not host mean."""
    results=[]
    for grp in ("control","test"):
        df=panel.loc[panel.experiment_group.eq(grp)]
        if len(df)==0:raise ValueError("Empty experimental group")
        values,_=_metric_arrays(df)
        y=list(values.mean(axis=0))
        y.append(float(df.captured_D14.sum()/df.completed.sum()) if df.completed.sum() else np.nan)
        for name,v in zip(METRICS,y):results.append({"group":grp,"metric":name,"estimate":v,"hosts":len(df),"projects":int(df.completed.sum())})
    return pd.DataFrame(results)


def bootstrap_host_differences(panel: pd.DataFrame, n_boot: int=2000, seed: int=SEED, batch: int=64) -> pd.DataFrame:
    """Percentile CIs; stratify by group and resample whole hosts, jointly M6 num/den."""
    if n_boot < 100 or batch < 1:raise ValueError("Bootstrap replicates/batch too small")
    rng=np.random.default_rng(seed)
    rep={}
    for grp in ("control","test"):
        df=panel.loc[panel.experiment_group.eq(grp)]
        if len(df)==0:raise ValueError("Empty group")
        vals,den=_metric_arrays(df)
        all_draws=np.empty((n_boot,6),dtype=float)
        for pos in range(0,n_boot,batch):
            n=min(batch,n_boot-pos)
            idx=rng.integers(len(df),size=(n,len(df)))
            sums=vals[idx].sum(axis=1)
            all_draws[pos:pos+n,:5]=sums/len(df)
            denominators=den[idx].sum(axis=1)
            all_draws[pos:pos+n,5]=np.divide(sums[:,3],denominators,out=np.full(n,np.nan),where=denominators>0)
        rep[grp]=all_draws
    difference=rep["test"]-rep["control"]
    if not np.isfinite(difference[:,:5]).all():raise AssertionError("Invalid host-level bootstrap replicate")
    # Rare in small synthetic samples: a host resample may have zero projects.
    # Do not invent a project-rate value for it; use valid joint-ratio draws.
    if np.isfinite(difference[:,5]).sum() < n_boot//2:
        raise AssertionError("Too few valid project-ratio bootstrap replicates")
    points=point_estimates(panel).pivot(index="metric",columns="group",values="estimate")
    rows=[]
    for i,name in enumerate(METRICS):
        c,t=points.loc[name,"control"],points.loc[name,"test"]
        rows.append({"metric":name,"control":c,"test":t,"difference":t-c,
                     "relative_percent":100*(t-c)/c if c else np.nan,
                     "ci95_low":float(np.nanpercentile(difference[:,i],2.5)),
                     "ci95_high":float(np.nanpercentile(difference[:,i],97.5)),
                     "bootstrap_replicates":n_boot,"valid_bootstrap_replicates":int(np.isfinite(difference[:,i]).sum())})
    return pd.DataFrame(rows)


def baseline_hc3(panel: pd.DataFrame, outcomes: tuple[str,...] =("completed", "captured_D14", "not_captured_D14")) -> pd.DataFrame:
    """Secondary host-level ANCOVA-style OLS, treatment + preperiod completions."""
    x=sm.add_constant(panel[["test","baseline_completions"]].astype(float),has_constant="add")
    rows=[]
    for y in outcomes:
        model=sm.OLS(panel[y].astype(float),x).fit(cov_type="HC3")
        lo,hi=model.conf_int(alpha=.05).loc["test"]
        rows.append({"outcome":y,"adjusted_test_minus_control":float(model.params["test"]),
                     "ci95_low":float(lo),"ci95_high":float(hi),"se_hc3":float(model.bse["test"]),
                     "n_hosts":len(panel),"baseline_coefficient":float(model.params["baseline_completions"])})
    return pd.DataFrame(rows)


def capture_horizon_table(project: pd.DataFrame, *, horizons=(1,7,14,30)) -> pd.DataFrame:
    """Cohort-specific ratios; D30 excludes last-day-uncertain coverage."""
    q=project.loc[project.in_experiment]
    rows=[]
    for d in horizons:
        coverage=q[f"coverage_D{d}"].eq("within_documented_horizon_conservative")
        for group in ("control","test"):
            g=q.loc[q.experiment_group.eq(group)]
            eligible=g.loc[coverage.reindex(g.index)]
            n=len(eligible)
            hits=int(eligible[f"capture_D{d}"].sum())
            rows.append({"horizon":f"D{d}","group":group,"eligible_projects":n,
                         "uncertain_or_beyond":len(g)-n,"captured":hits,"not_observed":n-hits,
                         "rate":hits/n if n else np.nan,
                         "captured_pre_completion":int((eligible[f"capture_D{d}"] & eligible.captured_before_completion).sum())})
    return pd.DataFrame(rows)


def bootstrap_capture_horizons(hosts: pd.DataFrame, project: pd.DataFrame, *, n_boot=2000, seed=SEED, batch=64) -> pd.DataFrame:
    """Joint host bootstrap of project-grain D1/D7/D14/D30 rates; distinct denominators."""
    q=project.loc[project.in_experiment]
    base=hosts[["host_id","experiment_group"]].copy()
    for d in (1,7,14,30):
        g=q.loc[q[f"coverage_D{d}"].eq("within_documented_horizon_conservative")]
        val=g.assign(c=g[f"capture_D{d}"].astype(int)).groupby("host_id").agg(**{f"num{d}":("c","sum"),f"den{d}":("c","size")})
        base=base.join(val,on="host_id")
        for col in (f"num{d}",f"den{d}"):base[col]=base[col].fillna(0).astype(int)
    rng=np.random.default_rng(seed)
    reps={}
    for group in ("control","test"):
        g=base.loc[base.experiment_group.eq(group)]
        mat=g[[f"num{d}" for d in (1,7,14,30)]+[f"den{d}" for d in (1,7,14,30)]].to_numpy(dtype=int)
        n=len(g); out=np.empty((n_boot,4))
        for start in range(0,n_boot,batch):
            count=min(batch,n_boot-start)
            ind=rng.integers(n,size=(count,n))
            sums=mat[ind].sum(axis=1)
            out[start:start+count]=np.divide(sums[:,:4],sums[:,4:],out=np.full((count,4),np.nan),where=sums[:,4:]>0)
        reps[group]=out
    diff=reps["test"]-reps["control"]
    if not np.all(np.isfinite(diff).sum(axis=0)>=n_boot//2):
        raise AssertionError("Too few valid horizon resampling denominators")
    rows=[]
    for i,d in enumerate((1,7,14,30)):
        cg=base.loc[base.experiment_group.eq("control")]
        tg=base.loc[base.experiment_group.eq("test")]
        c=cg[f"num{d}"].sum()/cg[f"den{d}"].sum();t=tg[f"num{d}"].sum()/tg[f"den{d}"].sum()
        rows.append({"horizon":f"D{d}","control":c,"test":t,"difference":t-c,
                     "ci95_low":np.nanpercentile(diff[:,i],2.5),"ci95_high":np.nanpercentile(diff[:,i],97.5),
                     "valid_bootstrap_replicates":int(np.isfinite(diff[:,i]).sum())})
    return pd.DataFrame(rows)
