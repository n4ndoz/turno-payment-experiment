# Turno — Final Inferential Validation

**Status:** Approved for commit and integration into `main` after technical review. Built on the approved EDA 1 branch `analysis/eda1-experiment-impact` at `a4a8523`. Python 3.13.5. All source CSVs and previously approved analytical modules/notebooks remain unchanged.

## 1. Final evidence — four decision contrasts

All estimates are **Test minus Control**. M1/M2/M4 use all **7,377 registered Control** and **7,331 registered Test** hosts (including activity zeros). D1 compares captured-within-24h project counts / completed project counts, *not* unweighted host capture rates. Observed capture is not verified full settlement.

| Measure | Control | Test | Raw difference [95% host-bootstrap CI] | Baseline-adjusted difference [95% HC3 CI] | Permutation p (two-sided) | Holm p |
|---|---:|---:|---|---|---:|---:|
| **M1 — completed projects / registered host** | 13.4004 | 13.9745 | **+0.5741** [−0.3322, +1.5983] | **+0.1742** [−0.2048, +0.5532] | 0.2542 | 0.5084 |
| **M2 — flagged historical first completions / registered host** | 0.1361 | 0.1509 | **+0.01477** [+0.00335, +0.02550] | **+0.01564** [+0.00450, +0.02678] | 0.0112 | 0.0337 |
| **M4 — projects with captured timestamp by D14 / registered host** | 13.3275 | 13.8849 | **+0.5574** [−0.3426, +1.5620] | **+0.1604** [−0.2198, +0.5405] | 0.2649 | 0.5084 |
| **D1 — project capture observed by 24h (project share)** | 98.8336% | 98.1034% | **−0.7302 pp** [−1.1220, −0.3322] | Not fitted; see baseline D1 below | 0.00025 | 0.00100 |

**Uncertainty methods.** Raw CIs: existing validated Sprint 1 host-stratified percentile bootstrap (2,000 replicates, seed `20261029`) for M1/M2/M4, independently reconciled with its previously saved outputs; D1 is reproduced in the same paired-period host bootstrap using 2,000 draws. Adjusted estimates: host-level OLS of each outcome on recorded Test indicator plus **baseline project-completion count**, with HC3 robust 95% CIs. All registered hosts remain. Conditional adjustment does not imply a difference-in-differences model. D1 has **no forced regression adjustment**: it conditions on projects that may themselves be affected by treatment, and a simple host-level OLS would silently change project weighting.

**Permutation:** 4,000 two-sided host-label permutations, preserving the observed group sizes; M1/M2/M4 use group mean differences and D1 recomputes the project-weighted capture ratios by reassigning **whole host** numerator/denominator bundles. Plus-one Monte Carlo p correction (minimum possible p `1/4001 ≈ 0.00025`). The original assignment mechanism, possible stratification and selection into the exposure register **cannot be reconstructed**. Thus the permutation p-values are **conditional checks assuming exchangeability of the registered labels**, not a proven reproduction of Turno's randomization distribution. The Holm family was assembled **after reviewing the outcomes**; adjusted p-values do not retroactively establish a preregistered confirmatory analysis.

## 2. Was the D1 disadvantage already present at baseline?

**Yes, directionally.** D1 is captured by `completed_at + 24 elapsed hours` using the first non-null `captured_at`; both periods are defined by UTC project **completion**, not payment-log creation.

| Period or comparison | Control captured / completed | Test captured / completed | Control | Test | Test − Control [95% host-bootstrap CI] |
|---|---:|---:|---:|---:|---|
| Baseline `[2025-07-18, 2025-08-18)` | 38,321 / 38,731 | 39,170 / 39,814 | 98.9414% | 98.3825% | **−0.5589 pp** [−1.5081, +0.1923] |
| Experiment `[2025-08-18, 2025-11-20)` | 97,702 / 98,855 | 100,504 / 102,447 | 98.8336% | 98.1034% | **−0.7302 pp** [−1.1220, −0.3322] |
| **Experiment contrast minus baseline contrast** | — | — | — | — | **−0.1713 pp** [−0.7130, +0.5838] |

The paired bootstrap preserves each host's baseline and experiment numerator/denominator in the **same** draw. Baseline contributors: **5,200 Control** hosts and **5,084 Test** hosts with at least one baseline completion; all **14,708 registered hosts** remain in the re-sampling frame. All baseline and experiment D1 deadlines fit within the documented follow-up window.

The baseline interval includes zero, but that is **not proof of balance**. The direction of the D1 gap predates the experiment, and the contrast change interval includes zero. Consequently, it is **not defensible to attribute the entire observed experimental D1 difference to removal of preauthorization**, nor to claim the incremental gap is established. This historical comparison is **not automatically causal difference-in-differences**, because parallel trends and exact original assignment were not verified.

## 3. Multiplicity and alternative inference

