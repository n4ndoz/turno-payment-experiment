# EDA 0 — Checkpoint B: Question and validation coverage

**Scope:** B09–B17 only; technical evidence, not causal analysis or financial metrics. Each question's procedure, results, validation and limitation appear in the notebook heading indicated below.

| ID | Notebook | Technical status | Main verification | Unresolved boundary |
|---|---|---|---|---|
| B09 | `01_B_conceptual_integrity.ipynb` §B09 | Answered for source nullness | Source count = null + non-null; direct count alternative | Cannot interpret a missing capture as unpaid project |
| B10 | Same notebook §B10 | Answered for source domains/formats | Category frequencies and derived timestamp parse checks | Meaning of events not encoded |
| B11 | Same notebook §B11 | Answered for observed attempts | Grouped capture/success totals equal raw attempts | Financial complementarity and duplicate charge unknown |
| B12 | Same notebook §B12 | Answered for field discrepancies | Full crosstab, raw masks, method totals, V8 CSV scan | Source-of-truth decision pending |
| B13 | Same notebook §B13 | Partially answerable | Flag/project and flag/host total checks | Historical first completion not directly verifiable |
| B14 | Same notebook §B14 | Answered for source duplicates | Row uniqueness; no-ID group frequency reconciliation | Similar attempts may be legitimate retries |
| B15 | Same notebook §B15 | Partially answerable | Status sets + no-logs = completed projects; tie audit | Operational event chronology unknown |
| B16 | Same notebook §B16 | Answered for observations, financial meaning limited | 279,847 project partition; raw attempt counts; V8 project-set CSV scan | No definitive capture success rate; ambiguous/no-log cases retained |
| B17 | Same notebook §B17 | Partially answerable | Direct/indirect/missing-field matrix for nine events | Incomplete operational and financial fields |

**V6:** synthetic test modules `tests/test_foundation_a.py` and `tests/test_foundation_b.py`; 23 checks. **V7:** OPEN — non-kernel sequential run succeeded but kernel execution failed (`ZMQError` / `DeadKernelError`). **V8:** separate standard-library `csv.DictReader` cross-check of B12/B16. No new business metrics or acceptance rules were imposed.
