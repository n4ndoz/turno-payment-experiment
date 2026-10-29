"""Synthetic, source-independent tests for experimental estimands and edge cases."""
import numpy as np
import pandas as pd
import pytest

from src.experiment_impact import (
    BASELINE_START, EXPERIMENT_START, EXPERIMENT_END, CS_START, CS_END,
    build_project_panel, build_host_panel, point_estimates, bootstrap_host_differences,
    baseline_hc3, capture_horizon_table, bootstrap_capture_horizons,
)


def fixture_data():
    h=pd.DataFrame({"host_id":["h1","h2","h3","h4"],"experiment_group":["control","control","test","test"],
                    "first_exposed_at":["2025-08-19 00:00:00"]*4},dtype="string")
    a=pd.DataFrame({"assignment_id":["a1","a2","a3","a4","a5","a6","a7"],
        "host_id":["h1","h1","h2","h3","h3","h3","h1"],
        "created_at":["2025-07-19 00:00:00","2025-08-20 00:00:00","2025-09-19 00:00:00","2025-08-15 00:00:00","2025-11-19 00:00:00","2025-08-21 00:00:00","2025-07-19 00:00:00"],
        "completed_at":["2025-08-20 00:00:00","2025-08-21 00:00:00","2025-09-20 00:00:00","2025-08-18 20:00:00","2025-11-19 23:00:00","2025-08-22 00:00:00","2025-07-20 00:00:00"],
        "is_first_completed_project":["true","false","false","true","false","false","false"]},dtype="string")
    l=pd.DataFrame({"payment_log_id":["l1","l2","l3","l4","l5","l6"],
       "assignment_id":["a1","a1","a2","a3","a5","a6"],
       "host_id":["h1","h1","h1","h2","h3","h3"],
       "payment_status":["failed","succeeded","succeeded","failed","voided","succeeded"],
       "captured_at":[pd.NA,"2025-08-20 00:00:00",pd.NA,"2025-10-10 00:00:00","2025-11-20 00:00:00","2025-08-21 23:00:00"]},dtype="string")
    return h,a,l


def test_zero_host_and_full_host_identity():
    h,a,l=fixture_data();p=build_project_panel(h,a,l);x=build_host_panel(h,p)
    assert len(p)==7 and p.assignment_id.is_unique and len(x)==4
    assert x.loc[x.host_id.eq("h4"),"completed"].item()==0
    assert x.completed.sum()==6 and x.captured_D14.sum()==3
    assert (x.completed == x.captured_D14+x.not_captured_D14).all()
    assert x.loc[x.host_id.eq("h1"),"baseline_completions"].item()==1


def test_capture_precompletion_and_status_disagreement():
    h,a,l=fixture_data();p=build_project_panel(h,a,l).set_index("assignment_id")
    assert p.loc["a1","captured_before_completion"] is False or not bool(p.loc["a1","captured_before_completion"])
    assert bool(p.loc["a6","captured_before_completion"])
    assert bool(p.loc["a3","has_capture"]) and not bool(p.loc["a3","has_success"])
    assert bool(p.loc["a2","has_success"]) and not bool(p.loc["a2","has_capture"])
    assert bool(p.loc["a1","capture_D14"])  # exact completion-boundary capture
    assert not bool(p.loc["a2","capture_D14"])  # success without timestamp is not timed capture
    assert not bool(p.loc["a3","capture_D14"])  # capture outside D14
    assert bool(p.loc["a5","capture_D14"])  # after completion but within D14
    assert int(p.log_rows.sum())==6


def test_zero_log_no_capture_and_window_edges():
    h,a,l=fixture_data();p=build_project_panel(h,a,l).set_index("assignment_id")
    assert p.loc["a4","log_rows"]==0
    assert not bool(p.loc["a4","capture_D14"])
    assert p.loc["a5","coverage_D30"]=="last_day_time_uncertain"
    assert p.loc["a5","coverage_D14"]=="within_documented_horizon_conservative"
    assert p.loc["a3","coverage_D30"]=="within_documented_horizon_conservative"


def test_group_estimates_are_project_ratios_not_host_ratios():
    h,a,l=fixture_data();p=build_project_panel(h,a,l);x=build_host_panel(h,p)
    z=point_estimates(x)
    test=z.loc[(z.group=="test") & z.metric.eq("M6_capture_D14_project_rate"),"estimate"].item()
    assert test==pytest.approx(2/3)
    assert x.loc[x.experiment_group.eq("test"),"completed"].sum()==3


