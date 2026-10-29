# EDA 0 — Checkpoint A: anomaly and limitation register

Do not confuse an *observation gap* with a confirmed data defect. No source records have been modified, dropped or imputed.

| Relevant ID | Observed issue | Extent and trace | Technical implication | Possible follow-up | Status / authority |
|---|---|---|---|---|---|
| A07 | Completed project has no corresponding payment log | **239 projects** (Control 56; Test 183 across documented calendar windows). Notebook A07 includes group/period split | Lack of payment log is **not** evidence of unpaid project; any later payment diagnosis must preserve an unknown/no-log case | Check completeness with source owner; consider distinct unknown category in approved metric definitions | Observed; business treatment requires Fernando + Jurandir |
| A06 | Host present in exposure records has no completed project in provided extract | **642 hosts** (Control 338, Test 304) | Excluding them would change the denominator in any later host-based descriptive/experimental view | Preserve in host base; clarify full randomization/recorded-exposure universe | Observed; do not infer churn |
| A08 | `captured_at` missing | **27,672 payment attempt rows**; other columns have no missing value | A missing captured timestamp cannot by itself classify the whole project as unpaid | B09–B17 must inspect attempted status, multiple logs and captures | Expected in principle per PDF; not a proven inconsistency |
| A01–A05 | Key collisions, orphan payments and attribution contradictions | **0 observed** for tested primary keys and relationships | Joins are safe at documented grain in this extract; does not prove event semantics | Continue with B on reviewed base | Checked technically; no relation blocker found |
| V7 | Headless Jupyter kernel instability in analysis environment | 10 cells ran in order in a fresh Python interpreter; a separate full `nbclient` attempt failed with reported `zmq.error.ZMQError: Socket operation on non-socket`, then `DeadKernelError`. Root cause unconfirmed; full raw traceback not retained | Local Jupyter clean-kernel run is **not yet independently validated** | Test Python 3.13 venv locally and rerun all cells | **OPEN — blocks final acceptance, not provisional review** |

**Not investigated in Checkpoint A:** contradictory payment status vs capture timestamps, multiple captures, method sequences, exposure timing relative to project creation, temporal censoring and host cohorts. These are B/C/D/E questions. This register is not a decision log: decisions should be recorded only after explicit approval.
