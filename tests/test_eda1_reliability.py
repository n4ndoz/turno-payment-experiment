"""Targeted synthetic EDA 1 tests; no original CSV data required."""
import numpy as np
import pandas as pd
import pytest

from src.eda1_reliability import (prepare_time_panel, empirical_capture_curve,
    rmst_horizon, metric_project_horizon, cluster_ratio_ci, label_incident_overlap,
    build_discordance_flags, friction_tables, card_alternative_journeys)

UTC='UTC'
BASE=pd.Timestamp('2025-09-01 00:00:00',tz=UTC)

def hosts():
    return pd.DataFrame({'host_id':['1','2','3','4'], 'experiment_group':['control','control','test','test']})

def panel():
    # Includes events before completion, on time zero, exact D1/D7/D14/D30,
    # just after D7, no log, and a last-day-uncertain project.
    offsets=[-3,0,24,168,336,720,168+1/3600,None,720]
    completion=[BASE]*8+[pd.Timestamp('2025-11-19 05:00',tz=UTC)]
    frame=pd.DataFrame({'assignment_id':[str(i) for i in range(9)],
       'host_id':['1','1','1','2','2','3','3','4','4'],
       'experiment_group':['control']*5+['test']*4,
       'completed_utc':completion,'in_experiment':[True]*9,
       'first_capture':[t+pd.Timedelta(hours=h) if h is not None else pd.NaT for t,h in zip(completion,offsets)]})
    for d in (1,7,14,30):
        frame[f'coverage_D{d}']='within_documented_horizon_conservative'
    frame.loc[8,'coverage_D30']='last_day_time_uncertain'
    return frame

@pytest.mark.parametrize('idx,expected',[(0,0),(1,0),(2,24),(3,168),(4,336),(5,720),(6,168+1/3600),(7,None),(8,720)])
def test_event_times_and_ties(idx,expected):
    q=prepare_time_panel(panel())
    value=q.iloc[idx].event_hours
    if expected is None: assert pd.isna(value)
    else: assert value==pytest.approx(expected)

@pytest.mark.parametrize('days,expected',[(1,24),(7,168),(14,336),(30,720)])
def test_exact_boundaries_and_right_after(days,expected):
    q=prepare_time_panel(panel())
    assert q.loc[q.assignment_id.eq('2'),f'event_D{days}'].iloc[0] is not None
    # Events equal to boundary count. Events just after D7 do not count at D7.
    if days==7:
        assert bool(q.loc[3,'event_D7'])
        assert not bool(q.loc[6,'event_D7'])
    assert bool(q.loc[7,f'restricted_uncaptured_hours_D{days}']==expected)

def test_before_completion_zero_and_no_capture_full_restriction():
    q=prepare_time_panel(panel())
    assert q.loc[0,'signed_capture_hours']==-3
    assert q.loc[0,'restricted_uncaptured_hours_D30']==0
    assert q.loc[7,'restricted_uncaptured_hours_D7']==168
    assert q.loc[7,'restricted_uncaptured_hours_D30']==720
    assert q.pre_completion.sum()==1

def test_last_day_uncertainty_and_common_population():
    q=prepare_time_panel(panel())
    assert not q.loc[8,'covered_D30']
    assert q.loc[8,'covered_D14']
    r=rmst_horizon(q,hosts(),7,n_boot=100,seed=4)
    c=rmst_horizon(q,hosts(),7,common_D30=True,n_boot=100,seed=4)
    assert r['n_control']+r['n_test']==9
    assert c['n_control']+c['n_test']==8
    x=rmst_horizon(q,hosts(),30,n_boot=100,seed=4)
    assert x['n_control']+x['n_test']==8

def test_empirical_curve_matches_discrete_events():
    q=prepare_time_panel(panel())
    c=empirical_capture_curve(q,np.array([0,24,168,336,720]))
    for g in ['control','test']:
        z=q.loc[q.covered_D30 & q.experiment_group.eq(g)]
        for h in (0,24,168,336,720):
            v=c.loc[c.group.eq(g)&c.hours.eq(h),'captured_fraction'].iloc[0]
            assert v==pytest.approx(((z.event_hours.notna()) & z.event_hours.le(h)).mean())

