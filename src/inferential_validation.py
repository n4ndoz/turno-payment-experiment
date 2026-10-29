"""Decision-focused inferential checks on registered-host experiment comparisons.

Original assignment/exposure mechanism is not fully observed: permutation below
assumes exchangeable recorded labels, NOT the original randomization mechanism.
Observed capture is not proof of full settlement. All resampling units are hosts.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm

from src.experiment_impact import SEED

METRIC_COLS = {"M1": "completed", "M2": "first_ever", "M4": "captured_D14"}


def paired_period_host_panel(hosts: pd.DataFrame, project: pd.DataFrame) -> pd.DataFrame:
    """One row per *registered* host, including zero projects in either period.

    Baseline and experiment D1 numerators and denominators stay together in
    every host bootstrap draw; a host can have zero in either period.
    """
    if not hosts.host_id.is_unique or hosts.host_id.isna().any():
        raise ValueError("Invalid registered-host key")
    if not project.assignment_id.is_unique:
        raise ValueError("Repeated completed project")
    if not set(project.host_id).issubset(set(hosts.host_id)):
        raise ValueError("Unregistered project host")
    if (project.baseline & project.in_experiment).any():
        raise ValueError("Overlapping time windows")
    if not project.loc[project.baseline | project.in_experiment, "coverage_D1"].eq("within_documented_horizon_conservative").all():
        raise ValueError("D1 horizon insufficiently documented")
    result = hosts[["host_id", "experiment_group"]].copy()
    for period, mask in (("baseline", project.baseline), ("experiment", project.in_experiment)):
        q = project.loc[mask]
        g = q.groupby("host_id").agg(projects=("assignment_id", "size"), captured_D1=("capture_D1", "sum"))
        for val, src in (("projects", "projects"), ("captured", "captured_D1")):
            result[f"{period}_{val}"] = result.host_id.map(g[src]).fillna(0).astype(np.int64)
        assert result[f"{period}_projects"].sum() == len(q)
        assert result[f"{period}_captured"].sum() == q.capture_D1.sum()
        assert (result[f"{period}_captured"] <= result[f"{period}_projects"]).all()
    assert len(result) == len(hosts) and result.host_id.is_unique
    return result


def paired_d1_bootstrap(paired: pd.DataFrame, *, n_boot: int = 2000, seed: int = SEED, batch: int = 64) -> tuple[pd.DataFrame, dict]:
    """Host-stratified percentile 95% CIs for baseline, experiment and contrast change.

    Rates are project-weighted ratios of sums; host resampling preserves both
    periods jointly. Difference-in-contrasts is descriptive, NOT causal DiD.
    """
    if n_boot < 100 or batch < 1:
        raise ValueError("Insufficient replicates")
    rng = np.random.default_rng(seed)
    arrays = {}
    points = {}
    counts = {}
    cols = ["baseline_captured", "baseline_projects", "experiment_captured", "experiment_projects"]
    for group in ("control", "test"):
        p = paired.loc[paired.experiment_group.eq(group)]
        values = p[cols].to_numpy(dtype=np.float64)
        if not len(p) or np.any(values.sum(axis=0)[[1,3]] == 0):
            raise ValueError("Missing group/period contribution")
        counts[group] = {"hosts":len(p),"baseline_projects":int(values[:,1].sum()),"experiment_projects":int(values[:,3].sum()),
                         "baseline_captured":int(values[:,0].sum()),"experiment_captured":int(values[:,2].sum()),
                         "hosts_with_baseline":int((values[:,1]>0).sum()),"hosts_with_experiment":int((values[:,3]>0).sum())}
        total = values.sum(axis=0)
        points[group] = np.array([total[0]/total[1], total[2]/total[3]])
        draws = np.full((n_boot,2),np.nan)
        for start in range(0,n_boot,batch):
            k = min(batch,n_boot-start)
            inds = rng.integers(0,len(p),size=(k,len(p)))
            sums = values[inds].sum(axis=1)
            draws[start:start+k,0] = np.divide(sums[:,0],sums[:,1],out=np.full(k,np.nan),where=sums[:,1]>0)
            draws[start:start+k,1] = np.divide(sums[:,2],sums[:,3],out=np.full(k,np.nan),where=sums[:,3]>0)
        arrays[group] = draws
    diffs = arrays["test"]-arrays["control"]
    estimates = points["test"]-points["control"]
    change = diffs[:,1]-diffs[:,0]
    ci = lambda x: (float(np.nanpercentile(x,2.5)),float(np.nanpercentile(x,97.5)))
    rows = []
    for i,period in enumerate(("baseline","experiment")):
        lo,hi = ci(diffs[:,i]);rows.append({"contrast":f"D1 {period}","control":points["control"][i],"test":points["test"][i],
                                  "difference":estimates[i],"ci_low":lo,"ci_high":hi,"valid_replicates":int(np.isfinite(diffs[:,i]).sum())})
    lo,hi=ci(change)
    rows.append({"contrast":"D1 change in contrasts (exploratory)","control":np.nan,"test":np.nan,
                 "difference":estimates[1]-estimates[0],"ci_low":lo,"ci_high":hi,"valid_replicates":int(np.isfinite(change).sum())})
    if min(x["valid_replicates"] for x in rows)<n_boot//2:
        raise ValueError("Too many zero-period bootstrap denominator draws")
    return pd.DataFrame(rows),counts


def hc3_adjusted_host_metrics(panel: pd.DataFrame) -> pd.DataFrame:
    """Host-level ANCOVA with only pre-period completed-project count as covariate.

    M2 uses the same pre-treatment baseline activity covariate as M1/M4. HC3
    measures conditional linear contrast; no causal identification is implied.
    """
    if not panel.host_id.is_unique:
        raise ValueError("Duplicate host")
    x=sm.add_constant(panel[["test","baseline_completions"]].astype(float),has_constant="add")
    rows=[]
    for metric,field in METRIC_COLS.items():
        fit=sm.OLS(panel[field].astype(float),x).fit(cov_type="HC3")
        lo,hi=fit.conf_int(alpha=.05).loc["test"]
        a=panel.loc[panel.test.eq(1),field].mean()-panel.loc[panel.test.eq(0),field].mean()
        rows.append({"metric":metric,"raw_difference":float(a),"adjusted_difference":float(fit.params["test"]),
                    "adjusted_ci_low":float(lo),"adjusted_ci_high":float(hi),"adjusted_p":float(fit.pvalues["test"]),
                    "baseline_slope":float(fit.params["baseline_completions"])})
    return pd.DataFrame(rows)


def _outcome_contrasts(values: np.ndarray, n_test: int) -> np.ndarray:
    """M1/M2/M4 host means and D1 project-weighted rate difference.

    First n_test rows are treated as Test, remainder Control; inputs have
    columns completed, first, captured14, D1 captured projects, D1 projects.
    """
    v = np.asarray(values,dtype=np.float64)
    if v.ndim!=2 or v.shape[1]!=5 or not 0<n_test<len(v):
        raise ValueError("Expected (host, 5) and nonempty group split")
    t=v[:n_test].sum(axis=0); c=v[n_test:].sum(axis=0)
    if t[4]==0 or c[4]==0:
        raise ValueError("Zero project denominator")
    return np.r_[(t[:3]/n_test-c[:3]/(len(v)-n_test)),t[3]/t[4]-c[3]/c[4]]


def host_label_permutation(panel: pd.DataFrame, paired: pd.DataFrame, *, n_perm: int=4000, seed: int=SEED) -> tuple[pd.DataFrame, np.ndarray]:
    """Two-sided approximate random-label permutation p-values among registered hosts.

    Assumes exchangeability of observed group labels and uniform assignment
    conditional on group sizes; not a reconstruction of stratified assignment.
    Project-wise permuting would be invalid; D1 ratios are re-aggregated within
    whole hosts each permutation. Add-one Monte Carlo correction.
    """
    if n_perm<100:
        raise ValueError("Too few permutations")
    if not panel.host_id.is_unique or not paired.host_id.is_unique:
        raise ValueError("Invalid host panel key")
    p=panel[["host_id","experiment_group","completed","first_ever","captured_D14"]].merge(
        paired[["host_id","experiment_group","experiment_captured","experiment_projects"]],
        on="host_id",validate="one_to_one",suffixes=("","_paired"))
    if not p.experiment_group.eq(p.experiment_group_paired).all():
        raise ValueError("Incompatible group labels")
    p=p.sort_values("experiment_group",ascending=False,kind="stable") # test first, then control
    if not p.experiment_group.isin(["control","test"]).all():
        raise ValueError("Unknown group")
    n_test=int(p.experiment_group.eq("test").sum())
    mat=p[["completed","first_ever","captured_D14","experiment_captured","experiment_projects"]].to_numpy(dtype=np.float64)
    observed=_outcome_contrasts(mat,n_test)
    rng=np.random.default_rng(seed)
    exceed=np.zeros(4,dtype=np.int64)
    for _ in range(n_perm):
        perm=mat[rng.permutation(len(mat))]
        value=_outcome_contrasts(perm,n_test)
        exceed+=(np.abs(value)>=np.abs(observed)-1e-12)
    pvals=(exceed+1)/(n_perm+1)
    result=pd.DataFrame({"metric":["M1","M2","M4","D1"],"observed_difference":observed,
        "perm_extreme":exceed,"p_permutation_two_sided":pvals,"n_permutations":n_perm,"seed":seed})
    return result,mat


def holm_adjust(p_values: np.ndarray) -> np.ndarray:
    """Holm step-down familywise adjusted p-values, retaining input order."""
    p=np.asarray(p_values,dtype=float)
    if p.ndim!=1 or len(p)<1 or not np.isfinite(p).all() or ((p<0)|(p>1)).any():
        raise ValueError("p-values must be finite and in [0,1]")
    order=np.argsort(p,kind="stable")
    sorted_adjust=np.maximum.accumulate((len(p)-np.arange(len(p)))*p[order])
    result=np.empty(len(p))
    result[order]=np.minimum(sorted_adjust,1.)
    return result


def influence_by_host(panel: pd.DataFrame, *, quantile: float=.99) -> tuple[pd.DataFrame,pd.DataFrame]:
    """Post-treatment diagnostic only: pooled 99th percentile cap and top 1% share.

    Cap based on combined host activity, applied identically to both groups.
    It changes the outcome; it is NOT a valid alternative causal estimand.
    """
    if not 0<quantile<1 or not panel.host_id.is_unique:
        raise ValueError("Invalid quantile or host identities")
    cutoff=float(panel.completed.quantile(quantile))
    rows=[]
    for g in ("control","test"):
        q=panel.loc[panel.experiment_group.eq(g),"completed"].to_numpy(dtype=float)
        if not len(q):raise ValueError("Empty group")
        top_n=max(1,int(np.ceil((1-quantile)*len(q))))
        top=int(np.partition(q,len(q)-top_n)[-top_n:].sum())
        rows.append({"group":g,"hosts":len(q),"projects":int(q.sum()),"mean":float(q.mean()),
                     "median":float(np.median(q)),"p75":float(np.quantile(q,.75)),"p90":float(np.quantile(q,.90)),
                     "p95":float(np.quantile(q,.95)),"p99":float(np.quantile(q,.99)),"max":int(q.max()),
                     "top_1pct_n":top_n,"top_1pct_share":float(top/q.sum()),
                     "pooled_p99_cap":cutoff,"capped_mean":float(np.minimum(q,cutoff).mean()),
                     "share_hosts_zero":float(np.mean(q==0))})
    summary=pd.DataFrame(rows)
    raw=summary.set_index("group").loc["test","mean"]-summary.set_index("group").loc["control","mean"]
    capped=summary.set_index("group").loc["test","capped_mean"]-summary.set_index("group").loc["control","capped_mean"]
    sensitivity=pd.DataFrame([{"diagnostic":"Full sample mean difference","test_minus_control":raw,"pooled_cap":np.nan},
        {"diagnostic":"Same pooled-p99 capped project count (post-treatment diagnostic)","test_minus_control":capped,"pooled_cap":cutoff}])
    return summary,sensitivity
