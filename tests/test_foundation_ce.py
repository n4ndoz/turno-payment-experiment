"""Small synthetic boundary checks for temporal and registered-host evidence."""
import pandas as pd
import pytest
from src.foundation_ce import compare_times, host_experiment_counts, parse_utc, potential_window_coverage, utc_timestamp


def test_parse_utc_naive_and_offset_and_missing():
    s = pd.Series(['2025-09-01 12:00:00','2025-09-01T09:00:00-03:00',pd.NA,'not a date'],dtype='string')
    v = parse_utc(s)
    assert v.iloc[0] == v.iloc[1] == utc_timestamp('2025-09-01 12:00:00')
    assert v.isna().sum()==2


def test_temporal_order_before_tie_after_missing():
    left = parse_utc(pd.Series(['2025-01-01','2025-01-02','2025-01-03',pd.NA], dtype='string'))
    right = parse_utc(pd.Series(['2025-01-02','2025-01-02','2025-01-02','2025-01-02'],dtype='string'))
    assert compare_times(left,right).tolist() == ['before','same_instant','after','unknown']


def test_temporal_rejects_different_index():
    a = pd.Series([pd.Timestamp('2025-01-01',tz='UTC')],index=[0])
    b = pd.Series([pd.Timestamp('2025-01-01',tz='UTC')],index=[1])
    with pytest.raises(ValueError):compare_times(a,b)


@pytest.mark.parametrize('date, expected',[
    ('2025-12-18 23:59:59','within_documented_horizon_conservative'),
    ('2025-12-19 00:00:00','last_day_time_uncertain'),
    ('2025-12-19 23:59:59','last_day_time_uncertain'),
    ('2025-12-20 00:00:00','beyond_documented_horizon'),
])
def test_last_day_uncertain_boundaries(date,expected):
    c=parse_utc(pd.Series([date]))
    assert potential_window_coverage(c,0).iloc[0]==expected


def test_followup_elapsed_days_in_utc_and_missing():
    c = parse_utc(pd.Series(['2025-11-18 23:59:59','2025-11-19 00:00:00',pd.NA],dtype='string'))
    assert potential_window_coverage(c,30).tolist()==['within_documented_horizon_conservative','last_day_time_uncertain','unknown_completion']


def test_window_negative_rejected():
    with pytest.raises(ValueError):potential_window_coverage(parse_utc(pd.Series(['2025-11-01'])), -1)


def test_host_experiment_population_preserves_zero_and_bounds():
    hosts=pd.DataFrame({'host_id':['a','b','c'],'experiment_group':['test','control','test'],'first_exposed_at':['2025-08-20']*3})
    projects=pd.DataFrame({'assignment_id':['1','2','3','4','5'],'host_id':['a','a','a','b','b'],
     'completed_at':['2025-08-17 23:59:59','2025-08-18 00:00:00','2025-11-19 23:59:59','2025-11-20 00:00:00','2025-08-20 00:00:00']})
    out=host_experiment_counts(hosts,projects)
    assert out.set_index('host_id')['experiment_completions'].to_dict()=={'a':2,'b':1,'c':0}
    assert out.experiment_completions.sum()==3


def test_host_experiment_rejects_orphan_or_duplicate():
    hosts=pd.DataFrame({'host_id':['a','b'],'experiment_group':['test','control'],'first_exposed_at':['2025-09-01']*2})
    projects=pd.DataFrame({'assignment_id':['1'],'host_id':['x'],'completed_at':['2025-09-03']})
    with pytest.raises(ValueError):host_experiment_counts(hosts,projects)
    projects.loc[0,'host_id']='a';hosts.loc[1,'host_id']='a'
    with pytest.raises(ValueError):host_experiment_counts(hosts,projects)


def test_elapsed_capture_exactly_at_deadline_counts_diagnostically():
    completed = utc_timestamp('2025-10-01 12:00:00')
    deadline = completed + pd.Timedelta(days=7)
    exact = utc_timestamp('2025-10-08 12:00:00')
    after = utc_timestamp('2025-10-08 12:00:01')
    assert exact <= deadline
    assert not (after <= deadline)


def test_incident_utc_midnight_boundaries():
    sep17=utc_timestamp('2025-09-17')
    oct1=utc_timestamp('2025-10-01')
    assert sep17 >= sep17 and sep17 < oct1
    assert not (oct1 < oct1)
    assert (oct1-pd.Timedelta(seconds=1)) < oct1
