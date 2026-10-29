"""Focused synthetic verification for the final decision checks; no real data."""
import numpy as np
import pandas as pd
import pytest
from src.final_decision_checks import (m2_recorded_exposure, second_within_30_days,
                                       d1_project_weighted_baseline_sensitivity)

UTC = lambda x: pd.Timestamp(x,tz='UTC')

def hosts():
    return pd.DataFrame({'host_id':['a','b','c','d'],
                         'experiment_group':['control','test','control','test']})


def project_rows():
    rows=[
        # Control a: first before recorded exposure, booked second before first.
        ('f1','a','control','2025-08-19 00:00','2025-08-18 20:00','2025-08-20 00:00',True,True),
        ('s1','a','control','2025-08-24 00:00','2025-08-21 02:00','2025-08-18 00:00',False,True),
        # Test b: first after exposure, second booked after first and exactly on D30.
        ('f2','b','test','2025-08-22 00:00','2025-08-21 00:00','2025-08-19 00:00',True,True),
        ('s2','b','test','2025-09-21 00:00','2025-08-25 00:00','2025-08-19 00:00',False,True),
        # Test d: first has incomplete D30 follow-up; cannot contribute.
        ('f4','d','test','2025-11-10 00:00','2025-11-09 00:00','2025-08-20 00:00',True,True),
    ]
    p=pd.DataFrame(rows,columns=['assignment_id','host_id','experiment_group',
                                    'completed_utc','created_utc','exposed_utc','is_first_true','in_experiment'])
    for f in ['completed_utc','created_utc','exposed_utc']:
        p[f]=pd.to_datetime(p[f],utc=True)
    return p


def test_m2_chronology_host_denominators_and_partition():
    r,q=m2_recorded_exposure(project_rows(),hosts())
    c,t=r.iloc[0],r.iloc[1]
    assert (c.registered_hosts,t.registered_hosts)==(2,2)
    assert (c.flagged_first,t.flagged_first)==(1,2)
    assert (c.pre_recorded_exposure,t.pre_recorded_exposure)==(1,0)
    assert (c.post_or_at_recorded_exposure,t.post_or_at_recorded_exposure)==(0,2)
    assert q.host_id.is_unique


def test_m2_duplicate_first_flag_fails():
    p=project_rows()
    p.loc[p.assignment_id.eq('s1'),'is_first_true']=True
    with pytest.raises(ValueError,match='More than one'):
        m2_recorded_exposure(p,hosts())


def test_second_d30_inclusive_boundary_and_prebooking_classification():
    r,cohort,d=second_within_30_days(project_rows())
    c,t=r.iloc[0],r.iloc[1]
    assert (c.eligible_hosts,t.eligible_hosts)==(1,1)
    assert (c.second_within_30d,t.second_within_30d)==(1,1)
    assert c.second_created_before_first==0  # s1 is booked two hours *after* first.
    assert t.second_created_after_first==1
    assert d['censored_firsts']==1
    assert cohort.loc[cohort.host_id.eq('b'),'second_assignment_id'].item()=='s2'


def test_second_booking_pre_first_and_simultaneous_are_disjoint():
    p=project_rows()
    p.loc[p.assignment_id.eq('s1'),'created_utc']=UTC('2025-08-18 23:00')
    p.loc[p.assignment_id.eq('s2'),'created_utc']=UTC('2025-08-22 00:00')
    r,_,_=second_within_30_days(p)
    assert r.iloc[0].second_created_before_first==1
    assert r.iloc[1].second_created_simultaneously==1
    assert r.iloc[1].second_created_after_first==0


def test_second_strictly_later_not_tied_and_excludes_d30_plus_second():
    p=project_rows()
    q=p.loc[p.assignment_id.eq('f2')].copy()
    q.loc[:,'assignment_id']='same_time'
    q.loc[:,'is_first_true']=False
    p=pd.concat([p,q],ignore_index=True)
    p.loc[p.assignment_id.eq('s2'),'completed_utc']=UTC('2025-09-21 00:00:01')
    r,c,d=second_within_30_days(p)
    assert r.iloc[1].second_within_30d==0
    assert d['tied_hosts']==1
    assert c.loc[c.host_id.eq('b'),'has_second_30d'].item()==False


def test_second_last_day_followup_is_conservatively_incomplete():
    p=project_rows()
    p.loc[p.assignment_id.eq('f2'),'completed_utc']=UTC('2025-10-21 00:00')
    r,c,d=second_within_30_days(p)
    assert d['eligible_firsts']==1
    assert d['censored_firsts']==2


def test_second_missing_or_duplicate_project_rejected():
    p=project_rows()
    p.loc[p.assignment_id.eq('s2'),'assignment_id']='f2'
    with pytest.raises(ValueError,match='Invalid assignment'):
        second_within_30_days(p)


def paired_panel():
    # More hosts than regression parameters; no fabricated baseline rate for zeros.
    n=80
    rng=np.random.default_rng(4312)
    experimental=rng.integers(2,20,size=n)
    historical=rng.integers(0,12,size=n)
    historical[:8]=0
    captured_exp=experimental-rng.binomial(experimental,0.05,size=n)
    captured_pre=historical-rng.binomial(historical,0.07,size=n)
    return pd.DataFrame({'host_id':[f'h{i}' for i in range(n)],
        'experiment_group':['control']*(n//2)+['test']*(n//2),
        'experiment_projects':experimental,'experiment_captured':captured_exp,
        'baseline_projects':historical,'baseline_captured':captured_pre})


def test_d1_adjustment_reproduces_project_weighted_ratio():
    p=paired_panel()
    x=d1_project_weighted_baseline_sensitivity(p)
    a=p.loc[p.experiment_group.eq('control')]
    b=p.loc[p.experiment_group.eq('test')]
    expected=b.experiment_captured.sum()/b.experiment_projects.sum()-a.experiment_captured.sum()/a.experiment_projects.sum()
    assert np.isclose(x['raw_diff'],expected,rtol=0,atol=1e-12)
    assert x['hosts_without_baseline']>=8
    assert x['hosts_total']==80 and x['projects_experiment']==p.experiment_projects.sum()
    assert np.isfinite([x['adjusted_diff'],x['ci95_low'],x['ci95_high']]).all()


def test_d1_adjustment_keeps_zero_experiment_hosts_in_frame():
    p=paired_panel()
    p.loc[0,'experiment_projects']=0
    p.loc[0,'experiment_captured']=0
    x=d1_project_weighted_baseline_sensitivity(p)
    assert x['hosts_total']==80 and x['hosts_with_experiment']==79
    assert x['hosts_with_zero_experiment']==1


def test_d1_invalid_capture_counts_rejected():
    p=paired_panel()
    p.loc[0,'baseline_captured']=p.loc[0,'baseline_projects']+1
    with pytest.raises(ValueError,match='Captured projects'):
        d1_project_weighted_baseline_sensitivity(p)
