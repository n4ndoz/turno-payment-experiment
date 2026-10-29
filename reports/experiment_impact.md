# Turno — Experimental Impact | Sprint 1

**Status:** Committed to the Foundation branch after explicit approval for Fernando and Jurandir's technical review; **not merged, no final product recommendation**. Repository base: `analysis/eda0-data-foundation`, approved Checkpoint D commit `13c67f1`. Python 3.13.5. All source data remain immutable.

## A. Executive Results Table

**Comparison:** Test − Control among *registered hosts*, not verified intention-to-treat (the exposure register is not demonstrated to contain the complete original randomized population). Host is the allocation and bootstrap unit. **M1/M4/M5 prioritized.** All estimates below cover completions in `[2025-08-18T00:00:00Z, 2025-11-20T00:00:00Z)` and preserve all 14,708 registered hosts, including 836 with no experimental completions.

| Candidate metric | Control | Test | Test − Control (95% cluster-bootstrap CI) | Relative difference | Unit / denominator |
|---|---:|---:|---:|---:|---|
| **M1 · completed projects per host** | 13.4004 | 13.9745 | **+0.5741** [−0.3322, +1.5983] | +4.28% | projects / registered host |
| M2 · first-ever completions per host | 0.1361 | 0.1509 | +0.0148 [+0.0033, +0.0255] | +10.85% | flagged historical first completions / registered host |
| M3 · hosts with ≥2 observed completions | 80.751% | 81.722% | +0.971 percentage points [−0.308, +2.275 pp] | +1.20% | hosts / registered hosts |
| **M4 · projects with observed capture by D14 per host** | 13.3275 | 13.8849 | **+0.5574** [−0.3426, +1.5620] | +4.18% | projects / registered host |
| **M5 · projects without observed capture by D14 per host** | 0.0729 | 0.0896 | **+0.0167** [−0.0127, +0.0429] | +22.89% | projects / registered host |
| M6 · D14 capture among completed projects | 99.4558% | 99.3587% | −0.0971 percentage points [−0.2877, +0.1169 pp] | −0.098% | captured projects / completed projects |

**Denominators:** Control = **7,377 registered hosts / 98,855 completed projects**; Test = **7,331 hosts / 102,447 completed projects**. M1–M5 use all registered hosts in their group. M6 is the ratio of project totals, **not** an unweighted mean of host-specific rates; its bootstrap resamples each host's captured-project numerator and completed-project denominator **jointly**.

**Inference:** 2,000 independent-in-group host bootstrap draws, seed `20261029`, percentile 95% CI for Test − Control. Each draw preserves within-host project clustering; all 2,000 replicates had valid project denominators. These are exploratory intervals without multiple-hypothesis correction. An interval containing zero **does not prove equality, noninferiority or absence of effect**. The registered-population and recorded-exposure limitations must be considered before attributing contrasts causally.

**Main takeaway:** Test is associated with **more observed completions and more projects captured by D14 per registered host at the point estimate**, but the 95% intervals for M1 and M4 include zero. M5 is higher in Test at the point estimate, also with an interval crossing zero. These findings do not establish either a causal benefit or a financial-loss increase. M2 has a positive unadjusted interval, but is not a measure of host acquisition and is part of a family of exploratory comparisons.

## B. Payment Reliability

### D14 reconciliation and identifiable outcomes

| Completed-project evidence | Control | Test | Total |
|---|---:|---:|---:|
| Completed projects | 98,855 | 102,447 | **201,302** |
| First recorded capture timestamp ≤ completion + 14 elapsed days | 98,317 | 101,790 | **200,107** |
| No capture timestamp observed by D14 | 538 | 657 | **1,195** |
| Capture timestamp before project completion (diagnostic subset of captured) | 63 | 38 | **101** |

**Identity:** Per host, `completed = captured_D14 + not_captured_D14`; after group aggregation, **M1 = M4 + M5** to floating-point precision. The 1,195-project remainder means **no timestamp observed by D14**, not failed billing, nonpayment, loss, or zero eventual collection. Projects with no payment logs and inconsistent status/timestamp evidence are retained.

**D14 coverage:** Every experiment completion's deadline precedes **2025-12-19 00:00:00 UTC** (latest possible D14 deadline: **2025-12-03 23:59:58 UTC**), so all experiment projects are **conservatively eligible** under the documented continuous-follow-up assumption. This does **not independently prove completeness of the extracted financial event records**. Records with a capture before project completion are counted by the rule and identified separately. The operative timestamp is `captured_at`, never `payment_logs.created_at`.

