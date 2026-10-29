"""Independent EDA 1 count/RMST audit using Python stdlib CSV and datetimes.

Run: python tests/check_eda1_source_reconciliations.py
Independent of pandas, EDA helpers and the notebook's groupby operations.
"""
from __future__ import annotations
import csv
from collections import defaultdict
from datetime import datetime,timedelta
from pathlib import Path
import json

DATA=Path(__file__).resolve().parents[1]/'data'/'raw'
START=datetime.fromisoformat('2025-08-18')
END=datetime.fromisoformat('2025-11-20')
D30_UNCERTAIN=datetime.fromisoformat('2025-12-19')

def read_rows(file):
    with (DATA/file).open(encoding='utf-8-sig',newline='') as f:
        yield from csv.DictReader(f)

def dt(value):
    return datetime.fromisoformat(value) if value else None

def run_audit():
    groups={h['host_id']:h['experiment_group'] for h in read_rows('experiment_exposures.csv')}
    if len(groups)!=14708: raise AssertionError('Registered host count changed')
    project={}
    group_counts=defaultdict(int)
    for a in read_rows('assignments.csv'):
        t=dt(a['completed_at'])
        if START<=t<END:
            grp=groups[a['host_id']]
            project[a['assignment_id']]={'host':a['host_id'],'group':grp,'completion':t,
                 'first':None,'discordant':False,'friction':False,'card_fail':False,'alt_capture':False}
            group_counts[grp]+=1
    assert len(project)==201302
    discordant_attempts=0
    for log in read_rows('payment_logs.csv'):
        p=project.get(log['assignment_id'])
        if p is None:continue
        captured=dt(log['captured_at'])
        status=log['payment_status']
        if captured and (p['first'] is None or captured<p['first']):p['first']=captured
        mismatch=(status=='succeeded') != (captured is not None)
        if mismatch:p['discordant']=True;discordant_attempts+=1
        if status in ('failed','declined'):
            p['friction']=True
            if log['payment_method']=='card':p['card_fail']=True
        if log['payment_method']!='card' and captured:p['alt_capture']=True
    audit={'total':len(project),'by_group':dict(group_counts),'discordant_attempts':discordant_attempts,
           'discordant_projects':sum(int(p['discordant']) for p in project.values())}
    count=defaultdict(lambda:defaultdict(int))
    sums=defaultdict(lambda:defaultdict(float))
    for p in project.values():
        group=p['group']; completed=p['completion']; cap=p['first']
        audit.setdefault('friction_by_group',{}).setdefault(group,0)
        audit.setdefault('card_fail_alt_capture_by_group',{}).setdefault(group,0)
        audit['friction_by_group'][group]+=int(p['friction'])
        audit['card_fail_alt_capture_by_group'][group]+=int(p['card_fail'] and p['alt_capture'])
        elapsed=max(0.0,(cap-completed).total_seconds()/3600) if cap is not None else float('inf')
        for days in (1,7,14,30):
            if days==30 and completed+timedelta(days=30)>=D30_UNCERTAIN:continue
            key=f'D{days}'
            count[group][key]+=1
            count[group][key+'_captured']+=int(elapsed<=24*days)
        for days in (7,14,30):
            if days==30 and completed+timedelta(days=30)>=D30_UNCERTAIN:continue
            sums[group][f'D{days}']+=min(elapsed,24*days)
            if completed+timedelta(days=30)<D30_UNCERTAIN:
                sums[group][f'D{days}_common_D30']+=min(elapsed,24*days)
    audit['counts']={g:dict(v) for g,v in count.items()}
    audit['rmst_hours']={g:{k:(v/count[g][f'D{k[1:].split("_")[0]}'] if '_common_D30' not in k else v/count[g]['D30']) for k,v in out.items()} for g,out in sums.items()}
    # Important: denominator for common-cohort RMST is the D30 cohort, not D7/D14 population.
    return audit

if __name__=='__main__':
    result=run_audit()
    print(json.dumps(result,indent=2,sort_keys=True))
