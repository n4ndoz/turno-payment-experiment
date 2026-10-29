# EDA 0 — C+E anomaly and observability inventory

The following **technical findings** do not authorize silent correction, exclusion, financial outcome labels, causality, or metric eligibility rules. All times are UTC. Sample record IDs and row evidence are inside the notebooks.

| Question | Technical evidence | Grain | Downstream dependency | Status / action |
|---|---|---|---|---|
| C19 | 9 project completion timestamps precede their booking timestamps | completed project | Timestamp validity for future timeline calculations | Open: retain and show examples; no auto-correction |
| C19 | 1,821 capture timestamps are 1–6 seconds earlier than payment-log creation time | payment attempt | Event order; operational interpretation | Open: may be clock/processing semantics; root cause unknown |
| C21/B12 | 156 timestamped capture records precede completion; B12 has 2,316 status/timestamp discordances | payment attempt | Capture definition and timing | Open: retain early captures; do not equate with full settlement |
| C22/E41 | 5,091 experiment-period completions precede first recorded host exposure | completed project | Future analysis population and timing | Open: do not decide treatment/exposure eligibility |
| C23 | 1,252 projects have their D30 deadline on Dec 19, with no proven exact last observation instant | completed project | Candidate 30-day follow-up / censoring | Open: obtain actual event-extraction cutoff and completeness assurance |
| C24 | Manual-flagged payment records can be created during reported Test CS alert incident | payment attempt | Incident attribution | Open: record creation does not date a failure, alert or CS outreach |
| E36 | 836 hosts have zero experiment-window completed projects; 642 have zero across entire file | registered host | Denominators, host activity | Account for all 14,708 registered hosts; do not call these churned |
| E41 | Original randomization roster / technical treatment application not contained in CSVs | host/experiment | ITT claim, treatment integrity | Open: request enrollment and feature-delivery logs |
| E42/E43 | Missing accepted/cancelled project records, complete host lifecycle, amounts and costs | platform / financial | Conversion, settlement and generalizability | Open: require additional sources before causal/business conclusions |
| V7-A/B | Earlier authoring kernels failed with `ZMQError` / `DeadKernelError` | execution environment | Earlier notebook acceptance | OPEN for A/B; not closed by successful C/E kernels |
| V7-C/E | The revised C notebook and E passed clean `nbclient` kernel runs with 10 code cells each | execution environment | Local reproducibility | Passed in authoring environment; independent user-local `.venv` run not yet verified |