### Speed of observed capture (candidate elapsed-time horizons)

| Window | Eligible Control / Test projects | Captured Control | Captured Test | Test − Control rate | Host-cluster bootstrap 95% CI |
|---|---|---:|---:|---:|---:|
| **D1** | 98,855 / 102,447 | 98.8336% | 98.1034% | **−0.7302 pp** | **[−1.1220, −0.3322] pp** |
| D7 | 98,855 / 102,447 | 99.3829% | 99.2201% | −0.1629 pp | [−0.3813, +0.0910] pp |
| D14 | 98,855 / 102,447 | 99.4558% | 99.3587% | −0.0971 pp | [−0.2877, +0.1169] pp |
| D30 | **98,239 / 101,811** | 99.5033% | 99.4264% | −0.0769 pp | [−0.2381, +0.0867] pp |

The **D1 gap is more negative for Test** and its exploratory cluster-bootstrap interval excludes zero; its interpretation is *timing of recorded capture*, not proof of loss. D7/D14/D30 differences are less pronounced, with intervals crossing zero. **D30 excludes 616 Control and 636 Test projects** (1,252 total) whose D30 deadline lands on 2025-12-19, because the exact final observation time that day is not documented. D30 therefore has a **different project denominator**, and direct cross-horizon change is not a same-cohort time-to-event estimate. The 196 projects with some eventual captured timestamp but none by D14 remain in the D14 not-observed complement.

### Identification boundaries

The CSVs cannot verify the amount due, partial payment, financial settlement, true operation-level retries/recoveries, or every Customer Support intervention. A `succeeded` status is not guaranteed to match `captured_at`; C/D previously recorded status/timestamp discordances. The outcome is **observed capture timing**, not cash collection or a ledger balance. M6 conditions on completed projects, which may be affected by the experiment, so the comparison does **not** identify a financial effect for a fixed underlying project cohort.

## C. Host Behavior

| Registered-host behavior | Control | Test |
|---|---:|---:|
| Registered hosts | 7,377 | 7,331 |
| Zero observed experiment completions | 439 | 397 |
| Hosts with ≥2 experiment completions | 5,957 | 5,991 |
| Projects flagged historical first-ever completion within experiment | 1,004 | 1,106 |
| Hosts with source-flagged first completion and later observed completion | 684 / 1,004 | 742 / 1,106 |
| Conditional descriptive repeat share of these flagged hosts | 68.13% | 67.09% |

M2 and M3 unadjusted intervals are in the executive table. M2 is the source's `is_first_completed_project` flag per host, not entry into the marketplace. The first-to-later count is observed within the extract, and is **not** a valid causal comparison of conversion among first completers, because first completion itself can be treatment-dependent and historical coverage is incomplete. No claims about true retention, churn or acceptance can be drawn from these files.

## D. Robustness

### S1 — Candidate capture evidence (untimed project classification)

| Criterion applied to completed experiment projects (no D14 timing) | Control projects / project share | Test projects / project share | Test − Control project-share contrast |
|---|---:|---:|---:|
| Any populated `captured_at` | 98,405 / 99.5448% | 101,898 / 99.4641% | −0.0807 pp |
| Any attempt `payment_status = succeeded` | 97,948 / 99.0825% | 101,372 / 98.9507% | −0.1318 pp |
| Both on **one attempt** | 97,880 / 99.0137% | 101,319 / 98.8989% | −0.1148 pp |

**Membership sensitivity:** 483 Control and 538 Test projects (**1,021 total**) differ under status versus timestamp; 525 Control and 579 Test (**1,104 total**) differ under timestamp versus same-attempt concordance. A further **88 Control and 108 Test projects** have a timestamp observed eventually but not by D14. **Status-only classifications cannot be called D14 captures**: `succeeded` without `captured_at` does not locate a capture instant. These results are *measurement sensitivity*, not alternative financial-settlement truth or causal policy effects.

### S2 — Recorded exposure chronology

