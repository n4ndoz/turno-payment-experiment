# EDA 1 — Payment Reliability & Experiment Impact

**Status:** Committed to `analysis/eda1-experiment-impact` for technical review after explicit approval. **No PR or merge has been performed.** All calculations use immutable source CSVs and the approved EDA 0 + Sprint 1 base (`84e25e5`). Python 3.13.5.

## A. Executive Summary

**Main conclusion on observed capture timing.** Test has **more mean restricted hours without a recorded capture** per completed project at D7 (+0.648 h, 95% host-bootstrap CI [+0.123, +1.140]), D14 (+0.841 h, CI [−0.075, +1.662]) and D30 (+1.221 h, CI [−0.387, +2.704]). The D7 interval is wholly positive; the longer-horizon intervals include zero. The D1 captured-project share is lower in Test by −0.730 percentage points, CI [−1.122, −0.332] pp. These exploratory, completed-project-conditioned contrasts are **not proof of full payment settlement or a causal effect on a fixed cohort of projects**.

**RMST D7, D14 and D30 — elapsed hours without observed capture, Test − Control:**

| Cohort and horizon | Control (h) | Test (h) | Difference (h) | 95% cluster bootstrap CI (h) | Projects C / T |
|---|---:|---:|---:|---|---|
| RMST D7 | 1.489 | 2.137 | +0.648 | [+0.123, +1.140] hours | 98,855 / 102,447 |
| RMST D14 | 2.452 | 3.293 | +0.841 | [-0.075, +1.662] hours | 98,855 / 102,447 |
| RMST D30 | 4.436 | 5.657 | +1.221 | [-0.387, +2.704] hours | 98,239 / 101,811 |
| RMST D7 (D30 cohort) | 1.488 | 2.140 | +0.652 | [+0.123, +1.147] hours | 98,239 / 101,811 |
| RMST D14 (D30 cohort) | 2.452 | 3.300 | +0.848 | [-0.071, +1.669] hours | 98,239 / 101,811 |

D7 and D14 use the full documented experiment-completion cohort (**201,302 projects, 98,855 Control / 102,447 Test**). D30 conservatively restricts to **200,050 projects (98,239 / 101,811)** because the final extraction **hour** on December 19, 2025 is unknown. The same 200,050 projects are used for the D7 and D14 **common-D30-cohort** rows; those contrasts hardly move. No right-censoring time has been inferred from the last observed payment event.

**Robustness of D1:** the negative Test − Control capture-rate contrast remains across the specified diagnostic scenarios, including symmetric exclusion of incident completions, requiring same-attempt status/capture concordance, and exclusion of discordance-affected projects. Each restriction changes the project denominator and must not be mistaken for a causal correction.

**Payment friction:** a completed-project record of at least one `failed`/`declined` attempt appears in **2,988 / 98,855 Control projects (3.023%)** and **2,967 / 102,447 Test projects (2.896%)**. Control records show more declined card attempts, but attempts and payment-method use can be influenced by the policy; within-method comparisons are descriptive. A card failure/decline plus capture on an alternate method is observed in **583 Control / 358 Test** projects, but voluntary switching and proven financial recovery are not identifiable.

**Decision boundary:** the data cannot verify amount owed, collection completeness, original randomization inventory, exact treatment timing, or all CS alerts/interventions. No Ship/Kill/Modified Ship recommendation is made. No unplanned exploratory segment or significance-driven horizon selection was performed.

## B. Continuous Capture Analysis

**Definition:** the earliest non-null `payment_logs.captured_at` in UTC is associated to the completed project; the clock starts at `assignments.completed_at`. A capture preceding completion (101 experiment projects) remains flagged but contributes as t=0. Exact boundary events at 24, 168, 336 and 720 hours count **on** the boundary. A project with no capture timestamp in a fully observed candidate window contributes the entire horizon to restricted uncaptured time. The presence of a timestamp does not prove that the full amount due was settled.

Two figures in the executed notebook show (1) the empirical, cumulative D0–D30 capture fraction in the **common D30 conservatively covered cohort**, and (2) a zoom of the first 24 hours. A Kaplan–Meier estimator is **not** automatically applied: the available data do not establish the exact individual censoring time of the last-day projects. These are empirical curves on the cohort with a documented complete candidate window, conditional on the stated continuous-followup premise.

**Discrete capture rates and reconciliation against Sprint 1:**

