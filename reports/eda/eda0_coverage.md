# EDA 0 — checkpoint coverage matrix

**Scope delivered now:** A01–A08 only. Technical evidence has been executed and saved; **local clean Jupyter kernel validation remains OPEN** for all eight questions. The status "answered" below therefore means *technical results available for review*, not that the checkpoint is formally accepted.

| ID | Notebook | Technical status | Primary evidence / validation | Outstanding |
|---|---|---|---|---|
| A01 | `00_A_structure.ipynb` § A01 | Answered provisionally | Source fingerprints, shape/key count reconciling | Local clean-kernel pass |
| A02 | Same § A02 | Answered provisionally | Repeated keys vs extra occurrences vs full-row duplicates; independent value counts | Local clean-kernel pass |
| A03 | Same § A03 | Answered provisionally | Guarded join cardinalities, groupby host conflicts, zero row multiplication | Local clean-kernel pass |
| A04 | Same § A04 | Answered provisionally | Exposure anti-join vs set difference | Local clean-kernel pass |
| A05 | Same § A05 | Answered provisionally | Project/host payment linkage and partition reconciling to logs | Local clean-kernel pass |
| A06 | Same § A06 | Answered provisionally | Registered-host zero/one/multiple buckets; project sums | Local clean-kernel pass |
| A07 | Same § A07 | Answered provisionally | Zero-log projects and attempts reconciled by period, group and set difference | Interpretation reserved; local clean-kernel pass |
| A08 | Same § A08 | Answered provisionally | 16-field dictionary, null/domain/date parse diagnostics | Business semantic validation reserved; local clean-kernel pass |

**B09–B17, C18–C24, D25–D34, E35–E43:** intentionally **not implemented or revalidated** under this contract. They remain pending future approved checkpoints. No other notebook in the previous unapproved local prototype is part of this review package.