def test_ratio_bootstrap_resamples_hosts_deterministically():
    p=pd.DataFrame({'host_id':['1','2','3','4'], 'experiment_group':['control','control','test','test'],
                    'total':[10.,0.,9.,3.], 'denominator':[1.,0.,1.,3.]})
    a=cluster_ratio_ci(p,n_boot=100,seed=91)
    b=cluster_ratio_ci(p,n_boot=100,seed=91)
    assert a==b
    assert a['control']==pytest.approx(10.)
    assert a['test']==pytest.approx(3.)
    assert a['difference']==pytest.approx(-7.)

def test_d1_sensitivity_does_not_mutate_full_coverage():
    q=prepare_time_panel(panel());q['concordant_D1']=q.event_D1
    before=q.covered_D1.copy(deep=True)
    s=pd.Series(False,index=q.index);s.iloc[0]=True;s.iloc[3]=True;s.iloc[5]=True
    metric_project_horizon(q,hosts(),1,subset=s,n_boot=1000,seed=9)
    assert q.covered_D1.equals(before)
    r=metric_project_horizon(q,hosts(),1,n_boot=100,seed=9)
    assert r['n_control']+r['n_test']==9
    r2=metric_project_horizon(q,hosts(),1,criterion='concordant',n_boot=100,seed=9)
    assert r2['n_control']+r2['n_test']==9

def test_right_censoring_not_invented_from_last_log():
    q=prepare_time_panel(panel());q.loc[8,'first_capture']=pd.NaT
    q=prepare_time_panel(q)
    assert q.loc[8,'restricted_uncaptured_hours_D30']==720
    assert not q.loc[8,'covered_D30']

def test_cs_window_overlap_without_labeling_cs_actions():
    q=panel()
    q.loc[0,'completed_utc']=pd.Timestamp('2025-09-16 23:30',tz=UTC)
    q.loc[1,'completed_utc']=pd.Timestamp('2025-10-01 00:00',tz=UTC)
    flags=label_incident_overlap(q)
    assert bool(flags.loc[0]) and not bool(flags.loc[1])

def test_discordance_same_and_distinct_timestamps():
    t='2025-09-02 00:00:00'
    df=pd.DataFrame({'assignment_id':['a','a','a','b','b','c'], 'payment_method':['card']*6,
      'payment_status':['succeeded','voided','failed','succeeded','voided','succeeded'],
      'captured_at':[t,t,'2025-09-03 00:00:00',t,'2025-09-04 00:00:00',None],
      'created_at':['2025-09-01']*6})
    p=pd.DataFrame({'assignment_id':['a','b','c'],'experiment_group':['control']*3,
        'completed_utc':[BASE]*3, 'in_experiment':[True]*3})
    result=build_discordance_flags(df,p).set_index('assignment_id')
    assert bool(result.loc['a','discordant_capture_same_time_as_concordant'])
    assert bool(result.loc['a','discordant_capture_distinct_time_from_concordant'])
    assert not bool(result.loc['b','discordant_capture_same_time_as_concordant'])
    assert bool(result.loc['b','discordant_capture_distinct_time_from_concordant'])
    assert bool(result.loc['c','any_discordance']) and not bool(result.loc['c','any_concordance'])

def test_card_failed_then_alt_capture_not_financial_proof():
    data=pd.DataFrame({'assignment_id':['a','a','b','b'], 'payment_method':['card','bank_account','card','credits'],
      'payment_status':['declined','succeeded','failed','succeeded'],
      'captured_at':[None,'2025-09-02',None,'2025-09-03'],
      'created_at':['2025-09-01','2025-09-02','2025-09-02','2025-09-01']})
    p=pd.DataFrame({'assignment_id':['a','b'], 'experiment_group':['control','test'],
                    'in_experiment':[True,True]})
    details,summary=card_alternative_journeys(data,p)
    assert len(details)==2
    assert details.alt_capture.sum()==2
    assert details.later_alt_record.sum()==1
    assert details.earlier_alt_record.sum()==1

def test_zero_attempt_project_in_friction_denominator():
    l=pd.DataFrame({'assignment_id':['a','a'], 'payment_method':['card','card'],
       'payment_status':['failed','declined'],'captured_at':[None,None]})
    p=pd.DataFrame({'assignment_id':['a','b'], 'experiment_group':['control','test'],
                    'baseline':[False,False],'in_experiment':[True,True]})
    a,b,c=friction_tables(l,p)
    assert c.completed_projects.sum()==2
    assert c.with_failed_or_declined.sum()==1
    assert a.total_attempts.sum()==2
