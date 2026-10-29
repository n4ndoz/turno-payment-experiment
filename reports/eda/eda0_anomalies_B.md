# EDA 0 — Checkpoint B: Observed anomalies and unresolved limitations

**Status:** Recorded for technical review. All counts describe the supplied immutable extract; no corrections, imputation, exclusions or business rules were applied.

| ID | Observation and technical evidence | Grain | Technical impact / dependency | Status |
|---|---|---|---|---|
| B12 / V4 | `succeeded` with missing `captured_at`: **239** attempts. Non-success status with populated `captured_at`: **2,077** attempts (**40 declined, 660 failed, 1,377 voided**). **2,316** total discordant attempts / **2,075** affected projects; **595** affected projects also have a concordant attempt. | Attempt; affected project | Future capture definition cannot use a silent field precedence. Requires business-methodology decision. | Open — no source of truth selected |
| B11 / B16 | **652** projects have multiple populated capture rows; **200** have captured fields across multiple payment methods; **154** have 2+ success-status attempts. | Project | Cannot infer amount paid, complementarity or duplicate financial charges. More detailed patterns belong to D. | Open — observational only |
| B16 / A07 | **239** completed projects have no payment-log row. | Project | Preserve in any completed-project universe; not automatically successful or failed. | Open observation gap |
| B13 | **7** hosts tie on the earliest *observed* completed_at; **0** have repeated true flags or flagged projects later than their earliest observed completion. | Host / project | First-ever completion cannot be fully authenticated due to history truncation and missing registration date. | Partially identifiable |
| B14 | **0** exact duplicate log rows or identical non-ID attribute groups; **17,986** attempt records belong to repeated project+method+status groups. | Attempt | Similarity is insufficient to deduplicate; these may be legitimate separate attempts. | Characterized, no deduplication |
| B15 | **1** project has tied `payment_logs.created_at` among attempts. | Project | No arbitrary chronological order; `created_at` may not reflect the underlying financial event time. Further work belongs to D. | Documented |
| B17 | No explicit event type for preauth/reauth/recovery; payment amounts, amount due and CS contact history unavailable. | Operational event | Cannot claim exact authorization/retry path or full financial settlement. | Not directly identifiable |
| V7 | An attempted full Jupyter-kernel run failed with `ZMQError(ENOTSOCK)` then `DeadKernelError`; `nbclient` cleanup raised `AssertionError`. All code cells passed in a fresh non-kernel Python interpreter; outputs were captured and tests passed. | Execution environment | Reproducibility of a **full clean Jupyter kernel execution remains unverified**. Root cause of kernel failure is unknown, even though the immediate socket failure is observed. | **OPEN** — local `.venv` Jupyter Restart & Run All required |

## V7 diagnostic excerpt from the attempted kernel run

```text
[IPKernelApp] ERROR | Exception in message handler:
  File ".../ipykernel/kernelbase.py", line 857, in execute_request
    reply_msg = self.session.send(...)
  File ".../jupyter_client/session.py", line 867, in send
    stream.send_multipart(...)
  File ".../zmq/sugar/socket.py", line 749, in send_multipart
    self.send(...)
zmq.error.ZMQError: Socket operation on non-socket

nbclient.exceptions.DeadKernelError: Kernel died

During kernel cleanup:
  File ".../nbclient/client.py", line 504, in _async_cleanup_kernel
    assert self.km is not None
AssertionError
```

This excerpt is **not the complete raw traceback**. It is a faithful condensed record of the current attempted run. The local execution log `_checkpoint_b_nbclient.log` is supplied separately for technical review, not committed to the repository. The observed exception does not establish that Pandas computations failed; it also does not establish the underlying OS or infrastructure cause.
