"""
Demo Script for Sentinal Module 1 (Data Ingestion) & Module 2 (Feature Engineering)
Processes raw incoming transactions (single payloads and batch CSV records),
validates them, and transforms valid transactions into ML feature vectors.
"""

from datetime import datetime, timezone, timedelta
import json
import sys
import os

# Add src directory to path if running directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from sentinal.ingestion import TransactionIngestor, TransactionValidationError
from sentinal.features import FeaturePipeline


def main():
    print("=" * 70)
    print(" SENTINAL — MODULE 1 (INGESTION) & MODULE 2 (FEATURE ENGINEERING) DEMO")
    print("=" * 70)

    ingestor = TransactionIngestor()
    pipeline = FeaturePipeline()

    # -------------------------------------------------------------
    # 1. Single Transaction Ingestion & Validation (Simulated API/Stream)
    # -------------------------------------------------------------
    print("\n--- [Step 1] Ingesting Single API Payload (FR-01 Trigger) ---")
    raw_api_payload = {
        "sender_account_id": "AC1042",
        "receiver_account_id": "AC8891",
        "amount": 45000.00,
        "currency": "USD",
        "transaction_type": "transfer",
        "channel": "online",
        "merchant_name": "CryptoExchange",
        "device_fingerprint": "dev_fp_9823",
        "timestamp": "2026-08-24T10:15:00Z",
    }
    print(f"Raw Input Payload:\n{json.dumps(raw_api_payload, indent=2)}")

    try:
        validated_txn = ingestor.validate_single(raw_api_payload)
        print(f"\n[Module 1 SUCCESS] Transaction validated successfully!")
        print(f"  Sender: {validated_txn.sender_account_id}")
        print(f"  Receiver: {validated_txn.receiver_account_id}")
        print(f"  Amount: {validated_txn.amount} {validated_txn.currency}")
        print(f"  Occurred At: {validated_txn.occurred_at}")
    except TransactionValidationError as e:
        print(f"\n[Module 1 ERROR] {e}")
        return

    # -------------------------------------------------------------
    # 2. Single Transaction Feature Engineering (Module 2)
    # -------------------------------------------------------------
    print("\n--- [Step 2] Feature Engineering for Single Payload ---")
    # Simulate prior 24h account history
    past_txn_1 = ingestor.validate_single({
        "sender_account_id": "AC1042",
        "receiver_account_id": "AC9999",
        "amount": 1000.00,
        "transaction_type": "payment",
        "channel": "mobile",
        "occurred_at": "2026-08-24T05:00:00Z",
    })
    
    feature_df = pipeline.transform_single(validated_txn, history=[past_txn_1])
    print("\n[Module 2 SUCCESS] Derived Feature Vector (1x19 DataFrame):")
    for col in feature_df.columns:
        print(f"  - {col:<25}: {feature_df.iloc[0][col]}")

    # -------------------------------------------------------------
    # 3. Batch Transaction Ingestion & Validation (Simulated CSV Ingestion)
    # -------------------------------------------------------------
    print("\n--- [Step 3] Ingesting Batch Stream with Invalid Records ---")
    batch_raw = [
        # Valid transaction 1
        {
            "sender_account_id": "AC5001",
            "receiver_account_id": "AC6001",
            "amount": 120.50,
            "transaction_type": "payment",
            "channel": "pos",
            "occurred_at": "2026-08-24T11:00:00Z",
        },
        # Invalid transaction: negative amount
        {
            "sender_account_id": "AC5002",
            "receiver_account_id": "AC6002",
            "amount": -50.00,
            "transaction_type": "transfer",
            "channel": "online",
        },
        # Invalid transaction: identical sender and receiver
        {
            "sender_account_id": "AC5003",
            "receiver_account_id": "AC5003",
            "amount": 300.00,
            "transaction_type": "withdrawal",
            "channel": "atm",
        },
        # Valid transaction 2
        {
            "sender_account_id": "AC5001",
            "receiver_account_id": "AC7001",
            "amount": 2500.00,
            "transaction_type": "transfer",
            "channel": "online",
            "occurred_at": "2026-08-24T12:30:00Z",
        },
    ]

    batch_result = ingestor.validate_batch(batch_raw)
    print(f"\n[Module 1 Batch Ingestion Results]")
    print(f"  Total Processed: {batch_result.total_processed}")
    print(f"  Valid Records  : {len(batch_result.valid_records)}")
    print(f"  Invalid Errors : {len(batch_result.errors)}")
    print(f"  Success Rate   : {batch_result.success_rate:.2f}%")

    if batch_result.errors:
        print("\n  Sample Isolated Validation Errors:")
        for err in batch_result.errors:
            print(f"   * Row #{err['index']}: {err['error']}")

    # -------------------------------------------------------------
    # 4. Batch Feature Engineering (Module 2)
    # -------------------------------------------------------------
    print("\n--- [Step 4] Batch Feature Transformation (Zero Train/Serve Skew) ---")
    batch_features_df = pipeline.transform_batch(batch_result.valid_records)
    print(f"\n[Module 2 SUCCESS] Generated Batch Feature Matrix shape: {batch_features_df.shape}")
    print("\nFeature Matrix Summary:")
    print(batch_features_df[["amount", "amount_log", "hour_of_day", "is_weekend", "type_transfer", "channel_online", "sender_amount_ratio_24h"]].to_string())

    print("\n" + "=" * 70)
    print(" DEMO COMPLETED SUCCESSFULLY: MODULE 1 & MODULE 2 FUNCTIONAL & READY")
    print("=" * 70)


if __name__ == "__main__":
    main()