| Horizon | Control captured / denominator | Test captured / denominator | Control rate | Test rate | Test − Control |
|---|---:|---:|---:|---:|---:|
| D1 | 97,702 / 98,855 | 100,504 / 102,447 | 98.834% | 98.103% | -0.730 pp |
| D7 | 98,245 / 98,855 | 101,648 / 102,447 | 99.383% | 99.220% | -0.163 pp |
| D14 | 98,317 / 98,855 | 101,790 / 102,447 | 99.456% | 99.359% | -0.097 pp |
| D30 | 97,751 / 98,239 | 101,227 / 101,811 | 99.503% | 99.426% | -0.077 pp |

These numerators/denominators exactly reproduce the D1, D7, D14 and conservative-D30 figures in the approved Sprint 1. The curve at the same landmarks agrees exactly when it uses **the same D30 cohort**; unrestricted D7/D14 and the D30-cohort curve have different denominators, which the notebook never silently mixes.

**RMST construction and statistical uncertainty:** D7/14/30 restrict the signed capture-to-completion time to t≥0 and upper bounds of 168/336/720 hours. An uncaptured project contributes the full restriction limit. RMST equals the exact integral of the uncaptured survival fraction over the horizon for full-followup records; the notebook checks this identity independently of the direct project-wise formula. Project totals and host-cluster bootstrap ratios are computed jointly. `n=2,000` seeded (`20261029`) stratified bootstrap draws resample **hosts**, retaining all their completed projects; 95% intervals are percentile differences Test − Control. The cluster rather than project is the reamplifying unit. There is no multiple-testing adjustment and a CI including zero is not evidence of equivalence.

**D30 cutoff sensitivity:** the 1,252 projects with D30 deadlines on the final calendar day comprise **616 Control / 636 Test**. Among these, 613 / 634 have a recorded capture by D30; the remaining 3 / 2 have none by D30, but the precise censorship instant is not known. A deliberately **unverified** complete-last-day assumption on the full 201,302 projects produces Control **4.435 h**, Test **5.643 h**, difference **+1.208 h**, CI **[−0.396, +2.675] h**. The conservative comparison is +1.221 h [−0.387, +2.704]. Similar point estimates do **not** establish that the final-day coverage was complete or validate formal censoring-based inference.

## C. D1 Robustness

| Scenario | Control D1 | Test D1 | Test − Control | 95% cluster CI | Projects C / T | Excluded total |
|---|---:|---:|---:|---|---|---:|
| Main timestamp | 98.834% | 98.103% | -0.730 pp | [-1.122, -0.332] pp | 98,855 / 102,447 | 0 |
| Exclude incident completion | 98.827% | 98.084% | -0.743 pp | [-1.139, -0.339] pp | 83,881 / 86,961 | 30,460 |
| Concordant capture | 98.134% | 97.435% | -0.699 pp | [-1.130, -0.235] pp | 98,855 / 102,447 | 0 |
| Exclude discordant projects | 98.852% | 98.137% | -0.715 pp | [-1.109, -0.329] pp | 98,100 / 101,630 | 1,572 |

**Incident definition:** UTC `[2025-09-17 00:00, 2025-10-01 00:00)`. Excluding *completions* during the incident removes 30,460 projects, symmetrically by calendar rule (14,974 Control / 15,486 Test). Separately, the **D1 post-completion interval** overlaps this incident for **32,288 projects**; **1,828 projects (921 / 907)** have a completion *outside* the incident but a D1 window spanning it. These are time-window overlaps, not observed CS alerts or failures, and excluding the incident is not an incident-free causal counterfactual.

**Capture evidence disagreements:** B found 2,316 discordant attempts across the full extract. Within the *experimental-completion* cohort only, **1,760 attempts** affect **1,572 distinct projects**: Control 864 attempts / 755 projects; Test 896 attempts / 817 projects. Comparing discordant non-success timestamps with successful-and-timestamped attempts within the *same project*, **0 projects** have an exact timestamp match and **421 projects** have a distinct timestamp comparison. Neither finding proves separate financial transactions or data artifacts. Other projects lack an appropriate concordant capture timestamp to compare; flags and contradictory events remain intact in the primary analysis.

The concordant-capture scenario requires `payment_status=succeeded` and a populated `captured_at` **on the same attempt** before D1, not a fabricated time for status-only success. The isolation scenario removes discordance-affected projects solely for diagnostic sensitivity and is not a valid replacement estimand by itself.

