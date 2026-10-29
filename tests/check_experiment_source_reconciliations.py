"""Independent Sprint 1 audit: Python standard-library CSV/datetime only.

Uses no Pandas, NumPy, main analysis code, or project helper functions.
Source-level regression anchors are deliberately asserted *after* computing
independent record groupings; they are not used to classify records.
Run from repository root: python tests/check_experiment_source_reconciliations.py
"""
from __future__ import annotations

from collections import Counter, defaultdict
import csv
from datetime import datetime, timedelta
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'data/raw'
DT='%Y-%m-%d %H:%M:%S'
D=lambda s:datetime.strptime(s,DT)
START=D('2025-08-18 00:00:00')
END=D('2025-11-20 00:00:00')
LAST=D('2025-12-19 00:00:00')
BASE=D('2025-07-18 00:00:00')
CS_START=D('2025-09-17 00:00:00')
CS_END=D('2025-10-01 00:00:00')


def read(name):
    with (RAW/name).open(newline='',encoding='utf-8') as f:
        yield from csv.DictReader(f)


def main():
    hosts={};grp=Counter()
    for h in read('experiment_exposures.csv'):
        k=h['host_id'];assert k not in hosts
        hosts[k]=(h['experiment_group'],D(h['first_exposed_at']))
        grp[h['experiment_group']]+=1
    projects={};exp=set();baseline=Counter()
    for a in read('assignments.csv'):
        ident=a['assignment_id'];assert ident not in projects
        host=a['host_id'];assert host in hosts
        finished=D(a['completed_at']);created=D(a['created_at'])
        projects[ident]=(host,finished,created,a['is_first_completed_project']=='true')
        if START<=finished<END: exp.add(ident)
        if BASE<=finished<START: baseline[host]+=1
    first_capture={};any_succeeded=set();concord=set();attempts=0;log_ids=set();projects_with_log=set()
    for l in read('payment_logs.csv'):
        attempts+=1
        ident=l['payment_log_id'];assert ident not in log_ids
        log_ids.add(ident)
        aid=l['assignment_id'];assert aid in projects and l['host_id']==projects[aid][0]
        projects_with_log.add(aid)
        if l['payment_status']=='succeeded':any_succeeded.add(aid)
        if l['captured_at']:
            t=D(l['captured_at'])
            if aid not in first_capture or t<first_capture[aid]:first_capture[aid]=t
            if l['payment_status']=='succeeded':concord.add(aid)
    count=Counter();host_completed=Counter();host_captured=Counter();host_first=Counter()
    for aid in exp:
        host,finish,created,first=projects[aid]
        group,exposed=hosts[host]
        count[(group,'projects')]+=1
        host_completed[host]+=1
        if first:
            host_first[host]+=1;count[(group,'first')]+=1
        if finish<exposed:count[(group,'pre_exposure')]+=1
        if created<exposed and finish>=exposed:count[(group,'booked_pre_completed_post')]+=1
        if CS_START<=finish<CS_END:count[(group,'incident_projects')]+=1
        captured=first_capture.get(aid)
        if captured is not None:
            count[(group,'any_capture')]+=1
            if captured<=finish+timedelta(days=1):count[(group,'D1')]+=1
            if captured<=finish+timedelta(days=7):count[(group,'D7')]+=1
            if captured<=finish+timedelta(days=14):
                count[(group,'D14')]+=1;host_captured[host]+=1
            if captured<finish:count[(group,'pre_completion_capture')]+=1
        if aid in any_succeeded:count[(group,'success')]+=1
        if aid in concord:count[(group,'concordant')]+=1
        if finish+timedelta(days=30)>=LAST:
            count[(group,'D30_uncertain_or_beyond')]+=1
        else:
            count[(group,'D30_eligible')]+=1
            if captured is not None and captured<=finish+timedelta(days=30):count[(group,'D30')]+=1
    assert len(hosts)==14708 and len(projects)==279847 and attempts==306957
    assert grp==Counter({'control':7377,'test':7331})
    assert len(exp)==201302
    for group,expected in {'control':(98855,98317,1004,63,2573,32299,616,98239,97751),
                           'test':(102447,101790,1106,38,2518,32995,636,101811,101227)}.items():
        keys=('projects','D14','first','pre_completion_capture','pre_exposure','booked_pre_completed_post',
              'D30_uncertain_or_beyond','D30_eligible','D30')
        actual=tuple(count[(group,k)] for k in keys)
        assert actual==expected,(group,actual,expected)
    assert sum(v==0 for h,v in ((k,host_completed[k]) for k in hosts))==836
    assert sum(v>=2 for k,v in ((h,host_completed[h]) for h in hosts))>0
    assert sum(host_completed.values())==sum(host_captured.values())+sum(host_completed[h]-host_captured[h] for h in hosts)
    assert len(projects)-len(projects_with_log)==239
    assert sum(count[(g,'pre_exposure')] for g in grp)==5091
    assert sum(count[(g,'booked_pre_completed_post')] for g in grp)==65294
    assert sum(count[(g,'D30_uncertain_or_beyond')] for g in grp)==1252
    print('PASS independent source CSV audit: hosts',len(hosts),'projects',len(projects),'attempts',attempts,
          'experiment projects',len(exp),'zero-experiment hosts',sum(host_completed[h]==0 for h in hosts))
    for group in ('control','test'):
        print(group,{k:count[(group,k)] for k in ('projects','D1','D7','D14','D30','D30_eligible','D30_uncertain_or_beyond',
                    'any_capture','success','concordant','pre_exposure','booked_pre_completed_post','incident_projects')})
    print('Source-only audit completed; denominators and project captures agree with notebook results.')

if __name__=='__main__':main()
