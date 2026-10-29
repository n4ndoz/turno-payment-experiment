# EDA 0 — Checkpoint E: Experimental population and coverage (E35–E43)

**Status:** Checkpoint E committed to `analysis/eda0-data-foundation` after explicit authorization; approved for technical review without analytical changes. No PR, KPI, causal estimator or superiority comparison. This checkpoint follows C but retains C23's final-observation-day ambiguity. Counts cover the registered-host population only.

## Reproduction and grain

- Notebook: `notebooks/00_data_foundation/04_E_population_coverage.ipynb` (nine explicit E headings with Python, real outputs, Plotly histogram and boxplot, tests and limitations).
- Raw source fingerprints and Python 3.13 setup match Checkpoint C and previous A/B checkpoints. All 14,708 unique hosts registered in `experiment_exposures` are retained, including zero completions.
- Baseline = `[2025-07-18 00:00Z, 2025-08-18 00:00Z)`; experiment completion window = `[2025-08-18 00:00Z, 2025-11-20 00:00Z)`. These are diagnostic calendar-day bounds; recorded host first exposure can occur *after* a project was completed within the experiment window.

## Observed results

| ID | Evidence | Validation and interpretation boundary | Technical status |
|---|---|---|---|
| E35 | Registered hosts: **7,377 Control**, **7,331 Test**; full-extract projects: 137,586 Control and 142,261 Test; experiment-period completions: 98,855 Control, 102,447 Test. Exposure-month cohorts are displayed. | Group hosts total 14,708, full projects total 279,847 and experiment completions total 201,302; no assignment-to-randomization inference. | Answered for registered records |
| E36 | **836** registered hosts have *zero experiment-period completions* (439 Control; 397 Test); **642** have zero projects in the entire available extract. The difference is **194** with baseline-only completions. | Left join starts from registered hosts; zero/one/multiple categories and project sums reconcile. | Answered for documented windows |
| E37 | **2,755** true first-completion flags, all on distinct hosts; no repeated true flags and no flagged project later than the earliest observed completion; **7** hosts have earliest-observed completion ties. **11,948** hosts have two or more experiment-window completions. | Flag and host/project counts reconciled; pre-baseline history absent. First historical completion does not establish signup date or new customer status. | Partially answerable |
| E38 | Presence matrix: **10,090** hosts in both baseline and experiment, **194** only baseline, **3,782** only experiment, **642** neither. | Four exclusive cells total 14,708; 78,545 baseline + 201,302 experiment projects total 279,847. No inference about signup from baseline absence. | Answered for observed coverage |
| E39 | Potential days from `first_exposed_at` to `2025-11-20T00:00:00Z`: median **87.07 days Control**, **86.91 days Test**; none negative or missing. Plotly histograms and boxplots saved in notebook. | Hosts/period-cohort totals reconciled; elapsed time is not cleaning demand nor actual delivered treatment. No exposure-normalized frequency produced. | Observable with limitations |
| E40 | Monthly exposure-cohort coverage and numbers of zero, one, multiple completions provided by registered group, with distinct follow-up opportunities. | Monthly categories reconcile to hosts and projects; descriptive distributions are not estimates of treatment effects. | Answered descriptively |
| E41 | Registered hosts and **recorded** first-exposure timestamps are identifiable. Original randomization roster/instant and technical treatment delivery are not. | Direct schema-to-concept evidence matrix. Cannot declare the original study population an intention-to-treat sample without additional logs. | Partially answerable |
| E42 | Extract covers registered experiment hosts, their completed marketplace projects and recorded payment attempts. Missing: broader Turno population, accepted/rejected/cancelled projects, full host lifecycle, external market information. | Populations grounded in available fields; no external generalizability claim. | Partially answerable |
| E43 | Preliminary answerability matrix covers 13 relevant candidate concepts, from host completion counts to recoveries, acceptance, churn and financial settlement. | Each row identifies fields, limitations and additional data needed; **not** a final business metric/estimand decision. | Answered as technical matrix |

### Baseline × experiment registered-host presence

| | Experiment: none | Experiment: at least one | Total |
|---|---:|---:|---:|
| Baseline: none | 642 | 3,782 | 4,424 |
| Baseline: at least one | 194 | 10,090 | 10,284 |
| **Total** | **836** | **13,872** | **14,708** |

## Important dependency for population eligibility

Checkpoint C identified **5,091 completed assignments during the experiment that precede the host's first recorded exposure**, including Control 2,573 and Test 2,518. This is **not** proof of a randomization flaw; assignment and exposure timing are not independently audited. It **does** mean that denominators based merely on calendar dates differ from a hypothetical *post-first-exposure* subset. No segmentation or post-exposure eligibility rule was approved in this checkpoint.

## Validation and governance

- **V1/V3/V8:** host and project partitions independently reconciled with `csv.DictReader` in `tests/check_ce_source_reconciliations.py`: 14,708 registered hosts; baseline/expt totals; 836 no experiment completion; 642 neither; 194 baseline only; 10,090 both; 3,782 experiment only.
- **V2:** project-to-host join is validated many-to-one and preserves projects, while the zero-project host population is retained.
- **V5:** all recorded first exposures and completion boundaries are handled in UTC, inclusive start and exclusive end.
- **V6:** synthetic tests cover zero activity, boundary completions and orphan/duplicate host/project keys; combined A+B+C/E suite is **36/36 passing**.
- **V7 (E): passed in the current author's Python 3.13.5 Jupyter kernel via `nbclient`**, 10 code cells and saved outputs. The user's local Python 3.13 `.venv` still requires an independent Restart & Run All. Historical A/B V7 remains OPEN.

**Pending Fernando/Jurandir decisions, deliberately not taken here:** original randomized/ITT population; treatment timing; pre-first-exposure project inclusion; eligible observation windows; capture hierarchy (B12); and any KPI, causal estimator or business recommendation. No Checkpoint D implementation is authorized.
