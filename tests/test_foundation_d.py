"""Synthetic only: technical invariants, no business payment truth."""
import pandas as pd
import pytest

from src.foundation_d import checked_attempts, project_journeys, ordered_record_diagnostics, completion_period


def sample():
    hosts = pd.DataFrame({"host_id": ["h1","h2","h3","h4","h5","h6","h7"], "experiment_group": ["Control","Test","Test","Control","Test","Control","Test"], "first_exposed_at": ["2025-08-20"]*7}, dtype="string")
    projects = pd.DataFrame({"assignment_id": ["a0","a1","a2","a3","a4","a5","a6"], "host_id": ["h1","h2","h3","h4","h5","h6","h7"], "completed_at": ["2025-09-02"]*7}, dtype="string")
    entries = [
        ("l1","a1","h2","card","failed","false","2025-09-01T10:00:00Z",None),
        ("l2","a1","h2","bank_account","succeeded","true","2025-09-01T11:00:00Z","2025-09-01T11:10:00Z"),
        ("l3","a2","h3","card","succeeded","false","2025-09-01T10:00:00Z",None),
        ("l4","a2","h3","credits","failed","false","2025-09-01T12:00:00Z","2025-09-01T12:05:00Z"),
        ("l5","a3","h4","card","succeeded","false","2025-09-01T10:00:00Z","2025-09-01T10:15:00Z"),
        ("l6","a3","h4","credits","succeeded","false","2025-09-01T12:00:00Z","2025-09-01T12:15:00Z"),
        ("l7","a4","h5","card","declined","false","2025-09-01T09:00:00Z",None),
        ("l8","a4","h5","card","voided","true","2025-09-01T09:00:00Z",None),
        ("l9","a5","h6","card","succeeded","false","2025-09-01T13:00:00Z",None),
        ("l10","a6","h7","card","failed","false","2025-09-01T13:10:00Z","2025-09-01T13:15:00Z"),
    ]
    logs = pd.DataFrame(entries,columns=["payment_log_id","assignment_id","host_id","payment_method","payment_status","is_manual_attempt","created_at","captured_at"]).astype("string")
    return hosts,projects,logs


def get():
    hosts,projects,logs = sample()
    a=checked_attempts(projects,logs,hosts)
    return projects,a,project_journeys(projects,a)


def test_exhaustive_partition_preserves_zero_logs():
    p,a,j=get()
    assert len(j)==7 and j.at[0,"financial_evidence_partition"]=="no_logs"
    assert j.financial_evidence_partition.value_counts().to_dict()=={
        "both_evidence_types":3,"no_logs":1,"capture_timestamp_only":1,"success_status_only":1,"logs_no_success_or_capture":1}
    assert j.at[2,"split_evidence_attempts_only"]
    assert j.at[3,"multiple_capture_methods"]
    assert j.at[1,"mixed_manual_auto"]
    assert j.at[4,"has_manual"] and not j.at[4,"has_success_status"]
    assert int(j.attempts.sum()) == len(a)


def test_discordant_attempts_are_not_repairs():
    _,a,j=get()
    assert int(a._discordant.sum())==4
    assert int(j.has_discordance.sum())==3
    assert int(j.has_concordant_attempt.sum())==2
    assert int(j.split_evidence_attempts_only.sum())==1


def test_multiple_captures_and_methods_remain_flags():
    _,a,j=get()
    row=j.set_index("assignment_id").loc["a3"]
    assert row.capture_rows==2 and row.capture_methods==2
    assert row.multiple_capture_rows and row.multiple_capture_methods
    assert row.financial_evidence_partition=="both_evidence_types"


def test_ties_do_not_produce_arbitrary_transitions():
    _,a,_=get()
    j,t=ordered_record_diagnostics(a)
    x=j.set_index("assignment_id")
    assert x.loc["a4","tied_created_timestamp"]
    assert not x.loc["a4","sequence_order_clear"]
    assert "a4" not in set(t.assignment_id)
    assert x.loc["a1","failure_record_before_success_record"]
    assert x.loc["a1","failure_record_before_manual_record"]


def test_missing_created_protects_sequence():
    h,p,l=sample();l.loc[l.payment_log_id.eq("l2"),"created_at"]=pd.NA
    a=checked_attempts(p,l,h)
    j,t=ordered_record_diagnostics(a)
    assert j.set_index("assignment_id").loc["a1","missing_or_invalid_created"]
    assert "a1" not in set(t.assignment_id)


def test_duplicate_attempt_id_rejected():
    h,p,l=sample();l.loc[1,"payment_log_id"]="l1"
    with pytest.raises(ValueError,match="payment_log_id"):
        checked_attempts(p,l,h)


def test_orphan_attempt_rejected():
    h,p,l=sample();l.loc[1,"assignment_id"]="absent"
    with pytest.raises(ValueError,match="Orphan"):
        checked_attempts(p,l,h)


def test_host_mismatch_rejected():
    h,p,l=sample();l.loc[1,"host_id"]="h3"
    with pytest.raises(ValueError,match="host"):
        checked_attempts(p,l,h)


def test_duplicate_project_rejected():
    h,p,l=sample();p.loc[1,"assignment_id"]="a0"
    with pytest.raises(ValueError):
        checked_attempts(p,l,h)


@pytest.mark.parametrize("date,label",[
    ("2025-07-17T23:59:59Z","out_of_documented_completion_periods"),
    ("2025-07-18T00:00:00Z","baseline"),
    ("2025-08-18T00:00:00Z","experiment"),
    ("2025-11-19T23:59:59Z","experiment"),
    ("2025-11-20T00:00:00Z","out_of_documented_completion_periods"),
    (None,"unknown_completion"),
])
def test_period_boundaries(date,label):
    assert completion_period(pd.Series([date], dtype="string")).iloc[0]==label


def test_project_attempt_join_rejects_missing_project():
    p,a,_=get()
    with pytest.raises(ValueError,match="Orphan"):
        project_journeys(p.loc[p.assignment_id.ne("a2")],a)