## D. Payment Friction

**Denominators:** attempts for status distribution by method; distinct projects with at least one log of the method for project-method flags; **all completed experiment projects** for overall project friction. All categories are supplied as observed (`card`, `bank_account`, `credits`; `succeeded`, `failed`, `declined`, `voided`). Voids are **not** combined with failed or declined. The baseline comparison uses `assignments.completed_at`, not `payment_logs.created_at`. No attempt is silently repaired, removed or deduplicated.

**Experiment-period attempt status by method:**

| Group | Method | Attempts | Failed | Declined | Failed or declined | Voided | Succeeded | Failed/declined % of attempts |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Control | bank_account | 36,420 | 616 | 12 | 628 | 2,824 | 32,968 | 1.72% |
| Control | card | 75,460 | 0 | 7,750 | 7,750 | 2,868 | 64,842 | 10.27% |
| Control | credits | 203 | 0 | 0 | 0 | 16 | 187 | 0.00% |
| Test | bank_account | 35,435 | 475 | 5 | 480 | 945 | 34,010 | 1.35% |
| Test | card | 73,299 | 1 | 4,767 | 4,768 | 1,316 | 67,215 | 6.50% |
| Test | credits | 266 | 0 | 0 | 0 | 66 | 200 | 0.00% |

**Project-level diagnostics, experiment period:**

| Group | Completed projects | With ≥1 failed or declined | Rate | Multiple methods | Multiple attempts |
|---|---:|---:|---:|---:|---:|
| Control | 98,855 | 2,988 | 3.023% | 1,330 | 5,778 |
| Test | 102,447 | 2,967 | 2.896% | 1,224 | 4,332 |

The method-specific **project table** and separate baseline attempt/project tables are preserved in the notebook, with `projects_failed`, `projects_declined`, `projects_failed_or_declined` and `projects_capture_flag`. Project-method counts overlap when a project used more than one method; they must not be summed as mutually exclusive. Differences in card declines and bank-account voids may reflect policy/process or method mix, but cannot isolate host payment friction, satisfaction, or within-method causal effects.

## E. Mixed-Method Journeys

A project is a candidate if it has a `failed`/`declined` card attempt and at least one alternative-method log. Destination counts are **project-method pairs**; combined project counts deduplicate within group. Captured timestamps on alternative method logs are directly observed, not proof that the card failure caused a later recovery.

| Group | Alternative method | Card fail + alternative projects | Alt `succeeded` | Alt capture timestamp | Alt earliest log created after card-fail log | Before |
|---|---|---:|---:|---:|---:|---:|---:|
| Control | bank_account | 604 | 487 | 579 | 212 | 392 |
| Control | credits | 5 | 4 | 4 | 4 | 1 |
| Test | bank_account | 403 | 291 | 354 | 159 | 244 |
| Test | credits | 5 | 4 | 4 | 4 | 1 |

**Unique combined totals:** Control **607** projects with card fail + alternative-method log, **583** with capture on an alternative method; Test **407**, **358** respectively. They represent 0.5898% vs 0.3494% of completed projects for the alt-capture pattern, not a comparable conditional causal recovery rate. `created_at` determines only the ordering of **records**, not the actual failure, host preference, or settlement. Credits and bank account may both occur in the same project.

## F. Decision Implications

1. **Is the Test associated with more time without recorded capture?** Yes at point estimate D7/D14/D30; the D7 cluster-bootstrap interval is positive, but D14/D30 are less precisely estimated and cross zero. The completed-project cohort is post-treatment selected.
2. **Is the gap early or persistent?** The D1 cumulative capture gap is −0.730 pp; the gap narrows by D7 and D14. RMST differences accumulate positively as elapsed restricted time increases, but longer-horizon uncertainty widens.
3. **Do D7, D14 and D30 imply different conclusions?** D7 has a positive 95% interval; D14/D30 do not establish a difference. Do not choose a horizon to optimize significance.
4. **Does the conclusion depend on censoring?** For D30 the cutoff is uncertain for 1,252 last-day projects; conservative and assumed-complete-last-day estimates are numerically similar, but the latter is explicitly unverifiable. D7/D14 common-cohort comparisons show little denominator-composition impact. No KM inference can be justified without identifiable censoring times.
5. **Does D1 survive robustness checks?** All four prespecified point estimates are negative, with their exploratory host-bootstrap intervals below zero; none rules out selection/measurement concerns.
6. **Is friction or method use different?** Attempt-level card decline share and project-level failed/declined share differ descriptively. Card-failure and alternative-method capture patterns are also different, but method is possibly affected by the treatment, and journeys are not fully reconstructed.
7. **Does EDA 1 change Sprint 1?** It substantiates the early-capture delay and shows the D7 restricted mean contrast; it does not overturn the uncertainty surrounding host-level activity and D14 captured-project volume or provide a verified dollar loss. Sprint 1 outputs were not changed.
8. **What is unidentifiable?** Monetary amount due/paid, partial/complete settlement, actual authorizations and reauthorizations, true failure/recovery times, voluntary host method migration, complete CS interventions, original randomization assignment ledger, exact treatment implementation, exact final data extraction instant, and incident-free counterfactual effects.