- **5,091** experiment-completed projects precede host `first_exposed_at`: **2,573 Control** and **2,518 Test**. These projects **remain in the main analysis**.
- A further **65,294** projects were booked before recorded exposure and completed after it: **32,299 Control**, **32,995 Test**. These also remain included.
- The restricted *post-recorded-exposure* subset, displayed descriptively only, changes Test − Control M1 to **+0.5794** projects/host (main +0.5741), M4 to **+0.5641** (main +0.5574), and M5 to **+0.0153** (main +0.0167). Registered hosts remain denominators, but the subset is **not causally equivalent** to main.
- Potential host observation from recorded exposure to experiment end averages **75.584 days Control** vs **75.334 days Test** (median **87.073** vs **86.912**). Time observed does not equal availability for cleaning projects, nor verify randomization or treatment application.

### S3 — CS incident completed-project exclusion

The primary analysis includes the **entire experiment**. A symmetric diagnostic exclusion removes **14,974 Control** and **15,486 Test** projects completed in `[2025-09-17 00:00 UTC, 2025-10-01 00:00 UTC)`, retaining the full **7,377 / 7,331 host denominators**.

| Metric | Full-period Test − Control | Without incident completions, Test − Control (95% host-bootstrap CI) |
|---|---:|---:|
| M1 projects/host | +0.5741 | +0.4915 [−0.2667, +1.3489] |
| M4 captured D14 projects/host | +0.5574 | +0.4774 [−0.2793, +1.3345] |
| M5 no observed D14 capture projects/host | +0.0167 | +0.0140 [−0.0119, +0.0384] |
| M6 project capture rate | −0.0971 pp | −0.0953 pp [−0.3011, +0.1319 pp] |

The directions of these contrasts are unchanged. **The exclusion changes the observed completion period; it is not the counterfactual experiment without the incident.** `created_at` is not substituted for the unobserved failure-alert time, and a missing manual attempt does not establish missing CS intervention.

### S4 — Baseline completed projects per host (HC3)

Pre-experiment activity is defined as completed projects in `[2025-07-18, 2025-08-18)` per **registered host**, including zero counts. Mean baseline completions: **5.2502 Control** and **5.4309 Test**. The host-level adjusted OLS is `outcome ~ Test + baseline completed projects`, with **HC3** robust standard errors (14,708 hosts):

| Outcome | Unadjusted Test − Control | Baseline-adjusted Test coefficient (95% HC3 CI) |
|---|---:|---:|
| M1 projects/host | +0.5741 | **+0.1742** [−0.2048, +0.5532] |
| M4 captured D14 projects/host | +0.5574 | **+0.1604** [−0.2198, +0.5405] |
| M5 no D14 capture projects/host | +0.0167 | **+0.0138** [−0.0142, +0.0418] |

Baseline adjustment substantially attenuates the activity and captured-project contrasts; the adjusted intervals still include zero. This is **not difference-in-differences** or a remedy for missing randomization records.

Descriptive strata: baseline-zero hosts = **2,177 Control, 2,247 Test**; baseline-positive hosts = **5,200 Control, 5,084 Test**. Within baseline-zero hosts, Test − Control M1 is **−0.0646** projects/host; within baseline-positive hosts it is **+1.0698**. M4 is **−0.0945** vs **+1.0586**, respectively. This is not an interaction significance test, and zero baseline completion does not prove a newly acquired host. No further exploratory segments were created.

## E. Decision Evidence and Original Case Questions

**Q1. Did Test increase completions per host?** The M1 point contrast is +0.5741, bootstrap 95% CI [−0.3322, +1.5983]. Baseline-adjusted +0.1742, HC3 CI [−0.2048, +0.5532]. **Not a robustly established improvement** on these intervals, and attenuated by baseline adjustment.

**Q2. Did first-ever completions and repeat observations improve?** M2 +0.0148 per host, CI [+0.0033, +0.0255] without multiplicity adjustment. M3 +0.971 pp, CI [−0.308, +2.275 pp]. These do not identify host acquisition, retention or first-to-second causal conversion. Descriptive first-flagged repeat shares were 68.13% Control and 67.09% Test.

**Q3. Were more completed projects captured by D14 per host?** M4 point contrast +0.5574, CI [−0.3426, +1.5620]; baseline adjusted +0.1604, CI [−0.2198, +0.5405]. **Evidence of a positive point contrast, not a firmly established difference.**

**Q4. Did the count without observed D14 capture increase?** M5 +0.0167 projects/host, CI [−0.0127, +0.0429]. The observed count is higher in Test, but direction is statistically uncertain and **not a monetary loss metric**.

