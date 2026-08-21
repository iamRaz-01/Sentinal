# AI-Powered Fraud Detection & Investigation Support System
### Project Documentation 

---

## Project Title

**"An AI-Powered Fraud Detection and Investigation Support System using Transaction-Level Machine Learning and Graph-Based Network Intelligence"**

---

## 2. Abstract (Draft)

Financial institutions process a high volume of transactions, a small fraction of which are fraudulent. Manual, transaction-by-transaction review by fraud analysts does not scale, and rule-based alerting systems tend to generate large numbers of false positives, increasing analyst workload without improving detection quality.

This project proposes a fraud detection and investigation support system in which a machine learning model (XGBoost) performs automated first-level risk scoring on incoming transactions. Transactions exceeding a configured risk threshold are flagged and surfaced to a Fraud Analyst through a risk-prioritized dashboard. The analyst reviews transaction details and the model's risk score, investigates further as needed, and records a final decision — Fraud, Legitimate, or Escalate. The system does not automate fraud decisions; it reduces analyst workload by performing the initial screening and prioritization that would otherwise be done manually.

The MVP is scoped to transaction-level detection only. A planned extension (Phase 2) introduces graph-based network intelligence via a Graph Neural Network (GNN) to detect coordinated, multi-account fraud patterns that transaction-level models cannot see in isolation.

---

## 3. Problem Statement

Fraud analysts at financial institutions are responsible for reviewing transactions flagged as potentially suspicious. As transaction volume grows, manual review becomes a bottleneck: analysts spend significant time on transactions that turn out to be legitimate, while genuinely high-risk transactions may not be reviewed promptly due to queue volume.

**The problem:** there is no automated first-level screening step that reliably prioritizes which transactions deserve an analyst's limited time, nor a consistent way to present the reasoning behind a risk flag so the analyst can investigate efficiently.

---

## 4. Objectives

1. Automatically calculate a fraud risk score for each incoming transaction using a trained ML model.
2. Flag transactions exceeding a configured risk threshold for analyst review.
3. Present flagged transactions to the analyst in a risk-ranked dashboard, so high-risk items are reviewed first.
4. Provide sufficient transaction detail and risk reasoning for the analyst to investigate without needing to query raw data separately.
5. Allow the analyst to record a final decision (Fraud / Legitimate / Escalate), keeping the analyst as the authoritative decision-maker.
6. Design the system architecture and database so that network-level fraud-ring detection (GNN) can be added in Phase 2 without redesigning the core system.

---

## 5. Scope

### In Scope — MVP 
- Transaction ingestion (batch or simulated stream) and risk scoring via XGBoost
- Threshold-based flagging
- Risk-ranked analyst dashboard
- Transaction detail view with risk score and top contributing risk factors
- Analyst decision recording (Fraud / Legitimate / Escalate)

### Phase 2 
- Account/transaction graph construction
- GNN-based network risk scoring (fraud-ring detection)
- Combined transaction + network risk score
- Connected-account view on the transaction detail screen

### Phase 3 
- Real-time streaming infrastructure (Kafka)
- Multi-analyst workload coordination (claim/ownership, SLA tracking)
- Feedback loop for model retraining from analyst decisions
- Management/reporting dashboards (fraud-dollar totals, model accuracy trends)

