"""Independent CSV-stream audit for D; no imports from src/ or Pandas.

Run from repository root: python tests/check_d_source_reconciliations.py
Counts reflect observational field patterns only, not payment settlement.
"""
from __future__ import annotations
import csv
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data/raw'


def rows(name):
    with (RAW / name).open(encoding='utf-8-sig', newline='') as stream:
        yield from csv.DictReader(stream)


def main():
    projects={row['assignment_id']: (row['host_id'],row['completed_at']) for row in rows('assignments.csv')}
    hosts={row['host_id']:row['experiment_group'] for row in rows('experiment_exposures.csv')}
    evidence=defaultdict(lambda: {'rows':0,'s':0,'c':0,'cc':0,'bad':0,'m':set(),'cm':set(),'manual':False,'failed':False})
    total=0;by_method=Counter(); discordant=0;unique_log_ids=set()
    for r in rows('payment_logs.csv'):
        total+=1
        logid=r['payment_log_id']
        assert logid not in unique_log_ids
        unique_log_ids.add(logid)
        aid=r['assignment_id']
        assert aid in projects and r['host_id']==projects[aid][0]
        assert r['host_id'] in hosts
        e=evidence[aid]
        e['rows']+=1
        s=r['payment_status']=='succeeded'
        c=bool(r['captured_at'])
        e['s']+=s;e['c']+=c;e['cc']+=(s and c);e['bad']+=(s!=c)
        e['m'].add(r['payment_method'])
        if c:e['cm'].add(r['payment_method'])
        e['manual']|=r['is_manual_attempt']=='true'
        e['failed']|=r['payment_status'] in ('failed','declined')
        by_method[r['payment_method']]+=1
        discordant+=(s!=c)
    exclusive=Counter()
    for aid in projects:
        if aid not in evidence:
            exclusive['no_logs']+=1
        else:
            e=evidence[aid];s=e['s']>0;c=e['c']>0
            if s and c:exclusive['both_evidence_types']+=1
            elif s:exclusive['success_status_only']+=1
            elif c:exclusive['capture_timestamp_only']+=1
            else:exclusive['logs_no_success_or_capture']+=1
    flag=lambda predicate:sum(bool(predicate(e)) for e in evidence.values())
    report={
        'completed_projects':len(projects),'registered_hosts':len(hosts),'attempt_rows':total,
        'no_logs':exclusive['no_logs'],'exclusive':dict(exclusive),
        'attempts_by_method':dict(by_method),
        'attempts_with_discordance':discordant,
        'projects_with_discordance':flag(lambda e:e['bad']>0),
        'projects_with_multiple_capture_rows':flag(lambda e:e['c']>1),
        'projects_with_multiple_capture_methods':flag(lambda e:len(e['cm'])>1),
        'projects_with_multiple_methods':flag(lambda e:len(e['m'])>1),
        'projects_with_manual':flag(lambda e:e['manual']),
        'projects_with_split_evidence_only':flag(lambda e:e['s']>0 and e['c']>0 and e['cc']==0),
        'candidate_status_projects':flag(lambda e:e['s']>0),
        'candidate_timestamp_projects':flag(lambda e:e['c']>0),
        'candidate_concordant_projects':flag(lambda e:e['cc']>0),
    }
    assert len(projects)==sum(exclusive.values())
    assert total==sum(e['rows'] for e in evidence.values())
    assert report['completed_projects']==279847 and report['attempt_rows']==306957
    assert report['no_logs']==239 and report['attempts_with_discordance']==2316
    assert report['projects_with_discordance']==2075
    assert report['projects_with_multiple_capture_rows']==652
    assert report['projects_with_multiple_capture_methods']==200
    print('Independent standard-library CSV stream: PASS')
    for k,v in report.items():print(k,'=',v)
    return report


if __name__=='__main__':main()
