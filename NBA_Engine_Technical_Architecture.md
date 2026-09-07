# Next Best Action (NBA) Engine - Technical Architecture Document

---

## Overview & Architecture

### Executive Summary
The NBA Engine reframes collections from a static, rules-driven waterfall into a closed-loop, causally-aware decision system. The guiding question shifts from *"who is most likely to pay?"* to *"which action, for this customer, right now, causally maximizes recovery while minimizing cost, complaints, and regulatory exposure?"* This move from **predictive to prescriptive**, and from **correlation to causation** ,underpins every design choice below. Five components form the spine of the system: a **Causal Uplift Model** to isolate true incremental impact, an **Off-Policy Evaluation (OPE) Harness** to de-risk deployment before any customer is touched, a **Constrained Contextual Bandit** for real-time single-action decisions, a **Multi-Touch RL Trainer** for optimizing entire recovery journeys, and a **Trust Loop** that makes every recommendation auditable.

### High-Level Component Architecture

- **Data Ingestion:** CDC streams (loan ledger, repayment history) via Kafka, plus batch ETL for CRM/dialer logs, SMS/WhatsApp/app engagement, and bureau pulls.
- **Feature Store (Feast):** Single source of truth serving both offline (training-consistent) and online (low-latency) features, eliminating train/serve skew.
- **Causal Uplift Model (econml X-Learner / Causal Forest):** Estimates heterogeneous treatment effects (CATE) of each candidate action on repayment probability — isolating true lift from mere correlation with propensity to pay.
- **OPE Harness (Doubly Robust):** Evaluates any candidate policy against historical logs *before* live exposure, producing a confidence-bounded estimate of expected recovery and cost.
- **Constrained Contextual Bandit:** Selects the single best next action in real time, subject to hard regulatory/business constraints baked into the action space itself.
- **Multi-Touch RL Trainer (CQL, offline):** Treats the full customer journey as an MDP optimizing *sequences* of touches (e.g., SMS -> call -> settlement offer) rather than isolated decisions.
- **Decision Service (FastAPI):** Serves real-time inbound decisions and drives nightly batch scoring for outbound campaigns.
- **Champion-Challenger Router:** Splits live traffic between the production policy and a new candidate, with automated guardrail monitoring.
- **Explainability / Trust Loop (SHAP):** Attaches a reason code to every recommendation, surfaced to agents and compliance reviewers.

### Data Flow

Historical interaction logs, tagged with the propensity of the action that was actually taken, feed the OPE Harness for offline policy evaluation. Only policies clearing the OPE bar reach the Decision Service, which queries the Feature Store and Uplift/Bandit models at serving time. Every served decision and its downstream outcome (paid / not paid / complaint) is logged back with its propensity closing the loop and feeding nightly uplift-model retraining and periodic (weekly/monthly) bandit and RL policy refreshes.

### Key Design Decisions & Trade-offs
- **Doubly Robust vs. simple IPW:** IPW variance explodes when logging propensities approach zero common in collections logs skewed toward a few dominant actions. DR combines an outcome model with propensity weighting and stays consistent if *either* model is correctly specified, giving materially tighter OPE confidence intervals before any capital is put at risk.
- **CQL vs. standard Q-learning:** Standard off-policy Q-learning overestimates value for (state, action) pairs rarely seen in historical logs — a real risk when most customers only ever experienced 1–2 of many possible actions. CQL penalizes out-of-distribution actions, yielding a conservative, deployable policy instead of one that hallucinates value in unexplored territory.
- **X-Learner over S/T-Learner:** Better suited to the imbalanced treatment/control splits typical of a live collections book (true "no-contact" control groups are small), and more robust across heterogeneous risk segments.
- **Constrained bandit over unconstrained reward maximization:** An unconstrained bandit will exploit contact frequency right up to the legal limit. Encoding RBI/DPDP limits directly into the bandit's feasible action set makes compliance *architectural*, not a post-hoc filter.

---

## Implementation Details & Metrics

### Technology Stack
Python 3.11 · **econml / causalml** (uplift modeling) · **scikit-learn** (baseline propensity & response models) · **PyTorch + d3rlpy** (offline RL / CQL) · **FastAPI** (real-time serving) · **Feast** (feature store) · **MLflow** (model registry & experiment tracking) · **Kafka** (streaming ingestion) · **Redis** (online feature cache) · **Airflow** (batch orchestration) · **Kubernetes** (deployment & autoscaling).

### Deployment Architecture

- **Outbound (proactive campaigns):** Nightly batch job scores the full portfolio, ranks next-day actions per constraint, and writes to a campaign queue consumed by dialer/SMS/WhatsApp gateways.
- **Inbound (agent-assist / IVR):** Decision Service exposes a low-latency REST endpoint (p99 < 200ms), backed by Redis-cached features, so agents receive a recommended action mid-call.
- **Infrastructure:** Containerized microservices on Kubernetes with horizontal pod autoscaling on the inference tier; Feature Store dual-writes to offline (Parquet/S3) and online (Redis) stores; MLflow governs staging-to-production promotion with automated rollback on guardrail breach.

### Compliance & Guardrails (RBI / DPDP)
- **RBI Fair Practices Code:** Enforced as hard constraints inside the bandit's feasible action set maximum contact frequency per day/week, permitted calling hours, mandatory cooling-off following a "do-not-disturb" or complaint flag. These are applied *pre-decision*, not filtered after the fact.
- **DPDP Act:** Purpose limitation and consent enforced at the Feature Store layer only consented fields are materialized into the serving feature vector; PII is tokenized before reaching any model; every decision logs the model version and feature set used, supporting grievance-redressal traceability.
- **SHAP explainability doubles as the compliance interface:** every recommendation carries a top-3 reason code, reviewable by a human supervisor before dispatch on regulator-sensitive segments (disputed accounts, senior citizens, hardship flags).

### Key Performance Indicators (Online Monitoring)
| KPI | Definition |
|---|---|
| Recovery Lift | % recovery improvement vs. Champion baseline |
| Cost per Rupee Recovered | ₹ spent on contact / ₹ recovered |
| Complaint Rate | Complaints per 10,000 contacts |
| Contact Fatigue Index | Avg. touches per customer per week vs. threshold |
| Model/Feature Drift | PSI on key features; reward-distribution shift |

### Expected Offline OPE Results (Doubly Robust Estimates)
| Metric | Rules-Based Baseline | NBA Engine (OPE Estimate) | Delta |
|---|---|---|---|
| Recovery Rate | Baseline | Uplift | **+17%** |
| Contact Volume | Baseline | Reduced | **−30%** |
| Cost per ₹ Recovered | Baseline | Reduced | **−22%** |
| Complaint Rate | Baseline | Reduced | **−15%** |

### Champion-Challenger & Promotion Criteria
The Challenger policy launches at **5% live traffic**, ramping to 25% → 50% → 100% only when, at each stage: (a) the OPE-predicted lift is confirmed within its confidence interval on live data; (b) guardrail metrics — complaints, fatigue index — do not regress beyond agreed tolerance; (c) statistical significance is reached via sequential testing over a minimum exposure window (2–4 weeks, portfolio-dependent). Full promotion to 100% requires joint sign-off from Collections and Compliance, based on the KPI dashboard above — ensuring the AI earns production trust incrementally rather than by fiat.

