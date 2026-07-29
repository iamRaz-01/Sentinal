# SentinelML — Real-Time Fraud Scoring System

> An ML *systems* engineering project: the model is intentionally simple. The point is everything around it — serving, monitoring, drift detection, and CI/CD.

---

## Problem Statement

Card-not-present fraud costs merchants **$4.61 for every $1 actually lost to fraud**, once chargeback fees, operational overhead, and customer churn are counted (LexisNexis Risk Solutions, 2026). Static, rule-based fraud filters (`IF amount > ₹50,000 THEN flag`) can't keep pace with shifting spend patterns — they either miss new fraud patterns or over-block legitimate customers, and nobody notices the degradation until losses spike.

Global e-commerce fraud losses reached **$48B in 2025** (up 16% YoY, Juniper Research) and are projected to hit $107B by 2029. The bottleneck isn't model accuracy — a gradient-boosted classifier gets you to ~95% AUC on a weekend. The bottleneck is:

- Scoring a transaction in **under ~100ms**, at volume
- Keeping the feature pipeline **identical** between training and serving (the #1 source of production ML bugs)
- Detecting when incoming transactions **drift** from the training distribution before losses show up in the numbers
- Retraining and redeploying **without downtime or manual babysitting**

This project builds that system, not just a classifier.

---

## Architecture

```
                                   ┌─────────────────┐
                                   │   GitHub Actions │
                                   │   CI/CD Pipeline │
                                   └────────┬─────────┘
                                            │ test → build → push → deploy
                                            ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────────┐
│  Transaction  │────▶│   FastAPI     │────▶│  Model Registry   │
│  (client/sim) │     │  Serving API  │◀────│    (MLflow)        │
└──────────────┘     └──────┬───────┘     └──────────────────┘
                             │
                 ┌───────────┼───────────┐
                 ▼           ▼           ▼
         ┌───────────┐ ┌───────────┐ ┌───────────┐
         │ Prediction │ │  Feature  │ │  Logging  │
         │  + Reason  │ │  Store    │ │  (drift   │
         │   Codes    │ │           │ │  reference)│
         └───────────┘ └───────────┘ └─────┬─────┘
                                            ▼
                                  ┌───────────────────┐
                                  │  Drift Monitor Job  │
                                  │ (scheduled, compares │
                                  │  live vs. training)  │
                                  └─────────┬───────────┘
                                            ▼
                                  ┌───────────────────┐
                                  │ Prometheus + Grafana│
                                  │   Dashboard + Alert │
                                  └─────────┬───────────┘
                                            ▼
                                  ┌───────────────────┐
                                  │   Slack Webhook     │
                                  │ "Drift detected —    │
                                  │  retrain recommended"│
                                  └───────────────────┘
```

**Design principle:** the serving layer talks to models through a registry interface, not a hardcoded model file — so a second risk model (loan default, AML) could be added later without touching the API contract. This project ships one model; the interface supports more.

---

## Tech Stack

| Layer | Tool | Why |
|---|---|---|
| Model | scikit-learn / XGBoost | Intentionally simple — accuracy isn't the point |
| Serving | FastAPI | Async, typed, fast to containerize |
| Model registry | MLflow | Versioning, not just a pickled file in a repo |
| Containerization | Docker | Separate images for training job vs. serving API |
| CI/CD | GitHub Actions | test → build → push → deploy on merge |
| Deployment | Railway / Fly.io | Real live endpoint, not just local code |
| Monitoring | Prometheus + Grafana | Latency, error rate, prediction distribution |
| Drift detection | Custom job (population stability index) | Compares live feature distribution to training baseline |
| Alerting | Slack webhook | Notifies when drift crosses threshold |
| Dataset | [Kaggle Credit Card Fraud / IEEE-CIS Fraud Detection] | Public, well-known — the system is the differentiator, not the data |

---

## Project Structure

```
sentinelml/
├── api/                  # FastAPI serving app
│   ├── main.py
│   ├── model_registry.py # Abstract interface — swap models without touching API
│   └── schemas.py
├── training/             # Training pipeline (separate Docker image)
│   ├── train.py
│   └── features.py
├── monitoring/
│   ├── drift_check.py    # Scheduled job, PSI/KS-test against baseline
│   └── alert.py          # Slack webhook
├── infra/
│   ├── Dockerfile.api
│   ├── Dockerfile.train
│   └── docker-compose.yml
├── .github/workflows/
│   └── ci-cd.yml
├── dashboards/
│   └── grafana-dashboard.json
└── README.md
```

---

## Roadmap

- [ ] **Stage 1 — Core API:** FastAPI service returning fraud probability + top contributing features (reason codes), backed by MLflow-registered model
- [ ] **Stage 2 — CI/CD:** Dockerize training + serving separately; GitHub Actions pipeline builds, tests, and deploys on merge to `main`
- [ ] **Stage 3 — Observability:** Prometheus metrics + Grafana dashboard (latency, throughput, prediction distribution); drift-detection job with Slack alerting
- [ ] **Stage 4 — Architecture proof:** Document (with diagram) how a second model would plug into the registry interface without changing the serving contract

---

## Running Locally

```bash
# Clone and set up
git clone https://github.com/iamRaz-01/sentinelml.git
cd sentinelml

# Start the full stack (API + monitoring)
docker compose up --build

# API available at http://localhost:8000/docs
# Grafana dashboard at http://localhost:3000
```

---

## What This Project Demonstrates

- Serving ML models behind a real, versioned API — not a notebook
- Separating training and serving concerns cleanly (different Docker images, shared feature logic)
- Production monitoring: knowing when a model is silently degrading, not just when it was trained
- CI/CD discipline applied to ML artifacts, not just application code
- System design that anticipates growth (multi-model registry) without over-building for a v1

---

## License

MIT
