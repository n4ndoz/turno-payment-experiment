# Turno — Final Decision-Oriented Analytical Checks

**Scope:** Last, narrowly scoped supplement to the approved EDA 0, Sprint 1, EDA 1 and final inferential validation. **Branch for review:** `analysis/eda1-experiment-impact`, at approved commit `4f28d1d` (already included in the merged `main`). **Status:** Complete for technical review and explicitly approved for publication to the repository and integration into `main`. No new KPI, eligibility change, causal retention inference or product recommendation. Python 3.13.5.

## A. M2 Chronology

**Question:** Is the exploratory positive signal in source-flagged historical first completions robust to their order relative to the first *recorded* host exposure?

| M2 event classification | Control | Test | Test − Control |
|---|---:|---:|---:|
| Registered hosts (fixed denominator) | 7,377 | 7,331 | — |
| Flagged first completions during experiment, **original M2** | 1,004 | 1,106 | +1.4767 percentage points |
| Flagged events before `first_exposed_at` | 26 (2.59% of flagged) | 27 (2.44% of flagged) | — |
| Flagged events at/after `first_exposed_at` | 978 | 1,079 | — |
| **Recorded post-exposure chronology sensitivity per registered host** | **13.2574%** | **14.7183%** | **+1.4609 pp** |

The 53 earlier-than-exposure first-completion events are **2.51%** of the 2,110 flagged first completions during the experiment. The descriptive Test-minus-Control signal changes by **−0.0159 pp**, preserving its sign and essentially its magnitude. **M2 remains the original all-registered-host measure.** This diagnostic does not approve excluding pre-exposure projects from a causal estimand: `first_exposed_at` is neither documented randomization nor verified policy-application time. Exposure recording times differ across hosts; differing observation opportunity remains unresolved. No project was deleted, and projects booked before recorded exposure remain in the analysis.

The previously reported M2 bootstrap, baseline-adjusted and retrospective-family Holm results remain unchanged; no significance test was newly applied to the chronology-filtered subset.

## B. Second-Project Behavior

**Previously approved M3, reconciled only:** Control **5,957 / 7,377 = 80.751%** and Test **5,991 / 7,331 = 81.721%** of registered hosts completed at least two experiment projects. The previously reported Test-minus-Control contrast was approximately +0.971 pp (95% host-bootstrap CI [−0.308, +2.275] pp). **M3 is not the 30-day second-completion rate below.**

**New conditional descriptive measure:** *Second Completion Within 30 Days of First-Ever Completion*. The eligible first project is source-flagged `is_first_completed_project = true` and completed during `[2025-08-18, 2025-11-20)` UTC. Require the exact **first completion + 30 days to be strictly before `2025-11-20 00:00 UTC`**. The right end of the experiment-completion window is exclusive; treating a first completion on October 21 as fully followed would incorrectly assume events at or beyond the boundary. This is conservative regarding final-day observation and assumes the documented completion window itself is complete. The latest eligible first completion occurred **2025-10-20 23:19:30 UTC**.

| Conditional second-completion measure | Control | Test |
|---|---:|---:|
| Flagged experiment first completions (original M2) | 1,004 | 1,106 |
| Hosts with strictly complete 30-day follow-up | **730** | **822** |
| Eligible hosts with a distinct **strictly later** completion by D30 inclusive | **489** | **566** |
| **Second-completion fraction of eligible hosts** | **66.99%** | **68.86%** |
| Earliest subsequent completed project **booked before** the first completion | 269 | 291 |
| Earliest subsequent completed project **booked exactly at** the first completion | 0 | 0 |
| Earliest subsequent completed project **booked after** the first completion | 220 | 275 |

The **descriptive** Test-minus-Control difference is **+1.87 pp**, with no newly requested test or confidence interval. Of the 2,110 flagged experiment first events, **1,552 qualify** for full 30-day completion follow-up and **558 do not**. One eligible host had another project with the **same completion timestamp** as the flagged first: this does **not** count as a strictly later second project. Across all 2,755 flagged first completions (baseline and experiment), **two hosts** had a tied completion for a distinct project; **none** had an observed *earlier* completed project. Both conditions were retained and documented; distinct `assignment_id` values and deterministic chronological ordering were enforced.

This is **not randomized retention or first-to-second conversion**. The cohort depends on completing a first-ever project, which can be influenced by treatment; the right-truncated 30-day eligibility also changes composition. A booking recorded before the first completion is not evidence of a subsequent return decision. The data exclude canceled and never-completed bookings and do not establish longer-term loyalty.

## C. D1 Baseline Adjustment — Conditional Sensitivity

The optional check was technically viable as a **single host-level WLS regression**. Each host contributes at most one row, with the response equal to experiment projects with an observed capture timestamp by D1 divided by experiment completed projects. WLS weights are **experiment completed-project counts**, preserving the project's contribution to the aggregate D1 rate. Model predictors are Test indicator and **`log1p(baseline completed-project count)`**. The sole adjustment variable is based strictly on pre-experimental *completions*. In particular, **baseline payment D1 outcomes are deliberately not used** as adjustment variables, since 24-hour payment windows for projects completed on the last baseline day could extend after the experiment began. No unobserved host-specific baseline capture rate was imputed.

