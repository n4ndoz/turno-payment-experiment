"""Independent stream implementation of selected critical C and E reconciliations."""
import csv
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1] / 'data' / 'raw'
def dt(s):return datetime.fromisoformat(s).replace(tzinfo=timezone.utc) if s else None
BASE=dt('2025-07-18 00:00:00');EX0=dt('2025-08-18 00:00:00');EXEND=dt('2025-11-20 00:00:00');CUT=dt('2025-12-19 00:00:00');CUTEND=dt('2025-12-20 00:00:00')
with (R/'experiment_exposures.csv').open(newline='',encoding='utf-8-sig') as f:
    hosts=list(csv.DictReader(f))
hids={x['host_id'] for x in hosts}
counts=Counter();baseline=Counter();completed=0;d30=Counter();neg=0
with (R/'assignments.csv').open(newline='',encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        completed+=1
        host=row['host_id'];assert host in hids
        c=dt(row['completed_at']);created=dt(row['created_at'])
        if c<created:neg+=1
        if BASE<=c<EX0:baseline[host]+=1
        if EX0<=c<EXEND:counts[host]+=1
        deadline=c+timedelta(days=30)
        if deadline<CUT:d30['conservative']+=1
        elif deadline<CUTEND:d30['uncertain']+=1
        else:d30['outside']+=1

status_capture=Counter();created_after_capture=0;captured=0
with (R/'payment_logs.csv').open(newline='',encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        status_capture[(row['payment_status'],bool(row['captured_at']))]+=1
        if row['captured_at']:
            captured+=1
            if dt(row['captured_at'])<dt(row['created_at']):created_after_capture+=1

experiment_zero=sum(counts[host['host_id']]==0 for host in hosts)
full_zero=sum(counts[host['host_id']]==0 and baseline[host['host_id']]==0 for host in hosts)
both=sum(counts[host['host_id']]>0 and baseline[host['host_id']]>0 for host in hosts)
base_only=sum(counts[host['host_id']]==0 and baseline[host['host_id']]>0 for host in hosts)
ex_only=sum(counts[host['host_id']]>0 and baseline[host['host_id']]==0 for host in hosts)
print('independent_csv_validation')
print({'hosts':len(hosts),'projects':completed,'experiment_projects':sum(counts.values()),'baseline_projects':sum(baseline.values()),'experiment_zero':experiment_zero,'full_extract_zero':full_zero,'both_periods':both,'baseline_only':base_only,'experiment_only':ex_only,'d30':dict(d30),'completed_before_booked':neg,'capture_before_created':created_after_capture,'timestamped_captures':captured,'payment_status_capture':dict(status_capture)})
assert len(hosts)==14708 and completed==279847 and sum(d30.values())==completed
assert sum(counts.values())+sum(baseline.values())==completed
assert experiment_zero==full_zero+base_only
assert both+base_only+ex_only+full_zero==len(hosts)
assert d30['uncertain']==1252
assert neg==9 and created_after_capture==1821
assert sum(status_capture.values())==306957
print('INDEPENDENT PASS')