Within the four **retrospectively selected** decision contrasts, M2 and D1 remain below 0.05 after the Holm step-down procedure **under the registered-label exchangeability assumption**. M1 and M4 do not. The permutation directions match the previous bootstrap estimates, and host-level HC3 adjustment retains M2's positive sign and an interval above zero. **However, M2 is a source-flagged first historical *completion*, not proof of platform-new hosts or acquired customers.** D1 remains a project-conditioned timing measure, with a pre-existing negative baseline contrast.

No interval including zero is treated as equivalence, a noninferiority demonstration or evidence of no effect. Additional exploratory horizons (D7/D14/D30), RMSTs and subgroups remain outside this narrow Holm family. The family selection and possible correlated outcomes require cautious interpretation.

## 4. Are the activity contrasts driven by very active hosts?

**The raw M1 difference is materially tail-sensitive.** The following distribution includes zero-activity hosts and uses completed projects **during the experiment**.

| Host-level diagnostic | Control | Test |
|---|---:|---:|
| Registered hosts | 7,377 | 7,331 |
| Total completed projects | 98,855 | 102,447 |
| Mean projects / host | 13.400 | 13.974 |
| Median | 7 | 7 |
| P75 / P90 | 16 / 28 | 16 / 28 |
| P95 | 42 | 43 |
| P99 | 112.24 | 111.70 |
| Maximum | 548 | 1,311 |
| Share of completed projects from the 74 most active hosts (**top ~1%**) | **14.29%** | **18.01%** |

**One deliberately symmetric diagnostic:** cap the *observed post-treatment count* at the **pooled P99 = 112 projects** for **each host in both groups** (no host dropped). The contrast changes from **+0.5741** to **−0.0203 projects per host**. The diagnostic is based on a potentially treatment-affected outcome; it changes the measure and **cannot replace the primary host-level causal comparison or establish a fixed top-activity subgroup**. It does demonstrate that the raw positive mean is not representative of a uniform shift throughout the host distribution. Baseline HC3 adjustment independently reduces M1 to +0.1742 with a CI crossing zero; M4 behaves similarly.

## 5. Implications for the decision (no product recommendation)

1. **D1 baseline:** a similar negative direction existed before the experiment, weakening any claim that the full −0.730 pp post-period difference was induced by the policy. The within-registered-host baseline-vs-experiment contrast change is imprecisely estimated.
2. **M2 activation signal:** the positive association is compatible with the host-level bootstrap, HC3 baseline adjustment and conditional permutation test even after Holm. It remains exploratory and does not establish new-customer acquisition.
3. **M1/M4 overall gains:** point estimates are positive but not robustly different from zero; baseline adjustment shrinks them substantially. M1 is strongly influenced by a small number of high-volume hosts.
4. **Alternative inference:** conditional permutation broadly agrees with previous uncertainty assessment. It does not validate undocumented randomization details.
5. **Still unknown:** underlying fully randomized population, original assignment/stratification, actual financial settlement and money amounts, application of treatment to every project, and a causal D1 effect on a fixed set of projects. Project completion and payment method may be post-treatment quantities.
6. **Defensible statement:** among *registered* groups, an exploratory positive first-completion signal exists and a negative D1 observed-capture contrast exists; neither should be relabeled as a validated causal change in acquisition or financial loss. M1/M4 benefits and the incremental D1 difference remain uncertain.

No Ship/Kill/Modified Ship recommendation or further exploratory modeling has been made.

## 6. Reproducibility and scope audit

- **Notebook:** `notebooks/02_eda1/inferential_validation.ipynb`. Executed from a **fresh Jupyter kernel** with Python 3.13.5: **6/6 code cells passed**, with saved outputs. This V7 verification is scoped to this new notebook; the historical EDA 1 notebook's V7 issue is still open.
- **New helper:** `src/inferential_validation.py`; focused synthetic checks `tests/test_inferential_validation.py`. No legacy notebook or analytical helper is modified.
- **Tests:** **96/96** pytest tests passed across the current project (including **8 new synthetic tests**); the new functions cover paired-period host resampling, fixed-seed permutation, Holm adjustment, HC3 handling of zero-project hosts, common tail cap and coverage guards.
- **Independent audit:** the notebook's `csv.DictReader` and `datetime` check rebuilt earliest capture timestamps and baseline/experiment D1 counts directly from unmodified original CSVs; all **four period × group numerators and denominators** matched the Pandas-based results. Previous Sprint 1 raw M1/M2/M4 effects reproduced exactly, without reimplementing its validated logic.
- **Source invariants:** 14,708 registered hosts (7,377 Control; 7,331 Test), 279,847 completed-project rows, 306,957 payment attempts; 78,545 baseline completions and 201,302 experimental completions. Hosts with zero experiment completions are retained (836).
- **No data edits, final business-metric decision or product recommendation.** Repository publication and integration into `main` were explicitly authorized after technical review. This is the final requested inferential check, not a new EDA.
