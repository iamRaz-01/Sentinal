"""
Unit tests for Module 1 (Data Ingestion).
"""

from datetime import datetime, timezone
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from sentinal.ingestion import (
    TransactionInput,
    ValidatedTransaction,
    TransactionValidationError,
    TransactionIngestor,
)


class TestIngestion(unittest.TestCase):
    def test_valid_transaction_single(self):
        ingestor = TransactionIngestor()
        raw = {
            "sender_account_id": "AC1042",
            "receiver_account_id": "AC8891",
            "amount": 45000.00,
            "currency": "USD",
            "transaction_type": "transfer",
            "channel": "online",
            "occurred_at": "2026-08-24T10:15:00Z",
        }
        validated = ingestor.validate_single(raw)
        self.assertIsInstance(validated, ValidatedTransaction)
        self.assertEqual(validated.sender_account_id, "AC1042")
        self.assertEqual(validated.receiver_account_id, "AC8891")
        self.assertEqual(validated.amount, 45000.00)
        self.assertEqual(validated.transaction_type, "transfer")
        self.assertEqual(validated.channel, "online")

    def test_invalid_negative_amount(self):
        ingestor = TransactionIngestor()
        raw = {
            "sender_account_id": "AC1042",
            "receiver_account_id": "AC8891",
            "amount": -500.00,
            "transaction_type": "transfer",
        }
        with self.assertRaises(TransactionValidationError) as ctx:
            ingestor.validate_single(raw)
        self.assertIn("amount must be strictly positive", str(ctx.exception))

    def test_invalid_same_sender_receiver(self):
        ingestor = TransactionIngestor()
        raw = {
            "sender_account_id": "AC1042",
            "receiver_account_id": "AC1042",
            "amount": 100.00,
            "transaction_type": "transfer",
        }
        with self.assertRaises(TransactionValidationError) as ctx:
            ingestor.validate_single(raw)
        self.assertIn("must not be identical", str(ctx.exception))

    def test_invalid_transaction_type(self):
        ingestor = TransactionIngestor()
        raw = {
            "sender_account_id": "AC1042",
            "receiver_account_id": "AC8891",
            "amount": 100.00,
            "transaction_type": "invalid_type",
        }
        with self.assertRaises(TransactionValidationError) as ctx:
            ingestor.validate_single(raw)
        self.assertIn("invalid transaction_type", str(ctx.exception))

    def test_batch_validation(self):
        ingestor = TransactionIngestor()
        records = [
            {
                "sender_account_id": "AC100",
                "receiver_account_id": "AC200",
                "amount": 150.00,
                "transaction_type": "transfer",
                "channel": "mobile",
            },
            {
                "sender_account_id": "AC100",
                "receiver_account_id": "AC100",
                "amount": 200.00,
                "transaction_type": "withdrawal",
            },
            {
                "sender_account_id": "AC300",
                "receiver_account_id": "AC400",
                "amount": 0.0,
                "transaction_type": "deposit",
            },
        ]

        result = ingestor.validate_batch(records)
        self.assertEqual(len(result.valid_records), 1)
        self.assertEqual(len(result.errors), 2)
        self.assertEqual(result.total_processed, 3)
        self.assertEqual(round(result.success_rate, 2), 33.33)
        self.assertEqual(result.valid_records[0].sender_account_id, "AC100")

    def test_csv_validation(self):
        ingestor = TransactionIngestor()
        csv_content = """sender_account_id,receiver_account_id,amount,transaction_type,channel,occurred_at
AC1,AC2,100.00,transfer,online,2026-08-24T10:00:00Z
AC3,AC4,250.50,payment,pos,2026-08-24T11:00:00Z
"""
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv") as tmp:
            tmp.write(csv_content)
            tmp_path = tmp.name

        try:
            result = ingestor.validate_csv(tmp_path)
            self.assertEqual(len(result.valid_records), 2)
            self.assertEqual(len(result.errors), 0)
            self.assertEqual(result.valid_records[0].sender_account_id, "AC1")
            self.assertEqual(result.valid_records[1].amount, 250.50)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


if __name__ == "__main__":
    unittest.main()