**Human review required:** Determine whether this evidence changes an executive Ship/Kill/Modified Ship judgment, whether reliability margins are required, which candidate outcome definition to approve, and how to handle the non-verified randomization/treatment timing. No autonomous product recommendation is included.

## Validation and Reproducibility

- **Source invariants:** 14,708 registered hosts; 279,847 completed projects in provided extract, 306,957 payment attempts; experiment cohort 201,302 projects. Secure host/project/attempt joins reuse approved Sprint 1 functions, no raw modifications, and preserve projects without payment logs and those completed before recorded exposure.
- **Capture & temporal logic:** one earliest timestamp per project or missing; pre-completion timestamps handled at t=0 with signed flags preserved; exact elapsed-hour boundaries included. D7 and D14 conservatively inside documented horizon for all projects; D30 excludes final-day-uncertain cases for primary RMST. No non-observed censoring times imputed.
- **Curve and RMST checks:** cumulative D30-cohort curve equals discrete D1/D7/D14/D30 counts on that same cohort; full-cohort D1/D7/D14 counts exactly equal approved Sprint 1; RMST direct project calculation equals exact area under uncaptured survival curve for each fully covered cohort.
- **Uncertainty:** `n=2,000` stratified bootstrap host resamples, seed `20261029`, cluster-level joint numerator/denominator; the group project-weighted contrasts are conditional on completed projects, not randomized-host policy ITT.
- **Synthetic tests:** **88/88 passed** on Python 3.13.5 (65 prior A–E/Sprint 1 + 23 EDA 1), covering precompletion, t=0, D1/D7/D14/D30 exact boundaries, immediately-after events, missing capture, D30 final-day uncertainty, status disagreement and same/distinct timestamps, alternate methods, host-bootstrap determinism, denominator preservation and empirical-curve reconciliation.
- **Independent cross-check:** `python tests/check_eda1_source_reconciliations.py` reads the original CSVs with Python `csv.DictReader` and `datetime`, without Pandas or analysis helpers, and matches group project counts, D1/D7/D14/D30 capture counts, D7/D14/D30 RMST point means including common-cohort rows, financial-status discordances, friction and alternative-method capture patterns.
- **Jupyter V7: OPEN for this notebook in the authoring environment.** An attempted full Jupyter/`nbclient` clean-kernel run failed with `zmq.error.ZMQError: Socket operation on non-socket` and `DeadKernelError`, followed by `AssertionError` in kernel cleanup. The notebook’s **10 code cells were executed sequentially in one clean Python interpreter**, without calculation exceptions; their tabular and Matplotlib outputs were saved. This alternative execution is **not** a clean Jupyter-kernel success. The full error traceback and local Python 3.13 virtual-environment verification remain pending. Earlier Sprint 1/C/D/E Jupyter passes do not validate this notebook by inheritance.
- **Repository governance:** GitHub branch `analysis/eda1-experiment-impact` was created from approved Sprint 1 commit `84e25e5`; EDA 1 analysis changes were committed after explicit authorization. No PR, merge, source-data change, KPI selection, or executive product recommendation.

**Reproduce from project root:** put unchanged original `experiment_exposures.csv`, `assignments.csv`, and `payment_logs.csv` in `data/raw/`; create local Python 3.13 `.venv`; run `python -m pip install -e ".[dev]"`, `python -m pytest -q`, `python tests/check_eda1_source_reconciliations.py`, then **Restart Kernel and Run All Cells** in `notebooks/02_eda1/payment_reliability_deep_dive.ipynb`. Preserve the Jupyter traceback if the same kernel failure recurs.
