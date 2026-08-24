# Fraud Investigation Support System — System Modules

Nine modules, organized by system responsibility rather than build sequence. Each maps back to a specific functional requirement — no module exists without a requirement driving it.

---

## Module 1 — Data Ingestion

**Purpose:** Bring transactions into the system for scoring.

**Responsibilities:** Read transactions from the source dataset (batch, or simulated stream); validate basic structure (required fields present, correct types) before passing downstream.

**Inputs:** Raw transaction records (CSV / simulated stream)

**Outputs:** Validated transaction objects, ready for feature engineering

**Dependencies:** None (entry point of the pipeline)

**APIs/Endpoints:** None (internal pipeline stage, or a future `POST /transactions/ingest` if streaming is added)

**Build Now / Later:** **Build now** — nothing downstream functions without it

---

## Module 2 — Feature Engineering

**Purpose:** Convert a raw transaction into the numeric feature vector the model expects.

**Responsibilities:** Derive features (transaction amount, time-based features, sender/receiver history if available); ensure feature computation is identical between training and live scoring, to avoid train/serve skew.

**Inputs:** Validated transaction object (Module 1)

**Outputs:** Feature vector

**Dependencies:** Module 1

**APIs/Endpoints:** None (internal)

**Build Now / Later:** **Build now** — required for FR-01

---

## Module 3 — Risk Scoring (XGBoost)

**Purpose:** Produce a fraud risk score for a transaction — the core of FR-01.

**Responsibilities:** Load the trained XGBoost model; score incoming feature vectors; apply the configured threshold to determine `is_flagged`.

**Inputs:** Feature vector (Module 2)

**Outputs:** `risk_score` (0–1), `is_flagged` (boolean)

**Dependencies:** Module 2; a trained model artifact (produced offline, not at request time)

**APIs/Endpoints:** None directly (consumed internally by the API layer)

**Build Now / Later:** **Build now** — this is FR-01 itself

---

## Module 4 — Explainability (SHAP)

**Purpose:** Generate the reason a transaction was flagged — required for FR-03 and NFR-02.

**Responsibilities:** Run SHAP on the model's prediction for a given transaction; convert raw feature contributions into short, human-readable reason tags.

**Inputs:** Feature vector and model output (Module 3)

**Outputs:** `risk_reason` (short text/tags)

**Dependencies:** Module 3

**APIs/Endpoints:** None directly (data feeds into persistence and the detail view)

**Build Now / Later:** **Build now** — without it, FR-03 is a bare number with nothing to investigate

---

## Module 5 — Persistence

**Purpose:** Store transactions, scores, reasons, and investigation outcomes durably.

**Responsibilities:** Write scored transactions to the `transaction` table; write analyst decisions to the `investigation` table; maintain referential integrity with `account` and `analyst`.

**Inputs:** Scored transaction (Modules 3–4); investigation decisions (Module 8)

**Outputs:** Queryable, durable records in PostgreSQL

**Dependencies:** Modules 1–4 for writes; consumed by Module 6 for reads

**APIs/Endpoints:** None directly (database layer beneath the API)

**Build Now / Later:** **Build now** — every other module depends on it either writing to or reading from here

---

## Module 6 — Backend API

**Purpose:** Expose stored data to the frontend — the connective layer for FR-02, FR-03, FR-04.

**Responsibilities:** Serve ranked alert lists; serve individual transaction details; accept and persist investigation decisions.

**Inputs:** Queries and requests from the frontend

**Outputs:** JSON responses

**Dependencies:** Module 5

**APIs/Endpoints:**
- `GET /alerts` — ranked, filterable list of flagged transactions
- `GET /transactions/{id}` — transaction detail, score, and risk reasons
- `POST /investigations` — record a decision

**Build Now / Later:** **Build now** — the frontend cannot function without it

---

## Module 7 — Dashboard UI

**Purpose:** Let the analyst see and prioritize flagged transactions — FR-02.

**Responsibilities:** Render the risk-ranked alert list; visually highlight high-risk items; support filtering (All/High/Medium) and search.

**Inputs:** `GET /alerts` response (Module 6)

**Outputs:** Rendered dashboard screen

**Dependencies:** Module 6

**APIs/Endpoints:** Consumes Module 6's `GET /alerts`

**Build Now / Later:** **Build now** — FR-02 has no other delivery mechanism

---

## Module 8 — Investigation & Decision UI

**Purpose:** Let the analyst review a transaction and record a decision — FR-03 and FR-04.

**Responsibilities:** Render transaction details, score, and risk reasons; capture the analyst's decision (Fraud/Legitimate/Escalate) and optional note; submit to the backend.

**Inputs:** `GET /transactions/{id}` response (Module 6)

**Outputs:** `POST /investigations` request (Module 6); rendered detail/decision screen

**Dependencies:** Module 6

**APIs/Endpoints:** Consumes Module 6's `GET /transactions/{id}` and `POST /investigations`

**Build Now / Later:** **Build now** — FR-03 and FR-04 have no other delivery mechanism

---

## Module 9 — Network Intelligence (GNN)

**Purpose:** Detect coordinated, multi-account fraud patterns invisible to a transaction-level model — the Phase 2 differentiator.

**Responsibilities:** Build an account/transaction graph from historical data; train a GNN to produce account risk embeddings; combine network risk with the transaction-level score at scoring time.

**Inputs:** Historical transactions (batch, offline); account relationships

**Outputs:** Account embeddings; combined risk score (Phase 2 extension to Module 3's output)

**Dependencies:** Requires Modules 1–6 already working, since it extends the existing scoring path rather than replacing it

**APIs/Endpoints:** Extends Module 6's existing endpoints with an additional score component; no new endpoint required

**Build Now / Later:** **Build later** — not required by FR-01–04; no MVP requirement depends on it. Documented now so the schema (Module 5) doesn't need to be redesigned when this is built.

---

## Summary

| Build Now (MVP-critical) | Build Later (Phase 2) |
|---|---|
| Data Ingestion | Network Intelligence (GNN) |
| Feature Engineering | |
| Risk Scoring (XGBoost) | |
| Explainability (SHAP) | |
| Persistence | |
| Backend API | |
| Dashboard UI | |
| Investigation & Decision UI | |

Eight of nine modules are required to satisfy FR-01–04 and must all be working for the MVP to function end-to-end. Module 9 is the only one that can be deferred without breaking a locked requirement.
