"""Focused synthetic tests for inferential validation only (no original CSVs)."""
import numpy as np
import pandas as pd
import pytest
from src.inferential_validation import (paired_period_host_panel, paired_d1_bootstrap,
    hc3_adjusted_host_metrics,host_label_permutation,holm_adjust,influence_by_host)


def toy():
    hosts=pd.DataFrame({'host_id':['a','b','c','d','e','f'],
                        'experiment_group':['control']*3+['test']*3})
    rows=[]
    cases=[('a','baseline',True),('a','in_experiment',False),('b','baseline',False),
           ('b','in_experiment',True),('d','baseline',True),('d','in_experiment',True),
           ('e','in_experiment',True)]
    for i,(host,period,captured) in enumerate(cases):
        rows.append({'assignment_id':str(i),'host_id':host,
                     'baseline':period=='baseline','in_experiment':period=='in_experiment',
                     'capture_D1':captured,'coverage_D1':'within_documented_horizon_conservative'})
    q=pd.DataFrame(rows)
    panel=hosts.copy()
    panel['test']=panel.experiment_group.eq('test').astype(int)
    panel['completed']=[1,1,0,1,1,0]
    panel['first_ever']=[0,1,0,0,1,0]
    panel['captured_D14']=[0,1,0,1,1,0]
    panel['baseline_completions']=[1,1,0,1,0,0]
    return hosts,q,panel


def test_paired_project_rates_and_zeros():
    h,q,p=toy();z=paired_period_host_panel(h,q)
    assert z.shape[0]==6
    assert z.loc[z.host_id=='f','experiment_projects'].iloc[0]==0
    assert z.baseline_projects.sum()==3 and z.experiment_projects.sum()==4
    b,counts=paired_d1_bootstrap(z,n_boot=250,seed=1337,batch=7)
    assert counts['control']['hosts']==3 and counts['test']['hosts']==3
    expected_baseline=1-1/2 # test 1/1, control 1/2
    expected_experiment=1-1/2
    assert b.loc[b.contrast.eq('D1 baseline'),'difference'].item()==pytest.approx(expected_baseline)
    assert b.loc[b.contrast.eq('D1 experiment'),'difference'].item()==pytest.approx(expected_experiment)
    assert b.loc[b.contrast.str.startswith('D1 change'),'difference'].item()==pytest.approx(0.)
    assert all(b.ci_low <= b.ci_high)


def test_paired_bootstrap_reproducible():
    h,q,p=toy(); z=paired_period_host_panel(h,q)
    x,_=paired_d1_bootstrap(z,n_boot=500,seed=42)
    y,_=paired_d1_bootstrap(z,n_boot=500,seed=42)
    pd.testing.assert_frame_equal(x,y)


def test_paired_window_guard_and_overlaps():
    h,q,p=toy();q.loc[0,'coverage_D1']='last_day_time_uncertain'
    with pytest.raises(ValueError,match='D1'):paired_period_host_panel(h,q)
    q.loc[0,'coverage_D1']='within_documented_horizon_conservative'
    q.loc[0,'in_experiment']=True
    with pytest.raises(ValueError,match='Overlapping'):paired_period_host_panel(h,q)


def test_permutation_is_host_cluster_and_reproducible():
    h,q,p=toy();z=paired_period_host_panel(h,q)
    a,_=host_label_permutation(p,z,n_perm=200,seed=11)
    b,_=host_label_permutation(p,z,n_perm=200,seed=11)
    pd.testing.assert_frame_equal(a,b)
    assert list(a.metric)==['M1','M2','M4','D1']
    assert a.p_permutation_two_sided.ge(1/201).all()
    assert a.p_permutation_two_sided.le(1).all()


def test_permutation_rejects_missing_group_key():
    h,q,p=toy();z=paired_period_host_panel(h,q)
    z.loc[0,'experiment_group']='test'
    with pytest.raises(ValueError,match='Incompatible'):host_label_permutation(p,z,n_perm=100)


def test_holm_stepdown_and_validation():
    x=holm_adjust(np.array([.03,.001,.04,.02]))
    assert x.tolist()==pytest.approx([.06,.004,.06,.06])
    assert np.all(holm_adjust([.4,.9,.3])<=1.)
    with pytest.raises(ValueError):holm_adjust([.1,np.nan])
    with pytest.raises(ValueError):holm_adjust([-0.1,.2])


def test_influence_cap_applies_same_pooled_threshold():
    h,q,p=toy();r,s=influence_by_host(p,quantile=.8)
    assert r.pooled_p99_cap.nunique()==1
    assert s.loc[s.diagnostic.str.startswith('Full'),'test_minus_control'].item()==pytest.approx(0.)
    assert r.top_1pct_share.between(0,1).all()


def test_hc3_keeps_zero_activity_hosts():
    h,q,p=toy()
    # Add more hosts for a full-rank nondegenerate synthetic design.
    big=pd.concat([p.assign(host_id=p.host_id+str(i),baseline_completions=p.baseline_completions+i%3)
                   for i in range(5)],ignore_index=True)
    a=hc3_adjusted_host_metrics(big)
    assert set(a.metric)=={'M1','M2','M4'}
    assert a[['adjusted_difference','adjusted_ci_low','adjusted_ci_high']].notna().all().all()
    assert a.adjusted_ci_high.ge(a.adjusted_ci_low).all()
