# Fraud Investigation Support System — API Specification

Every endpoint here traces to one of the four locked functional requirements. No endpoint exists without a requirement driving it. Base path: `/api/v1`.

**Scoping note:** No authentication/login endpoints are included. FR-01–04 never specified multi-analyst access control, so a full auth system would be scope creep. For the MVP, `analyst_id` is passed directly in the decision payload (a single hardcoded analyst is sufficient for a solo academic demo). If Phase 2 ever needs multi-analyst coordination, auth becomes its own scoped addition then — not now.

---

## 1. `POST /transactions/score`

**Maps to:** FR-01 (Transaction Risk Detection)
**Module:** Data Ingestion → Feature Engineering → Risk Scoring → Explainability → Persistence

**Purpose:** Submit a transaction for scoring. In production this would be triggered by a real transaction stream; for the MVP demo, this endpoint simulates that trigger.

**Request body:**
```json
{
  "sender_account_id": "AC1042",
  "receiver_account_id": "AC8891",
  "amount": 45000.00,
  "timestamp": "2026-08-24T10:15:00Z",
  "transaction_type": "transfer"
}
```

**Response `201 Created`:**
```json
{
  "transaction_id": "TXN10293",
  "risk_score": 0.85,
  "is_flagged": true,
  "risk_reason": ["large amount", "rapid transfer"]
}
```

**Error cases:** `400` — missing/invalid fields (e.g. negative amount, unknown account type)

---

## 2. `GET /alerts`

**Maps to:** FR-02 (Risk-Prioritized Dashboard)
**Module:** Backend API → Dashboard UI

**Purpose:** Return flagged transactions, ranked by risk score, for the analyst's queue.

**Query parameters:**
| Param | Type | Default | Notes |
|---|---|---|---|
| `risk_level` | string | `all` | `all` \| `high` \| `medium` |
| `search` | string | — | matches transaction ID |
| `limit` | int | 20 | page size |
| `offset` | int | 0 | pagination |

**Response `200 OK`:**
```json
{
  "total": 47,
  "alerts": [
    {
      "transaction_id": "TXN10293",
      "timestamp": "2026-08-24T10:15:00Z",
      "amount": 45000.00,
      "sender_masked": "AC***42",
      "receiver_masked": "AC***91",
      "risk_score": 0.85,
      "risk_level": "high",
      "flag_reason_tags": ["large amount"]
    }
  ]
}
```

---

## 3. `GET /transactions/{transaction_id}`

**Maps to:** FR-03 (Transaction Investigation)
**Module:** Backend API → Investigation & Decision UI

**Purpose:** Return full transaction detail, risk score, and reasoning for a single flagged transaction. Includes any existing investigation record, so the analyst (or reviewer re-checking) can see if it's already been decided.

**Response `200 OK`:**
```json
{
  "transaction_id": "TXN10293",
  "sender_account_id": "AC1042",
  "receiver_account_id": "AC8891",
  "amount": 45000.00,
  "timestamp": "2026-08-24T10:15:00Z",
  "transaction_type": "transfer",
  "risk_score": 0.85,
  "risk_level": "high",
  "risk_reason": ["large amount", "rapid transfer"],
  "investigation": null
}
```

If already investigated, `investigation` is populated:
```json
"investigation": {
  "investigation_id": "INV0042",
  "analyst_id": "AN001",
  "decision": "Escalate",
  "note": "Needs secondary review",
  "decided_at": "2026-08-24T11:02:00Z"
}
```

**Error cases:** `404` — transaction ID not found

---

## 4. `POST /investigations`

**Maps to:** FR-04 (Investigation Decision)
**Module:** Backend API → Investigation & Decision UI → Persistence

**Purpose:** Record the analyst's final decision on a flagged transaction.

**Request body:**
```json
{
  "transaction_id": "TXN10293",
  "analyst_id": "AN001",
  "decision": "Escalate",
  "note": "Needs secondary review"
}
```

`decision` must be one of: `Fraud`, `Legitimate`, `Escalate`

**Response `201 Created`:**
```json
{
  "investigation_id": "INV0042",
  "transaction_id": "TXN10293",
  "decided_at": "2026-08-24T11:02:00Z"
}
```

**Error cases:**
- `400` — `decision` not one of the three valid values
- `404` — `transaction_id` does not exist
- `409` — transaction already has a recorded investigation (prevents accidental duplicate decisions)

---

## 5. `GET /health`

**Maps to:** No functional requirement — standard operational practice, not scope creep. Confirms the API and database connection are alive; used for deployment checks in Module 8 (Integration & Deployment).

**Response `200 OK`:**
```json
{ "status": "ok", "db": "connected" }
```

---

## Summary Table

| Method & Path | Requirement | Purpose |
|---|---|---|
| `POST /transactions/score` | FR-01 | Score a new transaction, flag if above threshold |
| `GET /alerts` | FR-02 | Risk-ranked list for the dashboard |
| `GET /transactions/{id}` | FR-03 | Transaction detail + risk reasoning |
| `POST /investigations` | FR-04 | Record analyst decision |
| `GET /health` | — (operational) | Deployment/liveness check |

Five endpoints total. Every one is either directly required by a locked FR or a standard operational necessity — nothing added because it "might be useful later." Endpoints for accounts, analysts, or model retraining are deliberately absent; they belong to Phase 2/3 scope, not this MVP.