| D1 outcome among experiment-completed projects | Test − Control |
|---|---:|
| **Unadjusted, project-weighted D1 capture rate** | **−0.7302 pp** |
| **WLS baseline-activity-adjusted Test coefficient, HC3 95% CI** | **−0.7645 pp [−1.1770, −0.3520]** |

The WLS includes **13,872 hosts with experiment completions**, weighted by their number of projects; **836 registered hosts with zero experiment completions** remain in the source frame but necessarily have zero weight in a project-conditioned rate. **4,424 registered hosts** have zero baseline completed projects; their baseline-count covariate is a genuine zero, not a fabricated capture rate. The method uses one independent row per host with HC3 heteroskedasticity-robust covariance, so projects are not treated as independent observations. The treatment coefficient is a **common-slope, conditional linear association among observed completed projects**, not ITT or a fixed-project-set causal effect; post-treatment completion volume is itself potentially treatment-affected. Sensitivity to functional form and host weights remains possible.

**Interpretation:** this narrowly justified baseline-activity adjustment does not remove or reverse the negative observed D1 contrast. It is **not** causal difference-in-differences and does not establish policy-induced financial loss. The baseline D1 gap (previously −0.5589 pp) and descriptive contrast change (previously −0.1713 pp, CI spanning zero) remain important qualifications. No additional models or tests were added.

## D. Payment Risk in Business Units (Existing Estimates)

The following values are directly **reused** from the earlier approved capture-horizon reports; they were not reestimated here.

| Capture deadline | Additional projects with **no observed capture** per 1,000 completed projects, Test relative to Control |
|---|---:|
| D1 | **+7.30** |
| D7 | **+1.63** |
| D14 | **+0.97** |
| D30 | **+0.77** |

D30 uses the previously defined **conservatively complete-coverage subset**, not the same exact cohort as D1/D7/D14. These are differences in observed project-capture rates, **not monetary losses, delinquency, or proof of missing settlement**. The previously approved symmetric exclusion of **30,460** incident-period completed projects did not remove the negative D1 contrast (approximately −0.730 pp overall versus −0.743 pp excluding incident completions). This was **not** rerun and is not a valid counterfactual for an experiment without the incident.

## E. Final Reproducibility

- New executable notebook with saved code and outputs: `notebooks/02_eda1/final_decision_checks.ipynb`; **6/6 code cells** passed in a **fresh Python 3.13.5 Jupyter kernel** using `nbclient` (V7 **PASS for this new notebook only**). Existing EDA 1 payment-reliability notebook's historical V7 failure remains explicitly open.
- New minimal helper: `src/final_decision_checks.py`; new synthetic tests: `tests/test_final_decision_checks.py`. **106/106** tests passed across the reconstructed approved project snapshot (**10 new** checks, 96 existing). Code and documentation are in English.
- Independent `csv.DictReader` / standard-library `datetime` audit in the notebook reproduced **M2 26/978 and 27/1,079 chronological counts**, and the **730/489 and 822/566** eligible/second-event counts and all subsequent booking splits, without calling the new Pandas implementations.
- Previously approved M3 was reconciled at host granularity with **5,957 Control and 5,991 Test** two-plus-completion hosts, without rerunning its inferential analysis. D1 unadjusted difference exactly reproduces the prior value; the adjusted WLS is a new sensitivity, not a revision of an approved metric.
- Project/host/attempt counts: **14,708** registered hosts, **279,847** completed projects, **306,957** payment attempts, **201,302** experiment completions. No join multiplication or silent project drop. The three raw CSV SHA-256 fingerprints match the previously approved source fingerprints; no source data were changed or included in the review archive.
- All earlier modules, notebooks and reports are preserved; the analytical supplement creates **four new files only**, with a separate README navigation update. A Git-compatible incremental diff was supplied for technical review. Publication and main integration were explicitly approved subsequently.

## F. Decision Implications

1. **Is positive M2 chronologically consistent?** **Yes, descriptively.** Restriction to at/after recorded exposure changes +1.4767 pp to +1.4609 pp, without changing the sign. It is not a proof of causal activation or first-time customer acquisition.
2. **Is there evidence of continuity?** Among the 30-day-complete, first-completion-selected hosts, **489/730 (67.0%) Control** and **566/822 (68.9%) Test** complete another project, but **269** and **291**, respectively, had booked that second project before the first completion. Neither a booking made after completion nor a second completed project establishes randomized retention.
3. **Does D1 adjustment alter the interpretation?** The simple activity-only, project-weighted adjustment gives **−0.7645 pp** versus **−0.7302 pp** raw, with a negative HC3 interval. It does not overcome the baseline negative gap, project-selection concerns or unknown settlement.
4. **Does any new result require revising the executive story?** M2's chronology does not materially weaken the exploratory signal. Conditional second-completion behavior is a useful business description but not a causal guardrail. The narrowly defensible D1 adjustment does not dismiss the observed early capture gap. The older M1/M4 fragility, extreme-host sensitivity and D30 follow-up caveat remain unchanged.
5. **What must remain on the slides?** Registered versus fully randomized population; timestamped capture versus settled money; first recorded exposure versus actual assignment/application time; selected first-completion cohort; complete 30-day follow-up; the pre-existing D1 gap; pre-booked projects; and unresolved historical Jupyter validation caveats. No Ship/Kill/Modified Ship decision has been selected.