### Explicitly Out of Scope
- Real bank/UPI transaction data (regulatory restriction — public/synthetic datasets used instead, stated openly)
- Automated transaction blocking (system flags and informs; it never decides or acts on the analyst's behalf)

*Reviewer note:* Phase 3 items were present in earlier drafts (KPI strip, ownership chips, SLA aging) and have been deliberately excluded from the MVP — they solve coordination problems that don't exist for a single-analyst academic demo, and would consume build time without supporting FR-01–04.

---

## 6. Literature Survey

| System | Type | Relevant Technique | Gap / Difference from This Project |
|---|---|---|---|
| Stripe Radar | Production, proprietary | Large-scale ML scoring across network transaction data | Closed system; internals not inspectable or reusable for academic study |
| Feedzai | Enterprise platform | "WhiteBox Scoring" for explainable, regulator-facing risk scores | Closed-source, enterprise-only; validates that explainability is an industry-standard requirement, not an add-on |
| Typical academic/Kaggle fraud projects | Notebook-based | Binary classification on public datasets (e.g., ULB Credit Card Fraud) | Commonly report accuracy on an imbalanced dataset (misleading), stop at the notebook stage — no analyst-facing system, no explainability layer, no decision workflow |

**Identified gap this project addresses academically:** most public/academic fraud-detection work treats the task as a pure classification problem and stops at a trained model. This project treats it as an **analyst workflow support system** — scoring is only the first step; the deliverable is the decision-support loop around it (dashboard, explanation, decision recording), which is closer to how production systems like Feedzai are actually structured.

---

## 7. Tools & Technologies

| Layer | Choice | Reasoning |
|---|---|---|
| Transaction-level ML | XGBoost | Standard, well-documented, strong baseline for tabular imbalanced classification; fast to train and serve |
| Explainability | SHAP | Produces the top contributing factors needed for FR-03's risk reasoning, without requiring a separate model |
| Network intelligence (Phase 2) | PyTorch Geometric (GNN) | Only introduced when Phase 2 begins; not a Week 1–2 dependency |
| Backend/API | FastAPI | Lightweight, fast to build a scoring + dashboard-data endpoint; async-friendly for later real-time work |
| Database | PostgreSQL | Relational integrity for transactions/accounts/decisions; native support for future graph-adjacent queries (recursive CTEs) if Phase 2 needs lightweight graph features before a full GNN |
| Frontend | React (or Streamlit for faster MVP) | Dashboard + detail view are standard CRUD-style screens; no requirement demands a heavier framework |
| Deployment | Render / Railway (free tier) | Sufficient for an academic demo; no production-scale infra needed |

*Reviewer note:* No microservices, no Kafka, no Kubernetes in the MVP — none of the four locked requirements need them. If challenged in review: "the architecture is intentionally monolithic for the MVP because a single-service FastAPI app fully satisfies FR-01–04; distributed infrastructure would add operational complexity without functional benefit at this scale."

---

## 8. Software Requirements Specification (SRS)

### 8.1 Functional Requirements

**FR-01 — Transaction Risk Detection**
- Actor: System
- Trigger: New transaction received
- Flow: System extracts transaction features → XGBoost model calculates a risk score (0–1) → if score exceeds configured threshold, transaction is flagged
- Output: Transaction record updated with `risk_score`, `is_flagged`

**FR-02 — Risk-Prioritized Dashboard**
- Actor: Fraud Analyst
- Flow: Analyst opens dashboard → system queries flagged transactions → returns list sorted descending by `risk_score` → high-risk transactions (above a second, higher threshold) are visually highlighted
- Output: Ranked, highlighted list of open alerts

**FR-03 — Transaction Investigation**
- Actor: Fraud Analyst
- Flow: Analyst selects a flagged transaction → system returns transaction details, risk score, and top contributing risk factors (derived via SHAP on the XGBoost prediction)
- Output: Transaction detail view
- *Note: the risk-factor breakdown is included here because FR-04 (decision) is not meaningfully possible without it — an analyst cannot investigate a bare number.*

**FR-04 — Investigation Decision**
- Actor: Fraud Analyst
- Flow: Analyst reviews investigation → selects decision (Fraud / Legitimate / Escalate) → optionally adds a note → system records decision, analyst ID, and timestamp
- Output: Investigation record created; transaction status updated

### 8.2 Non-Functional Requirements

| ID | Requirement | Rationale |
|---|---|---|
| NFR-01 | Risk scoring must complete in under ~1 second per transaction | FR-01 must not create a backlog faster than it clears one; keeps the system usable for near-real-time ingestion |
| NFR-02 | Every flagged transaction must include a human-readable risk reason, not only a numeric score | Directly required to make FR-03 usable — an unexplained score is not investigable |
| NFR-03 | Risk score, threshold, and evaluation must use precision/recall/PR-AUC — never raw accuracy — as the reported metric | The dataset is highly imbalanced (fraud is a small minority class); accuracy is misleading and would misrepresent model quality |
| NFR-04 | System must record every analyst decision with a timestamp and analyst identity | Basic auditability — a fraud investigation record with no accountability trail is not realistic for this domain, even in an academic MVP |
| NFR-05 | Database schema must accommodate an `account_id`-linked transaction graph without restructuring existing tables | Enables Phase 2 (GNN) to be added additively, not as a redesign |

---

## 9. UML Diagrams

### 9.1 Use Case Diagram

```mermaid
graph LR
    Analyst((Fraud Analyst))
    System((Scoring System))

    Analyst --> UC1[View Risk-Ranked Dashboard]
    Analyst --> UC2[Investigate Transaction]
    Analyst --> UC3[Record Decision]
    System --> UC0[Score & Flag Transaction]

    UC2 -.includes.-> UC4[View Risk Factors]
```

### 9.2 Sequence Diagram — MVP End-to-End Flow

```mermaid
sequenceDiagram
    participant T as Transaction Source
    participant S as Scoring Service (XGBoost)
    participant DB as Database
    participant A as Fraud Analyst
    participant UI as Dashboard/Detail UI

    T->>S: New transaction
    S->>S: Calculate risk_score
    S->>DB: Store transaction + risk_score + is_flagged
    A->>UI: Open dashboard
    UI->>DB: Query flagged transactions, sorted by risk_score
    DB-->>UI: Ranked list
    A->>UI: Select transaction
    UI->>DB: Fetch transaction + risk factors
    DB-->>UI: Details + SHAP risk factors
    A->>UI: Submit decision (Fraud/Legitimate/Escalate)
    UI->>DB: Store investigation record
```

---

## 10. ER Diagram

```mermaid
erDiagram
    ACCOUNT ||--o{ TRANSACTION : "sends/receives"
    TRANSACTION ||--o| INVESTIGATION : "reviewed via"
    ANALYST ||--o{ INVESTIGATION : "performs"

    ACCOUNT {
        string account_id PK
        string account_type
        datetime created_at
    }

    TRANSACTION {
        string transaction_id PK
        string sender_account_id FK
        string receiver_account_id FK
        decimal amount
        datetime timestamp
        string transaction_type
        float risk_score
        boolean is_flagged
        string risk_reason
    }

    INVESTIGATION {
        string investigation_id PK
        string transaction_id FK
        string analyst_id FK
        string decision
        string note
        datetime decided_at
    }

    ANALYST {
        string analyst_id PK
        string name
    }
```

*Reviewer note:* `ACCOUNT` is modeled as a first-class entity now — not because Phase 1 needs account-level queries, but because `TRANSACTION.sender_account_id` / `receiver_account_id` are exactly the edges a Phase 2 graph needs. This satisfies NFR-05 without adding any Phase 1 build work.

---

## 11. Database Design

**Tables (PostgreSQL):**

```sql
CREATE TABLE account (
    account_id      VARCHAR PRIMARY KEY,
    account_type    VARCHAR,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE transaction (
    transaction_id      VARCHAR PRIMARY KEY,
    sender_account_id   VARCHAR REFERENCES account(account_id),
    receiver_account_id VARCHAR REFERENCES account(account_id),
    amount              DECIMAL(14,2) NOT NULL,
    timestamp            TIMESTAMP NOT NULL,
    transaction_type     VARCHAR,
    risk_score           FLOAT,
    is_flagged           BOOLEAN DEFAULT FALSE,
    risk_reason           TEXT
);

CREATE TABLE analyst (
    analyst_id   VARCHAR PRIMARY KEY,
    name         VARCHAR NOT NULL
);

CREATE TABLE investigation (
    investigation_id  VARCHAR PRIMARY KEY,
    transaction_id    VARCHAR REFERENCES transaction(transaction_id),
    analyst_id        VARCHAR REFERENCES analyst(analyst_id),
    decision          VARCHAR CHECK (decision IN ('Fraud','Legitimate','Escalate')),
    note              TEXT,
    decided_at        TIMESTAMP DEFAULT NOW()
);
```

**Design decisions:**
- `risk_reason` stored as text on `transaction` rather than a separate table — one score, one explanation, per transaction; no need for a join for something read every time the transaction is read (satisfies NFR-02 directly).
- `investigation` is separate from `transaction` (not just extra columns on it) because a transaction has exactly one score but should have an auditable decision record — this also cleanly supports NFR-04.
- No `graph_embedding` or `network_score` column added yet — deliberately withheld until Phase 2 is actually built, so the schema doesn't carry unused fields during Week 2 review.

---

## 12. System Architecture Diagram

```mermaid
graph TD
    subgraph Ingestion
        T[Incoming Transaction]
    end

    subgraph Scoring Service
        X[XGBoost Model]
        SH[SHAP Explainer]
    end

    subgraph Data Layer
        DB[(PostgreSQL:<br/>account, transaction,<br/>investigation, analyst)]
    end

    subgraph Application Layer
        API[FastAPI Backend]
    end

    subgraph Presentation
        DASH[Analyst Dashboard]
        DET[Transaction Detail View]
    end

    T --> X
    X --> SH
    X --> DB
    SH --> DB
    DB --> API
    API --> DASH
    API --> DET
    DASH --> API
    DET --> API
    API --> DB
```

**Phase 2 addition (shown for planning, not built now):**

```
Historical Transactions → Graph Builder → GNN → Account Embeddings → stored in DB
                                                        ↓
                                        Combined with XGBoost score at scoring time
```

*Reviewer note:* the architecture is intentionally a single FastAPI service, not split into microservices — every one of FR-01–04 is satisfied by one application talking to one database. Splitting this into separate services now would be solving a scaling problem this academic project doesn't have.

---

## 13. Consistency Check

| Requirement | Reflected in DB | Reflected in Architecture | Reflected in UML |
|---|---|---|---|
| FR-01 | `transaction.risk_score`, `is_flagged` | Scoring Service | Sequence diagram step 1–2 |
| FR-02 | Query: flagged transactions sorted by `risk_score` | API → Dashboard | Use case: View Dashboard |
| FR-03 | `transaction.risk_reason` | SHAP Explainer → DB → Detail View | Use case: Investigate Transaction |
| FR-04 | `investigation` table | API writes to DB | Use case: Record Decision |

Every requirement has a corresponding field, service, and diagram element — no orphaned requirements, no undocumented features.

---
