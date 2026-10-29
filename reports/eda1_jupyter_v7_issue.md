# EDA 1 — V7 Jupyter clean-kernel execution issue

**Status:** OPEN. The authoring environment's full `nbclient` execution of `payment_reliability_deep_dive.ipynb` failed on 2026-10-29. The recorded kernel stderr included:

```text
[IPKernelApp] ERROR | Exception in message handler:
  File ".../ipykernel/kernelbase.py", line 857, in execute_request
    reply_msg = self.session.send(...)
  File ".../jupyter_client/session.py", line 867, in send
    stream.send_multipart(...)
  File ".../zmq/sugar/socket.py", line 749, in send_multipart
    self.send(...)
zmq.error.ZMQError: Socket operation on non-socket
```

The client-side traceback then reported `nbclient.exceptions.DeadKernelError: Kernel died`; cleanup raised `AssertionError` at `assert self.km is not None` in `nbclient/client.py`. The additional file `eda1_nbclient_failure.log` contains the exact captured client-side cleanup traceback; the kernel excerpt above is transcribed from the contemporaneous execution stderr and is not a full retained raw kernel log. The underlying socket failure cause is not independently established.

**Alternative validation (not a V7 substitute):** all 10 notebook code cells were executed sequentially, without calculation exceptions, in one fresh Python 3.13.5 interpreter and saved with their actual outputs. A second independent analysis used Python `csv.DictReader`/`datetime`. All 88 synthetic tests passed. A clean Jupyter kernel run, preferably inside the user's Python 3.13 `.venv`, remains an acceptance check. Do not infer that other notebooks' past V7 success validates this notebook.