**Q5. Did proportional D14 capture reliability worsen?** M6 Test − Control = −0.0971 pp, CI [−0.2877, +0.1169 pp], with full host-clustered joint numerator/denominator bootstrap. A worse proportional capture rate is not established by this interval. Completed-project conditioning creates post-treatment selection concerns.

**Q6. Did capture speed differ?** At D1, Test's observed-capture rate is **0.7302 pp lower**, CI [−1.1220, −0.3322 pp]. Later horizon contrasts diminish and include zero. This is a timing-of-recorded-capture finding, **not proof of delayed settlement**; interval families are exploratory.

**Q7. Which sensitivities matter?** The baseline adjustment materially reduces the M1/M4 point differences. Recorded-exposure filtering changes the estimand and leaves their sign similar. Excluding incident completions changes the period but not their sign or main uncertainty. Capture-evidence choice changes **1,021 or 1,104** project memberships across the experimental population; status-only rules cannot be assigned a D14 time. The D30 denominator differs and its cutoff remains uncertain for 1,252 projects.

**Q8. What remains unidentifiable?** Project acceptance (the data contain completed projects, not requests/acceptance opportunities), amount owed, cash amounts settled or outstanding, authorization/re-authorization operations, fully reconstructed retries and CS contacts/alerts, original complete randomized cohort, technical start of treatment per project, and the counterfactual incident-free policy effect.

**For human decision makers:** Gains (point estimates): M1/M4, source-flagged M2. Risks/qualifications: lower D1 observed capture rate; M5 point estimate higher; M6 conditional selection; alternative capture evidence; baseline adjustment; incomplete treatment timing and original randomization population. The trade-off cannot be reduced to a verified cash-loss-versus-volume comparison from this dataset. **No Ship, Kill or Modified Ship conclusion is made here.**

## Validation and Reproducibility

- **Input invariants:** 14,708 registered hosts (7,377/7,331); 279,847 source projects; 306,957 attempts; all project/host/log keys checked before joins. Experiment = 201,302 completed projects (98,855/102,447). One project row per `assignment_id`; source CSVs are not edited.
- **Per-host identities:** All zero-activity hosts present; `completed = captured_D14 + not_captured_D14`; group totals reconcile to **200,107** captured by D14 and **1,195** without D14 timestamps. M6 ratios use those exact counts.
- **Candidate windows:** UTC elapsed durations and conservative documented cutoff; D1/D7/D14 complete under stated premise; D30 1,252 uncertain projects withheld from its denominator. No period inferred from `payment_logs.created_at`.
- **Uncertainty:** Host-grain group-stratified bootstrap, `n=2,000`, seed `20261029`; joint numerator/denominator for ratios; HC3 adjusted regressions. All primary and horizon bootstrap replicates had valid denominators on real data.
- **Synthetic tests:** 13 Sprint 1 tests added; **65 total pytest tests passed** with existing foundation tests. Handles empty hosts, no logs, incompatible statuses, captures before completion, source orphans, tied time boundaries, D30 last-day censoring, seeded bootstraps, incident filters and baseline OLS.
- **Independent cross-check:** `python tests/check_experiment_source_reconciliations.py` reads original CSVs via Python `csv.DictReader` + `datetime` only (no Pandas or shared source functions). All key controls and experiment D1/D7/D14/D30/group counts match, including zero-completion hosts and exposure chronology.
- **Jupyter V7 for Sprint 1:** 11/11 code cells **executed in a fresh Jupyter kernel** on Python 3.13.5, `nbclient`, with real outputs saved and no errors. This does **not retroactively validate A/B V7**; a clean run inside the user's own Python 3.13 `.venv` is still to be checked.
- **Figures:** Two decision-relevant plots (metric-contrast intervals and cumulative observed-capture rate). No decorative third plot.
- **Git:** Sprint 1 was explicitly authorized and committed to the Foundation branch for review; **no PR or merge is authorized**. Existing A/B/C/E/D notebooks and shared EDA 0 modules are untouched. Changes comprise one Sprint notebook, report, small reusable helper, synthetic tests, independent audit script, and necessary `pyproject.toml`/README dependency documentation.

**Reproduction from the project root:** with original CSVs in `data/raw/`, Python 3.13, `python -m pip install -e '.[dev]'`, `python -m pytest -q`, `python tests/check_experiment_source_reconciliations.py`, and **Restart Kernel and Run All Cells** on `notebooks/01_experiment/experiment_impact.ipynb`.
