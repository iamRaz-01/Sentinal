"""
Unit tests for Module 2 (Feature Engineering).
"""

from datetime import datetime, timezone, timedelta
import os
import sys
import unittest
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from sentinal.ingestion import ValidatedTransaction
from sentinal.features import FeaturePipeline, FEATURE_COLUMNS


class TestFeatures(unittest.TestCase):
    def test_feature_columns_and_ordering(self):
        pipeline = FeaturePipeline()
        txn = ValidatedTransaction(
            sender_account_id="AC1",
            receiver_account_id="AC2",
            amount=100.0,
            currency="USD",
            transaction_type="transfer",
            channel="online",
            occurred_at=datetime(2026, 8, 24, 14, 30, tzinfo=timezone.utc),
            status="completed",
        )

        df_feat = pipeline.transform_single(txn)
        self.assertEqual(list(df_feat.columns), FEATURE_COLUMNS)
        self.assertEqual(len(df_feat), 1)

    def test_temporal_and_numeric_features(self):
        pipeline = FeaturePipeline()
        dt = datetime(2026, 8, 23, 23, 15, tzinfo=timezone.utc)
        txn = ValidatedTransaction(
            sender_account_id="AC1",
            receiver_account_id="AC2",
            amount=99.0,
            currency="USD",
            transaction_type="withdrawal",
            channel="atm",
            occurred_at=dt,
            status="completed",
        )

        df_feat = pipeline.transform_single(txn)
        row = df_feat.iloc[0]

        self.assertEqual(row["amount"], 99.0)
        self.assertAlmostEqual(row["amount_log"], np.log1p(99.0), places=4)
        self.assertEqual(row["hour_of_day"], 23)
        self.assertEqual(row["day_of_week"], 6)
        self.assertEqual(row["is_weekend"], 1)
        self.assertEqual(row["is_night"], 1)
        self.assertEqual(row["type_withdrawal"], 1)
        self.assertEqual(row["type_transfer"], 0)
        self.assertEqual(row["channel_atm"], 1)
        self.assertEqual(row["channel_online"], 0)

    def test_historical_context_aggregations(self):
        pipeline = FeaturePipeline()
        base_time = datetime(2026, 8, 24, 12, 0, tzinfo=timezone.utc)

        past_1 = ValidatedTransaction(
            sender_account_id="AC100",
            receiver_account_id="AC999",
            amount=100.0,
            currency="USD",
            transaction_type="payment",
            channel="pos",
            occurred_at=base_time - timedelta(hours=5),
            status="completed",
        )
        past_2 = ValidatedTransaction(
            sender_account_id="AC100",
            receiver_account_id="AC998",
            amount=200.0,
            currency="USD",
            transaction_type="payment",
            channel="pos",
            occurred_at=base_time - timedelta(hours=2),
            status="completed",
        )

        current_txn = ValidatedTransaction(
            sender_account_id="AC100",
            receiver_account_id="AC997",
            amount=450.0,
            currency="USD",
            transaction_type="transfer",
            channel="online",
            occurred_at=base_time,
            status="completed",
        )

        df_feat = pipeline.transform_single(current_txn, history=[past_1, past_2])
        row = df_feat.iloc[0]

        self.assertEqual(row["sender_txn_count_24h"], 2)
        self.assertEqual(row["sender_avg_amount_24h"], 150.0)
        self.assertEqual(row["sender_amount_ratio_24h"], 3.0)

    def test_batch_transform_consistency(self):
        pipeline = FeaturePipeline()
        base_time = datetime(2026, 8, 24, 10, 0, tzinfo=timezone.utc)

        t1 = ValidatedTransaction(
            sender_account_id="A1", receiver_account_id="B1", amount=50.0,
            currency="USD", transaction_type="deposit", channel="branch",
            occurred_at=base_time, status="completed"
        )
        t2 = ValidatedTransaction(
            sender_account_id="A1", receiver_account_id="B2", amount=150.0,
            currency="USD", transaction_type="withdrawal", channel="atm",
            occurred_at=base_time + timedelta(minutes=30), status="completed"
        )

        df_batch = pipeline.transform_batch([t1, t2], compute_rolling_history=True)
        self.assertEqual(len(df_batch), 2)
        self.assertEqual(df_batch.iloc[0]["sender_txn_count_24h"], 0)
        self.assertEqual(df_batch.iloc[1]["sender_txn_count_24h"], 1)
        self.assertEqual(df_batch.iloc[1]["sender_avg_amount_24h"], 50.0)
        self.assertEqual(df_batch.iloc[1]["sender_amount_ratio_24h"], 3.0)


if __name__ == "__main__":
    unittest.main()