def test_horizon_table_excludes_uncertain_and_denominators_reconcile():
    h,a,l=fixture_data();p=build_project_panel(h,a,l);t=capture_horizon_table(p)
    d30=t.loc[(t.horizon=="D30") & t.group.eq("test")].iloc[0]
    assert d30.eligible_projects==2 and d30.uncertain_or_beyond==1
    for _,r in t.iterrows():
        assert r.captured+r.not_observed==r.eligible_projects
        assert r.captured_pre_completion<=r.captured


def test_joins_fail_closed_on_orphans_and_duplicates():
    h,a,l=fixture_data()
    with pytest.raises(ValueError,match="duplicate key"):
        build_project_panel(h,pd.concat([a,a.iloc[[0]]],ignore_index=True),l)
    bad=l.copy();bad.loc[0,"host_id"]="bad"
    with pytest.raises(ValueError,match="differs"):
        build_project_panel(h,a,bad)
    bad=l.copy();bad.loc[0,"assignment_id"]="unknown"
    with pytest.raises(ValueError,match="Orphan"):
        build_project_panel(h,a,bad)


def test_incident_filter_retains_registered_host_denominator():
    h,a,l=fixture_data();p=build_project_panel(h,a,l)
    all_h=build_host_panel(h,p);ex=build_host_panel(h,p,omit_incident=True)
    assert len(all_h)==len(ex)==4 and all_h.completed.sum()-ex.completed.sum()==1
    assert p.loc[p.in_experiment,"incident_completed"].sum()==1
    assert CS_START<CS_END


def test_pre_exposure_projects_preserved_in_main():
    h,a,l=fixture_data();p=build_project_panel(h,a,l)
    assert p.loc[p.in_experiment,"completed_pre_exposure"].sum()==1
    all_h=build_host_panel(h,p)
    post_h=build_host_panel(h,p,restrict_after_exposure=True)
    assert all_h.completed.sum()-post_h.completed.sum()==1
    assert post_h.completed.sum()<all_h.completed.sum()


def test_bootstrap_replicates_stable_and_group_resampling():
    h,a,l=fixture_data();x=build_host_panel(h,build_project_panel(h,a,l))
    b1=bootstrap_host_differences(x,n_boot=150,seed=99,batch=13)
    b2=bootstrap_host_differences(x,n_boot=150,seed=99,batch=13)
    pd.testing.assert_frame_equal(b1,b2)
    assert len(b1)==6 and np.isfinite(b1[["ci95_low","ci95_high"]]).all().all()
    assert (b1.ci95_low<=b1.ci95_high).all()
    # No fixed "successful effect" assertion: synthetic data are not random experiments.


def test_bootstrap_horizon_reproducibility():
    h,a,l=fixture_data();p=build_project_panel(h,a,l)
    z=bootstrap_capture_horizons(h,p,n_boot=150,seed=314,batch=10)
    assert list(z.horizon)==["D1","D7","D14","D30"]
    assert np.isfinite(z.difference).all()
    assert z.loc[z.horizon.eq("D30"),"test"].item()==pytest.approx(1/2)


def test_baseline_adjusted_hc3_has_expected_columns():
    h,a,l=fixture_data();x=build_host_panel(h,build_project_panel(h,a,l))
    # Add replicated independent synthetic hosts to avoid zero HC3 residual d.f.
    # and perfect leverage produced by a tiny four-host regression.
    x=pd.concat([x.assign(host_id=x.host_id+str(i)) for i in range(6)],ignore_index=True)
    r=baseline_hc3(x)
    assert len(r)==3
    assert (r.n_hosts==24).all()
    assert np.isfinite(r[["ci95_low","ci95_high","se_hc3"]]).all().all()
    assert set(r.outcome)=={"completed","captured_D14","not_captured_D14"}


def test_time_period_boundaries_half_open():
    assert BASELINE_START<EXPERIMENT_START<EXPERIMENT_END
    h,a,l=fixture_data();p=build_project_panel(h,a,l)
    assert int(p.baseline.sum())==1
    assert int(p.in_experiment.sum())==6


def test_bootstrap_rejects_zero_or_few_draws():
    h,a,l=fixture_data();x=build_host_panel(h,build_project_panel(h,a,l))
    with pytest.raises(ValueError):bootstrap_host_differences(x,n_boot=3)
